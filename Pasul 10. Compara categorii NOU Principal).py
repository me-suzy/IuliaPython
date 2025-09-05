import os
import re
from pathlib import Path

ro_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro'
en_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en'

def read_file_with_fallback_encoding(file_path):
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    print(f"Nu s-a putut citi fișierul {file_path}")
    return None

def normalize_value(val):
    if val is None:
        return None
    val = val.replace('\xa0', ' ').strip()
    val = val.replace('–', '-').replace('—', '-')
    return val  # Removed .lower() to preserve case sensitivity

def get_links_from_flags(content, filename, directory):
    flags_section = re.search(r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->', content, re.DOTALL)
    if not flags_section:
        print(f"\nFIȘIER PROBLEMATIC: {os.path.join(directory, filename)} - Nu s-a găsit secțiunea FLAGS")
        return None

    flags_content = flags_section.group(1)

    # Try the old format first (with img tags and title attributes)
    ro_match = re.search(r'<a href="https://neculaifantanaru\.com/+([^"]+)"[^>]*?><img[^>]*?title="ro"', flags_content)
    en_match = re.search(r'<a href="https://neculaifantanaru\.com/+en/([^"]+)"[^>]*?><img[^>]*?title="en"', flags_content)

    # If old format not found, try the new format (with li elements and cunt_code attributes)
    if not ro_match or not en_match:
        # New format patterns
        ro_match_new = re.search(r'<li><a cunt_code="\+40" href="https://neculaifantanaru\.com/([^"]+)"', flags_content)
        en_match_new = re.search(r'<li><a cunt_code="\+1" href="https://neculaifantanaru\.com/en/([^"]+)"', flags_content)

        # Use new format if found
        if ro_match_new:
            ro_match = ro_match_new
        if en_match_new:
            en_match = en_match_new

    # If still no matches found, try a more flexible approach for new format
    if not ro_match or not en_match:
        # Look for Romania link (RO)
        if not ro_match:
            ro_match_flexible = re.search(r'<li><a[^>]*href="https://neculaifantanaru\.com/([^"]+)"[^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>Romania</span>', flags_content)
            if ro_match_flexible:
                ro_match = ro_match_flexible

        # Look for United States link (EN)
        if not en_match:
            en_match_flexible = re.search(r'<li><a[^>]*href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*>[^<]*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>United States</span>', flags_content)
            if en_match_flexible:
                en_match = en_match_flexible

    if not ro_match or not en_match:
        print(f"\nFIȘIER PROBLEMATIC: {os.path.join(directory, filename)} - Lipsesc link-urile RO/EN")
        print(f"  RO găsit: {'Da' if ro_match else 'Nu'}")
        print(f"  EN găsit: {'Da' if en_match else 'Nu'}")
        # Debug: show a snippet of the flags content to help identify the issue
        print(f"  Preview flags content: {flags_content[:200]}...")
        return None

    return {
        'ro_link': normalize_value(ro_match.group(1)),
        'en_link': normalize_value(en_match.group(1))
    }

def compare_and_check_files():
    issues_found = []

    for ro_file in os.listdir(ro_directory):
        if not ro_file.endswith('.html'):
            continue

        print(f"Procesare fișier: {ro_file}", flush=True)

        ro_path = os.path.join(ro_directory, ro_file)
        ro_content = read_file_with_fallback_encoding(ro_path)
        if not ro_content:
            continue

        ro_links = get_links_from_flags(ro_content, ro_file, ro_directory)
        if not ro_links:
            continue

        # Verifică fișierul EN corespondent
        en_file = None
        en_path = None
        en_content = None
        en_links = None

        # Use the EN link from RO as the expected EN filename, preserving case
        expected_en_filename = ro_links['en_link']
        if expected_en_filename:
            # Check if the file exists with exact case
            en_path = os.path.join(en_directory, expected_en_filename)
            if os.path.exists(en_path):
                en_file = expected_en_filename
                en_content = read_file_with_fallback_encoding(en_path)
                if en_content:
                    en_links = get_links_from_flags(en_content, en_file, en_directory)
            else:
                # Check for case-insensitive match in directory
                en_files = [f for f in os.listdir(en_directory) if f.lower() == expected_en_filename.lower()]
                if en_files:
                    en_file = en_files[0]  # Take the first matching file (actual case)
                    en_path = os.path.join(en_directory, en_file)
                    en_content = read_file_with_fallback_encoding(en_path)
                    if en_content:
                        en_links = get_links_from_flags(en_content, en_file, en_directory)
                    print(f"  ⚠️ Fișierul EN există cu case diferit: {en_file} (așteptat: {expected_en_filename})")
                else:
                    print(f"  ⚠️ Fișierul EN nu există: {expected_en_filename}")

        # Verifică link-urile corecte, case-sensitive
        correct_ro_link = normalize_value(ro_file)
        correct_en_link = normalize_value(en_file) if en_file else normalize_value(expected_en_filename)

        # Debug: Afișează link-urile găsite și așteptate
        print(f"  🔎 RO file links: RO={ro_links['ro_link']}, EN={ro_links['en_link']}")
        print(f"  🔎 Expected: RO={correct_ro_link}, EN={correct_en_link}")
        if en_links:
            print(f"  🔎 EN file links: RO={en_links['ro_link']}, EN={en_links['en_link']}")

        ro_has_error = False
        en_has_error = False

        # Verifică greșelile în fișierul RO, case-sensitive
        if ro_links['ro_link'] != correct_ro_link:
            ro_has_error = True
        if ro_links['en_link'] != correct_en_link:
            ro_has_error = True

        # Verifică greșelile în fișierul EN, dacă există
        if en_links:
            if en_links['ro_link'] != correct_ro_link:
                en_has_error = True
            if en_links['en_link'] != correct_en_link:
                en_has_error = True

        if ro_has_error or en_has_error:
            issue_details = {
                'ro_file': ro_file,
                'en_file': en_file,
                'ro_has_error': ro_has_error,
                'en_has_error': en_has_error,
                'ro_links': ro_links,
                'en_links': en_links,
                'correct_ro_link': correct_ro_link,
                'correct_en_link': correct_en_link
            }
            issues_found.append(issue_details)

            print(f"  🔍 Identificată problemă în: {ro_file}")

            # Afișează erorile pentru fișierul RO
            if ro_has_error:
                print(f"    → Erori în fișierul RO: {ro_file}")
                if ro_links['ro_link'] != correct_ro_link:
                    print(f"      ✗ Link RO greșit: {ro_links['ro_link']} → Ar trebui să fie: {correct_ro_link}")
                if ro_links['en_link'] != correct_en_link:
                    print(f"      ✗ Link EN greșit: {ro_links['en_link']} → Ar trebui să fie: {correct_en_link}")
            else:
                print(f"    ✅ Fișierul RO este corect")

            # Afișează erorile pentru fișierul EN, dacă există
            if en_has_error:
                print(f"    → Erori în fișierul EN: {en_file}")
                if en_links['ro_link'] != correct_ro_link:
                    print(f"      ✗ Link RO greșit: {en_links['ro_link']} → Ar trebui să fie: {correct_ro_link}")
                if en_links['en_link'] != correct_en_link:
                    print(f"      ✗ Link EN greșit: {en_links['en_link']} → Ar trebui să fie: {correct_en_link}")
            else:
                if en_links:
                    print(f"    ✅ Fișierul EN este corect")

            print()

    return issues_found

# Rulează verificarea
print("\nVerificare link-uri în FLAGS...")
print("=" * 80)

issues_found = compare_and_check_files()

if issues_found:
    print(f"\n🔍 VERIFICARE COMPLETĂ!")
    print("=" * 80)
    print(f"Total fișiere cu probleme găsite: {len(issues_found)}")
    print("\nDetalii probleme găsite:")

    for i, issue in enumerate(issues_found, 1):
        print(f"\n{i}. Fișierul RO: {issue['ro_file']}")
        print(f"   Fișierul EN: {issue['en_file'] if issue['en_file'] else 'Nu există'}")
        if issue['ro_has_error']:
            print(f"   🔴 GREȘEALĂ în RO")
            if issue['ro_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['ro_links']['ro_link']} → Ar trebui să fie: {issue['correct_ro_link']}")
            if issue['ro_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['ro_links']['en_link']} → Ar trebui să fie: {issue['correct_en_link']}")
        else:
            print(f"   🟢 RO este corect")

        if issue['en_has_error']:
            print(f"   🔴 GREȘEALĂ în EN")
            if issue['en_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['en_links']['ro_link']} → Ar trebui să fie: {issue['correct_ro_link']}")
            if issue['en_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['en_links']['en_link']} → Ar trebui să fie: {issue['correct_en_link']}")
        else:
            if issue['en_links']:
                print(f"   🟢 EN este corect")
            else:
                print(f"   ⚠️ EN nu există")

    print("=" * 80)
else:
    print("✅ Nu s-au găsit probleme în fișiere.")

print("\n🔍 Verificare finală completată!")