import os
import re

def extract_ro_link_from_flags(content):
    """Extrage link-ul RO din secțiunea FLAGS"""
    flags_match = re.search(r'<!-- FLAGS_1 -->.*?<!-- FLAGS -->', content, re.DOTALL)
    if flags_match:
        flags_section = flags_match.group(0)
        ro_link_match = re.search(r'<a cunt_code="\+40" href="([^"]+)">', flags_section)
        if ro_link_match:
            return ro_link_match.group(1)
    return None

def url_to_local_path(url, base_dir):
    """Convertește URL-ul într-o cale locală"""
    if url.startswith('https://neculaifantanaru.com/'):
        filename = url.split('/')[-1]
        return os.path.join(base_dir, filename)
    return None

def extract_title_from_content(content, filename):
    """Extrage titlul din tag-ul <title> sau din alte surse"""
    print(f"[DEBUG] Looking for title in {filename}")

    # Pattern 1: Standard cu | Neculai Fantanaru
    title_match = re.search(r'<title>(.*?) \| Neculai Fantanaru</title>', content)
    if title_match:
        title = title_match.group(1).strip()
        print(f"[DEBUG] Found title (pattern 1): '{title}'")
        return title

    # Pattern 2: Fără | Neculai Fantanaru
    title_match = re.search(r'<title>(.*?)</title>', content)
    if title_match:
        title = title_match.group(1).strip()
        # Elimină " | Neculai Fantanaru" dacă există
        title = re.sub(r'\s*\|\s*Neculai Fantanaru\s*$', '', title)
        print(f"[DEBUG] Found title (pattern 2): '{title}'")
        return title

    # Pattern 3: Din h1 cu class="den_articol" și itemprop="name"
    h1_match = re.search(r'<h1[^>]*class="den_articol"[^>]*itemprop="name"[^>]*>(.*?)</h1>', content)
    if h1_match:
        title = h1_match.group(1).strip()
        print(f"[DEBUG] Found title (pattern 3 - h1): '{title}'")
        return title

    # Pattern 4: Orice h1 cu class="den_articol"
    h1_match = re.search(r'<h1[^>]*class="den_articol"[^>]*>(.*?)</h1>', content)
    if h1_match:
        title = h1_match.group(1).strip()
        print(f"[DEBUG] Found title (pattern 4 - h1 simple): '{title}'")
        return title

    # Afișează începutul fișierului pentru debug
    first_500_chars = content[:500]
    print(f"[DEBUG] Could not find title. First 500 chars of {filename}:")
    print(f"[DEBUG] {first_500_chars}")
    return ""

def extract_media_section_from_ro(ro_content):
    """Extrage secțiunea media din fișierul RO"""
    # Caută secțiunea între <!--FINNISHDATES--> și <!-- ARTICOL START -->
    media_match = re.search(r'<!--FINNISHDATES-->(.*?)<!-- ARTICOL START -->', ro_content, re.DOTALL)
    if media_match:
        media_section = media_match.group(1).strip()

        # Verifică dacă conține video YouTube
        if 'youtube.com/embed/' in media_section or 'iframe' in media_section:
            return media_section, 'video'
        # Verifică dacă conține imagine
        elif '<img' in media_section and 'feature-img-wrap' in media_section:
            return media_section, 'image'

    return None, None

def update_media_titles(media_section, english_title, media_type):
    """Actualizează titlurile din secțiunea media cu titlul englezesc"""
    if media_type == 'video':
        # Actualizează title din iframe
        media_section = re.sub(r'title="[^"]*"', f'title="{english_title} Video"', media_section)
    elif media_type == 'image':
        # Actualizează alt din img
        media_section = re.sub(r'alt="[^"]*"', f'alt="{english_title}"', media_section)

    return media_section

def update_html_files(directory):
    files_processed = 0
    files_skipped = 0
    replacements_made = {}

    # Calea către directorul RO
    ro_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro'
    print(f"[DEBUG] RO directory: {ro_directory}")
    print(f"[DEBUG] RO directory exists: {os.path.exists(ro_directory)}")

    # Lista fișierelor de sărit
    skip_files = [
        'index.html', 'leadership-and-attitude.html', 'leadership-magic.html',
        'successful-leadership.html', 'hr-human-resources.html', 'leadership-laws.html',
        'total-leadership.html', 'leadership-that-lasts.html', 'leadership-principles.html',
        'leadership-plus.html', 'qualities-of-a-leader.html', 'top-leadership.html',
        'leadership-impact.html', 'personal-development.html', 'leadership-skills-and-abilities.html',
        'real-leadership.html', 'basic-leadership.html', 'leadership-360.html',
        'leadership-pro.html', 'leadership-expert.html', 'leadership-know-how.html',
        'leadership-journal.html', 'alpha-leadership.html', 'leadership-on-off.html',
        'leadership-deluxe.html', 'leadership-xxl.html', 'leadership-50-extra.html',
        'leadership-fusion.html', 'leadership-v8.html', 'leadership-x3-silver.html',
        'leadership-q2-sensitive.html', 'leadership-t7-hybrid.html', 'leadership-n6-celsius.html',
        'leadership-s4-quartz.html', 'leadership-gt-accent.html', 'leadership-fx-intensive.html',
        'leadership-iq-light.html', 'leadership-7th-edition.html', 'leadership-xs-analytics.html',
        'leadership-z3-extended.html', 'leadership-ex-elite.html', 'leadership-w3-integra.html',
        'leadership-sx-experience.html', 'leadership-y5-superzoom.html', 'performance-ex-flash.html',
        'leadership-mindware.html', 'leadership-r2-premiere.html', 'leadership-y4-titanium.html',
        'leadership-quantum-xx.html', 'python-scripts-examples.html', 'lideri-si-atitudine.html',
        'leadership-de-succes.html', 'hr-resurse-umane.html', 'legile-conducerii.html',
        'leadership-total.html', 'leadership-de-durata.html', 'principiile-conducerii.html',
        'calitatile-unui-lider.html', 'leadership-de-varf.html', 'dezvoltare-personala.html',
        'aptitudini-si-abilitati-de-leadership.html', 'leadership-real.html',
        'leadership-de-baza.html', 'jurnal-de-leadership.html'
    ]

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            if filename in skip_files:
                print(f"Skipping file: {filename}")
                files_skipped += 1
                continue

            filepath = os.path.join(directory, filename)
            print(f"\n[PROCESS] Starting {filename}...")

            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                print(f"[DEBUG] Successfully read {filename} ({len(content)} characters)")
            except Exception as e:
                print(f"[ERROR] Error reading {filename}: {e}")
                files_skipped += 1
                continue

            # Extrage titlul din fișierul englez
            english_title = extract_title_from_content(content, filename)
            if not english_title:
                print(f"[ERROR] Could not extract title from {filename}")
                files_skipped += 1
                continue

            print(f"[SUCCESS] Extracted title: '{english_title}'")

            # Verifică dacă există deja media între <!--FINNISHDATES--> și <!-- ARTICOL START -->
            if re.search(r'<!--FINNISHDATES-->.*?(?:<img|<iframe).*?<!-- ARTICOL START -->', content, re.DOTALL):
                print(f"[SKIP] Media already exists in {filename}")
                files_skipped += 1
                continue

            # Extrage link-ul RO din FLAGS
            ro_url = extract_ro_link_from_flags(content)
            if not ro_url:
                print(f"[ERROR] Could not find RO link in FLAGS for {filename}")
                # Afișează secțiunea FLAGS pentru debug
                flags_match = re.search(r'<!-- FLAGS_1 -->.*?<!-- FLAGS -->', content, re.DOTALL)
                if flags_match:
                    print(f"[DEBUG] FLAGS section found but no RO link:")
                    print(f"[DEBUG] {flags_match.group(0)[:200]}...")
                else:
                    print(f"[DEBUG] No FLAGS section found in {filename}")
                files_skipped += 1
                continue

            print(f"[SUCCESS] Found RO URL: {ro_url}")

            # Convertește URL-ul într-o cale locală
            ro_filepath = url_to_local_path(ro_url, ro_directory)
            if not ro_filepath:
                print(f"[ERROR] Could not convert URL to local path: {ro_url}")
                files_skipped += 1
                continue

            print(f"[DEBUG] RO local path: {ro_filepath}")

            if not os.path.exists(ro_filepath):
                print(f"[ERROR] RO file not found: {ro_filepath}")
                files_skipped += 1
                continue

            print(f"[SUCCESS] Found RO counterpart: {os.path.basename(ro_filepath)}")

            # Citește fișierul RO
            try:
                with open(ro_filepath, 'r', encoding='utf-8') as file:
                    ro_content = file.read()
                print(f"[DEBUG] Successfully read RO file ({len(ro_content)} characters)")
            except Exception as e:
                print(f"[ERROR] Error reading RO file {ro_filepath}: {e}")
                files_skipped += 1
                continue

            # Extrage secțiunea media din fișierul RO
            media_section, media_type = extract_media_section_from_ro(ro_content)
            if not media_section:
                print(f"[ERROR] No media section found in RO file for {filename}")
                # Debug: verifică dacă există tagurile
                if '<!--FINNISHDATES-->' not in ro_content:
                    print(f"[DEBUG] No <!--FINNISHDATES--> found in RO file")
                if '<!-- ARTICOL START -->' not in ro_content:
                    print(f"[DEBUG] No <!-- ARTICOL START --> found in RO file")
                files_skipped += 1
                continue

            print(f"[SUCCESS] Found {media_type} in RO file")
            print(f"[DEBUG] Media section preview: {media_section[:100]}...")

            # Actualizează titlurile în secțiunea media
            updated_media_section = update_media_titles(media_section, english_title, media_type)

            replacements = []

            # Elimină </div> imediat după <!--FINNISHDATES-->
            content, div_count = re.subn(r'(<!--FINNISHDATES-->)\s*</div>', r'\1', content)
            if div_count > 0:
                replacements.append(f"Removed extra </div> after <!--FINNISHDATES--> ({div_count} times)")
                print(f"[DEBUG] Removed {div_count} extra </div> tags")

            # Înlocuiește secțiunea dintre <!--FINNISHDATES--> și <!-- ARTICOL START -->
            content, count = re.subn(
                r'(<!--FINNISHDATES-->)(?:\s*</div>)?\s*(<!-- ARTICOL START -->)',
                f'\\1\n{updated_media_section}\n\\2',
                content,
                flags=re.DOTALL
            )

            if count > 0:
                replacements.append(f"Added {media_type} section from RO file ({count} times)")
                print(f"[DEBUG] Made {count} media section replacements")

            if replacements:
                # Scrie conținutul actualizat înapoi în fișier
                try:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(content)
                    files_processed += 1
                    replacements_made[filename] = replacements
                    print(f"[SUCCESS] Updated {filename}")
                    print(f"[DEBUG] Replacements made in {filename}:")
                    for i, replacement in enumerate(replacements, 1):
                        print(f"  {i}. {replacement}")
                except Exception as e:
                    print(f"[ERROR] Error writing {filename}: {e}")
                    files_skipped += 1
            else:
                print(f"[INFO] No replacements needed in {filename}")

    print("\n" + "="*60)
    print("PROCESSING COMPLETE")
    print("="*60)
    print(f"Files updated: {files_processed}")
    print(f"Files skipped: {files_skipped}")

    if replacements_made:
        print("\nFiles successfully updated:")
        for file, reps in replacements_made.items():
            print(f"\n{file}:")
            for i, rep in enumerate(reps, 1):
                print(f"  {i}. {rep}")

    print(f"\nFiles processed but no changes needed:")
    for filename in os.listdir(directory):
        if (filename.endswith(".html") and
            filename not in replacements_made and
            filename not in skip_files):
            print(f"  {filename}")

# Actualizează această cale cu directorul care conține fișierele tale HTML
directory_path = r'c:\Folder1\fisiere_gata'
update_html_files(directory_path)