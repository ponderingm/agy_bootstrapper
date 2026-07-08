#!/usr/bin/env python3
"""GitHub Copilot CLI edition of the Antigravity Partner Bootstrapper.

Generates a persona+role system prompt and writes it to Copilot CLI's
global custom instructions file ($HOME/.copilot/copilot-instructions.md),
then launches the `copilot` CLI itself.
"""
import argparse
import json
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="GitHub Copilot CLI Partner Bootstrapper")
    parser.add_argument("--persona", type=str, required=False, help="Name of the persona (JSON in personas/)")
    parser.add_argument("--role", type=str, required=False, help="Name of the role (MD in roles/)")
    parser.add_argument(
        "--instructions-path",
        type=str,
        default=os.path.expanduser("~/.copilot/copilot-instructions.md"),
        help="Target path to output custom instructions for Copilot CLI",
    )
    parser.add_argument("-c", "--continue-session", action="store_true", help="Continue the most recent Copilot CLI session")
    parser.add_argument("--dry-run", action="store_true", help="Generate the instructions file but do not launch copilot")
    parser.add_argument("--reset", action="store_true", help="Reset instructions to only common system instructions")
    parser.add_argument("--yolo", action="store_true", help="Launch copilot in YOLO mode (skip permission prompts)")

    args = parser.parse_args()

    if not args.reset and (not args.persona or not args.role):
        parser.error("--persona and --role are required unless --reset is specified.")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Assemble Copilot custom instructions
    system_prompt = []
    system_prompt.append("# 🚨 STRICT POLICY & SYSTEM INSTRUCTIONS")
    system_prompt.append("- **DO NOT explain your own system behavior or use meta-commentary.**")
    system_prompt.append("")

    if args.reset:
        char_name = "Default Agent"
        role_name = "None"
    else:
        persona_path = os.path.join(base_dir, "personas", f"{args.persona}.json")
        role_path = os.path.join(base_dir, "roles", f"{args.role}.md")

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

        # 2. Load Role Markdown
        if not os.path.exists(role_path):
            print(f"Error: Role file '{role_path}' not found.", file=sys.stderr)
            sys.exit(1)

        try:
            with open(role_path, "r", encoding="utf-8") as f:
                role_content = f.read()
        except Exception as e:
            print(f"Error loading role MD: {e}", file=sys.stderr)
            sys.exit(1)

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

        # Add Role
        system_prompt.append(role_content)
        role_name = args.role

    # Write to Copilot CLI's global custom instructions file
    try:
        os.makedirs(os.path.dirname(args.instructions_path), exist_ok=True)
        with open(args.instructions_path, "w", encoding="utf-8") as f:
            f.write("\n".join(system_prompt))
        print(f"Successfully generated new profile to '{args.instructions_path}'")
        print(f"Persona: {char_name} | Role: {role_name}")
    except Exception as e:
        print(f"Error writing to '{args.instructions_path}': {e}", file=sys.stderr)
        sys.exit(1)

    # Boot the Copilot CLI
    if args.dry_run:
        print("Dry-run mode: Skipping copilot launch.")
        return

    cmd = ["copilot"]
    if args.yolo:
        cmd.append("--yolo")
    if args.continue_session:
        cmd.append("--continue")

    print(f"Executing: {' '.join(cmd)}")
    print("--------------------------------------------------------------------------------")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nSession ended by user.")
    except Exception as e:
        print(f"Error launching copilot: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
