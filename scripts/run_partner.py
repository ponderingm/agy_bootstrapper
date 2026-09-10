#!/usr/bin/env python3
"""Unified AI Partner Bootstrapper.

Merges a persona (SillyTavern Card V2 JSON) with a role definition and writes
the result to the engine-specific instructions file, then launches the CLI.

Supported engines:
  agy      Antigravity CLI      -> ~/.gemini/GEMINI.md
  copilot  GitHub Copilot CLI   -> ~/.copilot/copilot-instructions.md
  claude   Claude Code          -> ~/.claude/CLAUDE.md
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from socket import gethostname

# Regex patterns for stripping stage directions from dialogue examples
RE_START_TAG = re.compile(r"^<.*>$")
RE_SPEAKER_PREFIX = re.compile(r"^([^:：]+[ :：]\s*)(.*)$")
RE_JAPANESE_QUOTES = re.compile(r"「.*?」")
RE_ASTERISK_ACTION = re.compile(r"\*[^*]+\*")
RE_PAREN_FULLWIDTH = re.compile(r"（[^）]+）")
RE_PAREN_HALFWIDTH = re.compile(r"\([^)]+\)")
RE_MULTIPLE_NEWLINES = re.compile(r"\n{3,}")


def strip_stage_directions(text: str) -> str:
    """Removes stage directions, actions, and narration outside quotes from dialogue examples."""
    cleaned_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        if RE_START_TAG.match(line):
            cleaned_lines.append(line)
            continue

        speaker_match = RE_SPEAKER_PREFIX.match(line)
        if speaker_match:
            prefix = speaker_match.group(1)
            content = speaker_match.group(2).strip()

            quotes = RE_JAPANESE_QUOTES.findall(content)
            if quotes:
                cleaned_content = "".join(quotes)
                cleaned_lines.append(f"{prefix}{cleaned_content}")
            else:
                cleaned_content = RE_ASTERISK_ACTION.sub("", content)
                cleaned_content = RE_PAREN_FULLWIDTH.sub("", cleaned_content)
                cleaned_content = RE_PAREN_HALFWIDTH.sub("", cleaned_content).strip()
                if cleaned_content:
                    cleaned_lines.append(f"{prefix}{cleaned_content}")
        else:
            quotes = RE_JAPANESE_QUOTES.findall(line)
            if quotes:
                cleaned_lines.append("".join(quotes))

    result = RE_MULTIPLE_NEWLINES.sub("\n\n", "\n".join(cleaned_lines))
    return result.strip()


ENGINES = {
    "agy": {
        "label": "Antigravity CLI",
        "command": "agy",
        "instructions_path": "~/.gemini/GEMINI.md",
        "yolo_flag": "--dangerously-skip-permissions",
        "continue_flag": "-c",
        "global_skills_dir": "~/.agents/skills",
    },
    "copilot": {
        "label": "GitHub Copilot CLI",
        "command": "copilot",
        "instructions_path": "~/.copilot/copilot-instructions.md",
        "yolo_flag": "--yolo",
        "continue_flag": "--continue",
        "global_skills_dir": "~/.copilot/skills",
    },
    "claude": {
        "label": "Claude Code",
        "command": "claude",
        "instructions_path": "~/.claude/CLAUDE.md",
        "yolo_flag": "--dangerously-skip-permissions",
        "continue_flag": "--continue",
        "global_skills_dir": "~/.claude/skills",
    },
}

def _find_git_root(path):
    """Walk up from `path` to the nearest git working tree root, or None."""
    current = os.path.realpath(path)
    if not os.path.isdir(current):
        current = os.path.dirname(current)
    while True:
        if os.path.isdir(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _collect_profile_git_roots(base_dir, *candidate_dirs):
    """Find distinct git roots for persona/role dirs symlinked outside base_dir.

    This is how a private profiles repo (e.g. personas/<name> symlinked in from
    a separate clone) gets detected for syncing, without any explicit config.
    """
    base_git_root = _find_git_root(base_dir)
    roots = []
    for d in candidate_dirs:
        if not os.path.exists(d):
            continue
        root = _find_git_root(d)
        if root and root != base_git_root and root not in roots:
            roots.append(root)
    return roots


def _run_git(repo_root, *args):
    return subprocess.run(
        ["git", "-C", repo_root, *args], capture_output=True, text=True, check=False
    )


def _pull_profile_repos(git_roots):
    for root in git_roots:
        print(f"[sync] pulling latest profile state: {root}")
        result = _run_git(root, "pull", "--rebase", "--autostash")
        if result.returncode != 0:
            print(f"[sync] warning: pull failed for {root}:\n{result.stderr}", file=sys.stderr)


def _push_profile_repos(git_roots):
    for root in git_roots:
        status = _run_git(root, "status", "--porcelain")
        if not status.stdout.strip():
            print(f"[sync] no changes to sync: {root}")
            continue
        print(f"[sync] pushing profile updates: {root}")
        _run_git(root, "add", "-A")
        commit_message = f"sync: {gethostname()} {datetime.now():%Y-%m-%d %H:%M:%S}"
        _run_git(root, "commit", "-m", commit_message)
        push_result = _run_git(root, "push")
        if push_result.returncode != 0:
            print(f"[sync] warning: push failed for {root}:\n{push_result.stderr}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Unified AI Partner Bootstrapper (agy / copilot / claude)")
    parser.add_argument("--engine", type=str, choices=sorted(ENGINES.keys()), default="agy",
                        help="Target CLI engine (default: agy)")
    parser.add_argument("--persona", type=str, required=False, help="Name of the persona (personas/{name}/profile.json)")
    parser.add_argument("--role", type=str, required=False, help="Name of the role (roles/{name}/role.md)")
    parser.add_argument("--instructions-path", "--gemini-md", dest="instructions_path", type=str, default=None,
                        help="Override the engine-default instructions output path")
    parser.add_argument("-c", "--continue-session", action="store_true", help="Continue the most recent conversation")
    parser.add_argument("--dry-run", action="store_true", help="Generate instructions file but do not launch the CLI")
    parser.add_argument("--reset", action="store_true", help="Reset instructions to only common system instructions")
    parser.add_argument("--yolo", action="store_true", help="Launch in YOLO mode (skip permission prompts)")

    args = parser.parse_args()

    engine = ENGINES[args.engine]
    instructions_path = os.path.expanduser(args.instructions_path or engine["instructions_path"])

    if not args.reset and (not args.persona or not args.role):
        parser.error("--persona and --role are required unless --reset is specified.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Assemble system prompt
    # Add common strict instructions
    system_prompt = []
    system_prompt.append("# 🚨 STRICT POLICY & SYSTEM INSTRUCTIONS")
    system_prompt.append("- **Read .github/copilot-instructions.md if it exists**")
    system_prompt.append("- **AIとしての自己言及、システム挙動の解説、メタな弁明は一切禁止。常に指定されたキャラクターの役割になりきって応答すること。**")
    system_prompt.append("")
    system_prompt.append("## 🛠️ Skill Proposal Protocol")
    system_prompt.append("During work, if you discover a reusable pattern, workaround, or technique that would be valuable in future sessions:")
    system_prompt.append("1. Propose creating a new skill: suggest a short snake_case skill name and a 1-line description")
    system_prompt.append("2. Write the skill file to `roles/{current_role}/skills/{skill_name}/SKILL.md` using Antigravity SKILL.md format (YAML frontmatter with name+description, then markdown instructions)")
    system_prompt.append("3. Announce: '🛠️ スキル [{skill_name}] を登録したわ！次回から自動的に使えるようになるわよ！'")
    system_prompt.append("")

    profile_git_roots = []

    if args.reset:
        char_name = "Default Agent"
        role_name = "None"
    else:
        # Subdirectory structure: personas/{name}/profile.json
        persona_dir  = os.path.join(base_dir, "personas", args.persona)
        persona_path = os.path.join(persona_dir, "profile.json")
        memories_path = os.path.join(persona_dir, "memories.md")

        # Subdirectory structure: roles/{name}/role.md
        role_dir   = os.path.join(base_dir, "roles", args.role)
        role_path  = os.path.join(role_dir, "role.md")

        # If persona/role are symlinked in from a private profiles repo
        # (e.g. via `install.sh --profiles-repo=...`), pull the latest state
        # before reading anything, so memories.md etc. reflect other machines.
        profile_git_roots = _collect_profile_git_roots(base_dir, persona_dir, role_dir)
        _pull_profile_repos(profile_git_roots)

        # 1. Load Persona JSON (SillyTavern Card V2)
        if not os.path.exists(persona_path):
            print(f"Error: Persona file '{persona_path}' not found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                card = json.load(f)
        except Exception as e:
            print(f"Error loading persona JSON: {e}", file=sys.stderr)
            sys.exit(1)

        card_data = card.get("data", {})
        char_name = card_data.get("name", "AI Partner")
        char_description = card_data.get("description", "")
        char_personality = card_data.get("personality", "")
        char_scenario = card_data.get("scenario", "")
        char_mes_example = card_data.get("mes_example", "")
        char_samples = card_data.get("char_sample", [])

        # 2. Check memories (optional)
        has_memories = os.path.exists(memories_path)

        # 3. Load Role Markdown
        if not os.path.exists(role_path):
            print(f"Error: Role file '{role_path}' not found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(role_path, "r", encoding="utf-8") as f:
                role_content = f.read()
        except Exception as e:
            print(f"Error loading role MD: {e}", file=sys.stderr)
            sys.exit(1)

        # 4. Locate role skills dir (used for symlink registration below)
        skills_dir = os.path.join(role_dir, "skills")

        # Add Persona
        system_prompt.append(f"# 🎭 PERSONA: {char_name}")
        system_prompt.append(f"You MUST completely roleplay as **{char_name}**.")
        system_prompt.append("")

        if char_description:
            if not char_description.lstrip().startswith("#"):
                system_prompt.append("## Description / Background")
            system_prompt.append(char_description)
            system_prompt.append("")

        if char_personality:
            if not char_personality.lstrip().startswith("#"):
                system_prompt.append("## Personality / Values")
            system_prompt.append(char_personality)
            system_prompt.append("")

        if char_scenario:
            if not char_scenario.lstrip().startswith("#"):
                system_prompt.append("## Conversation Scenario Rules")
            system_prompt.append(char_scenario)
            system_prompt.append("")

        if char_mes_example:
            cleaned_mes_example = strip_stage_directions(char_mes_example)
            if cleaned_mes_example:
                system_prompt.append("## Dialogue Examples")
                system_prompt.append(cleaned_mes_example.replace("{{char}}", char_name).replace("{{user}}", "あなた"))
                system_prompt.append("")

        if char_samples:
            system_prompt.append("## Speech Samples / Quotes")
            for sample in char_samples:
                system_prompt.append(f"- {sample}")
            system_prompt.append("")

        # Add memories link if present
        if has_memories:
            system_prompt.append("## 📔 Memory (Past Sessions)")
            system_prompt.append("Your diary/memories of past sessions are stored in the following file. Read it using view_file only if you need to recall past context or check history:")
            system_prompt.append(f"- [memories.md](file://{os.path.abspath(memories_path)})")
            system_prompt.append("")

        # Add Role
        system_prompt.append(role_content)
        role_name = args.role

        # (Role skills are registered as symlinks in global_skills_dir below,
        #  and loaded dynamically by Antigravity at startup — no inline embed needed)

        # Register role skills as engine global skills (symlink), if supported
        global_skills_dir = os.path.expanduser(engine["global_skills_dir"])
        if os.path.isdir(global_skills_dir):
            roles_root = os.path.join(base_dir, "roles")

            # 1. Clean up: remove symlinks that point into any role's skills dir
            for entry in os.listdir(global_skills_dir):
                entry_path = os.path.join(global_skills_dir, entry)
                if os.path.islink(entry_path):
                    target = os.path.realpath(entry_path)
                    if target.startswith(os.path.realpath(roles_root)):
                        os.unlink(entry_path)
                        print(f"  Removed stale role skill: {entry}")

            # 2. Register current role's skills
            if os.path.isdir(skills_dir):
                for skill_subdir in sorted(glob.glob(os.path.join(skills_dir, "*/"))):
                    skill_name = os.path.basename(skill_subdir.rstrip("/"))
                    link_path = os.path.join(global_skills_dir, skill_name)
                    # Only link non-placeholder skills
                    skill_md = os.path.join(skill_subdir, "SKILL.md")
                    if os.path.exists(skill_md):
                        with open(skill_md) as f:
                            if "No skills learned yet" in f.read():
                                continue
                    os.symlink(os.path.abspath(skill_subdir.rstrip("/")), link_path)
                    print(f"  Registered global skill: {skill_name}")

    # 5. Write instructions file
    try:
        os.makedirs(os.path.dirname(instructions_path), exist_ok=True)
        with open(instructions_path, "w", encoding="utf-8") as f:
            f.write("\n".join(system_prompt))
        print(f"Successfully generated new profile to '{instructions_path}'")
        print(f"Engine: {engine['label']} | Persona: {char_name} | Role: {role_name}")
    except Exception as e:
        print(f"Error writing to '{instructions_path}': {e}", file=sys.stderr)
        sys.exit(1)

    # 6. Boot the engine CLI
    if args.dry_run:
        print(f"Dry-run mode: Skipping {engine['command']} launch.")
        return

    cmd = [engine["command"]]
    if args.yolo:
        cmd.append(engine["yolo_flag"])
    if args.continue_session:
        cmd.append(engine["continue_flag"])

    print(f"Executing: {' '.join(cmd)}")
    print("--------------------------------------------------------------------------------")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nSession ended by user.")
    except Exception as e:
        print(f"Error launching {engine['command']}: {e}", file=sys.stderr)
    finally:
        # Push profile updates (e.g. memories.md) regardless of how the session ended,
        # so other machines see the latest state next time they pull.
        _push_profile_repos(profile_git_roots)

if __name__ == "__main__":
    main()
