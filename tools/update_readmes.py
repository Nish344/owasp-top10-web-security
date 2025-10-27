#!/usr/bin/env python3
"""
update_readmes.py

Scans repo for category folders named like "01-Broken-Access-Control" or "01_Broken_Access_Control",
parses lab markdown metadata and generates:

- Root README.md with badges, progress chart, categories, recent labs.
- README.md inside each category with checklist and cheatsheet placeholder.
"""

import os
import re
from pathlib import Path

ROOT = Path('.').resolve()

# More flexible front-matter regex that handles both with and without --- delimiters
FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.IGNORECASE)
# Alternative: Parse metadata from first few lines if no --- delimiters
METADATA_LINE_RE = re.compile(r'^\*\*([^*]+)\*\*\s*:\s*(.+)$', re.MULTILINE)
KEY_VALUE_RE = re.compile(r'^\s*([A-Za-z0-9_\-]+)\s*:\s*(.+)\s*$', re.MULTILINE)

CATEGORY_FOLDER_RE = re.compile(r'^\d{2}[-_].+')

def parse_front_matter(md_text):
    """Return dict of front-matter/metadata keys (lowercased)."""
    data = {}
    
    # First, try standard YAML front-matter with --- delimiters
    m = FRONT_MATTER_RE.match(md_text)
    if m:
        block = m.group(1)
        for km in KEY_VALUE_RE.finditer(block):
            k = km.group(1).strip().lower().replace('_', '-')
            v = km.group(2).strip().strip('"').strip("'").strip('`')
            data[k] = v
        return data
    
    # Fallback: Parse **Key**: Value format (your current format)
    # Look at first 30 lines only for metadata
    lines = md_text.split('\n')[:30]
    header_text = '\n'.join(lines)
    
    for match in METADATA_LINE_RE.finditer(header_text):
        k = match.group(1).strip().lower().replace('_', '-').replace(' ', '-')
        v = match.group(2).strip().strip('"').strip("'").strip('`')
        data[k] = v
    
    return data

def extract_title_from_markdown(md_text):
    """Extract title from first # heading in markdown."""
    lines = md_text.split('\n')
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if line.startswith('# '):
            return line.lstrip('# ').strip()
    return None

def scan_categories(root):
    """Scan for category folders matching pattern 01-* or 01_*"""
    categories = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and CATEGORY_FOLDER_RE.match(p.name):
            # Skip hidden directories and common non-category dirs
            if not p.name.startswith('.') and p.name.lower() not in ['tools', 'scripts', 'assets']:
                categories.append(p)
    return categories

def scan_labs(category_path):
    """Scan all markdown files in category folder and extract metadata."""
    labs = []
    for md in sorted(category_path.glob('*.md')):
        # Skip README.md files in metadata extraction
        if md.name.upper() == 'README.MD':
            continue
            
        try:
            text = md.read_text(encoding='utf-8', errors='ignore')
            fm = parse_front_matter(text)
            
            # Extract title with multiple fallbacks
            title = fm.get('title', '')
            if not title:
                # Try to extract from first # heading
                title = extract_title_from_markdown(text)
            if not title:
                # Fallback to filename
                title = md.stem.replace('-', ' ').replace('_', ' ').title()
            
            lab_id = fm.get('lab-id', '')
            date_completed = fm.get('date-completed', '')
            tag = fm.get('tag', '')
            
            # Clean up tag formatting
            if tag:
                # Remove backticks and clean up
                tag = tag.replace('`', '').strip()
            
            labs.append({
                'filename': md.name,
                'title': title,
                'lab_id': lab_id,
                'date_completed': date_completed,
                'tag': tag,
            })
        except Exception as e:
            print(f"Warning: Could not parse {md.name}: {e}")
            continue
    
    return labs

def generate_category_readme(category_path, labs, category_title, done, total):
    """Generate README.md for a category folder while preserving any manual cheatsheet content."""
    readme_path = category_path / 'README.md'

    header = f"# {category_title}\n\n"
    intro = (
        f"This folder contains lab writeups for the **{category_title}** category.\n\n"
        f"### Progress\n\n"
        f"- Completed: **{done}** / **{total}**\n\n"
        "### Labs\n\n"
    )

    lines = []
    for l in labs:
        status = "✅" if l['date_completed'] else "⬜"
        lab_line = f"- {status} [{l['title']}]({l['filename'].replace(' ', '%20')})"
        if l['lab_id']:
            lab_line += f" — `{l['lab_id']}`"
        if l['tag']:
            lab_line += f" — _{l['tag']}_"
        lines.append(lab_line)

    auto_content = header + intro + "\n".join(lines) + "\n\n"

    # Cheatsheet heading we'll ensure exists; preserve user content if any
    cheatsheet_heading = "### Cheatsheet / Quick Notes\n\n"

    if readme_path.exists():
        existing = readme_path.read_text(encoding='utf-8', errors='ignore')
        # Look for the cheatsheet heading (exact match). If found, preserve everything after it.
        split_token = "### Cheatsheet / Quick Notes"
        if split_token in existing:
            # Keep heading + whatever follows (preserve trailing whitespace)
            _, trailing = existing.split(split_token, 1)
            # Reconstruct: auto_content + heading + preserved trailing (strip leading newlines)
            preserved = trailing.lstrip('\n')
            new_content = auto_content + cheatsheet_heading + preserved
        else:
            # No existing cheatsheet — create heading but leave body empty
            new_content = auto_content + cheatsheet_heading + "\n"
    else:
        # No README exists yet — create with empty cheatsheet section
        new_content = auto_content + cheatsheet_heading + "\n"

    readme_path.write_text(new_content, encoding='utf-8')
    print(f"✓ Wrote category README (preserved cheatsheet if present): {readme_path}")


def generate_root_readme(categories_info):
    """Generate main README.md at repository root."""
    readme_path = ROOT / 'README.md'
    
    total_labs = sum(info['total'] for info in categories_info)
    total_done = sum(info['done'] for info in categories_info)

    # header with badges
    header = (
        "# 🔐 OWASP Top 10 — Hands-on Lab Writeups\n\n"
        "_A curated collection of PortSwigger-style lab writeups, notes, and exploits for the OWASP Top 10 vulnerabilities._\n\n"
        "![GitHub repo size](https://img.shields.io/github/repo-size/Nish344/owasp-top10-web-security?color=green)\n"
        "![GitHub last commit](https://img.shields.io/github/last-commit/Nish344/owasp-top10-web-security)\n"
        "![License](https://img.shields.io/badge/License-MIT-brightgreen)\n"
        "![Workflow Status](https://github.com/Nish344/owasp-top10-web-security/actions/workflows/update-readme.yml/badge.svg)\n\n"
    )

    # progress summary + chart
    progress = f"**Overall progress:** {total_done} / {total_labs} labs completed.\n\n"
    chart = (
        "```mermaid\n"
        "pie showData\n"
        "  title OWASP Top 10 Lab Progress\n"
        f'  "Completed Labs" : {total_done}\n'
        f'  "Pending Labs" : {max(total_labs - total_done, 0)}\n'
        "```\n\n"
    )

    # categories with emoji
    categories = "## 📂 Categories\n\n"
    emoji_list = ["🟢","🔵","🟠","🟣","🟡","🔴","🟤","⚪","⚫","🟧"]
    for i, info in enumerate(categories_info):
        cat_name = info['name']
        rel = os.path.relpath(info['path'], ROOT)
        # Convert Windows paths to forward slashes for markdown
        rel = rel.replace('\\', '/')
        emoji = emoji_list[i % len(emoji_list)]
        categories += f"- {emoji} **{cat_name}** — {info['done']} / {info['total']} completed — [View]({rel}/README.md)\n"
    categories += "\n"

    # recent labs table
    labs_section = "## 🧪 Recent Labs\n\n"
    labs_section += "| Status | Lab | Category | Tags |\n"
    labs_section += "|--------|-----|----------|------|\n"
    
    for info in categories_info:
        # Show all labs, not just first 5
        for l in info['labs']:
            status = "✅" if l['date_completed'] else "⬜"
            rel_path = os.path.join(os.path.relpath(info['path'], ROOT), l['filename'])
            # Convert Windows paths to forward slashes
            rel_path = rel_path.replace('\\', '/')
            # URL encode spaces in filename
            rel_path = rel_path.replace(' ', '%20')
            tags = l['tag'] if l['tag'] else "-"
            labs_section += f"| {status} | [{l['title']}]({rel_path}) | {info['name']} | `{tags}` |\n"
    labs_section += "\n"

    # contribution + disclaimer
    footer = (
        "## 🤝 How to Contribute\n\n"
        "- Follow the filename and folder conventions: `NN-CategoryName/Lab-Name-ID.md`\n"
        "- Include front-matter at the top of each lab (see templates).\n"
        "- Submit a PR 🚀\n\n"
        "## ⚠️ Disclaimer\n\n"
        "> This repository is for **educational purposes only**.  \n"
        "> Do not attempt these techniques on systems you don't own or have explicit permission to test.\n"
    )

    content = header + progress + chart + categories + labs_section + footer
    readme_path.write_text(content, encoding='utf-8')
    print(f"✓ Wrote root README: {readme_path}")

def main():
    print("=" * 60)
    print("README Generator for OWASP Top 10 Lab Repository")
    print("=" * 60)
    print(f"\nScanning categories in: {ROOT}\n")
    
    cats = scan_categories(ROOT)
    
    if not cats:
        print("⚠️  No category folders found matching pattern 01-* or 01_*")
        return
    
    print(f"Found {len(cats)} categories:\n")
    
    categories_info = []
    # Manual lab totals override
    MANUAL_TOTALS = {
        '01 Broken Access Control': 13,
        '02 Cryptographic Failures': 10,
        '03 Injection': 20,
        # ... add more as needed
        }
    
    for cat in cats:
        name = cat.name.replace('_', ' ')
        labs = scan_labs(cat)
        done = sum(1 for l in labs if l['date_completed'])
        total = MANUAL_TOTALS.get(name, len(labs))
        print(f"  → Found {total} labs ({done} completed)")
        generate_category_readme(cat, labs, name, done, total)
        categories_info.append({
            'name': name,
            'path': cat,
            'labs': labs,
            'done': done,
            'total': total
        })
    
    print("\nGenerating root README.md...")
    generate_root_readme(categories_info)
    
    print("\n" + "=" * 60)
    print("✓ All READMEs generated successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
