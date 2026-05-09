#!/usr/bin/env python3
"""
Convert HTML to PDF using available tools.
Tries multiple methods in order of preference.
"""

import subprocess
import sys
import os
from pathlib import Path

def try_wkhtmltopdf():
    """Try using wkhtmltopdf if available."""
    try:
        subprocess.run(['wkhtmltopdf', '--version'], capture_output=True, check=True)
        subprocess.run([
            'wkhtmltopdf',
            'approach_document.html',
            'approach_document.pdf'
        ], check=True)
        print("✓ PDF created with wkhtmltopdf")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def try_weasyprint():
    """Try using weasyprint if available."""
    try:
        from weasyprint import HTML
        HTML('approach_document.html').write_pdf('approach_document.pdf')
        print("✓ PDF created with weasyprint")
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"weasyprint error: {e}")
        return False

def try_reportlab():
    """Try using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from html.parser import HTMLParser
        import re
        
        # Read HTML
        with open('approach_document.html', 'r') as f:
            html = f.read()
        
        # Extract text content
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.text = []
            def handle_data(self, d):
                self.text.append(d)
            def get_data(self):
                return ''.join(self.text)
        
        stripper = MLStripper()
        stripper.feed(html)
        text = stripper.get_data()
        
        # Create simple PDF
        c = canvas.Canvas('approach_document.pdf', pagesize=A4)
        width, height = A4
        
        # Add content
        y = height - 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "SHL Assessment Recommender")
        c.drawString(40, y - 20, "Approach Document")
        
        c.setFont("Helvetica", 9)
        y -= 50
        
        for line in text.split('\n'):
            line = line.strip()
            if line and y > 40:
                if len(line) > 85:
                    words = line.split()
                    current_line = ''
                    for word in words:
                        if len(current_line) + len(word) < 85:
                            current_line += word + ' '
                        else:
                            if current_line:
                                c.drawString(40, y, current_line)
                            y -= 10
                            current_line = word + ' '
                    if current_line:
                        c.drawString(40, y, current_line)
                    y -= 10
                else:
                    c.drawString(40, y, line)
                    y -= 10
            
            # Auto page break
            if y < 50:
                c.showPage()
                y = height - 40
        
        c.save()
        print("✓ PDF created with reportlab")
        return True
    except Exception as e:
        print(f"reportlab error: {e}")
        return False

def manual_instructions():
    """Print manual instructions."""
    print("""
════════════════════════════════════════════════════════════════
  To convert approach_document.html to PDF manually:
════════════════════════════════════════════════════════════════

OPTION 1 - Browser Print (Recommended):
  1. Open: approach_document.html in your browser
  2. Press: Ctrl+P (or Cmd+P on Mac)
  3. Select: "Save as PDF"
  4. Name it: approach_document.pdf

OPTION 2 - GitHub Web:
  1. Go to: https://github.com/contact-shreyas/SHL
  2. Open: approach_document.html
  3. Click: "Raw" button
  4. Right-click → "Save page as" → Select PDF

════════════════════════════════════════════════════════════════
    """)

if __name__ == '__main__':
    html_file = Path('approach_document.html')
    if not html_file.exists():
        print("Error: approach_document.html not found")
        sys.exit(1)
    
    # Try methods in order
    methods = [
        ("wkhtmltopdf", try_wkhtmltopdf),
        ("weasyprint", try_weasyprint),
        ("reportlab", try_reportlab),
    ]
    
    success = False
    for name, method in methods:
        print(f"Trying {name}...", end=" ")
        try:
            if method():
                success = True
                break
        except Exception as e:
            print(f"failed: {e}")
    
    if success:
        print(f"\n✓ PDF file created: approach_document.pdf")
        print(f"  Location: {Path('approach_document.pdf').absolute()}")
    else:
        print("\n✗ Could not auto-generate PDF with available tools.")
        print("  Using manual method instead...\n")
        manual_instructions()
        sys.exit(0)
