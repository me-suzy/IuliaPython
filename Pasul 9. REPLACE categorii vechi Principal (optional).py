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
    return None

def write_file_with_encoding(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Eroare: {e}")
        return False

def step1_fix_canonicals():
    """PASUL 1: Canonical = numele fișierului (case exact)"""
    print("PASUL 1: CANONICAL = NUMELE FIȘIERULUI")
    print("="*60)

    fixes = 0

    # RO files
    for filename in os.listdir(ro_directory):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(ro_directory, filename)
        content = read_file_with_fallback_encoding(filepath)
        if not content:
            continue

        # Găsește canonical actual
        canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>', content, re.IGNORECASE)
        if canonical_match:
            current = canonical_match.group(1)
            correct = f"https://neculaifantanaru.com/{filename}"

            if current != correct:
                print(f"RO {filename}: {current} → {correct}")
                new_content = re.sub(
                    r'<link\s+rel="canonical"\s+href="[^"]+"\s*/?>',
                    f'<link rel="canonical" href="{correct}" />',
                    content,
                    flags=re.IGNORECASE
                )
                if write_file_with_encoding(filepath, new_content):
                    fixes += 1

    # EN files
    for filename in os.listdir(en_directory):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(en_directory, filename)
        content = read_file_with_fallback_encoding(filepath)
        if not content:
            continue

        canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>', content, re.IGNORECASE)
        if canonical_match:
            current = canonical_match.group(1)
            correct = f"https://neculaifantanaru.com/en/{filename}"

            if current != correct:
                print(f"EN {filename}: {current} → {correct}")
                new_content = re.sub(
                    r'<link\s+rel="canonical"\s+href="[^"]+"\s*/?>',
                    f'<link rel="canonical" href="{correct}" />',
                    content,
                    flags=re.IGNORECASE
                )
                if write_file_with_encoding(filepath, new_content):
                    fixes += 1

    print(f"✅ Canonical-uri reparate: {fixes}\n")
    return fixes

def step2_fix_flags_match_canonical():
    """PASUL 2: FLAGS din același fișier = canonical din același fișier"""
    print("PASUL 2: FLAGS = CANONICAL (în același fișier)")
    print("="*60)

    fixes = 0

    # RO files
    for filename in os.listdir(ro_directory):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(ro_directory, filename)
        content = read_file_with_fallback_encoding(filepath)
        if not content:
            continue

        # Găsește canonical (care acum e corect din pasul 1)
        canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>', content, re.IGNORECASE)
        if not canonical_match:
            continue

        canonical_url = canonical_match.group(1)
        expected_ro_filename = canonical_url.split('/')[-1]  # extrage filename din URL

        # Verifică link RO din FLAGS
        ro_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*><img[^>]*title="ro"', content)
        if ro_flags_match:
            current_ro_link = ro_flags_match.group(1)

            if current_ro_link != expected_ro_filename:
                print(f"RO FLAGS în {filename}: {current_ro_link} → {expected_ro_filename}")

                # Repară link-ul RO în FLAGS
                new_content = re.sub(
                    r'(<a href="https://neculaifantanaru\.com/)[^"]+("[^>]*><img[^>]*title="ro")',
                    rf'\g<1>{expected_ro_filename}\g<2>',
                    content
                )

                if write_file_with_encoding(filepath, new_content):
                    fixes += 1

    # EN files
    for filename in os.listdir(en_directory):
        if not filename.endswith('.html'):
            continue

        filepath = os.path.join(en_directory, filename)
        content = read_file_with_fallback_encoding(filepath)
        if not content:
            continue

        # Găsește canonical (care acum e corect din pasul 1)
        canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/?>', content, re.IGNORECASE)
        if not canonical_match:
            continue

        canonical_url = canonical_match.group(1)
        expected_en_filename = canonical_url.split('/')[-1]  # extrage filename din URL

        # Verifică link EN din FLAGS
        en_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*><img[^>]*title="en"', content)
        if en_flags_match:
            current_en_link = en_flags_match.group(1)

            if current_en_link != expected_en_filename:
                print(f"EN FLAGS în {filename}: {current_en_link} → {expected_en_filename}")

                # Repară link-ul EN în FLAGS
                new_content = re.sub(
                    r'(<a href="https://neculaifantanaru\.com/en/)[^"]+("[^>]*><img[^>]*title="en")',
                    rf'\g<1>{expected_en_filename}\g<2>',
                    content
                )

                if write_file_with_encoding(filepath, new_content):
                    fixes += 1

    print(f"✅ FLAGS reparate să corespundă cu canonical: {fixes}\n")
    return fixes

def step3_sync_cross_references():
    """PASUL 3: Sincronizează cross-reference-urile RO ↔ EN"""
    print("PASUL 3: SINCRONIZARE CROSS-REFERENCES RO ↔ EN")
    print("="*60)

    fixes = 0

    # Construiește mapa de relații RO ↔ EN din canonical-uri
    ro_to_en_map = {}
    en_to_ro_map = {}

    # Scanează fișierele RO pentru a găsi link-urile EN din FLAGS
    for ro_filename in os.listdir(ro_directory):
        if not ro_filename.endswith('.html'):
            continue

        ro_filepath = os.path.join(ro_directory, ro_filename)
        ro_content = read_file_with_fallback_encoding(ro_filepath)
        if not ro_content:
            continue

        # Găsește link-ul EN din FLAGS
        en_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*><img[^>]*title="en"', ro_content)
        if en_flags_match:
            en_filename = en_flags_match.group(1)
            if en_filename != 'None':
                ro_to_en_map[ro_filename] = en_filename
                en_to_ro_map[en_filename] = ro_filename

    print(f"Găsite {len(ro_to_en_map)} perechi RO-EN")

    # Verifică și repară inconsistențele
    for ro_filename, en_filename in ro_to_en_map.items():
        needs_fix = False

        # Verifică EN file să aibă link-urile corecte în FLAGS
        en_filepath = os.path.join(en_directory, en_filename)
        if os.path.exists(en_filepath):
            en_content = read_file_with_fallback_encoding(en_filepath)
            if en_content:
                # Verifică link RO în EN FLAGS
                ro_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*><img[^>]*title="ro"', en_content)
                en_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*><img[^>]*title="en"', en_content)

                current_ro_link = ro_flags_match.group(1) if ro_flags_match else None
                current_en_link = en_flags_match.group(1) if en_flags_match else None

                if current_ro_link != ro_filename or current_en_link != en_filename:
                    needs_fix = True
                    print(f"EN {en_filename}: RO={current_ro_link}→{ro_filename}, EN={current_en_link}→{en_filename}")

                    # Repară beide link-uri în EN FLAGS
                    new_content = re.sub(
                        r'(<a href="https://neculaifantanaru\.com/)[^"]+("[^>]*><img[^>]*title="ro")',
                        rf'\g<1>{ro_filename}\g<2>',
                        en_content
                    )
                    new_content = re.sub(
                        r'(<a href="https://neculaifantanaru\.com/en/)[^"]+("[^>]*><img[^>]*title="en")',
                        rf'\g<1>{en_filename}\g<2>',
                        new_content
                    )

                    if write_file_with_encoding(en_filepath, new_content):
                        fixes += 1

        # Verifică RO file să aibă link-urile corecte în FLAGS
        ro_filepath = os.path.join(ro_directory, ro_filename)
        ro_content = read_file_with_fallback_encoding(ro_filepath)
        if ro_content:
            ro_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*><img[^>]*title="ro"', ro_content)
            en_flags_match = re.search(r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*><img[^>]*title="en"', ro_content)

            current_ro_link = ro_flags_match.group(1) if ro_flags_match else None
            current_en_link = en_flags_match.group(1) if en_flags_match else None

            if current_ro_link != ro_filename or current_en_link != en_filename:
                needs_fix = True
                print(f"RO {ro_filename}: RO={current_ro_link}→{ro_filename}, EN={current_en_link}→{en_filename}")

                # Repară beide link-uri în RO FLAGS
                new_content = re.sub(
                    r'(<a href="https://neculaifantanaru\.com/)[^"]+("[^>]*><img[^>]*title="ro")',
                    rf'\g<1>{ro_filename}\g<2>',
                    ro_content
                )
                new_content = re.sub(
                    r'(<a href="https://neculaifantanaru\.com/en/)[^"]+("[^>]*><img[^>]*title="en")',
                    rf'\g<1>{en_filename}\g<2>',
                    new_content
                )

                if write_file_with_encoding(ro_filepath, new_content):
                    fixes += 1

    print(f"✅ Cross-references reparate: {fixes}\n")
    return fixes

def main():
    print("REPARARE COMPLETĂ ÎN 3 PAȘI")
    print("="*80)

    # Pasul 1: Canonical = numele fișierului
    canonical_fixes = step1_fix_canonicals()

    # Pasul 2: FLAGS = canonical (în același fișier)
    flags_canonical_fixes = step2_fix_flags_match_canonical()

    # Pasul 3: Sincronizează cross-references
    cross_ref_fixes = step3_sync_cross_references()

    print("="*80)
    print("REZULTATE FINALE")
    print("="*80)
    print(f"Pasul 1 - Canonical-uri reparate: {canonical_fixes}")
    print(f"Pasul 2 - FLAGS → canonical: {flags_canonical_fixes}")
    print(f"Pasul 3 - Cross-references: {cross_ref_fixes}")
    print(f"🎉 TOTAL: {canonical_fixes + flags_canonical_fixes + cross_ref_fixes}")

if __name__ == "__main__":
    main()