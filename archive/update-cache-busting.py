#!/usr/bin/env python3
"""
Update HTML files with cache-busting parameters for JavaScript files
"""

import os
import re
import time
from pathlib import Path

def update_html_cache_busting():
    """Add cache-busting parameters to JavaScript includes in HTML files"""
    
    # Get current timestamp for cache busting
    timestamp = str(int(time.time()))
    
    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files to update")
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Pattern to match local JavaScript includes (not CDN)
            # Matches: <script src="path/to/file.js"></script>
            # But not: <script src="https://..."></script>
            js_pattern = r'<script\s+src="([^"]*\.js)"(?:\?v=\d+)?></script>'
            
            def replace_js_src(match):
                src = match.group(1)
                # Skip CDN URLs (those starting with http:// or https://)
                if src.startswith(('http://', 'https://')):
                    return match.group(0)  # Return unchanged
                
                # Add cache-busting parameter
                return f'<script src="{src}?v={timestamp}"></script>'
            
            # Replace JavaScript includes
            content = re.sub(js_pattern, replace_js_src, content)
            
            # Only write if content changed
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated: {html_file}")
            else:
                print(f"No changes: {html_file}")
                
        except Exception as e:
            print(f"Error updating {html_file}: {e}")

if __name__ == "__main__":
    print("🔄 Updating HTML files with cache-busting parameters...")
    update_html_cache_busting()
    print("✅ Cache-busting update complete!")