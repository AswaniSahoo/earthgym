"""A verifiers rollout of ibtracs-storm-v1's tools mode end to end with no model (review of
phase 6, M5): vf-eval against a scripted OpenAI-style endpoint on 127.0.0.1 that first calls
the query tool and then answers. It covers what the gold check does not: the interception
server, the tool server's launch, the tool call's round trip and the reward on the final
reply."""

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ibtracs_storm_v1 import contract
from ibtracs_storm_v1 import taskset as ts

SQL = "SELECT count(*) FROM track"


def scripted(seen: list) -> ThreadingHTTPServer:
    """An endpoint that calls `query` once, then replies `ANSWER: 6` once it has the result."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body)
            if body["messages"][-1]["role"] == "tool":
                message, finish = {"role": "assistant", "content": "ANSWER: 6"}, "stop"
            else:
                function = {"name": "query", "arguments": json.dumps({"sql": SQL})}
                call = {"id": "call_1", "type": "function", "function": function}
                message = {"role": "assistant", "content": None, "tool_calls": [call]}
                finish = "tool_calls"
            usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            head = {"id": "scripted", "created": 0, "model": body.get("model", "scripted")}
            if body.get("stream"):  # the client streams: one delta, the finish, the usage
                delta = message | {
                    "tool_calls": [c | {"index": 0} for c in message.get("tool_calls", [])]
                }
                chunks = [
                    {"choices": [{"index": 0, "delta": delta, "finish_reason": None}]},
                    {"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
                    {"choices": [], "usage": usage},
                ]
                events = [
                    f"data: {json.dumps(head | {'object': 'chat.completion.chunk'} | c)}\n\n"
                    for c in chunks
                ]
                data, kind = ("".join(events) + "data: [DONE]\n\n").encode(), "text/event-stream"
            else:
                choice = {"index": 0, "message": message, "finish_reason": finish}
                reply = head | {"object": "chat.completion", "choices": [choice], "usage": usage}
                data, kind = json.dumps(reply).encode(), "application/json"
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_a_verifiers_tools_rollout_queries_its_own_storm_and_pays_the_final_reply(tmp_path):
    seen = []
    server = scripted(seen)
    vf_eval = Path(sys.executable).with_name("vf-eval")
    command = [str(vf_eval), "ibtracs-storm-v1", "--no-push", "-m", "scripted", "-n", "1"]
    command += ["-r", "1", "--client.base-url", f"http://127.0.0.1:{server.server_port}/v1"]
    command += ["--client.api-key-var", "SCRIPTED_KEY", "--env.taskset.tools", "true"]
    command += ["--env.agent.runtime.type", "subprocess", "--env.agent.max-turns", "14"]
    try:
        done = subprocess.run(
            command,
            cwd=tmp_path,
            env=os.environ | {"SCRIPTED_KEY": "unused"},
            capture_output=True,
            text=True,
            timeout=300,
        )
    finally:
        server.shutdown()
    assert done.returncode == 0, done.stdout[-2000:] + done.stderr[-2000:]
    (traces,) = tmp_path.glob("outputs/*/traces.jsonl")
    (line,) = traces.read_text("utf-8").splitlines()
    trace = json.loads(line)["traces"]
    trace = trace[0] if isinstance(trace, list) else trace
    data = trace["task"]["data"]
    row = next(r for r in ts.records() if r["id"] == data["id"])
    # the model was offered the one tool, and the tool answered from this task's own rows
    assert [t["function"]["name"] for t in seen[0]["tools"]] == ["query"]
    replies = [m for s in seen for m in s["messages"] if m["role"] == "tool"]
    content = replies[0]["content"] if replies else ""
    text = content if isinstance(content, str) else " ".join(p.get("text", "") for p in content)
    assert [m["role"] for m in seen[-1]["messages"]] == ["user", "assistant", "tool"]
    assert len(replies) == 1 and f"count(*)\n{len(row['rows'])}" in text
    paid = trace["rewards"]["exact"]["score"]
    assert paid == contract.reward(data["question"], 6.0, row["key"])
