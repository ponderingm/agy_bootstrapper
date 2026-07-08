#!/usr/bin/env python3
import json
import os
import re
import sys

def parse_profile(gemini_md_path):
    if not os.path.exists(gemini_md_path):
        return None
        
    with open(gemini_md_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract Character Profile Section
    profile_match = re.search(r"--- キャラクタープロフィール ---(.*?)(?:---|人狼ゲーム)", content, re.DOTALL)
    if not profile_match:
        return None
        
    profile_text = profile_match.group(1).strip()
    
    # Simple parsers for fields
    name_match = re.search(r"# 名前:\s*(.*)", profile_text)
    name = name_match.group(1).strip() if name_match else os.path.basename(os.path.dirname(gemini_md_path)).capitalize()
    
    # Try to split into sections
    sections = re.split(r"\n##\s*", profile_text)
    
    description = ""
    personality = ""
    scenario = "Gemini Task Manager (Bonds & Memories) の一員として業務を遂行してください。"
    char_samples = []
    
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
            
        lines = sec.split("\n")
        title = lines[0].lower().strip()
        body = "\n".join(lines[1:]).strip()
        
        if "外見" in title or "本質" in title or "spec" in title:
            description += f"{sec}\n\n"
        elif "性格" in title:
            personality += body
        elif "口調" in title:
            personality += f"\n\n口調指示:\n{body}"
            # Extract sample dialogues
            samples = re.findall(r"-\s*「(.*?)」", body)
            char_samples.extend(samples)
            
    # Fallback to general lines if personality is empty
    if not personality:
        personality = profile_text
        
    # Build SillyTavern Card V2 structure
    card = {
      "spec": "chara_card_v2",
      "spec_version": "2.0",
      "data": {
        "name": name,
        "description": description.strip(),
        "personality": personality.strip(),
        "scenario": scenario,
        "mes_example": "",
        "first_mes": f"「マスター、{name}、ただいま起動いたしました。指示を待機中。」",
        "char_sample": char_samples,
        "tags": ["gemini-task-manager", "AI-partner", name.lower()],
        "creator": "import_personas_script",
        "creator_notes": "Automatically imported from gemini-task-manager."
      }
    }
    
    return card

def main():
    source_dir = "/home/pi/gemini-task-manager/data/partners"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, "personas")
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory '{source_dir}' not found.", file=sys.stderr)
        sys.exit(1)
        
    partners = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    
    print(f"Found partners in task manager: {', '.join(partners)}")
    imported_count = 0
    
    for partner in partners:
        gemini_md_path = os.path.join(source_dir, partner, "GEMINI.md")
        card = parse_profile(gemini_md_path)
        if card:
            target_path = os.path.join(target_dir, f"{partner}.json")
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(card, f, indent=2, ensure_ascii=False)
            print(f"Successfully imported and converted: {partner} -> personas/{partner}.json")
            imported_count += 1
        else:
            print(f"Warning: Could not parse profile for {partner}")
            
    print(f"Import complete. Total imported: {imported_count}")

if __name__ == "__main__":
    main()
