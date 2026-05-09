#!/usr/bin/env python3
"""Convert approach_document.md to HTML that can be printed to PDF."""

import re

# Read markdown
with open("approach_document.md", "r", encoding="utf-8") as f:
    content = f.read()

# Simple markdown to HTML conversion
html_content = content

# Headers
html_content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
html_content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
html_content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)

# Bold
html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)

# Code blocks
html_content = re.sub(
    r'```(.*?)```',
    lambda m: '<pre style="background-color: #f4f4f4; padding: 10px; overflow-x: auto; font-size: 11px;">' + m.group(1).strip() + '</pre>',
    html_content,
    flags=re.DOTALL
)

# Inline code
html_content = re.sub(r'`([^`]+)`', r'<code style="background-color: #f0f0f0; padding: 2px 5px; font-family: monospace;">\1</code>', html_content)

# Bullet points
html_content = re.sub(r'^- (.*?)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
html_content = re.sub(r'^• (.*?)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)

# Wrap lists
html_content = re.sub(r'(<li>.*?</li>)', lambda m: '<ul>' + m.group(1) if not m.group(1).startswith('<ul') else m.group(1), html_content)

# Tables (simple)
html_content = re.sub(
    r'\|(.*?)\|',
    lambda m: m.group(1).strip(),
    html_content
)

# Line breaks
html_content = re.sub(r'\n\n+', '</p><p>', html_content)

# Final HTML wrapper
html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SHL Assessment Recommender — Approach Document</title>
    <style>
        body {{
            font-family: Segoe UI, Tahoma, Geneva, Verdana, sans-serif;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 0.5in;
            line-height: 1.4;
            color: #333;
            font-size: 10px;
        }}
        h1 {{
            font-size: 16px;
            margin: 12px 0 6px 0;
            page-break-after: avoid;
        }}
        h2 {{
            font-size: 12px;
            margin: 10px 0 4px 0;
            page-break-after: avoid;
        }}
        h3 {{
            font-size: 11px;
            margin: 8px 0 3px 0;
            page-break-after: avoid;
        }}
        p {{
            margin: 4px 0;
        }}
        ul {{
            margin: 4px 0;
            padding-left: 20px;
        }}
        li {{
            margin: 2px 0;
        }}
        pre {{
            font-size: 9px !important;
            line-height: 1.2 !important;
        }}
        code {{
            font-size: 9px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 6px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 4px;
            text-align: left;
            font-size: 9px;
        }}
        th {{
            background-color: #f9f9f9;
        }}
        strong {{
            font-weight: bold;
        }}
        @media print {{
            body {{
                margin: 0;
                padding: 0.5in;
            }}
            h1, h2, h3 {{
                page-break-after: avoid;
            }}
            ul, p {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
<p>{html_content}</p>
</body>
</html>
"""

with open("approach_document.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("✓ HTML created: approach_document.html")
print("  (Open in browser and use Print → Save as PDF)")
