#!/usr/bin/env python3
"""
PROFESSIONAL EMOJI CLEANUP
Removes unprofessional hype emojis while preserving code structure
"""

import os
import re
from pathlib import Path

# Define specific hype emojis to remove (most unprofessional ones)
HYPE_EMOJIS_TO_REMOVE = [
    '', # Fire - hype
    '', # Rocket - hype
    '', # Money bag - unrealistic profit hype
    '', # Money with wings - hype
    '', # Dollar bills - hype
    '', # Sparkles - hype
    '', # Party - hype
    '', # Target - often hype
    '', # Diamond - crypto hype
    '', # Star - hype
    '', # Muscle - hype
    '', # Confetti - hype
    '', # Trophy - hype
    '', # Gold medal - hype
    '', # Crown - hype
    '', # 100 - hype
    '', # Money face - hype
    '', # Dollar sign - hype
    '', # Star eyes - hype
    '', # Heart eyes - hype
    '', # Party face - hype
    '', # Male detective - unprofessional
    '', # Detective - unprofessional
    '', # Ninja - unprofessional
    '', # Explosion - hype
    '', # Dizzy - hype
    '', # Rainbow - hype
    '', # Unicorn - unprofessional
    '', # Dragon - unprofessional
    '', # Crystal ball - unprofessional
    '', # Dice - gambling
    '', # Slot machine - gambling
    '', # 8-ball - unprofessional
]

# Professional emojis to keep (warnings, status, technical)
KEEP_EMOJIS = [
    '⚠️', # Warning - professional
    '❌', # X mark - professional error indicator
    '✅', # Check mark - professional success indicator
    '🟢', # Green circle - status indicator
    '🔴', # Red circle - status indicator
    '🟡', # Yellow circle - status indicator
    '🔵', # Blue circle - status indicator
    '📊', # Bar chart - data/analytics
    '📈', # Chart increasing - data
    '📉', # Chart decreasing - data
    '📋', # Clipboard - documentation
    '📝', # Memo - documentation
    '📄', # Document - documentation
    '📁', # Folder - file system
    '🔍', # Magnifying glass - search
    '🔧', # Wrench - tools/config
    '⚙️', # Gear - settings
    '🛠️', # Hammer and wrench - tools
    '🔒', # Lock - security
    '🔓', # Unlock - security
    '🔑', # Key - security/access
    '📡', # Satellite - network/communication
    '🌐', # Globe - network
    '💻', # Laptop - computing
    '🖥️', # Desktop - computing
    '📱', # Mobile phone - computing
    '⏰', # Clock - timing
    '⏱️', # Stopwatch - timing
    '⏲️', # Timer - timing
]

def clean_hype_emojis_from_text(text):
    """Remove only hype emojis from text, preserving structure."""
    original_text = text
    
    # Remove specific hype emojis
    for emoji in HYPE_EMOJIS_TO_REMOVE:
        text = text.replace(emoji, '')
    
    # Clean up any resulting double spaces, but preserve indentation
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Preserve leading whitespace (indentation)
        leading_whitespace = len(line) - len(line.lstrip())
        content = line.lstrip()
        
        # Clean up multiple spaces in content only
        content = re.sub(r' +', ' ', content)
        content = content.strip()
        
        # Reconstruct line with original indentation
        if content:
            cleaned_line = line[:leading_whitespace] + content
        else:
            cleaned_line = line[:leading_whitespace]
            
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)

def clean_file(file_path):
    """Clean hype emojis from a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        cleaned_content = clean_hype_emojis_from_text(original_content)
        
        if cleaned_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Clean hype emojis from all Python files."""
    print("=" * 60)
    print("PROFESSIONAL EMOJI CLEANUP - PHASE 2")
    print("Removing unprofessional hype emojis from entire codebase...")
    print("=" * 60)

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'node_modules', 'venv', '.venv']):
            continue

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files to process...")

    cleaned_files = 0
    total_files = len(python_files)

    for i, file_path in enumerate(python_files, 1):
        print(f"Processing [{i}/{total_files}]: {file_path}")

        if clean_file(file_path):
            cleaned_files += 1
            print(f" CLEANED: Removed hype emojis from {file_path}")
        else:
            print(f" SKIPPED: No hype emojis found")

    print("=" * 60)
    print(f"PROFESSIONAL CLEANUP COMPLETE!")
    print(f"Files processed: {total_files}")
    print(f"Files cleaned: {cleaned_files}")
    print(f"Files unchanged: {total_files - cleaned_files}")
    print("Codebase is now more professional!")
    print("=" * 60)

if __name__ == "__main__":
    main()
