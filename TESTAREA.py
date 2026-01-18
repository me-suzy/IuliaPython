import os
import re
import unidecode
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from datetime import datetime

def make_links_clickable(text):
    return re.sub(r'(https?://[^\s]+)', r'<a href="\1">\1</a>', text)

def extract_data_from_docx(file_path):
    doc = Document(file_path)
    articles = []
    current_title = None
    current_body = []
    current_id = None
    current_date = None
    current_category = None
    current_ro_link = None
    is_id_line = False
    is_date_line = False
    is_category_line = False
    is_ro_link_line = False

    for para in doc.paragraphs:
        text = para.text.strip()

        if para.alignment == WD_PARAGRAPH_ALIGNMENT.CENTER and text and not text.startswith(("ID:", "Date:", "Category:", "RO Link:")):
            if current_title:
                articles.append((current_title, current_body, current_id, current_date, current_category, current_ro_link))
                current_body = []
                current_id = None
                current_date = None
                current_category = None
                current_ro_link = None
            current_title = text
            is_id_line = True
        elif is_id_line and text.startswith("ID:"):
            current_id = text.replace("ID:", "").strip()
            is_id_line = False
            is_date_line = True
        elif is_date_line and text.startswith("Date:"):
            current_date = text.replace("Date:", "").strip()
            is_date_line = False
            is_category_line = True
        elif is_category_line and text.startswith("Category:"):
            current_category = text.replace("Category:", "").strip()
            is_category_line = False
            is_ro_link_line = True
        elif is_ro_link_line and text.startswith("RO Link:"):
            current_ro_link = text.replace("RO Link:", "").strip()
            is_ro_link_line = False
        elif current_title and text:
            is_id_line = is_date_line = is_category_line = is_ro_link_line = False
            formatted_text = []
            for run in para.runs:
                if run.bold and run.italic:
                    formatted_text.append(f'<strong><em>{run.text}</em></strong>')
                elif run.bold:
                    formatted_text.append(f'<strong>{run.text}</strong>')
                elif run.italic:
                    formatted_text.append(f'<em>{run.text}</em>')
                else:
                    formatted_text.append(run.text)
            paragraph_text = ''.join(formatted_text)
            paragraph_text = make_links_clickable(paragraph_text)
            current_body.append(paragraph_text)

    if current_title:
        articles.append((current_title, current_body, current_id, current_date, current_category, current_ro_link))

    return articles

def remove_diacritics(text):
    return unidecode.unidecode(text)

def generate_filename(title):
    normalized_title = remove_diacritics(title.lower())
    normalized_title = re.sub(r'[^a-z0-9\-]+', '-', normalized_title)
    normalized_title = re.sub(r'-+', '-', normalized_title).strip('-')
    return f"{normalized_title}.html"

def format_body(body):
    formatted_body = ""
    for paragraph in body:
        paragraph = paragraph.strip()
        numbered_paragraph = re.match(r'^(\d+\.\s+)(.*)', paragraph)
        if numbered_paragraph:
            num = numbered_paragraph.group(1)
            rest_of_paragraph = numbered_paragraph.group(2)
            formatted_body += f'<p class="text_obisnuit"><span class="text_obisnuit2"><strong>{num}</strong></span>{rest_of_paragraph}</p>\n'
        else:
            formatted_body += f'<p class="text_obisnuit">{paragraph}</p>\n'
    return formatted_body

def capitalize_title(title):
    words = title.split()
    capitalized_words = [word.capitalize() for word in words]
    return ' '.join(capitalized_words)

def extract_bold_from_body(body_paragraphs):
    bold_text_parts = []
    for paragraph in body_paragraphs:
        bold_matches = re.findall(r'<strong>(.*?)</strong>', paragraph)
        bold_text_parts.extend(bold_matches)
    bold_text = ' '.join(bold_text_parts).strip()
    bold_text = re.sub(r'<[^>]*>', '', bold_text)
    bold_text = re.sub(r'["*<>]', '', bold_text)
    bold_text = re.sub(r'\s+', ' ', bold_text)
    return bold_text

def update_flags_section(html_content, ro_link, en_filename):
    """
    Update the flags section in the HTML content with a direct string replacement approach.

    Args:
        html_content: The HTML content to update
        ro_link: The Romanian link (or None to keep existing)
        en_filename: The English filename to use

    Returns:
        The updated HTML content
    """
    print(f"Updating FLAGS section - RO link: {ro_link}, EN filename: {en_filename}")

    # Extract flags section for inspection
    flags_section_match = re.search(r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->', html_content, re.DOTALL)
    if not flags_section_match:
        print("FLAGS section not found")
        return html_content

    flags_section = flags_section_match.group(0)  # Include the markers
    print(f"Original FLAGS section length: {len(flags_section)} characters")

    # Extract existing RO link if needed
    if not ro_link:
        ro_match = re.search(r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*><img[^>]*?title="ro"', flags_section)
        if ro_match:
            ro_link = ro_match.group(1)
            print(f"Using existing RO link: {ro_link}")

    # Create a modified copy of the flags section for safety
    updated_flags = flags_section

    # Update Romanian link - using direct string replacement
    if ro_link:
        # Find the entire Romanian tag
        ro_tag_match = re.search(r'<a href="https://neculaifantanaru\.com/[^"]+"[^>]*><img[^>]*?title="ro"[^>]*?/></a>', updated_flags)

        if ro_tag_match:
            old_ro_tag = ro_tag_match.group(0)
            print(f"Found RO tag: {old_ro_tag}")

            # Create new tag by replacing just the URL part
            new_ro_tag = re.sub(
                r'(href="https://neculaifantanaru\.com/)[^"]+(">)',
                f'\\1{ro_link}\\2',
                old_ro_tag
            )

            print(f"New RO tag: {new_ro_tag}")

            # Replace the tag in the flags section
            updated_flags = updated_flags.replace(old_ro_tag, new_ro_tag)
            print(f"Updated RO link to: {ro_link}")

    # Update English link
    if en_filename:
        # Ensure we have the bare filename without path
        en_base = os.path.basename(en_filename)

        # Find the entire English tag
        en_tag_match = re.search(r'<a href="https://neculaifantanaru\.com/en/[^"]+"[^>]*><img[^>]*?title="en"[^>]*?/></a>', updated_flags)

        if en_tag_match:
            old_en_tag = en_tag_match.group(0)
            print(f"Found EN tag: {old_en_tag}")

            # Create new tag by replacing just the URL part
            new_en_tag = re.sub(
                r'(href="https://neculaifantanaru\.com/en/)[^"]+(">)',
                f'\\1{en_base}\\2',
                old_en_tag
            )

            print(f"New EN tag: {new_en_tag}")

            # Replace the tag in the flags section
            updated_flags = updated_flags.replace(old_en_tag, new_en_tag)
            print(f"Updated EN link to: {en_base}")

    # Check if we made any changes
    if updated_flags == flags_section:
        print("No changes made to FLAGS section")
        return html_content

    # Replace the entire flags section in the HTML content
    modified_html = html_content.replace(flags_section, updated_flags)

    # Verify the modification worked
    if modified_html == html_content:
        print("ERROR: Failed to update HTML content - no changes applied")

        # Use a more basic approach as a last resort
        if ro_link:
            print("Trying direct RO link replacement")
            modified_html = re.sub(
                r'(<a href="https://neculaifantanaru\.com/)[^"]+("><img[^>]*?title="ro")',
                f'\\1{ro_link}\\2',
                html_content
            )

        if en_filename:
            print("Trying direct EN link replacement")
            modified_html = re.sub(
                r'(<a href="https://neculaifantanaru\.com/en/)[^"]+("><img[^>]*?title="en")',
                f'\\1{en_base}\\2',
                modified_html
            )

        if modified_html != html_content:
            print("Direct replacements applied successfully")
    else:
        print("FLAGS section updated successfully")

    return modified_html

def update_html_content(html_content, title, body, filename, article_id, date, category, ro_link):
    """Update all necessary parts of the HTML content."""
    print(f"\nUpdating HTML for article: {title}")
    print(f"ID: {article_id}, Filename: {filename}")

    # 1. Update article ID
    if article_id:
        id_comment = f'<!-- $item_id = {article_id}; // ID-ul din fisierul limba romana -->\n'
        if '<!-- $item_id =' not in html_content:
            html_content = id_comment + html_content
        else:
            html_content = re.sub(r'<!-- \$item_id = \d+;.*?-->\n?', id_comment, html_content)
        print(f"Updated article ID to: {article_id}")

    # 2. Update title and capitalize
    title_without_diacritics = remove_diacritics(title)
    capitalized_title = capitalize_title(title_without_diacritics)

    # Update <title> tag
    html_content = re.sub(r'<title>.*?</title>', f'<title>{capitalized_title} | Neculai Fantanaru (en)</title>', html_content)
    print(f"Updated page title to: {capitalized_title} | Neculai Fantanaru (en)")

    # Update article title (h1)
    html_content = re.sub(r'<h1 class="den_articol" itemprop="name">.*?</h1>', f'<h1 class="den_articol" itemprop="name">{capitalize_title(title)}</h1>', html_content)
    print(f"Updated article title to: {capitalize_title(title)}")

    # 3. Update filename references
    html_content = html_content.replace('zzz.html', filename)
    print(f"Updated filename references to: {filename}")

    # 4. Update meta description
    bold_text = extract_bold_from_body(body)
    html_content = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{bold_text}">', html_content)
    print("Updated meta description with bold text from article")

    # 5. Update article body
    formatted_body = format_body(body)
    html_content = re.sub(r'<!-- SASA-1 -->.*?<!-- SASA-2 -->', f'<!-- SASA-1 -->\n{formatted_body}\n<!-- SASA-2 -->', html_content, flags=re.DOTALL)
    print("Updated article body content")

    # 6. Update flags section
    html_content = update_flags_section(html_content, ro_link, filename)

    return html_content

def post_process_html(html_content):
    replacements = {
        "NBSP": " ",
        "\u00A0": " ",
        "&nbsp;": " "
    }
    for old, new in replacements.items():
        html_content = html_content.replace(old, new)
    return html_content

def extract_text_obisnuit2(html_content):
    pattern = r'<p class="text_obisnuit2">(.*?)</p>'
    matches = re.findall(pattern, html_content, re.DOTALL)
    cleaned_text = ' '.join(matches).replace('"', '')
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    description = ' '.join(sentences[:8]).strip()
    if "Latest articles accessed by readers" in description:
        description = description.split("Latest articles accessed by readers")[0].strip()
    return description

def clean_meta_description(description):
    cleaned = re.sub(r'["*]', '', description)
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    cleaned = re.sub(r'<e ', ' ', cleaned)
    cleaned = re.sub(r'[<>]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def update_meta_description(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    text_obisnuit2 = extract_text_obisnuit2(content)
    if text_obisnuit2:
        cleaned_description = clean_meta_description(text_obisnuit2)
        updated_content = re.sub(
            r'<meta name="description" content=".*?">',
            f'<meta name="description" content="{cleaned_description}">',
            content
        )
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

def remove_empty_paragraphs(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    pattern = r'(<!-- ARTICOL START -->.*?<!-- ARTICOL FINAL -->)'
    article_section = re.search(pattern, content, re.DOTALL)
    if article_section:
        article_content = article_section.group(1)
        updated_article_content = re.sub(r'<p class="text_obisnuit"></p>\s*', '', article_content)
        content = content.replace(article_content, updated_article_content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def format_numbered_paragraphs(content):
    content = re.sub(
        r'<strong>(\d+\.\s+)</strong>(.*?)</p>',
        r'<p class="text_obisnuit"><span class="text_obisnuit2">\1</span>\2</p>',
        content
    )
    return content

def final_regex_replacements(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content = format_numbered_paragraphs(content)
    content = re.sub(
        r'<p class="text_obisnuit"><strong><em>(.*?)</em></strong></p>',
        r'<p class="text_obisnuit2"><em>\1</em></p>',
        content
    )
    content = re.sub(
        r'<p class="text_obisnuit"><strong>(.*?)</strong></p>',
        r'<p class="text_obisnuit2">\1</p>',
        content
    )
    content = re.sub(
        r'<p class="text_obisnuit"><strong>(.*?)</strong>(.*?)</p>',
        r'<p class="text_obisnuit"><span class="text_obisnuit2">\1</span>\2</p>',
        content
    )
    content = re.sub(
        r'(<p class="text_obisnuit"><span class="text_obisnuit2">\* Note:)',
        r'<br><br>\n\1',
        content
    )
    content = re.sub(r'<e</p>', '</p>', content)
    content = re.sub(r'</span></p>', '</p>', content)
    content = re.sub(r'<em></em>', '', content)
    content = re.sub(r'</strong>\s*<strong>', '', content)
    content = re.sub(r'<strong>', '', content)
    content = re.sub(r'</strong>', '', content)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    docx_path = "bebe.docx"
    html_path = "index.html"
    output_dir = "output"

    if not os.path.exists(docx_path):
        print(f"Error: File '{docx_path}' not found.")
        return

    if not os.path.exists(html_path):
        print(f"Error: File '{html_path}' not found.")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    articles = extract_data_from_docx(docx_path)

    if not articles:
        print("No articles found in the document.")
        return

    for title, body, article_id, date, category, ro_link in articles:
        filename = generate_filename(title)
        print(f"Processing article: {title}")
        print(f"Article ID: {article_id}")
        print(f"Generated filename: {filename}")

        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        if not body:
            print(f"Warning: Empty body for article '{title}'. Skipping.")
            continue

        updated_html = update_html_content(
            html_content, title, body, filename,
            article_id, date, category, ro_link
        )
        updated_html = post_process_html(updated_html)

        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(updated_html)

        update_meta_description(output_path)
        remove_empty_paragraphs(output_path)
        final_regex_replacements(output_path)

        print(f"Saved and updated meta description for: {filename}")

    print("All articles have been processed successfully.")

if __name__ == "__main__":
    main()