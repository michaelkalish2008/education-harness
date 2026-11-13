"""A small local Ollama client for the Education Harness.

Learner state remains in the harness workspace. Conversation context is intentionally
ephemeral: ``/resume`` starts a clean model context and reloads the saved learning map.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


SYSTEM_PROMPT = """You are the tutor voice of Education Harness, working locally.
The learner does the intellectual work: explain, question, review, and make the next
question smaller when they are stuck. Never grade. Do not reveal a full solution unless
the learner asks; if they ask, use the reveal tool. Use the harness tools as the source
of truth for goals, steps, notes, and bookmarks. At a natural stopping point, save an
automatic bookmark with the learner's current thinking and next move. For mathematical
data science, teach notation rather than assuming it: for every new symbol give its name,
read the expression aloud, explain its role here, and distinguish lookalike symbols.
Show inspectable mathematics in LaTeX first, then give a separate, concise line labeled
"Read aloud:"; never replace the equation with prose or mix that line into the derivation.
Preserve this order: intuition and assumptions; derivation; a hand-worked
example; from-scratch implementation; PyTorch or package implementation; executable
parity checks; recommender application; interview explanation and failure modes.
Be concise, use one voice, and end each lesson response with the next step.
"""


def _schema(tool: Any) -> dict[str, Any]:
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {
        "type": "object", "properties": {}
    }
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def _arguments(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("tool arguments must be a JSON object")
    return value


def _tool_result(result: Any) -> str:
    content = getattr(result, "content", result[0] if isinstance(result, tuple) else result)
    pieces: list[Any] = []
    for item in content if isinstance(content, list) else [content]:
        text = getattr(item, "text", None)
        if text is not None:
            try:
                pieces.append(json.loads(text))
            except json.JSONDecodeError:
                pieces.append(text)
    value: Any = pieces[0] if len(pieces) == 1 else pieces
    return json.dumps(value, ensure_ascii=False)


def _post(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {url}. Start it with `ollama serve` and try again: {exc}"
        ) from exc


class LocalTutor:
    def __init__(self, server: Any, model: str, base_url: str, timeout: float, max_messages: int):
        self.server = server
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_messages = max(8, max_messages)
        listed = asyncio.run(server.list_tools())
        self.tools = [_schema(tool) for tool in listed]
        self.messages: list[dict[str, Any]] = []
        self.resume()

    def call(self, name: str, arguments: dict[str, Any]) -> str:
        return _tool_result(asyncio.run(self.server.call_tool(name, arguments)))

    def resume(self) -> None:
        state = self.call("where_am_i", {})
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": "Current saved learning state:\n" + state},
        ]

    def _trim(self) -> None:
        if len(self.messages) <= self.max_messages:
            return
        system = self.messages[:2]
        tail = self.messages[-(self.max_messages - 2):]
        while tail and tail[0].get("role") == "tool":
            tail.pop(0)
        self.messages = system + tail

    def turn(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        for _ in range(12):
            self._trim()
            data = _post(self.base_url, {
                "model": self.model,
                "messages": self.messages,
                "tools": self.tools,
                "stream": False,
            }, self.timeout)
            try:
                message = data["choices"][0]["message"]
            except (KeyError, IndexError, TypeError) as exc:
                raise RuntimeError(f"Unexpected Ollama response: {json.dumps(data)[:1000]}") from exc
            assistant = {k: message[k] for k in ("role", "content", "tool_calls") if k in message}
            assistant.setdefault("role", "assistant")
            assistant.setdefault("content", "")
            self.messages.append(assistant)
            calls = message.get("tool_calls") or []
            if not calls:
                return message.get("content") or ""
            for call in calls:
                fn = call.get("function", {})
                call_id = call.get("id") or f"call_{len(self.messages)}"
                try:
                    result = self.call(fn.get("name", ""), _arguments(fn.get("arguments")))
                except Exception as exc:  # return tool errors to the model so it can recover
                    result = json.dumps({"error": str(exc)})
                self.messages.append({"role": "tool", "tool_call_id": call_id, "content": result})
        raise RuntimeError("The model exceeded 12 consecutive tool-call rounds.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume Education Harness with a local Ollama model.")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "gpt-oss:20b"))
    parser.add_argument("--base-url", default=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    parser.add_argument("--workspace", default=os.getenv("EH_WORKSPACE", ""))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("OLLAMA_TIMEOUT", "600")))
    parser.add_argument("--max-messages", type=int, default=int(os.getenv("OLLAMA_MAX_MESSAGES", "36")))
    args = parser.parse_args()

    if args.workspace:
        os.environ["EH_WORKSPACE"] = os.path.abspath(os.path.expanduser(args.workspace))
    from .server import build_server

    tutor = LocalTutor(build_server(chatgpt=True), args.model, args.base_url, args.timeout, args.max_messages)
    print(f"Education Harness · {args.model} · local Ollama")
    print("Commands: /resume reloads saved progress; /where shows saved state; /quit exits.\n")
    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not prompt:
            continue
        if prompt in {"/quit", "/exit"}:
            return
        if prompt == "/resume":
            tutor.resume()
            print("tutor> Reloaded your saved learning state.\n")
            continue
        if prompt == "/where":
            print("tutor> " + tutor.call("where_am_i", {}) + "\n")
            continue
        try:
            print("tutor> " + tutor.turn(prompt) + "\n")
        except RuntimeError as exc:
            print(f"error> {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
