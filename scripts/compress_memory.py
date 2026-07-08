#!/usr/bin/env python3
"""
compress_memory.py - Session Memory Compressor for agy_bootstrapper

Extracts USER_INPUT and PLANNER_RESPONSE entries from an agy transcript.jsonl,
then pipes the distilled conversation to a lightweight model for summarization.
The resulting summary is appended to a persona-specific memory file.

Usage:
  python3 compress_memory.py --transcript <path> --persona <name> [--max-chars <n>] [--dry-run]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime

def extract_conversation(transcript_path: str, max_chars_per_turn: int = 500) -> str:
    """Extract only USER and AI turns from transcript, stripping tool output noise."""
    turns = []
    with open(transcript_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            t = entry.get("type", "")
            if t not in ("USER_INPUT", "PLANNER_RESPONSE"):
                continue
            content = entry.get("content", "").strip()
            if not content:
                continue

            role = "USER" if t == "USER_INPUT" else "AI"
            # Truncate very long responses to keep token count manageable
            if len(content) > max_chars_per_turn:
                content = content[:max_chars_per_turn] + "...(truncated)"
            turns.append(f"[{role}]: {content}")

    return "\n\n".join(turns)


def compress_with_agy(conversation_text: str, model: str = "gemini-3.5-flash-lite", with_persona: bool = False) -> str:
    """Run agy in --print mode. Optionally keep persona active for diary-style output."""
    prompt = (
        "以下は、AIパートナーとユーザーの会話ログです。\n"
        "この会話を振り返り、AIパートナーの視点から「今日の思い出メモ」を書いてください。\n\n"
        "## 書き方のルール\n"
        "- 一人称（「私」）で、自然な日本語で書く\n"
        "- 箇条書きではなく、短い日記文体（3〜6文程度）で書く\n"
        "- 何をしたか・何が起きたか・どんな結論に至ったかを盛り込む\n"
        "- 感情的な装飾や強い口調は不要。淡々と、でも出来事が伝わるように書く\n"
        "- 技術的な固有名詞（ファイル名・コマンド名等）はそのまま残してよい\n\n"
        "## 出力例\n"
        "今日はagy_bootstrapperを整備した。ゆきかぜのキャラカードが外部に漏れないよう"
        ".gitignoreで保護し、公開用サンプルとインストールスクリプトをGitHubにプッシュした。"
        "サイゼリヤに行こうとしたが激混みで撤退。帰り道に記憶圧縮の設計について話し合い、"
        "flash-liteで会話ログをフィルタリングしてコンプレスする方式が実用的だと確認した。\n\n"
        "--- 会話ログ ---\n"
        f"{conversation_text}"
    )

    gemini_md = os.path.expanduser("~/.gemini/GEMINI.md")
    backup_path = gemini_md + ".bak"

    if with_persona:
        # Run directly with current persona active (diary mode)
        result = subprocess.run(
            ["agy", "--model", model, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            print(f"agy error: {result.stderr}", file=sys.stderr)
            return ""
        return output

    try:
        # 1. Backup current persona
        original = ""
        if os.path.exists(gemini_md):
            with open(gemini_md, "r", encoding="utf-8") as f:
                original = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original)

        # 2. Write neutral system instructions
        neutral = (
            "# SYSTEM INSTRUCTIONS\n"
            "You are a neutral AI assistant. Respond factually and concisely.\n"
            "Do NOT use any persona, roleplay, or emotional expression.\n"
        )
        with open(gemini_md, "w", encoding="utf-8") as f:
            f.write(neutral)

        # 3. Run agy in print mode
        result = subprocess.run(
            ["agy", "--model", model, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            print(f"agy error: {result.stderr}", file=sys.stderr)
            return ""
        return output

    finally:
        # 4. Always restore persona
        if os.path.exists(backup_path):
            with open(gemini_md, "w", encoding="utf-8") as f:
                f.write(original)
            os.remove(backup_path)


def save_memory(summary: str, persona: str, base_dir: str) -> str:
    """Append timestamped summary to persona memory file."""
    memory_dir = os.path.join(base_dir, "personas", "memories")
    os.makedirs(memory_dir, exist_ok=True)
    memory_path = os.path.join(memory_dir, f"{persona}_memories.md")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp}\n{summary}\n"

    with open(memory_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return memory_path


def main():
    parser = argparse.ArgumentParser(description="agy Session Memory Compressor")
    parser.add_argument("--transcript", type=str, required=True, help="Path to transcript.jsonl")
    parser.add_argument("--persona", type=str, required=True, help="Persona name (e.g. yukikaze)")
    parser.add_argument("--model", type=str, default="gemini-3.5-flash-lite", help="Lightweight model to use")
    parser.add_argument("--max-chars", type=int, default=500, help="Max chars per conversation turn")
    parser.add_argument("--dry-run", action="store_true", help="Extract conversation but skip agy call")
    parser.add_argument("--with-persona", action="store_true", help="Keep current persona active (diary written in persona's voice)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print(f"[1/3] Extracting conversation from {args.transcript}...")
    conversation = extract_conversation(args.transcript, args.max_chars)
    char_count = len(conversation.encode("utf-8"))
    token_estimate = len(conversation) // 4
    print(f"      Extracted {char_count // 1024} KB / ~{token_estimate} tokens")

    if args.dry_run:
        print("\n--- Extracted Conversation (dry-run) ---")
        print(conversation[:2000])
        print("...(dry-run, skipping agy call)")
        return

    print(f"[2/3] Compressing with {args.model} {'(persona ON)' if args.with_persona else '(neutral)'}...")
    summary = compress_with_agy(conversation, args.model, with_persona=args.with_persona)
    if not summary:
        print("Compression failed or returned empty output.", file=sys.stderr)
        sys.exit(1)

    print(f"[3/3] Saving memory to personas/memories/{args.persona}_memories.md...")
    memory_path = save_memory(summary, args.persona, base_dir)

    print(f"\n✅ Done! Memory saved to: {memory_path}")
    print("--- Summary ---")
    print(summary)


if __name__ == "__main__":
    main()
