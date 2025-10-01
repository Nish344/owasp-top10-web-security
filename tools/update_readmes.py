#!/usr/bin/env python3
"""
update_readmes.py

Scans repo for category folders named with a numeric prefix like "01-Injection",
parses lab markdown front-matter (YAML style at top of file) and generates:

- README.md (root) with summary, badges, category index, and per-category progress.
- README.md inside each category folder with quick summary and checklist of labs.

Front-matter supported keys (case-insensitive): Title, title, Lab_ID, lab_id, Category,
category, Date_Completed, date_completed, Tag, tag (comma separated or single string).

This script avoids external deps and uses regex parsing.
"""

import os
import re
from pathlib import Path
from datetime import datetime

ROOT = Path('.').resolve()
TOOLS_DIR = ROOT / 'tools'

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.IGNORECASE)
KEY_RE = re.compile(r'^\s*([A-Za-z0-9_\-]+)\s*:\s*(.+)\s*$', re.MULTILINE)

CATEGORY_FOLDER_RE = re.compile(r'^\d{2}-.+')

def parse_front_matter(md_text):
    """Return dict of front-matter keys (lowercased) if present, else {}."""
    m = FRONT_MATTER_RE.match(md_text)
    if not m:
        return {}
    block = m.group(1)
    data = {}
    for km in KEY_RE.finditer(block):
        k = km.group(1).strip().lower()
        v = km.group(2).strip().strip('"').strip("'")
        data[k] = v
    return data

def scan_categories(root):
    categories = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and CATEGORY_FOLDER_RE.match(p.name):
            categories.append(p)
    return categories

def scan_labs(category_path):
    labs = []
    for md in sorted(category_path.glob('*.md')):
        text = md.read_text(encoding='utf-8', errors='ignore')
        fm = parse_front_matter(text)
        title = fm.get('title') or fm.get('Title') or ''
        lab_id = fm.get('lab_id') or fm.get('Lab_ID') or ''
        date_completed = fm.get('date_completed') or fm.get('Date_Completed') or ''
        tag = fm.get('tag') or fm.get('Tag') or ''
        # fallback title from filename if not present
        if not title:
            title = md.stem.replace('-', ' ').replace('_', ' ').title()
        labs.append({
            'path': md,
            'filename': md.name,
            'title': title,
            'lab_id': lab_id,
            'date_completed': date_completed,
            'tag': tag,
        })
    return labs

def generate_category_readme(category_path, labs, category_title):
    """Create/overwrite README.md inside category folder."""
    readme_path = category_path / 'README.md'
    completed = sum(1 for l in labs if l['date_completed'])
    total = len(labs)
    header = f"# {category_title}\n\n"
    intro = (
        "This folder contains lab writeups for the **" + category_title + "** category.\n\n"
        "### Progress\n\n"
        f"- Completed: **{completed}** / **{total}**\n\n"
        "### Labs\n\n"
    )
    lines = []
    for l in labs:
        status = "✅" if l['date_completed'] else "⬜"
        lab_line = f"- {status} [{l['title']}]({l['filename']})"
        if l['lab_id']:
            lab_line += f" — `{l['lab_id']}`"
        if l['tag']:
            lab_line += f" — _{l['tag']}_"
        lines.append(lab_line)
    cheatsheet = "\n\n### Cheatsheet / Quick Notes\n\n- (Add category-specific payloads / detection tips here)\n"
    content = header + intro + "\n".join(lines) + cheatsheet + "\n"
    readme_path.write_text(content, encoding='utf-8')
    print(f"Wrote category README: {readme_path}")

def generate_root_readme(categories_info):
    """Generate root README.md (overwrites)."""
    readme_path = ROOT / 'README.md'
    # Basic header / badges (customize as needed)
    header = (
        "# OWASP Top 10 — Hands-on Lab Writeups\n\n"
        "A curated collection of PortSwigger / lab-style writeups for the OWASP Top 10.\n\n"
    )
    badges = (
        "<!-- badges: start -->\n"
        "![License](https://img.shields.io/badge/license-MIT-brightgreen)\n"
        "![Progress](https://img.shields.io/badge/progress-up--to--date-green)\n"
        "<!-- badges: end -->\n\n"
    )
    toc = "## Categories\n\n"
    total_labs = sum(info['total'] for info in categories_info)
    total_done = sum(info['done'] for info in categories_info)
    summary = f"**Overall progress:** {total_done} / {total_labs} labs completed.\n\n"
    # categories list
    cat_lines = []
    for info in categories_info:
        cat_name = info['name']
        rel = os.path.relpath(info['path'], ROOT)
        cat_lines.append(f"- **{cat_name}** — {info['done']} / {info['total']} completed — [{rel}/{ 'README.md' }]({rel}/README.md)")
    cat_section = "\n".join(cat_lines) + "\n\n"
    # auto-generated table of contents per category (first 5 labs shown)
    labs_section = "## Recent / Example Labs\n\n"
    for info in categories_info:
        labs = info['labs']
        if not labs:
            continue
        labs_section += f"### {info['name']}\n\n"
        for l in labs[:10]:
            status = "✅" if l['date_completed'] else "⬜"
            rel_path = os.path.join(os.path.relpath(info['path'], ROOT), l['filename'])
            labs_section += f"- {status} [{l['title']}]({rel_path})"
            if l['lab_id']:
                labs_section += f" — `{l['lab_id']}`"
            labs_section += "\n"
        labs_section += "\n"
    footer = (
        "## How to contribute\n\n"
        "- Follow the filename and folder conventions: `NN-CategoryName/Short-Name-NNN.md`\n"
        "- Include front-matter at the top of each lab (see templates).\n"
        "- Open a PR and add yourself to the contributors list.\n\n"
        "## Disclaimer\n\n"
        "This repository is for educational purposes only. Do not test these techniques on systems you do not own or have authorization to test.\n"
    )
    content = header + badges + summary + toc + cat_section + labs_section + footer
    readme_path.write_text(content, encoding='utf-8')
    print(f"Wrote root README: {readme_path}")

def main():
    print("Scanning categories...")
    cats = scan_categories(ROOT)
    categories_info = []
    for cat in cats:
        name = cat.name
        labs = scan_labs(cat)
        done = sum(1 for l in labs if l['date_completed'])
        total = len(labs)
        # Generate category README
        generate_category_readme(cat, labs, name.replace('-', ' '))
        categories_info.append({
            'name': name.replace('-', ' '),
            'path': cat,
            'labs': labs,
            'done': done,
            'total': total
        })
    # Sort categories by prefix numeric order if present
    categories_info.sort(key=lambda x: x['name'])
    generate_root_readme(categories_info)
    print("Done.")

if __name__ == '__main__':
    main()
