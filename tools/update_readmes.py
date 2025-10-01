#!/usr/bin/env python3
"""
update_readmes.py

Scans repo for category folders named like "01-Broken-Access-Control" or "01_Broken_Access_Control",
parses lab markdown front-matter and generates:

- Root README.md with badges, progress chart, categories, recent labs.
- README.md inside each category with checklist and cheatsheet placeholder.
"""

import os
import re
from pathlib import Path

ROOT = Path('.').resolve()

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.IGNORECASE)
KEY_RE = re.compile(r'^\s*([A-Za-z0-9_\-]+)\s*:\s*(.+)\s*$', re.MULTILINE)

CATEGORY_FOLDER_RE = re.compile(r'^\d{2}[-_].+')

def parse_front_matter(md_text):
    """Return dict of front-matter keys (lowercased)."""
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
        title = fm.get('title', '') or md.stem.replace('-', ' ').replace('_', ' ').title()
        lab_id = fm.get('lab_id', '')
        date_completed = fm.get('date_completed', '')
        tag = fm.get('tag', '')
        labs.append({
            'filename': md.name,
            'title': title,
            'lab_id': lab_id,
            'date_completed': date_completed,
            'tag': tag,
        })
    return labs

def generate_category_readme(category_path, labs, category_title):
    readme_path = category_path / 'README.md'
    completed = sum(1 for l in labs if l['date_completed'])
    total = len(labs)
    header = f"# {category_title}\n\n"
    intro = (
        f"This folder contains lab writeups for the **{category_title}** category.\n\n"
        f"### Progress\n\n- Completed: **{completed}** / **{total}**\n\n### Labs\n\n"
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
        emoji = emoji_list[i % len(emoji_list)]
        categories += f"- {emoji} **{cat_name}** — {info['done']} / {info['total']} completed — [View]({rel}/README.md)\n"
    categories += "\n"

    # recent labs table
    labs_section = "## 🧪 Recent Labs\n\n"
    labs_section += "| Status | Lab | Category | Tags |\n"
    labs_section += "|--------|-----|----------|------|\n"
    for info in categories_info:
        for l in info['labs'][:5]:
            status = "✅" if l['date_completed'] else "⬜"
            rel_path = os.path.join(os.path.relpath(info['path'], ROOT), l['filename'])
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
        "> Do not attempt these techniques on systems you don’t own or have explicit permission to test.\n"
    )

    content = header + progress + chart + categories + labs_section + footer
    readme_path.write_text(content, encoding='utf-8')
    print(f"Wrote root README: {readme_path}")

def main():
    print("Scanning categories...")
    cats = scan_categories(ROOT)
    categories_info = []
    for cat in cats:
        name = cat.name.replace('_','-')
        labs = scan_labs(cat)
        done = sum(1 for l in labs if l['date_completed'])
        total = len(labs)
        generate_category_readme(cat, labs, name.replace('-', ' '))
        categories_info.append({
            'name': name.replace('-', ' '),
            'path': cat,
            'labs': labs,
            'done': done,
            'total': total
        })
    generate_root_readme(categories_info)
    print("Done.")

if __name__ == '__main__':
    main()
