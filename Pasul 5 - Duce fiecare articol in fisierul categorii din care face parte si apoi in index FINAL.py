import os
import re
import shutil
from bs4 import BeautifulSoup, Comment
from datetime import datetime, timedelta

# Track processing start time
START_TIME = datetime.now()

# Configuration
DEBUG = True
OUTPUT_DIR = r"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\output"
EN_DIR = r"e:\Carte\BB\17 - Site Leadership\Principal\en"
RO_DIR = r"e:\Carte\BB\17 - Site Leadership\Principal\ro"
BACKUP_DIR = r"c:\Folder1\fisiere_html"

def log(message):
    if DEBUG:
        print(message)

def clear_backup_directory():
    """Clear all contents from backup directory"""
    log("[STEP] Starting to clear backup directory...")
    try:
        if os.path.exists(BACKUP_DIR):
            # Remove all files and subdirectories
            for filename in os.listdir(BACKUP_DIR):
                file_path = os.path.join(BACKUP_DIR, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    log(f"[DELETE] Removed file: {filename}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    log(f"[DELETE] Removed directory: {filename}")
            log(f"[SUCCESS] Cleared backup directory: {BACKUP_DIR}")
        else:
            # Create the directory if it doesn't exist
            os.makedirs(BACKUP_DIR, exist_ok=True)
            log(f"[CREATE] Created backup directory: {BACKUP_DIR}")

    except Exception as e:
        log(f"[ERROR] Failed to clear backup directory: {str(e)}")
        raise

def copy_index_to_backup():
    """Copy the main index.html to backup directory at the start"""
    log("[STEP] Copying index.html to backup directory...")
    try:
        index_source = os.path.join(EN_DIR, 'index.html')
        index_backup = os.path.join(BACKUP_DIR, 'index.html')

        log(f"[DEBUG] Source: {index_source}")
        log(f"[DEBUG] Destination: {index_backup}")

        if os.path.exists(index_source):
            shutil.copy2(index_source, index_backup)
            log(f"[SUCCESS] Copied index.html to backup directory")
            return True
        else:
            log(f"[ERROR] Source index.html not found: {index_source}")
            return False
    except Exception as e:
        log(f"[ERROR] Failed to copy index.html: {str(e)}")
        return False

def read_file_with_fallback(file_path):
    log(f"[DEBUG] Reading file: {file_path}")
    encodings = ['utf-8', 'latin1', 'cp1252']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                log(f"[SUCCESS] Read file with {encoding} encoding")
                return content
        except UnicodeDecodeError:
            log(f"[DEBUG] Failed with {encoding} encoding, trying next...")
            continue
    log(f"[ERROR] Failed to read {file_path}")
    return None

def extract_article_data(html_content):
    log("[STEP] Extracting article data from OUTPUT_DIR file...")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title
    title_tag = soup.find('h1', class_='den_articol')
    if not title_tag:
        log("[ERROR] No title tag found")
        return None
    title = title_tag.get_text().strip()
    log(f"[DEBUG] Found title: {title}")

    # Extract canonical URL
    canonical = soup.find('link', rel='canonical')
    if not canonical:
        log("[ERROR] No canonical URL found")
        return None
    url = canonical.get('href', '').strip()
    log(f"[DEBUG] Found canonical URL: {url}")

    # Extract date and category
    meta_tag = soup.find('td', class_='text_dreapta')
    if not meta_tag:
        log("[ERROR] No meta tag found")
        return None

    # Date extraction
    date_match = re.search(r'On (.*?),', meta_tag.get_text())
    if not date_match:
        log("[ERROR] No date match found")
        return None
    date_str = date_match.group(1).strip()
    log(f"[DEBUG] Extracted date string: '{date_str}'")

    # Ensure date has year - FIXED LOGIC
    if not re.search(r'\d{4}$', date_str):
        date_str += f", {datetime.now().year}"
        log(f"[DEBUG] Added current year to date: {date_str}")
    else:
        log(f"[DEBUG] Date already has year: {date_str}")

    # Category extraction
    category_tag = meta_tag.find('a')
    if not category_tag:
        log("[ERROR] No category tag found")
        return None
    category_url = category_tag.get('href', '').strip()
    category_name = category_tag.get_text().strip()
    log(f"[DEBUG] Found category: {category_name} -> {category_url}")

    # Extract RO link from flags
    ro_flag = soup.find('img', {'title': 'ro', 'alt': 'ro'})
    ro_link = ro_flag.parent.get('href', '').strip() if ro_flag else None
    log(f"[DEBUG] RO link: {ro_link}")

    # Extract quote
    quote_tag = soup.find('p', class_='text_obisnuit2')
    quote = quote_tag.get_text().strip() if quote_tag else None
    log(f"[DEBUG] Found quote: {quote}")

    # Parse date for sorting
    try:
        if ',' in date_str:
            article_date = datetime.strptime(date_str, '%B %d, %Y')
        else:
            article_date = datetime.strptime(date_str, '%d %B %Y')
        log(f"[DEBUG] Parsed date: {article_date}")
    except ValueError as e:
        log(f"[ERROR] Date parsing failed: {e}")
        article_date = datetime.now()

    return {
        'title': title,
        'url': url,
        'date': date_str,
        'category_url': category_url,
        'category_name': category_name,
        'ro_link': ro_link,
        'quote': quote,
        'date_obj': article_date,
        'sort_key': article_date.strftime('%Y%m%d')
    }

def extract_backup_article_data(html_content, filename):
    """Extract article data from backup files with different structure"""
    log(f"[STEP] Extracting article data from backup file: {filename}")
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract canonical URL
    canonical = soup.find('link', rel='canonical')
    if not canonical:
        log(f"[ERROR] No canonical URL found in {filename}")
        return None
    url = canonical.get('href', '').strip()
    log(f"[DEBUG] Found canonical URL: {url}")

    # Extract title from h1 with itemprop="name"
    title_tag = soup.find('h1', class_='den_articol', attrs={'itemprop': 'name'})
    if not title_tag:
        log(f"[ERROR] No title tag found in {filename}")
        return None
    title = title_tag.get_text().strip()
    log(f"[DEBUG] Found title: {title}")

    # Extract date and category from td with class="text_dreapta"
    meta_tag = soup.find('td', class_='text_dreapta')
    if not meta_tag:
        log(f"[ERROR] No meta tag found in {filename}")
        return None

    meta_text = meta_tag.get_text()
    log(f"[DEBUG] Meta tag text: {meta_text}")

    # Date extraction - IMPROVED LOGIC TO PRESERVE ORIGINAL DATE
    date_match = re.search(r'On (.*?),', meta_text)
    if not date_match:
        log(f"[ERROR] No date match found in {filename}")
        return None
    date_str = date_match.group(1).strip()
    log(f"[DEBUG] Extracted original date string: '{date_str}'")

    # Check if we need to parse the full date including year from the meta text
    full_date_match = re.search(r'On (.*?), (\d{4})', meta_text)
    if full_date_match:
        # We have the full date with year
        date_str = f"{full_date_match.group(1)}, {full_date_match.group(2)}"
        log(f"[DEBUG] Found full date with year: {date_str}")
    else:
        # Try to extract year from anywhere in the meta text
        year_match = re.search(r'\b(19|20)\d{2}\b', meta_text)
        if year_match:
            year = year_match.group()
            if not re.search(r'\d{4}$', date_str):
                date_str += f", {year}"
                log(f"[DEBUG] Added extracted year to date: {date_str}")
        else:
            log(f"[WARNING] No year found in meta text for {filename}")

    # Category extraction
    category_tag = meta_tag.find('a')
    if not category_tag:
        log(f"[ERROR] No category tag found in {filename}")
        return None
    category_url = category_tag.get('href', '').strip()
    category_name = category_tag.get_text().strip()
    log(f"[DEBUG] Found category: {category_name} -> {category_url}")

    # Extract quote - IMPROVED METHOD
    quote = None
    log("[DEBUG] Searching for quote...")

    # Method 1: Find HTML comments containing SASA-1
    try:
        html_comments = soup.find_all(string=lambda text: isinstance(text, Comment) and 'SASA-1' in text)
        log(f"[DEBUG] Found {len(html_comments)} SASA-1 comments")

        for comment in html_comments:
            log("[DEBUG] Found SASA-1 comment, looking for next p tag...")
            # Look for the next p tag with class text_obisnuit2
            current = comment.parent
            while current:
                current = current.next_sibling
                if hasattr(current, 'name') and current.name == 'p':
                    if current.get('class') and 'text_obisnuit2' in current.get('class'):
                        em_tag = current.find('em')
                        if em_tag:
                            quote = em_tag.get_text().strip()
                            log(f"[DEBUG] Found quote via SASA-1 method: {quote}")
                            break
                elif hasattr(current, 'name') and current.name:
                    # Stop if we hit another major element
                    break
            if quote:
                break
    except Exception as e:
        log(f"[DEBUG] SASA-1 method failed: {e}")

    # Method 2: If not found, try to find any p with class text_obisnuit2
    if not quote:
        log("[DEBUG] SASA-1 method failed, trying direct p tag search...")
        quote_tag = soup.find('p', class_='text_obisnuit2')
        if quote_tag:
            em_tag = quote_tag.find('em')
            if em_tag:
                quote = em_tag.get_text().strip()
                log(f"[DEBUG] Found quote via direct search: {quote}")

    # Method 3: Default quote if nothing found
    if not quote:
        quote = 'True knowledge begins where you dare to transcend the limits imposed by the teachings of others.'
        log("[DEBUG] Using default quote")

    # Parse date for sorting - KEEP ORIGINAL YEAR
    try:
        if ',' in date_str:
            article_date = datetime.strptime(date_str, '%B %d, %Y')
        else:
            article_date = datetime.strptime(date_str, '%d %B %Y')
        log(f"[DEBUG] Parsed date successfully: {article_date}")
    except ValueError as e:
        log(f"[ERROR] Date parsing failed for '{date_str}': {e}")
        # Try to extract year manually if possible
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = int(year_match.group())
            log(f"[DEBUG] Found year {year} in date string")
            try:
                # Try to parse month and day
                month_day_match = re.search(r'([A-Za-z]+)\s+(\d+)', date_str)
                if month_day_match:
                    month_name = month_day_match.group(1)
                    day = int(month_day_match.group(2))
                    article_date = datetime.strptime(f"{month_name} {day}, {year}", '%B %d, %Y')
                    log(f"[DEBUG] Successfully parsed date with extracted components: {article_date}")
                else:
                    article_date = datetime(year, 1, 1)  # Use January 1st as fallback
                    log(f"[DEBUG] Using fallback date: {article_date}")
            except:
                article_date = datetime(year, 1, 1)  # Use January 1st as fallback
        else:
            article_date = datetime.now()
            log("[DEBUG] Using current date as fallback")

    result = {
        'title': title,
        'url': url,
        'date': date_str,
        'category_url': category_url,
        'category_name': category_name,
        'quote': quote,
        'date_obj': article_date,
        'sort_key': article_date.strftime('%Y%m%d'),
        'filename': filename
    }

    log(f"[SUCCESS] Extracted data for {filename}: {title} ({date_str})")
    return result

def generate_article_html(article):
    """Generate HTML for an article with proper formatting"""
    log(f"[DEBUG] Generating HTML for: {article['title']}")
    # Note: Added newline before the table to ensure proper spacing
    return f"""<table width="638" border="0">
        <tr>
          <td><span class="den_articol"><a href="{article['url']}" class="linkMare">{article['title']}</a></span></td>
        </tr>
        <tr>
          <td class="text_dreapta">On {article['date']}, in <a href="{article['category_url']}" title="View all articles from {article['category_name']}" class="external" rel="category tag">{article['category_name']}</a>, by Neculai Fantanaru</td>
        </tr>
      </table>
      <p class="text_obisnuit2"><em>{article['quote']}</em></p>
      <table width="552" border="0">
        <tr>
          <td width="552"><div align="right" id="external2"><a href="{article['url']}">read more </a><a href="https://neculaifantanaru.com/en/" title=""><img src="Arrow3_black_5x7.gif" alt="" width="5" height="7" class="arrow" /></a></div></td>
        </tr>
      </table>
      <p class="text_obisnuit"></p>
"""

def update_backup_index_with_all_articles():
    """Update the backup index.html with all articles from backup directory"""
    log("\n" + "="*60)
    log("STEP 5: UPDATING BACKUP INDEX WITH ALL ARTICLES")
    log("="*60)

    # Files to exclude
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

    backup_index_path = os.path.join(BACKUP_DIR, 'index.html')
    log(f"[DEBUG] Backup index path: {backup_index_path}")

    # Check if backup index exists
    if not os.path.exists(backup_index_path):
        log("[ERROR] Backup index.html not found")
        return False

    # Read backup index content
    log("[STEP] Reading backup index content...")
    index_content = read_file_with_fallback(backup_index_path)
    if not index_content:
        log("[ERROR] Failed to read backup index.html")
        return False

    # Collect articles from backup directory
    backup_articles = []
    log(f"[STEP] Scanning backup directory: {BACKUP_DIR}")

    all_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.html')]
    log(f"[DEBUG] Found {len(all_files)} HTML files in backup directory")

    for filename in all_files:
        log(f"[DEBUG] Processing file: {filename}")

        if filename in category_files:
            log(f"[SKIP] Excluded category file: {filename}")
            continue

        filepath = os.path.join(BACKUP_DIR, filename)
        content = read_file_with_fallback(filepath)
        if not content:
            log(f"[ERROR] Failed to read content from {filename}")
            continue

        article = extract_backup_article_data(content, filename)
        if article:
            backup_articles.append(article)
            log(f"[SUCCESS] Extracted: {filename} -> {article['title']} ({article['date']})")
        else:
            log(f"[ERROR] Failed to extract article data from {filename}")

    if not backup_articles:
        log("[INFO] No articles found in backup directory")
        return True

    # Sort articles by date (descending - newest first)
    log("[STEP] Sorting articles by date (newest first)...")
    backup_articles.sort(key=lambda x: x['date_obj'], reverse=True)

    log(f"[INFO] Found {len(backup_articles)} articles to add to index:")
    for i, article in enumerate(backup_articles):
        log(f"  {i+1}. {article['date']} - {article['title']}")

    # Find the insertion point in index.html
    start_marker = '<!-- ARTICOL CATEGORIE START -->'
    end_marker = '<!-- ARTICOL CATEGORIE FINAL -->'

    log("[STEP] Finding article section markers in backup index...")
    start_pos = index_content.find(start_marker)
    end_pos = index_content.find(end_marker)

    if start_pos == -1 or end_pos == -1:
        log("[ERROR] Could not find article section markers in backup index")
        log(f"[DEBUG] start_marker found at: {start_pos}")
        log(f"[DEBUG] end_marker found at: {end_pos}")
        return False

    log(f"[DEBUG] Article section found: {start_pos} to {end_pos}")

    # Extract existing content before and after the section
    before_section = index_content[:start_pos + len(start_marker)]
    after_section = index_content[end_pos:]

    log("[STEP] Building new article section...")
    # Build new content with all articles
    new_section_content = '\n'
    for i, article in enumerate(backup_articles):
        log(f"[DEBUG] Adding article {i+1}: {article['title']}")
        new_section_content += generate_article_html(article)

    # Combine all parts
    updated_content = before_section + new_section_content + after_section

    # Write updated index back
    log("[STEP] Writing updated backup index...")
    try:
        with open(backup_index_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        log(f"[SUCCESS] Updated backup index with {len(backup_articles)} articles")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to write updated backup index: {str(e)}")
        return False

def update_category_file(category_path, articles):
    log(f"[STEP] Updating category file: {os.path.basename(category_path)}")
    content = read_file_with_fallback(category_path)
    if not content:
        return False

    # Determine the category URL from the file name
    category_filename = os.path.basename(category_path)
    expected_category_url = f"https://neculaifantanaru.com/en/{category_filename}"
    log(f"[DEBUG] Expected category URL: {expected_category_url}")

    # Extract the section between <!-- ARTICOL CATEGORIE START --> and <!-- ARTICOL CATEGORIE FINAL -->
    section_pattern = re.compile(r'<!-- ARTICOL CATEGORIE START -->.*?<!-- ARTICOL CATEGORIE FINAL -->', re.DOTALL)
    section_match = section_pattern.search(content)
    if not section_match:
        log(f"[ERROR] Nu s-a găsit secțiunea de articole în {category_filename}")
        return False

    section_content = section_match.group(0)

    # Find existing article URLs within the section
    existing_urls = set(re.findall(r'href="(https://neculaifantanaru\.com/en/[^"]+)"', section_content))
    log(f"[DEBUG] Found {len(existing_urls)} existing URLs in category")

    # Filter new articles: only those that belong to this category and are not duplicates
    new_articles = [
        article for article in articles
        if article['category_url'] == expected_category_url and article['url'] not in existing_urls
    ]
    log(f"[DEBUG] Found {len(new_articles)} new articles for this category")

    if not new_articles:
        log(f"[INFO] Niciun articol nou pentru categoria {category_filename}")
        return True

    # Find insertion point
    insert_pos = content.find('<!-- ARTICOL CATEGORIE START -->')
    if insert_pos == -1:
        log(f"[ERROR] Nu s-a găsit punctul de inserare în {category_filename}")
        return False
    insert_pos = content.find('<div align="justify">', insert_pos) + len('<div align="justify">')

    # Generate new content
    new_content = content[:insert_pos]
    for article in new_articles:
        new_content += '\n' + generate_article_html(article)
    new_content += content[insert_pos:]

    # Write updated file
    try:
        with open(category_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log(f"[SUCCESS] Updated {category_filename} with {len(new_articles)} articles")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to write {category_path}: {str(e)}")
        return False

def update_index_file(en_index_path, articles, ro_index_path):
    log(f"\n[STEP] Updating index file: {os.path.basename(en_index_path)}")

    # Read the current EN index content
    content = read_file_with_fallback(en_index_path)
    if not content:
        log("[ERROR] Failed to read EN index file")
        return False

    # Extract all existing article URLs to avoid duplicates
    existing_urls = set()
    for match in re.finditer(r'href="(https://neculaifantanaru\.com/en/[^"]+)"', content):
        existing_urls.add(match.group(1))
    log(f"[DEBUG] Found {len(existing_urls)} existing articles in index")

    # Read RO index if exists
    ro_content = ""
    if os.path.exists(ro_index_path):
        ro_content = read_file_with_fallback(ro_index_path) or ""
        log("[DEBUG] RO index content loaded")
    else:
        log("[WARNING] RO index file not found")

    # Filter articles - must be:
    # 1. Not already in index
    # 2. Have RO version if RO index exists
    # 3. From last 4 months
    four_months_ago = datetime.now() - timedelta(days=120)
    valid_articles = []

    for article in articles:
        if article['url'] in existing_urls:
            log(f"[SKIP] Articol deja existent in index: {article['title']}")
            continue

        if article['date_obj'] < four_months_ago:
            log(f"[SKIP] Article too old: {article['title']} ({article['date']})")
            continue

        if ro_content and article.get('ro_link'):
            ro_filename = os.path.basename(article['ro_link'].split('?')[0])
            if f'/{ro_filename}"' not in ro_content and f'/{ro_filename}?' not in ro_content:
                log(f"[SKIP] Missing RO version for: {article['title']}")
                continue

        valid_articles.append(article)

    if not valid_articles:
        log("[INFO] Niciun articol nou de adaugat")
        return True

    # Sort articles by date (ascending)
    valid_articles.sort(key=lambda x: x['date_obj'])

    # Find insertion point - IMPROVED SEARCH
    insert_pos = -1

    # Try multiple patterns to find insertion point
    patterns = [
        r'<!-- ARTICOL CATEGORIE START -->\s*',
        r'<!-- ARTICOL CATEGORIE START -->',
    ]

    for pattern in patterns:
        insert_match = re.search(pattern, content)
        if insert_match:
            insert_pos = insert_match.end()
            log(f"[DEBUG] Found insertion point with pattern: {pattern}")
            break

    if insert_pos == -1:
        log("[ERROR] Could not find insertion point in index")
        return False

    # Build new content
    new_content = content[:insert_pos] + '\n'
    for article in valid_articles:
        new_content += generate_article_html(article)
    new_content += content[insert_pos:]

    # Write updated file
    try:
        with open(en_index_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log(f"[SUCCESS] Added {len(valid_articles)} articles to index")
        return True
    except Exception as e:
        log(f"[ERROR] Failed to write index: {str(e)}")
        return False

def main():
    # Verifică existența directorului OUTPUT_DIR
    if not os.path.exists(OUTPUT_DIR):
        log(f"[FATAL ERROR] Output directory not found: {OUTPUT_DIR}")
        return

    # Verifică drepturi de scriere în EN_DIR
    if not os.access(EN_DIR, os.W_OK):
        log(f"[FATAL ERROR] No write permissions in: {EN_DIR}")
        return

    log("="*60)
    log(f"Process started at {START_TIME}")
    log("STARTING ARTICLE PROCESSING")
    log("="*60)

    log("\nSTEP 0: Creating backup directory and copying index...")
    # CLEAR BACKUP DIRECTORY FIRST
    clear_backup_directory()

    # Copy index.html to backup directory
    if not copy_index_to_backup():
        log("[ERROR] Failed to copy index.html to backup")
        return

    # Process all articles
    articles = []
    categories = set()
    modified_files = set()

    log("\n" + "="*60)
    log("STEP 1: PROCESSING OUTPUT DIRECTORY ARTICLES")
    log("="*60)
    for filename in os.listdir(OUTPUT_DIR):
        if not filename.endswith('.html'):
            continue

        log(f"\n[PROCESS] Starting {filename}...")
        filepath = os.path.join(OUTPUT_DIR, filename)
        content = read_file_with_fallback(filepath)
        if not content:
            continue

        article = extract_article_data(content)
        if article:
            articles.append(article)
            categories.add(article['category_url'])

            # Copy to EN directory
            en_path = os.path.join(EN_DIR, filename)
            shutil.copy2(filepath, en_path)
            modified_files.add(en_path)
            log(f"[COPY] {filename} -> EN directory")

    log("\n" + "="*60)
    log("PROCESSING COMPLETE")
    log(f"Processed articles: {len(articles)}")
    log(f"Updated categories: {len(categories)}")
    log(f"Total processing time: {datetime.now() - START_TIME}")
    log("="*60)

    if not articles:
        log("[ERROR] No articles processed")
        return

    log("\n" + "="*60)
    log("STEP 2: UPDATING CATEGORY FILES")
    log("="*60)
    for category_url in categories:
        category_file = os.path.basename(category_url)
        category_path = os.path.join(EN_DIR, category_file)
        if os.path.exists(category_path):
            if update_category_file(category_path, articles):
                modified_files.add(category_path)

    log("\n" + "="*60)
    log("STEP 3: UPDATING EN INDEX")
    log("="*60)
    en_index = os.path.join(EN_DIR, 'index.html')
    ro_index = os.path.join(RO_DIR, 'index.html')
    if update_index_file(en_index, articles, ro_index):
        modified_files.add(en_index)

    log("\n" + "="*60)
    log("STEP 4: CREATING BACKUP OF MODIFIED FILES")
    log("="*60)
    try:
        # Copy the new files to backup
        backed_up = 0
        for filepath in modified_files:
            if os.path.exists(filepath):
                dest = os.path.join(BACKUP_DIR, os.path.basename(filepath))
                shutil.copy2(filepath, dest)
                log(f"[BACKUP] {os.path.basename(filepath)}")
                backed_up += 1

        if backed_up > 0:
            log(f"[SUCCESS] Backed up {backed_up} files to {BACKUP_DIR}")
        else:
            log("[INFO] No files needed backup")

    except Exception as e:
        log(f"[ERROR] Backup failed: {str(e)}")

    # NEW STEP: Update backup index with all articles
    update_backup_index_with_all_articles()

    log("\n" + "="*60)
    log("FINAL PROCESSING REPORT")
    log(f"Total articles processed: {len(articles)}")
    log(f"Categories updated: {len(categories)}")
    log(f"Files backed up: {len(modified_files)}")
    log(f"Total processing time: {datetime.now() - START_TIME}")
    log("="*60)

if __name__ == "__main__":
    main()