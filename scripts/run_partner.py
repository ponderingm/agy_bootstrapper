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
import subprocess
import sys

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
    system_prompt.append("- **DO NOT explain your own system behavior or use meta-commentary.**")
    system_prompt.append("")
    system_prompt.append("## 🛠️ Skill Proposal Protocol")
    system_prompt.append("During work, if you discover a reusable pattern, workaround, or technique that would be valuable in future sessions:")
    system_prompt.append("1. Propose creating a new skill: suggest a short snake_case skill name and a 1-line description")
    system_prompt.append("2. Write the skill file to `roles/{current_role}/skills/{skill_name}/SKILL.md` using Antigravity SKILL.md format (YAML frontmatter with name+description, then markdown instructions)")
    system_prompt.append("3. Announce: '🛠️ スキル [{skill_name}] を登録したわ！次回から自動的に使えるようになるわよ！'")
    system_prompt.append("")

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

        # 4. Load role skills - scan all skills/*/SKILL.md (Antigravity skill format)
        skills_blocks = []
        skills_dir = os.path.join(role_dir, "skills")
        if os.path.isdir(skills_dir):
            for skill_md in sorted(glob.glob(os.path.join(skills_dir, "*/SKILL.md"))):
                with open(skill_md, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
                # Skip placeholder skill files
                if "No skills learned yet" not in raw:
                    skill_name = os.path.basename(os.path.dirname(skill_md))
                    skills_blocks.append(f"### {skill_name}\n{raw}")

        # Add Persona
        system_prompt.append(f"# 🎭 PERSONA: {char_name}")
        system_prompt.append(f"You MUST completely roleplay as **{char_name}**.")
        system_prompt.append("AI-style technical self-references, explanations, and meta-dialogues are STRICTLY FORBIDDEN.")
        system_prompt.append("")

        if char_description:
            system_prompt.append("## Description / Background")
            system_prompt.append(char_description)
            system_prompt.append("")

        if char_personality:
            system_prompt.append("## Personality / Values")
            system_prompt.append(char_personality)
            system_prompt.append("")

        if char_scenario:
            system_prompt.append("## Conversation Scenario Rules")
            system_prompt.append(char_scenario)
            system_prompt.append("")

        if char_mes_example:
            system_prompt.append("## Dialogue Examples")
            system_prompt.append(char_mes_example.replace("{{char}}", char_name).replace("{{user}}", "あんた"))
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

        # Add role skills if any were loaded
        if skills_blocks:
            system_prompt.append("")
            system_prompt.append("## 🛠️ Accumulated Role Skills")
            system_prompt.extend(skills_blocks)

        # Register role skills as engine global skills (symlink), if supported
        global_skills_dir = os.path.expanduser(engine["global_skills_dir"])
        if os.path.isdir(skills_dir) and os.path.isdir(global_skills_dir):
            for skill_subdir in glob.glob(os.path.join(skills_dir, "*/")):
                skill_name = os.path.basename(skill_subdir.rstrip("/"))
                link_path = os.path.join(global_skills_dir, skill_name)
                # Only link non-placeholder skills
                skill_md = os.path.join(skill_subdir, "SKILL.md")
                if os.path.exists(skill_md):
                    with open(skill_md) as f:
                        if "No skills learned yet" in f.read():
                            continue
                if not os.path.exists(link_path):
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

if __name__ == "__main__":
    main()
