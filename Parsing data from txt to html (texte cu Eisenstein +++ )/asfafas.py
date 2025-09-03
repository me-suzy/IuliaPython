import re
import os
from unidecode import unidecode

# specificatii Trebuie sa ai asa: ----- IDEE 29------
# specificatii Trebuie sa ai asa: Titlul Articolului
# specificatii Trebuie sa ai asa: Corpul Articolului

def read_model_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_articles(file_path):
    # Explicit UTF-8 reading, ensures proper decoding of special characters and diacritics
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Print content to check for correct reading
    print("Conținut citit din fișierul txt:\n", content[:1000])  # Afișează primele 1000 de caractere
    return re.split(r'^---.*?$', content, flags=re.MULTILINE | re.DOTALL)[1:]


def create_slug(title):
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', unidecode(title.lower()))
    slug = re.sub(r'\s+', '-', slug)
    return slug.strip('-')

def format_content(content, description):
    lines = content.split('\n')
    formatted_lines = []

    if description:
        formatted_lines.append(f'\t\t<p class="text_obisnuit2"><em>{description}</em></p>')

    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('Leadership:'):
                formatted_lines.append(f'\t\t<p class="text_obisnuit2">{line}</p>')
            elif line.lower().startswith('nota:') or line.lower().startswith('* nota:'):
                # Separăm "Nota:" de restul conținutului
                nota_parts = line.split(':', 1)
                if len(nota_parts) > 1:
                    nota_text = nota_parts[0] + ':'
                    nota_content = nota_parts[1].strip()
                    formatted_line = f'\t\t<p class="text_obisnuit"><span class="text_obisnuit2">* {nota_text} </span>{nota_content}</p>'
                    formatted_lines.append(formatted_line)
                else:
                    # În cazul în care nu există conținut după "Nota:", formatăm linia ca atare
                    formatted_lines.append(f'\t\t<p class="text_obisnuit"><span class="text_obisnuit2">{line}</span></p>')
            else:
                formatted_lines.append(f'\t\t<p class="text_obisnuit">{line}</p>')

    return '\n'.join(formatted_lines)

def fix_double_quotes(content):
    def replace_quotes(match):
        attr = match.group(1)
        value = match.group(2).replace('"', "'")
        return f'{attr}="{value}"'

    return re.sub(r'(\w+)="([^"]*)"', replace_quotes, content)



def clean_description(description):
    return re.sub(r'[":\'`]', '', description)

def create_html_file(model, article, output_dir):
    # Process article content
    lines = article.strip().split('\n')
    title = lines[0].strip()
    description = lines[2].strip() if len(lines) > 2 else ""
    content = '\n'.join(lines[3:]) if len(lines) > 3 else ""

    slug = create_slug(title)
    formatted_content = format_content(content, description)

    clean_title = clean_description(title)
    clean_desc = clean_description(description)

    clean_title_no_diacritics = unidecode(clean_title)
    clean_desc_no_diacritics = unidecode(clean_desc)

    new_content = model
    canonical_link = f"https://neculaifantanaru.com/{slug}.html"

    # Actualizează secțiunile <title>, <meta description> și <link rel="canonical">
    new_content = re.sub(r'<title>.*?\| Neculai Fantanaru</title>', f'<title>{clean_title_no_diacritics} | Neculai Fantanaru</title>', new_content)
    new_content = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{clean_desc_no_diacritics}">', new_content)
    new_content = re.sub(r'<link rel="canonical" href=".*?"', f'<link rel="canonical" href="{canonical_link}"', new_content)

    # Înlocuirea URL-ului în secțiunea FLAGS_1
    flags_pattern = r'(<!-- FLAGS_1 -->.*?<div class="cautareField">.*?<div align="right">.*?<a href=").*?(".*?<img src="index_files/flag_lang_ro\.jpg")'
    new_content = re.sub(flags_pattern, f'\\1{canonical_link}\\2', new_content, flags=re.DOTALL)

    # Setăm encoding-ul corect în HTML
    new_content = re.sub(r'<meta charset=".*?">', '<meta charset="UTF-8">', new_content)

    # Înlocuirea conținutului articolului
    content_pattern = r'(<!-- ARTICOL START -->.*?<table.*?<td><h1 class="den_articol" itemprop="name">).*?(</h1></td>.*?</table>\s*)(.*?)(</div>\s*<p align="justify" class="text_obisnuit style3">&nbsp;</p>\s*<!-- ARTICOL FINAL -->)'
    replacement = r'\1{}\2\n{}\n\4'.format(clean_title, formatted_content)
    new_content = re.sub(content_pattern, replacement, new_content, flags=re.DOTALL)

    # Fixează ghilimelele duble
    new_content = fix_double_quotes(new_content)

    # Scrie fișierul nou creat
    output_file = os.path.join(output_dir, f"{slug}.html")

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(new_content)

    print(f"Fișier creat: {output_file}")


def main():
    model_file = 'e:\\Carte\\BB\\17 - Site Leadership\\alte\\Ionel Balauta\\Aryeht\\Task 1 - Traduce tot site-ul\\Doar Google Web\\Andreea\\Meditatii\\2023\\Iulia Python\\Parsing data from txt to html\\index.html'
    input_file = 'e:\\Carte\\BB\\17 - Site Leadership\\alte\\Ionel Balauta\\Aryeht\\Task 1 - Traduce tot site-ul\\Doar Google Web\\Andreea\\Meditatii\\2023\\Iulia Python\\Parsing data from txt to html\\bebe.txt'
    output_dir = 'e:\\Carte\\BB\\17 - Site Leadership\\alte\\Ionel Balauta\\Aryeht\\Task 1 - Traduce tot site-ul\\Doar Google Web\\Andreea\\Meditatii\\2023\\Iulia Python\\Parsing data from txt to html\\output'

    print(f"Citire fișier model: {model_file}")
    model = read_model_file(model_file)

    print(f"Citire fișier de intrare: {input_file}")
    articles = read_articles(input_file)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Procesare articole și creare fișiere HTML în: {output_dir}")
    for i, article in enumerate(articles, 1):
        print(f"Procesare articol {i} din {len(articles)}")
        create_html_file(model, article, output_dir)

    print("Procesare completă. Toate fișierele HTML au fost create.")

if __name__ == "__main__":
    main()
