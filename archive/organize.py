#!/usr/bin/env python3
"""
Risk Runners - File Organization Script
Helps migrate existing company HTML files to the new organized structure.
"""

import os
import shutil
import json
from pathlib import Path

def organize_company_files():
    """Move company HTML files to the companies directory"""
    base_dir = Path('.')
    companies_dir = base_dir / 'companies'
    
    # Ensure companies directory exists
    companies_dir.mkdir(exist_ok=True)
    
    # Find all HTML files that appear to be company files
    company_files = []
    for file_path in base_dir.glob('*.html'):
        # Skip the main index files and other non-company files
        if file_path.name not in ['000_index.html', 'index.html']:
            company_files.append(file_path)
    
    print(f"Found {len(company_files)} company files to organize")
    
    # Move files to companies directory
    moved_count = 0
    for file_path in company_files:
        try:
            destination = companies_dir / file_path.name
            if not destination.exists():
                shutil.move(str(file_path), str(destination))
                moved_count += 1
                print(f"Moved: {file_path.name}")
        except Exception as e:
            print(f"Error moving {file_path.name}: {e}")
    
    print(f"Successfully moved {moved_count} files to /companies/")
    return moved_count

def update_search_index_paths():
    """Update search index to reflect new file paths"""
    search_index_path = Path('data/002_search-index.json')
    
    if not search_index_path.exists():
        print("Search index not found, skipping path updates")
        return
    
    try:
        with open(search_index_path, 'r') as f:
            search_data = json.load(f)
        
        # Update URLs to point to companies directory
        updated_count = 0
        for item in search_data:
            if 'url' in item and not item['url'].startswith('companies/'):
                # Only update if it's a company HTML file
                if item['url'].endswith('.html') and not item['url'].startswith('http'):
                    item['url'] = f"companies/{item['url']}"
                    updated_count += 1
        
        # Write back the updated data
        with open(search_index_path, 'w') as f:
            json.dump(search_data, f, indent=2)
        
        print(f"Updated {updated_count} URLs in search index")
        
    except Exception as e:
        print(f"Error updating search index: {e}")

def create_company_index():
    """Create an index of all companies for easier navigation"""
    companies_dir = Path('companies')
    
    if not companies_dir.exists():
        print("Companies directory not found")
        return
    
    companies = []
    for html_file in companies_dir.glob('*.html'):
        # Extract company info from filename
        name = html_file.stem.replace('_', ' ').title()
        companies.append({
            'name': name,
            'filename': html_file.name,
            'url': f"companies/{html_file.name}"
        })
    
    # Sort alphabetically
    companies.sort(key=lambda x: x['name'])
    
    # Save company index
    index_path = Path('data/company-index.json')
    with open(index_path, 'w') as f:
        json.dump(companies, f, indent=2)
    
    print(f"Created company index with {len(companies)} entries")

def main():
    """Main organization function"""
    print("🚀 Risk Runners - Website Organization Script")
    print("=" * 50)
    
    # Step 1: Organize company files
    print("\n📁 Step 1: Organizing company files...")
    moved_count = organize_company_files()
    
    # Step 2: Update search index paths
    print("\n🔍 Step 2: Updating search index paths...")
    update_search_index_paths()
    
    # Step 3: Create company index
    print("\n📊 Step 3: Creating company index...")
    create_company_index()
    
    print("\n✅ Organization complete!")
    print(f"   • Moved {moved_count} company files")
    print("   • Updated search index paths")
    print("   • Created company directory index")
    print("\n💡 Next steps:")
    print("   • Test the new index.html file")
    print("   • Update any hardcoded links")
    print("   • Consider adding a sitemap")

if __name__ == "__main__":
    main()