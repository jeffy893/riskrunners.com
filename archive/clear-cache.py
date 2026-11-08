#!/usr/bin/env python3
"""
Clear browser cache by updating cache-busting parameters
"""

import os
import sys
from pathlib import Path

def main():
    print("🧹 Clearing browser cache...")
    print("This will update cache-busting parameters in HTML files")
    print("to force browsers to reload JavaScript files.")
    print()
    
    # Run the cache-busting update
    script_dir = Path(__file__).parent
    update_script = script_dir / "update-cache-busting.py"
    
    if update_script.exists():
        os.system(f"python3 {update_script}")
        print()
        print("✅ Cache cleared! JavaScript files will be reloaded on next page visit.")
        print("💡 If you're still seeing old behavior:")
        print("   1. Hard refresh your browser (Ctrl+F5 or Cmd+Shift+R)")
        print("   2. Open browser dev tools and disable cache")
        print("   3. Try an incognito/private window")
    else:
        print("❌ Cache-busting script not found!")
        sys.exit(1)

if __name__ == "__main__":
    main()