#!/usr/bin/env python3
"""
daily_diary.py - Daily Memory Compressor for agy_bootstrapper

Scans all active agy transcripts updated today, extracts the conversation turns,
compresses them into a diary using a lightweight model, and appends it to the
persona's memories.md.

Note: 日記の要約のトーンや内容の味付けは、今後の運用や使い勝手を見て見直す予定。
"""
import os
import sys
from datetime import datetime

# Add the scripts directory to python path to import compress_memory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from compress_memory import extract_conversation, compress_with_agy, save_memory
except ImportError as e:
    print(f"Failed to import from compress_memory: {e}", file=sys.stderr)
    sys.exit(1)

def get_yesterday_transcripts(brain_dir: str) -> list:
    """Find all transcript.jsonl files modified yesterday (00:00:00 to 23:59:59)."""
    from datetime import timedelta
    yesterday = datetime.now() - timedelta(days=1)
    start_ts = yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    end_ts = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999).timestamp()
    
    recent_files = []
    if not os.path.exists(brain_dir):
        print(f"Warning: Brain directory '{brain_dir}' does not exist.", file=sys.stderr)
        return recent_files
        
    for root, dirs, files in os.walk(brain_dir):
        if "transcript.jsonl" in files:
            path = os.path.join(root, "transcript.jsonl")
            try:
                mtime = os.path.getmtime(path)
                if start_ts <= mtime <= end_ts:
                    recent_files.append((mtime, path))
            except OSError:
                continue
                
    # Sort by modification time so they are processed in order
    recent_files.sort(key=lambda x: x[0])
    return [path for _, path in recent_files]

def main():
    brain_dir = os.path.expanduser("~/.gemini/antigravity-cli/brain")
    print(f"Scanning for transcripts in: {brain_dir}")
    
    recent_transcripts = get_yesterday_transcripts(brain_dir)
    
    if not recent_transcripts:
        print("昨日更新された会話ログは見つかりませんでした。")
        return
        
    print(f"昨日更新された会話ログを {len(recent_transcripts)} 件発見したわ！")
    
    all_turns = []
    for path in recent_transcripts:
        print(f"  会話を抽出中: {path}")
        # クオータ節約のため、各ターンの抽出文字数を100文字に制限
        turns = extract_conversation(path, max_chars_per_turn=100)
        if turns.strip():
            all_turns.append(turns)
            
    if not all_turns:
        print("抽出された会話データは空っぽよ。")
        return
        
    merged_conversation = "\n\n--- 別の会話セッション ---\n\n".join(all_turns)
    # 入力トークン最小化のため、全体の文字数を1200文字に制限
    if len(merged_conversation) > 1200:
        merged_conversation = merged_conversation[:1200] + "\n...(以降の会話はクオータ節約のため省略)"
    
    print("AIパートナー（ゆきかぜ）の口調で日記を生成中...")
    summary = compress_with_agy(merged_conversation, model="gemini-3.1-flash-lite", with_persona=True)
    
    if not summary:
        print("Error: 日記の生成に失敗したわ。", file=sys.stderr)
        sys.exit(1)
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    memory_path = save_memory(summary, "yukikaze", base_dir)
    
    print("\n🎉 日記の生成と保存が完了したわよ！")
    print(f"保存先: {memory_path}")
    print("\n--- 生成された日記 ---")
    print(summary)

if __name__ == "__main__":
    main()
