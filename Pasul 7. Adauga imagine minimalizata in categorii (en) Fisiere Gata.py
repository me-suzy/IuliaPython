import os
from bs4 import BeautifulSoup, Comment
import time

def get_local_file_path_from_url(url, base_local_path):
    """Convertește URL-ul într-o cale de fișier local"""
    if 'neculaifantanaru.com/en/' in url:
        filename = url.split('/en/')[-1]
        if not filename.endswith('.html'):
            filename += '.html'
        return os.path.join(base_local_path, filename)
    return None

def get_image_from_local_file(file_path):
    """Extrage imaginea din fișierul HTML local cu debugging îmbunătățit"""
    try:
        if not os.path.exists(file_path):
            print(f"    Fișierul nu există: {file_path}")
            return None, None

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"    Citit fișier local: {file_path} ({len(content)} caractere)")
        soup = BeautifulSoup(content, 'html.parser')

        # Caută imaginea în feature-img-wrap
        feature_img = soup.find('div', class_='feature-img-wrap')
        if feature_img:
            print(f"    Găsit feature-img-wrap")

            # Caută imagine directă
            img = feature_img.find('img')
            if img and img.get('src'):
                img_src = img.get('src')
                img_alt = img.get('alt', '')
                print(f"    Găsită imagine directă: {img_src}")
                return img_src, img_alt

            # Caută iframe pentru video YouTube - direct
            iframe = feature_img.find('iframe')
            if iframe and 'youtube.com/embed/' in str(iframe.get('src', '')):
                iframe_src = iframe.get('src')
                video_id = iframe_src.split('/embed/')[-1].split('?')[0]
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                title = iframe.get('title', 'Video YouTube')
                print(f"    Găsit YouTube iframe direct: {video_id}")
                return thumbnail_url, title

            # Caută iframe înglobat în div embed-responsive
            embed_div = feature_img.find('div', class_='embed-responsive')
            if embed_div:
                print(f"    Găsit embed-responsive div")
                iframe = embed_div.find('iframe')
                if iframe and 'youtube.com/embed/' in str(iframe.get('src', '')):
                    iframe_src = iframe.get('src')
                    video_id = iframe_src.split('/embed/')[-1].split('?')[0]
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    title = iframe.get('title', 'Video YouTube')
                    print(f"    Găsit YouTube iframe înglobat: {video_id}")
                    return thumbnail_url, title

        # Fallback - caută orice imagine cu 'images/'
        print(f"    Caut fallback imagini...")
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if 'images/' in src and not src.endswith('.gif'):
                print(f"    Găsită imagine fallback: {src}")
                return src, img.get('alt', '')

        print(f"    Nu s-a găsit nicio imagine validă")
        return None, None

    except Exception as e:
        print(f"    Eroare la citirea fișierului local {file_path}: {e}")
        return None, None

def get_lead_from_local_file(file_path):
    """Extrage lead-ul din fișierul local"""
    try:
        if not os.path.exists(file_path):
            print(f"    Fișierul nu există pentru lead: {file_path}")
            return ""

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')

        # Caută lead-ul în <h2 class="text_obisnuit2">
        lead_h2 = soup.find('h2', class_='text_obisnuit2')
        if lead_h2:
            lead_text = lead_h2.get_text(strip=True)
            print(f"    Lead găsit în h2: {lead_text[:100]}...")
            return lead_text

        # Fallback: caută în div cu itemprop="articleBody"
        article_body = soup.find('div', itemprop='articleBody')
        if article_body:
            for p in article_body.find_all(['p', 'h2']):
                if p.get_text(strip=True) and len(p.get_text(strip=True)) > 20:
                    lead_text = p.get_text(strip=True)
                    print(f"    Lead găsit în articleBody: {lead_text[:100]}...")
                    return lead_text

        print(f"    Nu s-a găsit lead în fișierul local")
        return ""

    except Exception as e:
        print(f"    Eroare la extragerea lead-ului: {e}")
        return ""

def get_image_and_lead_from_local_folders(url, priority_folder, individual_files_folder):
    """Extrage imaginea și lead-ul din fișiere locale - fără requests HTTP"""
    try:
        # Extrage numele fișierului din URL
        if url.startswith('https://neculaifantanaru.com/en/'):
            file_name = url.replace('https://neculaifantanaru.com/en/', '')
        elif url.startswith('https://neculaifantanaru.com/'):
            file_name = url.replace('https://neculaifantanaru.com/', '')
        else:
            return None, None, ""

        if not file_name.endswith('.html'):
            file_name += '.html'

        # Caută mai întâi în folderul prioritar
        priority_path = os.path.join(priority_folder, file_name)
        print(f"    Caut în folder prioritar: {priority_path}")
        img_src, img_alt = get_image_from_local_file(priority_path)
        lead = get_lead_from_local_file(priority_path)

        if img_src:
            print(f"    Găsit în folder prioritar: imagine={img_src}, lead={lead[:50]}...")
            return img_src, img_alt, lead

        # Caută în folderul cu fișiere individuale
        individual_path = os.path.join(individual_files_folder, file_name)
        print(f"    Caut în folder individual: {individual_path}")
        img_src, img_alt = get_image_from_local_file(individual_path)
        if not lead:  # Doar dacă nu am găsit lead în priority
            lead = get_lead_from_local_file(individual_path)

        if img_src:
            print(f"    Găsit în folder individual: imagine={img_src}, lead={lead[:50]}...")
            return img_src, img_alt, lead

        print(f"    Nu s-a găsit în niciun folder local")
        return None, None, lead  # Returnează lead-ul chiar dacă nu găsim imaginea

    except Exception as e:
        print(f"Eroare la căutarea în foldere locale pentru {url}: {e}")
        return None, None, ""

def process_html_file(file_path, priority_folder, individual_files_folder, base_url="https://neculaifantanaru.com"):
    """Procesează fișierul HTML cu căutare în două foldere locale"""

    print(f"Procesez: {file_path}")

    try:
        # Citește fișierul
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Adaugă CSS dacă nu există
        css_code = '''    <style type="text/css">
        .article-card-new { padding: 15px; margin-bottom: 20px; border-bottom: 1px solid #eee; }
        .desktop-layout .article-header { display: flex; gap: 20px; align-items: flex-start; }
        .desktop-layout .article-image-container { flex-shrink: 0; width: 180px; }
        .desktop-layout .article-card-img { width: 100%; height: 135px; object-fit: cover; border-radius: 8px; box-shadow: 0 3px 15px rgba(0,0,0,0.12); }
        .desktop-layout .article-header-content { flex: 1; padding-top: 10px; }
        .desktop-layout .article-spacing { height: 10px; }
        .desktop-layout .article-body { margin-top: 10px; }
        .mobile-layout { text-align: left; }
        .mobile-image-container { width: 100%; margin-bottom: 15px; }
        .mobile-article-img { width: 100%; height: 200px; object-fit: cover; border-radius: 8px; }
        .mobile-title { margin-bottom: 15px; }
        .mobile-lead { margin-bottom: 15px; }
        .mobile-date { margin-bottom: 20px; }
    </style>'''

        if 'article-card-new' not in content:
            head_pos = content.find('</head>')
            if head_pos != -1:
                content = content[:head_pos] + css_code + '\n' + content[head_pos:]

        # Parsează HTML pentru a găsi articolele
        soup = BeautifulSoup(content, 'html.parser')

        # Găsește comentariile
        start_comment = None
        end_comment = None

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            if 'ARTICOL START' in str(comment):
                start_comment = comment
            elif 'ARTICOL FINAL' in str(comment):
                end_comment = comment
                break

        if not start_comment or not end_comment:
            print(f"Nu găsesc comentariile în {file_path}")
            return

        # Găsește toate articolele între comentarii
        current = start_comment.next_sibling
        articles = []

        while current and current != end_comment:
            if hasattr(current, 'name') and current.name == 'article':
                if current.get('class') and 'blog-box' in current.get('class'):
                    articles.append(current)
            current = current.next_sibling

        print(f"Găsite {len(articles)} articole")

        if not articles:
            print(f"Nu am găsit articole în {file_path}")
            return

        # Procesează fiecare articol
        new_articles = []

        for i, article in enumerate(articles):
            print(f"\n  Procesez articolul {i+1}/{len(articles)}")
            print(f"  {'─'*30}")

            try:
                # Extrage datele din articol
                title_link = article.find('h2', class_='custom-h1')
                if not title_link:
                    continue

                link_tag = title_link.find('a')
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                url = link_tag.get('href')
                print(f"  Titlu: {title}")
                print(f"  URL: {url}")

                # Data
                time_elem = article.find('time')
                date = time_elem.get_text(strip=True).replace('On ', '') if time_elem else ""

                # Categoria
                category_link = article.find('a', class_='color-green')
                category = category_link.get_text(strip=True) if category_link else ""
                category_url = category_link.get('href') if category_link else ""

                # Autorul
                author_elem = article.find('span', id='hidden2')
                author = author_elem.get_text(strip=True).replace('by ', '') if author_elem else "Neculai Fantanaru"

                # Descrierea din articol curent
                desc_p = article.find('p', class_='mb-35px')
                current_description = desc_p.get_text(strip=True) if desc_p else ""

                # URL complet
                if url.startswith('/'):
                    full_url = base_url + url
                elif not url.startswith('http'):
                    full_url = base_url + '/' + url
                else:
                    full_url = url

                # Extrage imaginea și lead-ul din fișiere locale
                img_src, img_alt, lead_description = get_image_and_lead_from_local_folders(
                    full_url, priority_folder, individual_files_folder
                )

                # Folosește lead-ul găsit sau descrierea curentă
                description = lead_description if lead_description else current_description

                if not img_src:
                    print(f"    Nu am găsit imagine pentru {title}")
                    img_src = "https://neculaifantanaru.com/images/default-article.jpg"
                    img_alt = title

                # URL complet pentru imagine
                if img_src and img_src.startswith('/'):
                    img_src = base_url + img_src
                elif img_src and not img_src.startswith('http'):
                    img_src = base_url + '/' + img_src

                print(f"  Imagine finală: {img_src}")
                print(f"  Lead final: {description[:100]}...")

                # Creează noul HTML
                new_article_html = f'''                    <article class="blog-box heading-space-half">
    <div class="blog-listing-inner news_item">
        <div class="article-card-new">
            <!-- Layout DESKTOP -->
            <div class="desktop-layout d-none d-md-block">
                <div class="article-header d-flex">
                    <div class="article-image-container">
                        <a href="{url}">
                            <img src="{img_src}" alt="{img_alt}" class="article-card-img">
                        </a>
                    </div>
                    <div class="article-header-content">
                        <h2 class="custom-h1" itemprop="name">
                            <a href="{url}" class="color-black">{title}</a>
                        </h2>
                        <div class="article-spacing"></div>
                        <div class="article-spacing"></div>
                        <div class="blog-post d-flex align-items-center flex-wrap">
                            <i class="fa fa-calendar mx-1"></i>
                            <time datetime="{date.split()[-1]}" class="color-black">{date}, in</time>
                            <a href="{category_url}" class="color-green font-weight-600 mx-1">{category}</a>
                        </div>
                        <div class="author-info color-black">by {author}</div>
                    </div>
                </div>
                <div class="article-body">
                    <div class="article-spacing"></div>
                    <div class="article-spacing"></div>
                    <p class="color-grey line-height-25px">{description}</p>
                    <a href="{url}" class="btn-setting color-black btn-hvr-up btn-blue btn-hvr-pink">
                        read more<span class="sr-only"> about {title}</span>
                    </a>
                </div>
            </div>
            <!-- Layout MOBIL -->
            <div class="mobile-layout d-block d-md-none">
                <div class="mobile-image-container">
                    <a href="{url}">
                        <img src="{img_src}" alt="{img_alt}" class="mobile-article-img">
                    </a>
                </div>
                <h2 class="custom-h1 mobile-title">
                    <a href="{url}" class="color-black">{title}</a>
                </h2>
                <p class="color-grey line-height-25px mobile-lead">{description}</p>
                <div class="blog-post mobile-date">
                    <i class="fa fa-calendar mx-1"></i>
                    <time datetime="{date.split()[-1]}" class="color-black">{date}, in</time>
                    <a href="{category_url}" class="color-green font-weight-600 mx-1">{category}</a>
                </div>
                <a href="{url}" class="btn-setting color-black btn-hvr-up btn-blue btn-hvr-pink mobile-read-more">
                    Read More<span class="sr-only"> about {title}</span>
                </a>
            </div>
        </div>
    </div>
</article>'''

                new_articles.append(new_article_html)
                time.sleep(0.1)  # Pauză mică pentru fișiere locale

            except Exception as e:
                print(f"    Eroare la procesarea articolului: {e}")
                continue

        # Înlocuiește în conținutul original
        if new_articles:
            start_pos = content.find('<!-- ARTICOL START -->')
            end_pos = content.find('<!-- ARTICOL FINAL -->')

            if start_pos != -1 and end_pos != -1:
                start_replace = start_pos + len('<!-- ARTICOL START -->')
                new_articles_content = '\n' + '\n'.join(new_articles) + '\n\t\t\t\t\t'
                final_content = (
                    content[:start_replace] +
                    new_articles_content +
                    content[end_pos:]
                )

                if final_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(final_content)
                    print(f"✓ SALVAT: {file_path}")
                else:
                    print(f"- Neschimbat: {file_path}")
            else:
                print(f"✗ Nu găsesc pozițiile comentariilor în {file_path}")

    except Exception as e:
        print(f"✗ Eroare la procesarea {file_path}: {e}")

def main():
    # Lista fișierelor categorii
    category_files = [
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

    # Căile folderelor - DOAR DOUĂ FOLDERE ACUM
    priority_folder = r"c:\Folder1\fisiere_gata"                                    # Fișierele categorii
    individual_files_folder = r"e:\Carte\BB\17 - Site Leadership\Principal 2022\en"  # Fișierele individuale pentru imagini/lead

    print("Începe procesarea cu căutare DOAR în foldere locale...")
    print(f"Folder prioritar (categorii): {priority_folder}")
    print(f"Folder fișiere individuale: {individual_files_folder}")
    print("=" * 60)

    # Procesez doar fișierele din lista categorii care există în folderul prioritar
    processed_files = 0
    for file_name in category_files:
        file_path = os.path.join(priority_folder, file_name)
        if os.path.exists(file_path):
            process_html_file(file_path, priority_folder, individual_files_folder)
            processed_files += 1
        else:
            print(f"- Nu există în folder prioritar: {file_name}")
        print("-" * 30)

    print(f"Finalizat! Procesate {processed_files} fișiere folosind doar resurse locale.")

if __name__ == "__main__":
    main()