#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_json_loose(text: str) -> dict[str, Any]:
    import re

    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {"value": payload}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        payload = json.loads(match.group(0))
        return payload if isinstance(payload, dict) else {"value": payload}


def render_template(value: str, request: dict[str, Any], request_json: Path, response_json: Path, prompt_file: Path) -> str:
    return value.format(
        request_json=str(request_json),
        response_json=str(response_json),
        prompt_file=str(prompt_file),
        paper_key=str(request.get("paper_key", "")),
        stage=str(request.get("stage", "")),
    )


def build_command(request: dict[str, Any], request_json: Path, response_json: Path, prompt_file: Path) -> list[str]:
    template = os.environ.get("PAPER_HELPER_ACP_COMMAND", "").strip()
    if template:
        rendered = render_template(template, request, request_json, response_json, prompt_file)
        return shlex.split(rendered, posix=(os.name != "nt"))

    node = os.environ.get("PAPER_HELPER_ACPX_NODE", "").strip()
    acpx_js = os.environ.get("PAPER_HELPER_ACPX_JS", "").strip()
    if node and acpx_js:
        base = [node, acpx_js]
    else:
        base = [os.environ.get("PAPER_HELPER_ACPX_BIN", "acpx")]

    agent = os.environ.get("PAPER_HELPER_ACPX_AGENT", "codex")
    subcommand = os.environ.get("PAPER_HELPER_ACPX_SUBCOMMAND", "exec")
    output_format = os.environ.get("PAPER_HELPER_ACPX_FORMAT", "quiet")
    return [*base, agent, subcommand, "--file", str(prompt_file), "--format", output_format]


def make_env() -> dict[str, str]:
    env = os.environ.copy()
    extra_path = env.get("PAPER_HELPER_EXTRA_PATH", "").strip()
    node_dir = env.get("PAPER_HELPER_NODE_DIR", "").strip()
    additions = [path for path in [extra_path, node_dir] if path]
    if additions:
        env["PATH"] = os.pathsep.join(additions + [env.get("PATH", "")])
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge paper-contribution-helper command-file LLM requests to an ACP CLI through prompt files.")
    parser.add_argument("--request-json", type=Path, default=None)
    parser.add_argument("--response-json", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=None)
    args = parser.parse_args()

    request_json = (args.request_json or Path(os.environ["LLM_REQUEST_JSON"])).resolve()
    request = read_json(request_json)
    response_json = (args.response_json or Path(os.environ.get("LLM_RESPONSE_JSON") or request["response_json"])).resolve()
    timeout = args.timeout or int(os.environ.get("PAPER_HELPER_ACP_TIMEOUT", os.environ.get("LLM_TIMEOUT", "900")))

    prompt = str(request.get("prompt") or "")
    if not prompt:
        raise SystemExit(f"Request file has no prompt: {request_json}")

    prompt_file = request_json.with_suffix(".prompt.txt")
    prompt_file.write_text(prompt, encoding="utf-8")
    command = build_command(request, request_json, response_json, prompt_file)

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=make_env(),
    )

    log_path = request_json.with_suffix(".acp.log.json")
    write_json(
        log_path,
        {
            "schema_version": "1.0",
            "command": command,
            "returncode": proc.returncode,
            "stdout_chars": len(proc.stdout or ""),
            "stderr_tail": (proc.stderr or "")[-4000:],
        },
    )
    if proc.returncode != 0:
        raise SystemExit(f"ACP command failed with code {proc.returncode}; see {log_path}")

    payload = parse_json_loose(proc.stdout)
    write_json(response_json, payload)
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
