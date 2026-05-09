#!/usr/bin/env python3
"""Convert approach_document.md to PDF using reportlab."""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re

# Read markdown
with open("approach_document.md", "r", encoding="utf-8") as f:
    content = f.read()

# Create PDF
pdf_filename = "approach_document.pdf"
doc = SimpleDocTemplate(pdf_filename, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch,
                        leftMargin=0.5*inch, rightMargin=0.5*inch)
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=14,
    textColor=colors.HexColor('#000000'),
    spaceAfter=6,
    fontName='Helvetica-Bold'
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=11,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=4,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['BodyText'],
    fontSize=9,
    leading=10,
    alignment=TA_LEFT,
    spaceAfter=3
)

code_style = ParagraphStyle(
    'Code',
    parent=styles['Code'],
    fontSize=8,
    leading=9,
    fontName='Courier',
    textColor=colors.HexColor('#333333'),
    spaceAfter=2
)

# Parse markdown and build story
story = []

# Split by sections
lines = content.split('\n')
i = 0

while i < len(lines):
    line = lines[i].strip()
    
    # Skip empty lines
    if not line:
        i += 1
        continue
    
    # Title (# )
    if line.startswith('# '):
        title = line[2:].strip()
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.1*inch))
        i += 1
    
    # Heading (## )
    elif line.startswith('## '):
        heading = line[3:].strip()
        story.append(Paragraph(heading, heading_style))
        story.append(Spacer(1, 0.05*inch))
        i += 1
    
    # Subheading (### )
    elif line.startswith('### '):
        subheading = line[4:].strip()
        story.append(Paragraph(subheading, heading_style))
        story.append(Spacer(1, 0.03*inch))
        i += 1
    
    # Code block
    elif line.startswith('```'):
        code_lines = []
        i += 1
        while i < len(lines) and not lines[i].strip().startswith('```'):
            code_lines.append(lines[i])
            i += 1
        code_text = '\n'.join(code_lines).strip()
        if code_text:
            # For code, use preformatted text
            story.append(Paragraph('<font name="Courier" size="7">' + code_text.replace('\n', '<br/>') + '</font>', body_style))
            story.append(Spacer(1, 0.05*inch))
        i += 1
    
    # Bullet points (- or *)
    elif line.startswith('- ') or line.startswith('* '):
        bullet_text = line[2:].strip()
        story.append(Paragraph('• ' + bullet_text, body_style))
        i += 1
    
    # Regular paragraph (starts with |, which is table delimiter)
    elif '|' in line:
        # Simple table handling
        i += 1
    
    # Regular text
    elif line:
        # Clean up markdown formatting
        text = line.replace('**', '<b>').replace('__', '<b>')
        text = text.replace('**', '</b>').replace('__', '</b>')
        text = text.replace('`', '<font name="Courier">')
        # Count backticks to handle closing
        story.append(Paragraph(text, body_style))
        i += 1
    else:
        i += 1

# Build PDF
doc.build(story)
print(f"✓ PDF created: {pdf_filename}")
