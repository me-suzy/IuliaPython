import os
import re
import sys
import io
from datetime import datetime
from bs4 import BeautifulSoup

# Fix encoding pentru Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ========== CONFIGURARE ==========
# Folderul cu articolele noi (sursă) - format nou
SOURCE_FOLDER = r"c:\Folder1\fisiere_gata"

# Folderul cu fișierele categorii (destinație) - format article-card-new
DEST_FOLDER = r"e:\Carte\BB\17 - Site Leadership\Principal 2022\en"

# Folderul RO pentru imagini
RO_FOLDER = r"e:\Carte\BB\17 - Site Leadership\Principal 2022\ro"

# Base URL pentru articole
BASE_URL = "https://neculaifantanaru.com/en/"

# Lista fișierelor categorii (să le excludem din procesare)
CATEGORY_FILES = [
    "index.html", "leadership-and-attitude.html", "leadership-magic.html",
    "successful-leadership.html", "hr-human-resources.html", "leadership-laws.html",
    "total-leadership.html", "leadership-that-lasts.html", "leadership-principles.html",
    "leadership-plus.html", "qualities-of-a-leader.html", "top-leadership.html",
    "leadership-impact.html", "personal-development.html", "leadership-skills-and-abilities.html",
    "real-leadership.html", "basic-leadership.html", "leadership-360.html",
    "leadership-pro.html", "leadership-expert.html", "leadership-know-how.html",
    "leadership-journal.html", "alpha-leadership.html", "leadership-on-off.html",
    "leadership-deluxe.html", "leadership-xxl.html", "leadership-50-extra.html",
    "leadership-fusion.html", "leadership-v8.html", "leadership-x3-silver.html",
    "leadership-q2-sensitive.html", "leadership-t7-hybrid.html", "leadership-n6-celsius.html",
    "leadership-s4-quartz.html", "leadership-gt-accent.html", "leadership-fx-intensive.html",
    "leadership-iq-light.html", "leadership-7th-edition.html", "leadership-xs-analytics.html",
    "leadership-z3-extended.html", "leadership-ex-elite.html", "leadership-w3-integra.html",
    "leadership-sx-experience.html", "leadership-y5-superzoom.html", "performance-ex-flash.html",
    "leadership-mindware.html", "leadership-r2-premiere.html", "leadership-y4-titanium.html",
    "leadership-quantum-xx.html"
]

# ========== FUNCȚII HELPER ==========

def read_file_with_fallback(file_path):
    """Citește fișierul cu multiple encodings"""
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None

def parse_date(date_str):
    """Parsează data din format 'On December 25, 2025'"""
    try:
        date_str = date_str.replace('On ', '').strip()
        return datetime.strptime(date_str, '%B %d, %Y')
    except:
        return datetime(1900, 1, 1)

def get_ro_filename_from_en(en_file_path):
    """Extrage numele fișierului RO din secțiunea FLAGS a fișierului EN"""
    try:
        content = read_file_with_fallback(en_file_path)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Caută link-ul RO în country-wrapper
        flags_section = soup.find('div', class_='country-wrapper')
        if flags_section:
            ro_link = flags_section.find('a', attrs={'cunt_code': '+40'})
            if ro_link and ro_link.get('href'):
                ro_url = ro_link.get('href')
                if 'neculaifantanaru.com/' in ro_url:
                    return ro_url.split('neculaifantanaru.com/')[-1]
        
        return None
    except:
        return None

def get_image_from_ro_file(ro_file_path):
    """Extrage imaginea din fișierul RO"""
    try:
        if not os.path.exists(ro_file_path):
            return None, None
        
        content = read_file_with_fallback(ro_file_path)
        if not content:
            return None, None
        
        # Caută imaginea în feature-img-wrap
        match = re.search(r'<div class="feature-img-wrap">\s*<img src="([^"]+)"[^>]*alt="([^"]*)"', content, re.DOTALL)
        if match:
            return match.group(1), match.group(2)
        
        # Fallback: caută orice imagine cu _image.jpg
        match = re.search(r'<img src="(https://neculaifantanaru\.com/images/[^"]+_image\.jpg)"[^>]*alt="([^"]*)"', content)
        if match:
            return match.group(1), match.group(2)
        
        return None, None
    except:
        return None, None

def get_image_for_article(en_file_path, ro_folder):
    """Obține imaginea pentru articol din fișierul RO echivalent"""
    # Încearcă să găsească fișierul RO
    ro_filename = get_ro_filename_from_en(en_file_path)
    
    if ro_filename:
        ro_file_path = os.path.join(ro_folder, ro_filename)
        img_src, img_alt = get_image_from_ro_file(ro_file_path)
        if img_src:
            return img_src, img_alt
    
    # Fallback: caută imaginea direct în fișierul EN
    content = read_file_with_fallback(en_file_path)
    if content:
        soup = BeautifulSoup(content, 'html.parser')
        feature_img = soup.find('div', class_='feature-img-wrap')
        if feature_img:
            img = feature_img.find('img')
            if img and img.get('src'):
                return img.get('src'), img.get('alt', '')
        
        # Fallback og:image
        og_image = soup.find('meta', property='og:image')
        if og_image:
            return og_image.get('content', ''), ''
    
    return None, None

def extract_article_data(file_path, ro_folder):
    """Extrage datele articolului din fișierul HTML"""
    try:
        content = read_file_with_fallback(file_path)
        if not content:
            print(f"    Nu pot citi fișierul: {os.path.basename(file_path)}")
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extrage titlul
        title_elem = soup.find('h1', class_='custom-h1')
        if not title_elem:
            title_elem = soup.find('h1', class_='den_articol')
        if not title_elem:
            print(f"    Nu găsesc titlul în {os.path.basename(file_path)}")
            return None
        title = title_elem.get_text(strip=True)
        
        # Extrage data
        date_str = ""
        date_obj = datetime(1900, 1, 1)
        
        date_match = re.search(r'On (\w+ \d+, \d{4})', content)
        if date_match:
            date_str = date_match.group(0)
            date_obj = parse_date(date_str)
        
        # Extrage categoria
        category_link = soup.find('a', class_='color-green')
        if not category_link:
            category_link = soup.find('a', class_='external')
        
        if not category_link:
            print(f"    Nu găsesc categoria în {os.path.basename(file_path)}")
            return None
        
        category_url = category_link.get('href', '')
        category_name = category_link.get_text(strip=True)
        
        # Extrage lead-ul
        lead = ""
        articol_start = content.find('<!-- ARTICOL START -->')
        if articol_start != -1:
            articol_section = content[articol_start:]
            soup_articol = BeautifulSoup(articol_section, 'html.parser')
            lead_elem = soup_articol.find('p', class_='text_obisnuit2')
            if lead_elem:
                em_elem = lead_elem.find('em')
                if em_elem:
                    lead = em_elem.get_text(strip=True)
                else:
                    lead = lead_elem.get_text(strip=True)
        
        # Extrage imaginea din RO
        img_src, img_alt = get_image_for_article(file_path, ro_folder)
        if not img_src:
            img_src = "https://neculaifantanaru.com/images/default-article.jpg"
        if not img_alt:
            img_alt = title
        
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
            'img_src': img_src,
            'img_alt': img_alt,
            'filename': filename
        }
        
    except Exception as e:
        print(f"    Eroare: {e}")
        return None

def generate_article_html(article):
    """Generează HTML pentru articol în format article-card-new"""
    year = str(article['date_obj'].year) if article['date_obj'].year > 1900 else ""
    display_date = article['date_str'].replace('On ', '')
    
    return f'''                    <article class="blog-box heading-space-half">
    <div class="blog-listing-inner news_item">
        <div class="article-card-new">
            <!-- Layout DESKTOP -->
            <div class="desktop-layout d-none d-md-block">
                <div class="article-header d-flex">
                    <div class="article-image-container">
                        <a href="{article['url']}">
                            <img src="{article['img_src']}" alt="{article['img_alt']}" class="article-card-img">
                        </a>
                    </div>
                    <div class="article-header-content">
                        <h2 class="custom-h1" itemprop="name">
                            <a href="{article['url']}" class="color-black">{article['title']}</a>
                        </h2>
                        <div class="article-spacing"></div>
                        <div class="article-spacing"></div>
                        <div class="blog-post d-flex align-items-center flex-wrap">
                            <i class="fa fa-calendar mx-1"></i>
                            <time datetime="{year}" class="color-black">{display_date}, in</time>
                            <a href="{article['category_url']}" class="color-green font-weight-600 mx-1">{article['category_name']}</a>
                        </div>
                        <div class="author-info color-black">by Neculai Fantanaru</div>
                    </div>
                </div>
                <div class="article-body">
                    <div class="article-spacing"></div>
                    <div class="article-spacing"></div>
                    <p class="color-grey line-height-25px">{article['lead']}</p>
                    <a href="{article['url']}" class="btn-setting color-black btn-hvr-up btn-blue btn-hvr-pink">
                        read more<span class="sr-only"> about {article['title']}</span>
                    </a>
                </div>
            </div>
            <!-- Layout MOBIL -->
            <div class="mobile-layout d-block d-md-none">
                <div class="mobile-image-container">
                    <a href="{article['url']}">
                        <img src="{article['img_src']}" alt="{article['img_alt']}" class="mobile-article-img">
                    </a>
                </div>
                <h2 class="custom-h1 mobile-title">
                    <a href="{article['url']}" class="color-black">{article['title']}</a>
                </h2>
                <p class="color-grey line-height-25px mobile-lead">{article['lead']}</p>
                <div class="blog-post mobile-date">
                    <i class="fa fa-calendar mx-1"></i>
                    <time datetime="{year}" class="color-black">{display_date}, in</time>
                    <a href="{article['category_url']}" class="color-green font-weight-600 mx-1">{article['category_name']}</a>
                </div>
                <a href="{article['url']}" class="btn-setting color-black btn-hvr-up btn-blue btn-hvr-pink mobile-read-more">
                    Read More<span class="sr-only"> about {article['title']}</span>
                </a>
            </div>
        </div>
    </div>
</article>
'''

def get_category_filename(category_url):
    """Extrage numele fișierului categoriei din URL"""
    if 'neculaifantanaru.com/en/' in category_url:
        return category_url.split('/en/')[-1]
    elif 'neculaifantanaru.com/' in category_url:
        return category_url.split('/')[-1]
    return None

def insert_articles_in_category(category_path, articles):
    """Inserează articolele în categoria"""
    try:
        content = read_file_with_fallback(category_path)
        if not content:
            print(f"    Nu pot citi: {os.path.basename(category_path)}")
            return False
        
        start_marker = '<!-- ARTICOL START -->'
        start_pos = content.find(start_marker)
        
        if start_pos == -1:
            print(f"    Nu găsesc markerul în {os.path.basename(category_path)}")
            return False
        
        # Filtrează articolele care nu există
        new_articles = []
        for article in articles:
            if article['url'] not in content:
                new_articles.append(article)
                print(f"    + Adaug: {article['title']}")
            else:
                print(f"    - Există deja: {article['title']}")
        
        if not new_articles:
            print(f"    Niciun articol nou de adăugat")
            return False
        
        # Sortează după dată
        new_articles.sort(key=lambda x: x['date_obj'], reverse=True)
        
        # Generează HTML
        new_html = ""
        for article in new_articles:
            new_html += generate_article_html(article)
        
        # Inserează
        insert_pos = start_pos + len(start_marker)
        new_content = content[:insert_pos] + '\n' + new_html + content[insert_pos:]
        
        with open(category_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"    ✓ Salvat: {len(new_articles)} articole adăugate")
        return True
        
    except Exception as e:
        print(f"    Eroare: {e}")
        return False

def main():
    print("=" * 60)
    print("SCRIPT: Adaugă articole în categorii Principal 2022 EN")
    print("Format: article-card-new cu imagini din RO")
    print("=" * 60)
    print(f"Sursă: {SOURCE_FOLDER}")
    print(f"Destinație: {DEST_FOLDER}")
    print(f"Imagini RO: {RO_FOLDER}")
    print("=" * 60)
    
    if not os.path.exists(SOURCE_FOLDER):
        print(f"EROARE: {SOURCE_FOLDER} nu există")
        return
    
    if not os.path.exists(DEST_FOLDER):
        print(f"EROARE: {DEST_FOLDER} nu există")
        return
    
    # Pas 1: Extrage datele
    print("\n[PAS 1] Extrag datele din articole...")
    print("-" * 40)
    
    articles_by_category = {}
    
    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith('.html') and filename not in CATEGORY_FILES:
            file_path = os.path.join(SOURCE_FOLDER, filename)
            print(f"\nProcesez: {filename}")
            
            article = extract_article_data(file_path, RO_FOLDER)
            if article:
                cat_file = get_category_filename(article['category_url'])
                if cat_file:
                    if cat_file not in articles_by_category:
                        articles_by_category[cat_file] = []
                    articles_by_category[cat_file].append(article)
                    print(f"    Titlu: {article['title']}")
                    print(f"    Data: {article['date_str']}")
                    print(f"    Categorie: {article['category_name']}")
                    print(f"    Imagine: {article['img_src'][:50]}...")
    
    # Pas 2: Inserează în categorii
    print("\n" + "=" * 60)
    print("[PAS 2] Inserez în categorii...")
    print("-" * 40)
    
    updated = 0
    for cat_file, articles in articles_by_category.items():
        cat_path = os.path.join(DEST_FOLDER, cat_file)
        print(f"\nCategorie: {cat_file} ({len(articles)} articole)")
        
        if os.path.exists(cat_path):
            if insert_articles_in_category(cat_path, articles):
                updated += 1
        else:
            print(f"    NU EXISTĂ: {cat_file}")
    
    # Rezumat
    print("\n" + "=" * 60)
    print("REZUMAT")
    print(f"Articole: {sum(len(a) for a in articles_by_category.values())}")
    print(f"Categorii: {len(articles_by_category)}")
    print(f"Actualizate: {updated}")
    print("=" * 60)

if __name__ == "__main__":
    main()
