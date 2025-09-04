import os
import re
from pathlib import Path

ro_directory = r'e:\Carte\BB\17 - Site Leadership\Principal\ro'
en_directory = r'e:\Carte\BB\17 - Site Leadership\Principal\en'

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

def write_file_with_encoding(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Eroare la scrierea fișierului {file_path}: {e}")
        return False

def normalize_value(val):
    if val is None:
        return None
    val = val.replace('\xa0', ' ').strip()
    val = val.replace('–', '-').replace('—', '-')
    return val  # Case-sensitive

def standardize_filename(filename):
    base, ext = os.path.splitext(filename)
    parts = base.split('-')
    roman_numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv']
    if len(parts) > 1 and parts[-1].lower() in roman_numerals:
        parts[-1] = parts[-1].upper()
        new_base = '-'.join(parts)
        return new_base + ext
    return filename

def get_links_from_flags(content, filename, directory):
    flags_section = re.search(r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->', content, re.DOTALL)
    if not flags_section:
        print(f"\nFIȘIER PROBLEMATIC: {os.path.join(directory, filename)} - Nu s-a găsit secțiunea FLAGS")
        return None

    flags_content = flags_section.group(1)

    ro_match = re.search(r'<a href="https://neculaifantanaru\.com/+([^"]+)"[^>]*?><img[^>]*?title="ro"', flags_content)
    en_match = re.search(r'<a href="https://neculaifantanaru\.com/+en/([^"]+)"[^>]*?><img[^>]*?title="en"', flags_content)

    if not ro_match or not en_match:
        print(f"\nFIȘIER PROBLEMATIC: {os.path.join(directory, filename)} - Lipsesc link-urile RO/EN")
        return None

    return {
        'ro_link': normalize_value(ro_match.group(1)),
        'en_link': normalize_value(en_match.group(1))
    }

def fix_flags_links(content, correct_ro_filename, correct_en_filename):
    """Înlocuiește link-urile din FLAGS cu cele corecte"""

    def replace_flags_section(match):
        flags_content = match.group(1)

        # Înlocuiește link-ul RO
        flags_content = re.sub(
            r'(<a href="https://neculaifantanaru\.com/+)[^"]+("[^>]*?><img[^>]*?title="ro")',
            rf'\1{correct_ro_filename}\2',
            flags_content
        )

        # Înlocuiește link-ul EN
        flags_content = re.sub(
            r'(<a href="https://neculaifantanaru\.com/+en/)[^"]+("[^>]*?><img[^>]*?title="en")',
            rf'\1{correct_en_filename}\2',
            flags_content
        )

        return f'<!-- FLAGS_1 -->{flags_content}<!-- FLAGS -->'

    # Aplică înlocuirea
    new_content = re.sub(
        r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->',
        replace_flags_section,
        content,
        flags=re.DOTALL
    )

    return new_content

def compare_and_fix_files():
    issues_found = []
    fixes_applied = 0

    for ro_file in os.listdir(ro_directory):
        if not ro_file.endswith('.html'):
            continue

        print(f"Procesare fișier: {ro_file}", flush=True)

        # Standardize RO filename
        correct_ro_link = standardize_filename(ro_file)
        ro_path = os.path.join(ro_directory, ro_file)
        if correct_ro_link != ro_file:
            new_ro_path = os.path.join(ro_directory, correct_ro_link)
            if not os.path.exists(new_ro_path):
                try:
                    os.rename(ro_path, new_ro_path)
                    print(f"    ✅ Redenumit fișier RO: {ro_file} → {correct_ro_link}")
                    ro_path = new_ro_path
                    ro_file = correct_ro_link
                except Exception as e:
                    print(f"    ❌ Eroare la redenumirea fișierului RO: {e}")
                    continue
            else:
                print(f"    ⚠️ Fișierul RO standardizat deja există: {correct_ro_link}")

        ro_content = read_file_with_fallback_encoding(ro_path)
        if not ro_content:
            continue

        ro_links = get_links_from_flags(ro_content, ro_file, ro_directory)
        if not ro_links:
            continue

        # Find EN file
        expected_en_filename = ro_links['en_link']
        en_file = None
        en_path = None
        en_content = None
        en_links = None
        en_exists = False

        if expected_en_filename:
            standardized_expected = standardize_filename(expected_en_filename)
            en_path = os.path.join(en_directory, standardized_expected)
            if os.path.exists(en_path):
                en_file = standardized_expected
                en_exists = True
            else:
                en_path = os.path.join(en_directory, expected_en_filename)
                if os.path.exists(en_path):
                    en_file = expected_en_filename
                    en_exists = True
                else:
                    # Case-insensitive search
                    en_files = [f for f in os.listdir(en_directory) if f.lower() == expected_en_filename.lower()]
                    if en_files:
                        en_file = en_files[0]
                        en_path = os.path.join(en_directory, en_file)
                        en_exists = True
                        print(f"  ⚠️ Fișierul EN există cu case diferit: {en_file} (așteptat: {expected_en_filename})")

            if en_exists:
                # Standardize EN filename
                correct_en_link = standardize_filename(en_file)
                if correct_en_link != en_file:
                    new_en_path = os.path.join(en_directory, correct_en_link)
                    if not os.path.exists(new_en_path):
                        try:
                            os.rename(en_path, new_en_path)
                            print(f"    ✅ Redenumit fișier EN: {en_file} → {correct_en_link}")
                            en_path = new_en_path
                            en_file = correct_en_link
                        except Exception as e:
                            print(f"    ❌ Eroare la redenumirea fișierului EN: {e}")
                            en_exists = False
                    else:
                        print(f"    ⚠️ Fișierul EN standardizat deja există: {correct_en_link}")
            else:
                correct_en_link = standardize_filename(expected_en_filename)
                print(f"  ⚠️ Fișierul EN nu există: {expected_en_filename}")

        if en_exists:
            en_content = read_file_with_fallback_encoding(en_path)
            if en_content:
                en_links = get_links_from_flags(en_content, en_file, en_directory)

        # Expected links are the standardized ones
        correct_ro_link = standardize_filename(ro_file)  # Already done, but confirm
        correct_en_link = standardize_filename(en_file) if en_file else standardize_filename(expected_en_filename)

        # Debug
        print(f"  🔎 RO file links: RO={ro_links['ro_link']}, EN={ro_links['en_link']}")
        print(f"  🔎 Expected: RO={correct_ro_link}, EN={correct_en_link}")
        if en_links:
            print(f"  🔎 EN file links: RO={en_links['ro_link']}, EN={en_links['en_link']}")

        ro_has_error = False
        en_has_error = False

        if ro_links['ro_link'] != correct_ro_link or ro_links['en_link'] != correct_en_link:
            ro_has_error = True

        if en_links and (en_links['ro_link'] != correct_ro_link or en_links['en_link'] != correct_en_link):
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

            if en_exists:
                # Repară RO
                if ro_has_error:
                    print(f"    → Reparare fișier RO: {ro_file}")
                    if ro_links['ro_link'] != correct_ro_link:
                        print(f"      ✗ Link RO greșit: {ro_links['ro_link']} → {correct_ro_link}")
                    if ro_links['en_link'] != correct_en_link:
                        print(f"      ✗ Link EN greșit: {ro_links['en_link']} → {correct_en_link}")

                    fixed_ro_content = fix_flags_links(ro_content, correct_ro_link, correct_en_link)
                    if write_file_with_encoding(ro_path, fixed_ro_content):
                        fixes_applied += 1
                        print(f"    ✅ Fișierul RO reparat!")
                    else:
                        print(f"    ❌ Nu s-a putut repara fișierul RO.")

                # Repară EN
                if en_has_error:
                    print(f"    → Reparare fișier EN: {en_file}")
                    if en_links['ro_link'] != correct_ro_link:
                        print(f"      ✗ Link RO greșit: {en_links['ro_link']} → {correct_ro_link}")
                    if en_links['en_link'] != correct_en_link:
                        print(f"      ✗ Link EN greșit: {en_links['en_link']} → {correct_en_link}")

                    fixed_en_content = fix_flags_links(en_content, correct_ro_link, correct_en_link)
                    if write_file_with_encoding(en_path, fixed_en_content):
                        fixes_applied += 1
                        print(f"    ✅ Fișierul EN reparat!")
                    else:
                        print(f"    ❌ Nu s-a putut repara fișierul EN.")
            else:
                print(f"    ⚠️ Nu s-a putut modifica, deoarece fișierul nu există.")

            print()

    return issues_found, fixes_applied

# Rulează
print("\nVerificare și reparare link-uri în FLAGS...")
print("=" * 80)

issues_found, fixes_applied = compare_and_fix_files()

if issues_found:
    print(f"\n🔧 REPARARE COMPLETĂ!")
    print("=" * 80)
    print(f"Total fișiere cu probleme găsite: {len(issues_found)}")
    print(f"Total reparări aplicate: {fixes_applied}")
    print("\nDetalii probleme găsite:")

    for i, issue in enumerate(issues_found, 1):
        print(f"\n{i}. Fișierul RO: {issue['ro_file']}")
        print(f"   Fișierul EN: {issue['en_file'] if issue['en_file'] else 'Nu există'}")

        if issue['ro_has_error']:
            print(f"   🔴 GREȘEALĂ în RO")
            if issue['ro_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['ro_links']['ro_link']} → {issue['correct_ro_link']}")
            if issue['ro_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['ro_links']['en_link']} → {issue['correct_en_link']}")
        else:
            print(f"   🟢 RO este corect")

        if issue['en_has_error']:
            print(f"   🔴 GREȘEALĂ în EN")
            if issue['en_links']['ro_link'] != issue['correct_ro_link']:
                print(f"      ✗ Link RO greșit: {issue['en_links']['ro_link']} → {issue['correct_ro_link']}")
            if issue['en_links']['en_link'] != issue['correct_en_link']:
                print(f"      ✗ Link EN greșit: {issue['en_links']['en_link']} → {issue['correct_en_link']}")
        else:
            if issue['en_links']:
                print(f"   🟢 EN este corect")
            else:
                print(f"   ⚠️ EN nu există")

    print("=" * 80)
else:
    print("✅ Nu s-au găsit probleme în fișiere.")

print("\n🔍 Verificare finală completată!")