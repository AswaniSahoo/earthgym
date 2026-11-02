"""The tools-mode server started the way verifiers 0.4.0 starts it for a rollout: as
`python -m ibtracs_storm_v1.taskset`, fed one task over a stand-in /task channel, and queried
with verifiers' own MCP client (review of phase 6, M5). Local ports only."""

import asyncio
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import AsyncExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from ibtracs_storm_v1 import taskset as ts
from verifiers.v1.harnesses.utils.mcp import call_mcp, connect_mcp


@pytest.fixture
def channel():
    """A stand-in for the rollout's state channel: every GET gets one tools-mode task's data."""
    row = next(r for r in ts.records() if r["question"] == "hurricane_hours")
    data = ts.to_data(row, tools=True)
    cls = f"{type(data).__module__}:{type(data).__qualname__}"
    payload = json.dumps({"cls": cls, "task": data.model_dump_json()}).encode()
    asked = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            asked.append(self.path)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_port, row, asked
    server.shutdown()


def wait_for_port(port_file, server) -> int:
    for _ in range(240):
        if port_file.exists() and (text := port_file.read_text().strip()).isdigit():
            return int(text)
        assert server.poll() is None, server.communicate()[1]
        time.sleep(0.25)
    raise TimeoutError("the server wrote no port")


def test_the_launched_server_serves_its_rollouts_storm_through_one_query_tool(channel, tmp_path):
    channel_port, row, asked = channel
    port_file = tmp_path / "port"
    env = os.environ | {
        "VF_CONFIG": "{}",
        "VF_STATE_URL": f"http://127.0.0.1:{channel_port}/state",
        "VF_STATE_SECRET": "test",
        "MCP_PORT_FILE": str(port_file),
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "ibtracs_storm_v1.taskset"],
        env=env,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        port = wait_for_port(port_file, server)
        for _ in range(120):  # as verifiers probes: any HTTP reply means it is serving
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/mcp", timeout=2)
                break
            except urllib.error.HTTPError:
                break
            except OSError:
                time.sleep(0.25)

        async def talk():
            async with AsyncExitStack() as stack:
                config = {"mcpServers": {"": {"url": f"http://127.0.0.1:{port}/mcp"}}}
                tools, dispatch, servers = await connect_mcp(config, stack)
                sql = "SELECT count(*), max(wind) FROM track"
                read = await call_mcp(servers, dispatch, "query", {"sql": sql})
                refused = await call_mcp(servers, dispatch, "query", {"sql": "DELETE FROM track"})
                return tools, read, refused

        tools, read, refused = asyncio.run(talk())
    finally:
        server.terminate()
        try:
            server.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.communicate()
    assert [t["function"]["name"] for t in tools] == ["query"]
    assert list(tools[0]["function"]["parameters"]["properties"]) == ["sql"]
    expected = f"count(*) | max(wind)\n{len(row['rows'])} | {max(r[2] for r in row['rows'])}"
    assert expected in str(read)  # this task's own rows, fetched over the channel
    assert "error: not authorized" in str(refused)
    assert any(path.endswith("/task") for path in asked)
