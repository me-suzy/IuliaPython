import os
import regex

def remove_quotes_from_meta_description(html_content):
    """Curăță meta name="description" """
    pattern = regex.compile(r'(<meta name="description" content=")(.*?)(">)', regex.DOTALL)

    def replace_quotes(match):
        content = match.group(2)
        quote_chars = ['"', '„', '”', "'", '|', '&quot;', '&#39;', '&ldquo;', '&rdquo;', '&lsquo;', '&rsquo;']
        quotes_found = {char: content.count(char) for char in quote_chars if content.count(char) > 0}
        if quotes_found:
            print(f"   - Meta description: found quotes {quotes_found}")

        content_clean = content
        for char in quote_chars:
            content_clean = content_clean.replace(char, '')
        content_clean = content_clean.replace('\\"', '')  # Handle escaped quotes

        chars_removed = len(content) - len(content_clean)
        if chars_removed > 0:
            print(f"   - Meta description: eliminat {chars_removed} caractere")
        return match.group(1) + content_clean + match.group(3)

    return pattern.sub(replace_quotes, html_content), len(pattern.findall(html_content))

def remove_quotes_from_og_description(html_content):
    """Curăță meta property="og:description" """
    pattern = regex.compile(r'(<meta property="og:description" content=")(.*?)("\s*/>)', regex.DOTALL)

    def replace_quotes(match):
        content = match.group(2)
        quote_chars = ['"', '„', '”', "'", '|', '&quot;', '&#39;', '&ldquo;', '&rdquo;', '&lsquo;', '&rsquo;']
        quotes_found = {char: content.count(char) for char in quote_chars if content.count(char) > 0}
        if quotes_found:
            print(f"   - OG description: found quotes {quotes_found}")

        content_clean = content
        for char in quote_chars:
            content_clean = content_clean.replace(char, '')
        content_clean = content_clean.replace('\\"', '')  # Handle escaped quotes

        chars_removed = len(content) - len(content_clean)
        if chars_removed > 0:
            print(f"   - OG description: eliminat {chars_removed} caractere")
        return match.group(1) + content_clean + match.group(3)

    return pattern.sub(replace_quotes, html_content), len(pattern.findall(html_content))

def remove_quotes_from_json_description(html_content):
    """Curăță "description": "..." and "description":"..." """
    patterns = [
        (regex.compile(r'("description":\s*")(.*?)(",)', regex.DOTALL), "JSON description (with spaces)"),
        (regex.compile(r'("description":")(.*?)(",)', regex.DOTALL), "JSON description (no spaces)")
    ]

    total_matches = 0
    modified_content = html_content

    for pattern, name in patterns:
        def replace_quotes(match):
            content = match.group(2)
            quote_chars = ['"', '„', '”', "'", '|', '&quot;', '&#39;', '&ldquo;', '&rdquo;', '&lsquo;', '&rsquo;']
            quotes_found = {char: content.count(char) for char in quote_chars if content.count(char) > 0}
            if quotes_found:
                print(f"   - {name}: found quotes {quotes_found}")

            content_clean = content
            for char in quote_chars:
                content_clean = content_clean.replace(char, '')
            content_clean = content_clean.replace('\\"', '')  # Handle escaped quotes

            chars_removed = len(content) - len(content_clean)
            if chars_removed > 0:
                print(f"   - {name}: eliminat {chars_removed} caractere")
            return match.group(1) + content_clean + match.group(3)

        modified_content = pattern.sub(replace_quotes, modified_content)
        total_matches += len(pattern.findall(html_content))

    return modified_content, total_matches

def extract_date_from_text_dreapta(html_content):
    """Extracts date like 'On Martie 18, 2025' from <td class="text_dreapta">"""
    BSR = r'<td class="text_dreapta">'
    ESR = r',\s+in\s+<a href="'
    FR = r'On\s+\w+\s+\d{1,2},\s+\d{4}'
    pattern = fr'(?-si:{BSR}|(?!\A)\G)(?s-i:(?!{ESR}).)*?\K(?-si:{FR})'

    matches = regex.findall(pattern, html_content, regex.DOTALL)
    chars_removed = 0
    modified_content = html_content

    if matches:
        print(f"   - Found {len(matches)} date matches in <td class=\"text_dreapta\">")
        for i, match in enumerate(matches):
            print(f"     - Date {i+1}: {match}")
            # Optionally replace the date with itself (or modify as needed)
            # For now, we just extract and report
        # If replacement is needed, uncomment and define RR
        # RR = r'\1'  # Example: keep the date
        # pattern_replace = fr'({BSR})(.*?)({FR})(.*?)({ESR})'
        # modified_content = regex.sub(pattern_replace, r'\1\2\3\4\5', html_content)
        # chars_removed = len(html_content) - len(modified_content)

    return modified_content, chars_removed, len(matches)

def replace_h3_with_h2(html_content):
    """Înlocuiește h3 class="text_obisnuit2" cu h2 class="text_obisnuit2" """
    patterns = [
        (regex.compile(r'<h3(\s+class=text_obisnuit2[^>]*)>(.*?)</h3>', regex.DOTALL), "h3 without quotes"),
        (regex.compile(r'<h3(\s+class="text_obisnuit2"[^>]*)>(.*?)</h3>', regex.DOTALL), "h3 with quotes")
    ]

    total_changes = 0
    modified_content = html_content

    for pattern, name in patterns:
        matches = pattern.findall(html_content)
        if matches:
            print(f"   - Found {len(matches)} {name} tags")
            for i, match in enumerate(matches):
                print(f"     - {name} match {i+1}: <h3{match[0]}>{match[1][:50]}...</h3>")
            modified_content = pattern.sub(r'<h2 class="text_obisnuit2">\2</h2>', modified_content)
            total_changes += len(matches)

    if total_changes > 0:
        print(f"   - Replaced {total_changes} h3 tags with h2")

    return modified_content, total_changes

def process_html_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.html'):
            file_path = os.path.join(folder_path, filename)
            print(f'\nProcesare: {filename}')

            try:
                with open(file_path, 'r', encoding='utf-8-sig') as file:
                    content = file.read()
                print(f"Successfully read {filename} ({len(content)} characters)")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                continue

            original_length = len(content)
            total_changes = 0

            # Remove quotes from descriptions
            content, meta_matches = remove_quotes_from_meta_description(content)
            content, og_matches = remove_quotes_from_og_description(content)
            content, json_matches = remove_quotes_from_json_description(content)

            # Extract date from <td class="text_dreapta">
            content, date_chars_removed, date_matches = extract_date_from_text_dreapta(content)

            # Replace h3 with h2
            content, h3_changes = replace_h3_with_h2(content)

            total_changes = meta_matches + og_matches + json_matches + date_matches + h3_changes
            chars_removed = original_length - len(content)

            if total_changes > 0 or chars_removed > 0:
                try:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"   - File updated successfully! (Removed {chars_removed} characters, {total_changes} total changes)")
                except Exception as e:
                    print(f"   - Error writing {file_path}: {e}")
            else:
                print("   - No changes made to file")

    print('\nToate fișierele au fost procesate.')

# Test
folder_path = r'c:\Folder1\fisiere_gata'
if os.path.exists(folder_path):
    print(f'=== Procesare folder: {folder_path} ===')
    process_html_files(folder_path)
else:
    print(f"Folder not found: {folder_path}")