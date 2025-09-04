import os
import re
from collections import defaultdict

# Define directories
base_dir = r'e:\Carte\BB\17 - Site Leadership\Principal 2022'
ro_dir = os.path.join(base_dir, 'ro')
en_dir = os.path.join(base_dir, 'en')

# Function to extract canonical from HTML content
def extract_canonical(content):
    match = re.search(r'<link rel="canonical" href="https://neculaifantanaru\.com/(en/)?([^"]+)\.html" />', content)
    if match:
        return (match.group(1) or '') + match.group(2) + '.html'
    return None

# Function to extract flags section
def extract_flags(content):
    flags_start = content.find('<!-- FLAGS_1 -->')
    flags_end = content.find('<!-- FLAGS -->', flags_start)
    if flags_start != -1 and flags_end != -1:
        return content[flags_start:flags_end + len('<!-- FLAGS -->')]
    return None

# Function to replace canonical in content
def replace_canonical(content, new_href):
    return re.sub(r'<link rel="canonical" href="[^"]+" />', f'<link rel="canonical" href="{new_href}" />', content)

# Function to replace specific flag link in flags (case-sensitive)
def replace_flag_link(flags, code, new_href):
    pattern = rf'<li><a cunt_code="{code}" href="[^"]+">'
    replacement = f'<li><a cunt_code="{code}" href="{new_href}">'
    return re.sub(pattern, replacement, flags, count=1)

# Function to update file
def update_file(file_path, new_content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

# PASUL 1: Canonical = Numele fișierului
print('================================================================================')
print('PASUL 1: CANONICAL = NUMELE FIȘIERULUI')
print('============================================================')

canonical_fixed_ro = 0
canonical_fixed_en = 0

# Process RO files
ro_files = [f for f in os.listdir(ro_dir) if f.endswith('.html')]
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    expected_canonical = filename[:-5]  # without .html, case-sensitive
    expected_href = f'https://neculaifantanaru.com/{expected_canonical}.html'
    if canonical != expected_canonical:
        new_content = replace_canonical(content, expected_href)
        update_file(file_path, new_content)
        canonical_fixed_ro += 1
        print(f'Corectat RO: {filename} canonical → {expected_canonical}.html')

# Process EN files
en_files = [f for f in os.listdir(en_dir) if f.endswith('.html')]
for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    expected_canonical = f'en/{filename[:-5]}'  # en/ + name without .html
    expected_href = f'https://neculaifantanaru.com/{expected_canonical}.html'
    if canonical != expected_canonical:
        new_content = replace_canonical(content, expected_href)
        update_file(file_path, new_content)
        canonical_fixed_en += 1
        print(f'Corectat EN: {filename} canonical → {expected_canonical}.html')

print(f'✅ Canonical-uri reparate: RO={canonical_fixed_ro}, EN={canonical_fixed_en}, TOTAL={canonical_fixed_ro + canonical_fixed_en}')

# PASUL 2: FLAGS = Canonical (în același fișier)
print('\nPASUL 2: FLAGS = CANONICAL (în același fișier)')
print('============================================================')

flags_fixed_ro = 0
flags_fixed_en = 0

# Process RO files for own flag (+40)
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    flags = extract_flags(content)
    if flags and canonical:
        match = re.search(r'<li><a cunt_code="\+40" href="([^"]+)"', flags)
        expected_href = f'https://neculaifantanaru.com/{canonical[:-5]}.html'
        if match and match.group(1) != expected_href:
            new_flags = replace_flag_link(flags, r'\+40', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            flags_fixed_ro += 1
            print(f'Corectat RO flags own: {filename} → {expected_href}')

# Process EN files for own flag (+1)
for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    canonical = extract_canonical(content)
    flags = extract_flags(content)
    if flags and canonical:
        match = re.search(r'<li><a cunt_code="\+1" href="([^"]+)"', flags)
        expected_href = f'https://neculaifantanaru.com/{canonical}.html'
        if match and match.group(1) != expected_href:
            new_flags = replace_flag_link(flags, r'\+1', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            flags_fixed_en += 1
            print(f'Corectat EN flags own: {filename} → {expected_href}')

print(f'✅ FLAGS reparate: RO={flags_fixed_ro}, EN={flags_fixed_en}, TOTAL={flags_fixed_ro + flags_fixed_en}')

# PASUL 3: SINCRONIZARE CROSS-REFERENCES RO ↔ EN
print('\nPASUL 3: SINCRONIZARE CROSS-REFERENCES RO ↔ EN')
print('============================================================')

# Build mappings (bidirectional, avoid conflicts)
ro_to_en_map = {}
en_to_ro_map = {}
ro_files_set = set(ro_files)
en_files_set = set(en_files)

# First, try to match based on existing flags
for filename in ro_files:
    file_path = os.path.join(ro_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        match = re.search(r'<li><a cunt_code="\+1" href="https://neculaifantanaru\.com/en/([^"]+)\.html"', flags)
        if match:
            en_name = match.group(1) + '.html'
            if en_name in en_files_set and filename not in ro_to_en_map:
                ro_to_en_map[filename] = en_name
                if en_name not in en_to_ro_map:
                    en_to_ro_map[en_name] = filename

for filename in en_files:
    file_path = os.path.join(en_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        match = re.search(r'<li><a cunt_code="\+40" href="https://neculaifantanaru\.com/([^"]+)\.html"', flags)
        if match:
            ro_name = match.group(1) + '.html'
            if ro_name in ro_files_set and ro_name not in ro_to_en_map:
                ro_to_en_map[ro_name] = filename
                if filename not in en_to_ro_map:
                    en_to_ro_map[filename] = ro_name

# Fallback: Match by filename similarity (case-insensitive for fallback only)
for ro_filename in ro_files:
    if ro_filename not in ro_to_en_map:
        ro_base = ro_filename[:-5].lower()
        for en_filename in en_files:
            en_base = en_filename[:-5].lower()
            if ro_base == en_base or ro_base.replace('-', ' ') == en_base.replace('-', ' '):
                if en_filename not in en_to_ro_map:
                    ro_to_en_map[ro_filename] = en_filename
                    en_to_ro_map[en_filename] = ro_filename
                    break

print(f'Găsite {len(ro_to_en_map)} perechi RO→EN și {len(en_to_ro_map)} perechi EN→RO')

# Correct cross-references
cross_fixed = 0

# Correct RO files: set +1 to mapped EN
for ro_filename, en_filename in ro_to_en_map.items():
    file_path = os.path.join(ro_dir, ro_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        match = re.search(r'<li><a cunt_code="\+1" href="([^"]+)"', flags)
        expected_href = f'https://neculaifantanaru.com/en/{en_filename[:-5]}.html'
        if match and match.group(1) != expected_href:
            new_flags = replace_flag_link(flags, r'\+1', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            cross_fixed += 1
            print(f'Corectat RO {ro_filename}: EN link → {en_filename}')

# Correct EN files: set +40 to mapped RO
for en_filename, ro_filename in en_to_ro_map.items():
    file_path = os.path.join(en_dir, en_filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    flags = extract_flags(content)
    if flags:
        match = re.search(r'<li><a cunt_code="\+40" href="([^"]+)"', flags)
        expected_href = f'https://neculaifantanaru.com/{ro_filename[:-5]}.html'
        if match and match.group(1) != expected_href:
            new_flags = replace_flag_link(flags, r'\+40', expected_href)
            new_content = content.replace(flags, new_flags)
            update_file(file_path, new_content)
            cross_fixed += 1
            print(f'Corectat EN {en_filename}: RO link → {ro_filename}')

print(f'✅ Cross-references reparate: {cross_fixed}')

# Final results
print('================================================================================')
print('REZULTATE FINALE')
print('================================================================================')
print(f'Pasul 1 - Canonical-uri reparate: {canonical_fixed_ro + canonical_fixed_en}')
print(f'Pasul 2 - FLAGS → canonical: {flags_fixed_ro + flags_fixed_en}')
print(f'Pasul 3 - Cross-references: {cross_fixed}')
print(f'🎉 TOTAL: {canonical_fixed_ro + canonical_fixed_en + flags_fixed_ro + flags_fixed_en + cross_fixed}')