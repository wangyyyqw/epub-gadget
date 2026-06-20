#!/usr/bin/env python3
"""
Analyze EPUB annotation/note formats
"""
import zipfile
import re
from html.parser import HTMLParser

def analyze_epub(filepath, name):
    print(f"\n{'='*80}")
    print(f"EPUB: {name}")
    print(f"Path: {filepath}")
    print('='*80)
    
    # Patterns to search for
    patterns = {
        'sup_tags': r'<sup[^>]*>.*?</sup>',
        'a_href_fn': r'<a[^>]*href=["\'][^"\']*#fn[^"\']*["\'][^>]*>.*?</a>',
        'a_href_anchors': r'<a[^>]*href=["\'][^"\']*#(?!fn)[^"\']*["\'][^>]*>.*?</a>',
        'aside': r'<aside[^>]*>.*?</aside>',
        'footnote': r'<footnote[^>]*>.*?</footnote>',
        'noteref': r'<noteref[^>]*>.*?</noteref>',
        'note_class': r'class=["\'][^"\']*note[^"\']*["\']',
        'reader_spans': r'<span[^>]*class=["\'][^"\']*reader[^"\']*["\'][^>]*>.*?</span>',
        'js_readerFooterNote': r'class=["\'][^"\']*js_readerFooterNote[^"\']*["\']',
        'fn_ref': r'<a[^>]*href=["\'][^"\']*#fnref[^"\']*["\'][^>]*>.*?</a>',
    }
    
    html_files = []
    css_files = []
    opf_files = []
    ncxml_files = []
    
    with zipfile.ZipFile(filepath) as z:
        all_items = z.namelist()
        print(f"\nTotal files in EPUB: {len(all_items)}")
        
        # List all files
        print("\n--- All files in EPUB ---")
        for item in sorted(all_items):
            print(f"  {item}")
        
        for item in z.infolist():
            name_lower = item.filename.lower()
            if name_lower.endswith(('.html', '.xhtml')):
                html_files.append((item.filename, z.read(item.filename).decode('utf-8', errors='ignore')))
            elif name_lower.endswith('.css'):
                css_files.append((item.filename, z.read(item.filename).decode('utf-8', errors='ignore')))
            elif name_lower.endswith('.opf'):
                opf_files.append((item.filename, z.read(item.filename).decode('utf-8', errors='ignore')))
            elif 'ncx' in name_lower or name_lower.endswith('.ncx'):
                ncxml_files.append((item.filename, z.read(item.filename).decode('utf-8', errors='ignore')))
    
    # Analyze HTML files
    print("\n" + "="*80)
    print("HTML/XHTML ANALYSIS")
    print("="*80)
    
    for filename, content in html_files:
        print(f"\n--- File: {filename} ---")
        found_any = False
        
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                found_any = True
                print(f"\n  [{pattern_name}] Found {len(matches)} matches:")
                for i, match in enumerate(matches[:10]):  # Limit to 10 matches per pattern
                    # Get context (surrounding text)
                    idx = content.find(match)
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(match) + 100)
                    context = content[start:end]
                    # Clean up for display
                    context_clean = context.replace('\n', ' ').replace('\r', ' ')
                    print(f"    Example {i+1}: ...{context_clean}...")
        
        if not found_any:
            print("  No note/annotation patterns found.")
    
    # Analyze CSS files for note-related styles
    print("\n" + "="*80)
    print("CSS ANALYSIS - Note-related styles")
    print("="*80)
    
    for filename, content in css_files:
        print(f"\n--- File: {filename} ---")
        # Find note-related CSS rules
        note_styles = re.findall(r'[^{]*\{[^}]*note[^}]*\}', content, re.IGNORECASE)
        sup_styles = re.findall(r'[^{]*\{[^}]*sup[^}]*\}', content, re.IGNORECASE)
        footnote_styles = re.findall(r'[^{]*\{[^}]*footnote[^}]*\}', content, re.IGNORECASE)
        reader_styles = re.findall(r'[^{]*\{[^}]*reader[^}]*\}', content, re.IGNORECASE)
        
        all_styles = set(note_styles + sup_styles + footnote_styles + reader_styles)
        
        if all_styles:
            for style in all_styles:
                print(f"  {style.strip()}")
        else:
            print("  No note-related CSS rules found.")
            
        # Also print all unique class selectors
        classes = re.findall(r'\.[\w-]+', content)
        note_classes = [c for c in classes if 'note' in c.lower() or 'fn' in c.lower() or 'reader' in c.lower()]
        if note_classes:
            print(f"\n  Note-related classes found: {set(note_classes)}")
    
    # Analyze OPF files
    print("\n" + "="*80)
    print("OPF MANIFEST ANALYSIS")
    print("="*80)
    
    for filename, content in css_files:
        print(f"\n--- CSS File: {filename} ---")
        if 'note' in content.lower() or 'footnote' in content.lower():
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if any(kw in line.lower() for kw in ['note', 'footnote', 'fn']):
                    context = lines[max(0,i-2):i+3]
                    print("  Context lines:")
                    for ctx in context:
                        print(f"    {ctx}")
                    print()

# Run analysis
epub_files = [
    ('/Users/aaa/Documents/github/epub-gadget/逃离未来.epub', '逃离未来'),
    ('/Users/aaa/Documents/github/epub-gadget/油炸绿番茄__美_范妮·弗拉格.epub', '油炸绿番茄'),
]

for filepath, name in epub_files:
    try:
        analyze_epub(filepath, name)
    except Exception as e:
        print(f"Error analyzing {name}: {e}")
        import traceback
        traceback.print_exc()
