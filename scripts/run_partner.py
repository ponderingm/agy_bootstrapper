#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Antigravity AI Partner Bootstrapper")
    parser.add_argument("--persona", type=str, required=False, help="Name of the persona (JSON in personas/)")
    parser.add_argument("--role", type=str, required=False, help="Name of the role (MD in roles/)")
    parser.add_argument("--gemini-md", type=str, default="/home/pi/.gemini/GEMINI.md", help="Target path to output GEMINI.md")
    parser.add_argument("-c", "--continue-session", action="store_true", help="Continue the most recent agy conversation")
    parser.add_argument("--dry-run", action="store_true", help="Generate GEMINI.md but do not launch agy")
    parser.add_argument("--reset", action="store_true", help="Reset GEMINI.md to only common system instructions")
    parser.add_argument("--yolo", action="store_true", help="Launch agy in YOLO mode (skip permissions)")
    
    args = parser.parse_args()

    if not args.reset and (not args.persona or not args.role):
        parser.error("--persona and --role are required unless --reset is specified.")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 3. Assemble GEMINI.md Prompt
    # Add common strict instructions
    system_prompt = []
    system_prompt.append("# 🚨 STRICT POLICY & SYSTEM INSTRUCTIONS")
    system_prompt.append("- **Read .github/copilot-instructions.md if it exists**")
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
        system_prompt.append(f"AI-style technical self-references, explanations, and meta-dialogues are STRICTLY FORBIDDEN.")
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
        
    # 4. Write to GEMINI.md
    try:
        os.makedirs(os.path.dirname(args.gemini_md), exist_ok=True)
        with open(args.gemini_md, "w", encoding="utf-8") as f:
            f.write("\n".join(system_prompt))
        print(f"Successfully generated new profile to '{args.gemini_md}'")
        print(f"Persona: {char_name} | Role: {role_name}")
    except Exception as e:
        print(f"Error writing to GEMINI.md: {e}", file=sys.stderr)
        sys.exit(1)
        
    # 5. Boot agy
    if args.dry_run:
        print("Dry-run mode: Skipping agy launch.")
        return

    cmd = ["agy"]
    if args.yolo:
        cmd.append("--dangerously-skip-permissions")
    if args.continue_session:
        cmd.append("-c")
        
    print(f"Executing: {' '.join(cmd)}")
    print("--------------------------------------------------------------------------------")
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nSession ended by user.")
    except Exception as e:
        print(f"Error launching agy: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
