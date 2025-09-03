import re
import os
from unidecode import unidecode

def read_model_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def read_articles(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
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
            else:
                formatted_lines.append(f'\t\t<p class="text_obisnuit">{line}</p>')

    return '\n'.join(formatted_lines)

def fix_double_quotes(content):
    def replace_quotes(match):
        attr = match.group(1)
        value = match.group(2).replace('"', "'")
        return f'{attr}="{value}"'

    return re.sub(r'(\w+)="([^"]*)"', replace_quotes, content)

def fix_double_quotes_final(content):
    return re.sub(r'""', '"', content)

def clean_description(description):
    return re.sub(r'[":\'`]', '', description)

def fix_romanian_characters(text):
    replacements = {
        # Corecții pentru caracterele codate incorect
        'Ã®': 'î', 'Ã¢': 'â', 'Äƒ': 'ă', 'ÅŸ': 'ș', 'È›': 'ț',
        'Ã‚': 'Â', 'Ãž': 'Î', 'Äˆ': 'Ă', 'ÅÂ': 'Ș', 'Èš': 'Ț',
        'Ã¡': 'á', 'Ã©': 'é', 'Ã³': 'ó', 'Ã½': 'ý',
        'Ã': 'Á', 'Ã‰': 'É', 'Ã"': 'Ó', 'Ã': 'Ý',
        'Ã¢': 'â', 'Ãª': 'ê', 'Ã´': 'ô', 'Ã»': 'û',
        'Ã‚': 'Â', 'ÃŠ': 'Ê', 'Ã"': 'Ô', 'Ã›': 'Û',
        'Ã£': 'ã', 'Ã±': 'ñ', 'Ãµ': 'õ',
        'Ãƒ': 'Ã', 'Ã‘': 'Ñ', 'ÃÕ': 'Õ',
        'Ã¤': 'ä', 'Ã«': 'ë', 'Ã¯': 'ï', 'Ã¶': 'ö', 'Ã¼': 'ü', 'Ã¿': 'ÿ',
        'Ã„': 'Ä', 'Ã‹': 'Ë', 'Ã': 'Ï', 'Ã–': 'Ö', 'Ãœ': 'Ü', 'Å¸': 'Ÿ',
        # Înlocuiri fără diacritice
        'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
        'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
    }
    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)
    return text



def create_html_file(model, article, output_dir):
    lines = article.strip().split('\n')
    title = fix_romanian_characters(lines[0].strip())
    description = fix_romanian_characters(lines[2].strip()) if len(lines) > 2 else ""
    content = fix_romanian_characters('\n'.join(lines[3:])) if len(lines) > 3 else ""

    slug = create_slug(title)
    formatted_content = format_content(content, description)

    clean_title = clean_description(title)
    clean_desc = clean_description(description)

    new_content = model
    # Extrage link-ul canonical nou generat
    canonical_link = f"https://neculaifantanaru.com/{slug}.html"

    # Actualizează secțiunile <title>, <meta description> și <link rel="canonical">
    new_content = re.sub(r'<title>.*?\| Neculai Fantanaru</title>', f'<title>{clean_title} | Neculai Fantanaru</title>', new_content)
    new_content = re.sub(r'<meta name="description" content=".*?">', f'<meta name="description" content="{clean_desc}">', new_content)
    new_content = re.sub(r'<link rel="canonical" href="https://neculaifantanaru.com/.*?"', f'<link rel="canonical" href="{canonical_link}"', new_content)

    # Înlocuirea primului link din secțiunea FLAGS
    flags_pattern = r'(<a href="https://neculaifantanaru.com/.*?"><img src="index_files/flag_lang_ro.jpg"[^>]*>)'
    new_content = re.sub(flags_pattern, f'<a href="{canonical_link}"><img src="index_files/flag_lang_ro.jpg"', new_content, count=1)

    # Înlocuiește conținutul articolului
    content_pattern = r'(<!-- ARTICOL START -->.*?<table.*?<td><h1 class="den_articol" itemprop="name">).*?(</h1></td>.*?</table>\s*)(.*?)(</div>\s*<p align="justify" class="text_obisnuit style3">&nbsp;</p>\s*<!-- ARTICOL FINAL -->)'
    replacement = r'\1{}\2\n{}\n\4'.format(clean_title, formatted_content)
    new_content = re.sub(content_pattern, replacement, new_content, flags=re.DOTALL)

    # Fixează ghilimelele
    new_content = fix_double_quotes(new_content)
    new_content = fix_double_quotes_final(new_content)

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