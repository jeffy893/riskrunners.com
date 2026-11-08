import json
import os
from bs4 import BeautifulSoup
import re
import random

# Define the directory containing the HTML files ('.' means the current directory)
html_directory = '.'
# Define the output filename for the search index
output_filename = '002_search-index.json'
# Define the file to exclude from indexing
exclude_file = '000_index.html' # Or whatever your main index file is named

# Global lists/dictionaries to collect data across all files
all_table_data = [] # Stores items from Industries, Exposures, Event Codes tables
# Stores unique source/target strings found across all files, mapping node string to the first file where found
unique_link_nodes_global = {}

# Helper function to clean text
def clean_text(text):
    # Remove leading/trailing whitespace and excess internal whitespace
    return ' '.join(text.split()).strip()

# --- Define the extraction logic ---
def extract_data_from_html(html_content, source_filename):
    """
    Extracts Industries, Exposures, Event Codes from tables
    and collects unique link nodes from script tags for global processing.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    print(f"Processing: {source_filename}")

    # --- Extract Industries, Exposures, Event Codes (Add to global list) ---
    sections_to_extract = {
        'industry': 'Industry',
        'exposure': 'Exposure',
        'event_code': 'Event Code'
    }

    for section_id, section_name in sections_to_extract.items():
        header_tag = soup.find('th', id=section_id)
        if header_tag:
            table = header_tag.find_parent('table')
            if table:
                items = table.select('tbody tr td')
                for item_tag in items:
                    item_text = clean_text(item_tag.get_text())
                    if item_text:
                        all_table_data.append({ # Add to global list
                            "title": item_text,
                            "type": section_name,
                            "url": f"{source_filename}#{section_id}",
                            "source_file": source_filename
                        })
            # else warnings could be added here if tables are expected

    # --- Collect Unique Link Nodes from script tags (Add to global dict) ---
    script_tags = soup.find_all('script')

    for script in script_tags:
        script_content = script.string
        if script_content:
            match = re.search(r'var\s+links\s*=\s*(\[\s*\{.*?\}\s*\])\s*;', script_content, re.DOTALL)

            if match:
                links_array_string = match.group(1)

                try:
                    # Convert JS object literal keys to JSON string keys
                    json_compatible_string = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', links_array_string)
                    links_data = json.loads(json_compatible_string)

                    # Add nodes found in THIS file to the global unique set, recording the source file
                    nodes_in_this_file = set()
                    for link in links_data:
                        source = clean_text(link.get('source', ''))
                        target = clean_text(link.get('target', ''))

                        if source and source != "START_HERE":
                            nodes_in_this_file.add(source)
                        if target and target != "START_HERE":
                            nodes_in_this_file.add(target)

                    # Add nodes unique to this file to the global dictionary
                    for node in nodes_in_this_file:
                         if node not in unique_link_nodes_global:
                              unique_link_nodes_global[node] = source_filename # Record the first file this node was found in

                except (json.JSONDecodeError, re.error, AttributeError) as e:
                    print(f"  Warning: Could not parse links array in {source_filename}. Error: {e}")

                # Assuming the links array is only defined once per relevant file, stop after finding it
                break # Stop after finding the first links array

    # Optional: Print stats for the file
    # print(f"  Finished processing tables and collecting link nodes from {source_filename}") # Uncomment for verbose output


# --- Iterate through files and process ---
try:
    all_files_in_dir = os.listdir(html_directory)
    html_files_to_process = [
        f for f in all_files_in_dir
        if os.path.isfile(os.path.join(html_directory, f)) and f.lower().endswith('.html') and f != exclude_file
    ]

    if not html_files_to_process:
        print(f"No HTML files found in '{html_directory}' (excluding '{exclude_file}').")

    for filename in html_files_to_process:
        filepath = os.path.join(html_directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Extract data and collect link nodes from the current file
            extract_data_from_html(html_content, filename)

        except Exception as e:
            print(f"  Error processing file {filename}: {e}")

except Exception as e:
    print(f"Error accessing directory {html_directory}: {e}")


# --- Sample 1/8th of the globally unique link nodes ---
all_unique_node_strings = list(unique_link_nodes_global.keys())
total_unique_nodes = len(all_unique_node_strings)
num_to_sample_links = max(0, total_unique_nodes // 8) # Calculate 1/8th - THIS LINE IS CHANGED

# Ensure we don't try to sample more than exist
num_to_sample_links = min(num_to_sample_links, total_unique_nodes)

print(f"\nTotal unique link nodes found across all files: {total_unique_nodes}")
print(f"Sampling {num_to_sample_links} (approx 1/8th) for the index.")

sampled_node_strings = random.sample(all_unique_node_strings, num_to_sample_links)

# --- Prepare the final search data by combining table data and sampled link data ---
final_search_data = list(all_table_data) # Start with all collected table data
sampled_link_data = []

for node_string in sampled_node_strings:
     source_file = unique_link_nodes_global[node_string] # Get the source file recorded earlier
     sampled_link_data.append({
         "title": node_string, # The node string is the title
         "type": "Link Node",
         "url": source_file, # Link to the source file where it was first found
         "source_file": source_file
     })

final_search_data.extend(sampled_link_data) # Add the sampled link nodes


# --- Write the combined data to search-index.json ---
if final_search_data:
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            # Use indent=None and separators=(',', ':') for the absolute smallest file size
            json.dump(final_search_data, f, indent=None, ensure_ascii=False, separators=(',', ':'))

        # Check the file size
        file_size_bytes = os.path.getsize(output_filename)
        file_size_mb = file_size_bytes / (1024 * 1024)

        print(f"\nSearch index generated successfully: {output_filename}")
        print(f"Total items indexed (tables + sampled links): {len(final_search_data)}")
        print(f"Generated file size: {file_size_mb:.2f} MB")

        if file_size_mb > 15: # Still warning if over 15MB
            print("\nWarning: The generated index is still larger than 15MB.")
            print("Achieving a ~10MB target with this volume of data is extremely difficult.")
            print("The current index only contains table items and sampled link nodes (title, type, URL, source file).")
            print("For reliable search performance, server-side is strongly recommended.")


    except Exception as e:
        print(f"Error writing search index file {output_filename}: {e}")
else:
    print("\nNo data extracted or sampled. No search index file was created.")