import re
import os

def replace_headers_in_html(file_path):
    # Read the content of the HTML file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Store original content for comparison
    original_content = content

    # Case 1: Replace <h3 class="text_obisnuit2">(.*?)</h3> with <h2 class="text_obisnuit2"><em>(.*?)</em></h2>
    # Made pattern more flexible with optional whitespace and non-greedy matching
    pattern1 = r'<div itemprop="articleBody">\s*<!--\s*SASA-1\s*-->\s*<h3 class="text_obisnuit2">(.*?)</h3>'
    replacement1 = r'<div itemprop="articleBody">\n\n<!-- SASA-1 -->\n        <h2 class="text_obisnuit2"><em>\1</em></h2>'
    content, count1 = re.subn(pattern1, replacement1, content, flags=re.DOTALL)

    # Case 2: Add <!-- SASA-1 --> before <h2 class="text_obisnuit2"><em>(.*?)</em></h2>
    # Made pattern more flexible with optional whitespace
    pattern2 = r'<div itemprop="articleBody">\s*<h2 class="text_obisnuit2"><em>(.*?)</em></h2>'
    replacement2 = r'<div itemprop="articleBody">\n\n<!-- SASA-1 -->\n        <h2 class="text_obisnuit2"><em>\1</em></h2>'
    content, count2 = re.subn(pattern2, replacement2, content, flags=re.DOTALL)

    # Check if any replacements were made
    if count1 > 0 or count2 > 0:
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"Replaced {count1} occurrence(s) of pattern 1 and {count2} occurrence(s) of pattern 2 in {file_path}")
    else:
        print(f"No matches found in {file_path}")
        # Log a snippet of the content for debugging
        snippet = content[:500]  # First 500 characters
        print(f"Content snippet: {snippet}")

def process_html_files(directory):
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}")
                replace_headers_in_html(file_path)

# Specify the directory paths
directories = [
    r"c:\Folder1\fisiere_gata"
]

# Process both directories
for directory in directories:
    print(f"\n=== Processing directory: {directory} ===")
    if os.path.exists(directory):
        process_html_files(directory)
        print(f"=== Finished processing: {directory} ===\n")
    else:
        print(f"Directory does not exist: {directory}\n")