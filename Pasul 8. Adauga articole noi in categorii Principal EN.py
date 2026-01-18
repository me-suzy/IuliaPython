import os
import re
import sys
import io
from datetime import datetime
from bs4 import BeautifulSoup

# Fix encoding pentru Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ========== CONFIGURARE ==========
# Folderul cu articolele noi (sursă)
SOURCE_FOLDER = r"c:\Folder1\fisiere_html"

# Folderul cu fișierele categorii (destinație)
DEST_FOLDER = r"e:\Carte\BB\17 - Site Leadership\Principal\en"

# Base URL pentru articole
BASE_URL = "https://neculaifantanaru.com/en/"

# ========== FUNCȚII HELPER ==========

def parse_date(date_str):
    """Parsează data din format 'On December 25, 2025' în obiect datetime"""
    try:
        # Elimină 'On ' de la început
        date_str = date_str.replace('On ', '').strip()
        # Parsează data
        return datetime.strptime(date_str, '%B %d, %Y')
    except Exception as e:
        print(f"    Eroare la parsarea datei '{date_str}': {e}")
        return datetime(1900, 1, 1)  # Data implicită pentru erori

def format_date(date_obj):
    """Formatează data pentru afișare: 'On December 25, 2025'"""
    return date_obj.strftime('On %B %d, %Y')

def extract_article_data(file_path):
    """Extrage datele articolului din fișierul HTML"""
    try:
        # Încearcă mai multe encodings
        content = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"    Nu pot citi fișierul cu niciun encoding: {os.path.basename(file_path)}")
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Găsește secțiunea ARTICOL START
        articol_start = content.find('<!-- ARTICOL START -->')
        if articol_start == -1:
            print(f"    Nu găsesc ARTICOL START în {os.path.basename(file_path)}")
            return None
        
        # Extrage titlul
        title_elem = soup.find('h1', class_='den_articol')
        if not title_elem:
            print(f"    Nu găsesc titlul în {os.path.basename(file_path)}")
            return None
        title = title_elem.get_text(strip=True)
        
        # Extrage data și categoria din text_dreapta
        text_dreapta = soup.find('td', class_='text_dreapta')
        if not text_dreapta:
            print(f"    Nu găsesc text_dreapta în {os.path.basename(file_path)}")
            return None
        
        # Extrage data
        text_content = text_dreapta.get_text()
        date_match = re.search(r'On (\w+ \d+, \d{4})', text_content)
        if date_match:
            date_str = date_match.group(0)
            date_obj = parse_date(date_str)
        else:
            print(f"    Nu găsesc data în {os.path.basename(file_path)}")
            date_str = "On January 01, 2020"
            date_obj = datetime(2020, 1, 1)
        
        # Extrage categoria
        category_link = text_dreapta.find('a', class_='external')
        if category_link:
            category_url = category_link.get('href', '')
            category_name = category_link.get_text(strip=True)
        else:
            print(f"    Nu găsesc categoria în {os.path.basename(file_path)}")
            return None
        
        # Extrage lead-ul (primul text_obisnuit2 cu em)
        lead = ""
        # Caută după ARTICOL START
        articol_section = content[articol_start:]
        soup_articol = BeautifulSoup(articol_section, 'html.parser')
        lead_elem = soup_articol.find('p', class_='text_obisnuit2')
        if lead_elem:
            em_elem = lead_elem.find('em')
            if em_elem:
                lead = em_elem.get_text(strip=True)
            else:
                lead = lead_elem.get_text(strip=True)
        
        # Construiește URL-ul articolului
        filename = os.path.basename(file_path)
        article_url = BASE_URL + filename
        
        return {
            'title': title,
            'url': article_url,
            'date_str': date_str,
            'date_obj': date_obj,
            'category_url': category_url,
            'category_name': category_name,
            'lead': lead,
            'filename': filename
        }
        
    except Exception as e:
        print(f"    Eroare la extragerea datelor din {file_path}: {e}")
        return None

def generate_article_html(article):
    """Generează HTML-ul pentru un articol în format categorie"""
    html = f'''    <table width="636" border="0">
        <tr>
          <td><span class="den_articol"><a href="{article['url']}" class="linkMare">{article['title']}</a></span></td>
          </tr>
          <tr>
          <td class="text_dreapta">{article['date_str']}, in <a href="{article['category_url']}" title="View all articles from {article['category_name']}" class="external" rel="category tag">{article['category_name']}</a>, by Neculai Fantanaru</td>
        </tr>
      </table>
      <p class="text_obisnuit2"><em>{article['lead']}</em></p>
      <table width="552" border="0">
        <tr>
          <td width="552"><div align="right" id="external2"><a href="{article['url']}">read more </a><a href="https://neculaifantanaru.com/en/" title=""><img src="Arrow3_black_5x7.gif" alt="" width="5" height="7" class="arrow" /></a></div></td>
        </tr>
      </table>
      <p class="text_obisnuit"></p>
'''
    return html

def get_category_filename_from_url(category_url):
    """Extrage numele fișierului categoriei din URL"""
    # Exemplu: https://neculaifantanaru.com/en/top-leadership.html -> top-leadership.html
    if 'neculaifantanaru.com/en/' in category_url:
        return category_url.split('/en/')[-1]
    elif 'neculaifantanaru.com/' in category_url:
        return category_url.split('/')[-1]
    return None

def article_exists_in_category(content, article_url):
    """Verifică dacă articolul există deja în categoria"""
    return article_url in content

def insert_articles_in_category(category_path, articles):
    """Inserează articolele în fișierul categoriei"""
    try:
        with open(category_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifică dacă există markerii
        start_marker = '<!-- ARTICOL CATEGORIE START -->'
        end_marker = '<!-- ARTICOL CATEGORIE FINAL -->'
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos == -1 or end_pos == -1:
            print(f"    Nu găsesc markerii în {os.path.basename(category_path)}")
            return False
        
        # Filtrează articolele care nu există deja
        new_articles = []
        for article in articles:
            if not article_exists_in_category(content, article['url']):
                new_articles.append(article)
                print(f"    + Adaug: {article['title']}")
            else:
                print(f"    - Există deja: {article['title']}")
        
        if not new_articles:
            print(f"    Niciun articol nou de adăugat în {os.path.basename(category_path)}")
            return False
        
        # Sortează articolele noi după dată (cele mai recente primele)
        new_articles.sort(key=lambda x: x['date_obj'], reverse=True)
        
        # Generează HTML pentru articolele noi
        new_html = ""
        for article in new_articles:
            new_html += generate_article_html(article)
        
        # Găsește poziția după <div align="justify"> care urmează după start_marker
        insert_pos = content.find('<div align="justify">', start_pos)
        if insert_pos == -1:
            # Dacă nu găsește, inserează direct după start_marker
            insert_pos = start_pos + len(start_marker)
        else:
            insert_pos = content.find('>', insert_pos) + 1  # După >
        
        # Inserează HTML-ul nou
        new_content = content[:insert_pos] + '\n' + new_html + content[insert_pos:]
        
        # Salvează fișierul
        with open(category_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"    ✓ Salvat: {len(new_articles)} articole adăugate în {os.path.basename(category_path)}")
        return True
        
    except Exception as e:
        print(f"    Eroare la procesarea {category_path}: {e}")
        return False

def main():
    print("=" * 60)
    print("SCRIPT: Adaugă articole noi în categorii (Principal EN)")
    print("=" * 60)
    print(f"Sursă articole: {SOURCE_FOLDER}")
    print(f"Destinație categorii: {DEST_FOLDER}")
    print("=" * 60)
    
    # Verifică dacă folderele există
    if not os.path.exists(SOURCE_FOLDER):
        print(f"EROARE: Folderul sursă nu există: {SOURCE_FOLDER}")
        return
    
    if not os.path.exists(DEST_FOLDER):
        print(f"EROARE: Folderul destinație nu există: {DEST_FOLDER}")
        return
    
    # Pas 1: Extrage datele din toate articolele din folderul sursă
    print("\n[PAS 1] Extrag datele din articolele noi...")
    print("-" * 40)
    
    articles_by_category = {}  # {category_filename: [articles]}
    
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith('.html') and filename != 'index.html':
            file_path = os.path.join(SOURCE_FOLDER, filename)
            print(f"\nProcesez: {filename}")
            
            article_data = extract_article_data(file_path)
            if article_data:
                category_file = get_category_filename_from_url(article_data['category_url'])
                if category_file:
                    if category_file not in articles_by_category:
                        articles_by_category[category_file] = []
                    articles_by_category[category_file].append(article_data)
                    print(f"    Titlu: {article_data['title']}")
                    print(f"    Data: {article_data['date_str']}")
                    print(f"    Categorie: {article_data['category_name']} ({category_file})")
                    print(f"    Lead: {article_data['lead'][:80]}...")
    
    # Pas 2: Inserează articolele în fișierele categorii
    print("\n" + "=" * 60)
    print("[PAS 2] Inserez articolele în fișierele categorii...")
    print("-" * 40)
    
    categories_updated = 0
    articles_added = 0
    
    for category_file, articles in articles_by_category.items():
        category_path = os.path.join(DEST_FOLDER, category_file)
        print(f"\nCategorie: {category_file}")
        print(f"  Articole de adăugat: {len(articles)}")
        
        if os.path.exists(category_path):
            if insert_articles_in_category(category_path, articles):
                categories_updated += 1
                articles_added += len([a for a in articles if not article_exists_in_category(open(category_path, 'r', encoding='utf-8').read(), a['url'])])
        else:
            print(f"    ATENȚIE: Fișierul categoriei nu există: {category_file}")
    
    # Rezumat
    print("\n" + "=" * 60)
    print("REZUMAT")
    print("=" * 60)
    print(f"Articole procesate: {sum(len(arts) for arts in articles_by_category.values())}")
    print(f"Categorii găsite: {len(articles_by_category)}")
    print(f"Categorii actualizate: {categories_updated}")
    print("=" * 60)
    
    # Afișează articolele grupate pe categorii
    print("\nARTICOLE PE CATEGORII:")
    for category_file, articles in sorted(articles_by_category.items()):
        print(f"\n  {category_file}:")
        for art in sorted(articles, key=lambda x: x['date_obj'], reverse=True):
            print(f"    - {art['date_str']}: {art['title']}")

if __name__ == "__main__":
    main()
