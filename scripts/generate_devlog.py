#!/usr/bin/env python3
"""
generate_devlog.py
──────────────────
Reads commit list from a file, calls Claude API, and prints
a bilingual (Vietnamese / English) devlog to stdout.

Environment variables (required):
  ANTHROPIC_API_KEY  – Anthropic secret key
  FROM_COMMIT        – Starting commit ref (excluded from range)
  TO_COMMIT          – Ending commit ref
  COMMIT_COUNT       – Number of commits (used in the prompt)

File (required):
  /tmp/commits.txt   – One commit per line: "<hash> | <subject> | <author> | <date>"
"""

import json
import os
import sys
import urllib.error
import urllib.request

# ── Config ────────────────────────────────────────────────────────────────────

API_URL   = "https://api.anthropic.com/v1/messages"
API_VER   = "2023-06-01"
MODEL     = "claude-sonnet-4-20250514"
MAX_TOKENS = 2048
COMMITS_FILE = "/tmp/commits.txt"

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_env(*keys: str) -> dict[str, str]:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return {k: os.environ[k] for k in keys}


def read_commits(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Commits file not found: {path}", file=sys.stderr)
        sys.exit(1)


def build_prompt(git_log: str, from_commit: str, to_commit: str, count: str) -> str:
    return f"""Bạn là một technical writer giàu kinh nghiệm.
Dựa vào {count} commit dưới đây (từ {from_commit} → {to_commit}), hãy tạo một devlog/changelog song ngữ Việt – Anh chuyên nghiệp.

Yêu cầu định dạng:
- Mỗi mục: nội dung Tiếng Việt trước, sau đó (English) trên cùng dòng hoặc dòng kế.
- Nhóm theo danh mục (chỉ hiển thị danh mục có thay đổi):
  ✨ Tính năng mới / New Features
  🐛 Sửa lỗi / Bug Fixes
  ♻️ Cải tiến / Improvements
  🔒 Bảo mật / Security
  🔧 Khác / Others
- Mỗi gạch đầu dòng ngắn gọn, súc tích (≤ 15 từ mỗi ngôn ngữ).
- Kết thúc bằng một dòng tóm tắt ngắn song ngữ.

Danh sách commit:
{git_log}

Chỉ trả về nội dung devlog, không thêm giải thích hay markdown code block."""


def call_claude(api_key: str, prompt: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "x-api-key":         api_key,
            "anthropic-version": API_VER,
            "content-type":      "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ Claude API error {e.code}: {body}", file=sys.stderr)
        sys.exit(1)

    return "\n".join(
        block["text"]
        for block in data.get("content", [])
        if block.get("type") == "text"
    ).strip()


def print_devlog(devlog: str, from_commit: str, to_commit: str, count: str) -> None:
    sep = "═" * 60
    print()
    print(sep)
    print(f"  DEVLOG  {from_commit} → {to_commit}  ({count} commits)")
    print(sep)
    print()
    print(devlog)
    print()
    print(sep)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    env = load_env("ANTHROPIC_API_KEY", "FROM_COMMIT", "TO_COMMIT", "COMMIT_COUNT")

    git_log = read_commits(COMMITS_FILE)
    prompt  = build_prompt(
        git_log,
        env["FROM_COMMIT"],
        env["TO_COMMIT"],
        env["COMMIT_COUNT"],
    )
    devlog  = call_claude(env["ANTHROPIC_API_KEY"], prompt)
    print_devlog(devlog, env["FROM_COMMIT"], env["TO_COMMIT"], env["COMMIT_COUNT"])


if __name__ == "__main__":
    main()
