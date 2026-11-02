"""Small open-model runs on Kaggle's T4 x2 (decision 0025).

Built by earthgym.kaggle.samples_kernel, which fills CONFIG_JSON. The repo comes from the git
bundle in the earthgym-src dataset and its environment from uv.lock. One worker a GPU: each
starts llama-server for its model (build b11960, decision 0022) and runs every environment as
an Inspect eval set into /kaggle/working/logs, which Kaggle keeps as the kernel's output. An eval
set run again on the same log directory skips what is complete and reruns the rest, so a stopped
session resumes when the next one finds the earlier logs in the earthgym-small-models-logs
dataset. At the deadline the workers interrupt their evals, which then write their logs.
"""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

CONFIG_JSON = "{}"

OUT = Path("/kaggle/working")
WORK = Path("/kaggle/tmp")
START = time.time()
LOCK = threading.Lock()


def note(event: str, **fields) -> None:
    """One line of progress, with the seconds since the start, to progress.jsonl and stdout."""
    line = json.dumps({"seconds": round(time.time() - START, 1), "event": event, **fields})
    with LOCK:
        with open(OUT / "progress.jsonl", "a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line, flush=True)


def fetch(url: str, path: Path, sha256: str) -> None:
    """Download url to path unless it is there, and check its sha256."""
    if not path.exists():
        subprocess.run(["curl", "-fsSL", "--retry", "5", "-o", str(path), url], check=True)
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    if digest.hexdigest() != sha256:
        raise ValueError(f"{path.name}: sha256 {digest.hexdigest()}, not {sha256}")


def find(name: str) -> Path | None:
    """A file or folder under /kaggle/input, wherever Kaggle mounted its dataset."""
    return next(Path("/kaggle/input").rglob(name), None)


def setup(config: dict) -> tuple[Path, Path]:
    """The repo at the config's commit with its locked environment, and llama-server."""
    WORK.mkdir(parents=True, exist_ok=True)
    repo = WORK / "earthgym"
    if not repo.exists():
        subprocess.run(["git", "clone", "-q", str(find("earthgym.bundle")), str(repo)], check=True)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != config["commit"]:
        raise ValueError(f"the bundle holds {head}, not {config['commit']}")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", config["uv"]], check=True)
    env = os.environ | {"UV_CACHE_DIR": str(WORK / "uv-cache")}
    subprocess.run(
        ["uv", "sync", "--locked", "--all-groups", "--python", "3.12"],
        cwd=repo,
        env=env,
        check=True,
    )
    llama = WORK / "llama"
    llama.mkdir(exist_ok=True)
    for asset in config["llama"]:
        tarball = WORK / asset["url"].rsplit("/", 1)[-1]
        fetch(asset["url"], tarball, asset["sha256"])
        subprocess.run(["tar", "-xzf", str(tarball), "-C", str(llama)], check=True)
    server = next(p for p in llama.rglob("llama-server") if p.is_file())
    earlier = find("earthgym-small-models-logs")
    if earlier is not None:  # the logs of the sessions before this one
        shutil.copytree(earlier / "logs", OUT / "logs", dirs_exist_ok=True)
        note("earlier logs", files=len(list((OUT / "logs").rglob("*.eval"))))
    gpus = ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]
    note("set up", gpus=subprocess.run(gpus, capture_output=True, text=True).stdout.strip())
    return repo, server


def worker(w: dict, repo: Path, server: Path, deadline: float) -> None:
    """One model on one GPU: its server, then each environment's eval set, until the deadline."""
    logs = OUT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    model = w["model"]
    gguf = WORK / "models" / w["gguf"]["file"]
    gguf.parent.mkdir(exist_ok=True)
    fetch(w["gguf"]["url"], gguf, w["gguf"]["sha256"])
    env = os.environ | {
        "CUDA_VISIBLE_DEVICES": str(w["gpu"]),
        "LD_LIBRARY_PATH": f"{server.parent}:{os.environ.get('LD_LIBRARY_PATH', '')}",
        "LLAMACPP_BASE_URL": f"http://127.0.0.1:{w['port']}/v1",
        "LLAMACPP_API_KEY": "local",
        "UV_CACHE_DIR": str(WORK / "uv-cache"),
    }
    server_log = logs / f"llama-server-{model}.log"

    def start() -> subprocess.Popen:
        cmd = [str(server), *(str(gguf) if x == "{gguf}" else x for x in w["server"][1:])]
        before = server_log.stat().st_size if server_log.exists() else 0
        with open(server_log, "ab") as log:  # the server keeps its own handle
            p = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(900):
            if p.poll() is not None:
                raise RuntimeError(f"llama-server for {model} exited with {p.returncode}")
            with open(server_log, "rb") as f:
                f.seek(before)
                if b"listening on" in f.read():
                    return p
            time.sleep(1)
        raise TimeoutError(f"llama-server for {model} did not listen")

    srv = start()
    note("server up", model=model, gpu=w["gpu"])
    for name, cmd in w["commands"].items():
        if time.time() > deadline:
            note("not started, past the deadline", model=model, env=name)
            continue
        note("start", model=model, env=name)
        with open(logs / f"inspect-{model}.out", "ab") as out:  # the eval keeps its own handle
            p = subprocess.Popen(cmd, cwd=repo, env=env, stdout=out, stderr=subprocess.STDOUT)
        while p.poll() is None:
            if srv.poll() is not None:
                note("server gone; restarting", model=model)
                srv = start()
            if time.time() > deadline:
                note("deadline: interrupting", model=model, env=name)
                p.send_signal(signal.SIGINT)
                try:
                    p.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    p.kill()
                break
            time.sleep(10)
        note("end", model=model, env=name, code=p.wait())
    srv.terminate()


def main() -> None:
    config = json.loads(CONFIG_JSON)
    OUT.mkdir(parents=True, exist_ok=True)
    note("begin", commit=config["commit"])
    try:
        repo, server = setup(config)
    except BaseException:
        note("failed", error=traceback.format_exc())
        raise
    deadline = START + config["deadline_hours"] * 3600

    def run(w: dict) -> None:
        try:
            worker(w, repo, server, deadline)
        except BaseException:
            note("worker failed", model=w["model"], error=traceback.format_exc())

    threads = [threading.Thread(target=run, args=(w,)) for w in config["workers"]]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    note("done")


if __name__ == "__main__":
    main()
