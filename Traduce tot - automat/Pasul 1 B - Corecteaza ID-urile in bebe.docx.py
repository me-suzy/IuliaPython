# -*- coding: utf-8 -*-
"""
Pasul 1.5 - Corectează ID-urile în bebe.docx
Acest script caută fișierele RO corespunzătoare articolelor din bebe.docx
bazat pe titluri și actualizează ID-urile cu cele corecte.
"""

import os
import re
from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from bs4 import BeautifulSoup
import unidecode

def normalize_title(title):
    """Normalizează titlul pentru comparare"""
    normalized = unidecode.unidecode(title.lower())
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def generate_filename_from_title(title):
    """Generează numele fișierului din titlu (similar cu Pasul 2)"""
    normalized = unidecode.unidecode(title.lower())
    normalized = re.sub(r'[^a-z0-9\-]+', '-', normalized)
    normalized = re.sub(r'-+', '-', normalized).strip('-')
    return f"{normalized}.html"

def extract_id_from_html(file_path):
    """Extrage ID-ul din fișierul HTML"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        patterns = [
            r'<!-- \$item_id = (\d+);',
            r'\$item_id = (\d+);'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        print(f"    [WARN] Nu s-a găsit ID în: {os.path.basename(file_path)}")
        return None
    except Exception as e:
        print(f"    [ERR] Eroare la citirea {file_path}: {e}")
        return None

def extract_title_from_html(file_path):
    """Extrage titlul din fișierul HTML"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        title_tag = soup.find('h1', class_='den_articol')
        if title_tag:
            return title_tag.get_text().strip()
        print(f"    [WARN] Nu s-a găsit <h1 class='den_articol'> în: {os.path.basename(file_path)}")
        return None
    except Exception as e:
        print(f"    [ERR] Eroare la citirea titlului din {file_path}: {e}")
        return None

def build_ro_index(ro_dir):
    """Construiește un index al fișierelor RO cu titluri și ID-uri"""
    index = {}
    filename_index = {}

    print(f"\n{'='*60}")
    print(f"INDEXARE fișiere din: {ro_dir}")
    print(f"{'='*60}")

    all_files = [f for f in os.listdir(ro_dir) if f.endswith('.html')]
    total = len(all_files)
    print(f"Total fișiere HTML găsite: {total}")

    skipped_no_title = 0
    skipped_no_id = 0

    for idx, filename in enumerate(all_files, 1):
        if idx % 100 == 0 or idx == total:
            print(f"  Indexare... {idx}/{total} ({idx*100//total}%)")

        file_path = os.path.join(ro_dir, filename)
        title = extract_title_from_html(file_path)
        item_id = extract_id_from_html(file_path)

        if not title:
            skipped_no_title += 1
            continue
        if not item_id:
            skipped_no_id += 1
            continue

        normalized = normalize_title(title)
        index[normalized] = (filename, item_id, title)

        filename_base = os.path.splitext(filename)[0]
        filename_index[filename_base] = (filename, item_id, title)

    print(f"\n--- Rezultat indexare ---")
    print(f"  Indexate cu succes: {len(index)}")
    print(f"  Sărite (fără titlu): {skipped_no_title}")
    print(f"  Sărite (fără ID):    {skipped_no_id}")
    print(f"  Total procesate:     {total}")
    return index, filename_index

def find_matching_ro_file(en_title, ro_index, ro_filename_index):
    """Găsește fișierul RO corespunzător titlului EN"""
    normalized_en = normalize_title(en_title)

    # Metoda 1: potrivire exactă normalizată
    if normalized_en in ro_index:
        print(f"    -> Potrivire EXACTĂ (titlu normalizat)")
        return ro_index[normalized_en]

    # Metoda 2: potrivire după numele fișierului
    expected_filename = generate_filename_from_title(en_title)
    expected_base = os.path.splitext(expected_filename)[0]

    if expected_base in ro_filename_index:
        print(f"    -> Potrivire după FILENAME: {expected_filename}")
        return ro_filename_index[expected_base]

    # Metoda 3: potrivire parțială
    en_words = set(normalized_en.split())
    best_match = None
    best_score = 0

    for norm_title, data in ro_index.items():
        ro_words = set(norm_title.split())
        common = len(en_words & ro_words)
        if common >= 3 and common > best_score:
            best_score = common
            best_match = data

    if best_match:
        print(f"    -> Potrivire PARȚIALĂ (scor: {best_score} cuvinte comune)")
        print(f"       Fișier găsit: {best_match[0]}")
    else:
        print(f"    -> NICIO potrivire găsită!")
        print(f"       Titlu normalizat: '{normalized_en}'")
        print(f"       Filename așteptat: '{expected_base}'")

    return best_match

def correct_ids_in_docx(docx_path, ro_dir, output_path=None):
    """Corectează ID-urile în documentul Word"""
    if output_path is None:
        output_path = docx_path

    ro_index, ro_filename_index = build_ro_index(ro_dir)

    doc = Document(docx_path)
    total_paragraphs = len(doc.paragraphs)

    corrections = []
    already_ok = 0
    not_found = 0
    current_title = None
    current_title_para_idx = None
    titles_found = 0
    id_lines_found = 0

    print(f"\n{'='*60}")
    print(f"PROCESARE document: {docx_path}")
    print(f"Total paragrafe: {total_paragraphs}")
    print(f"{'='*60}\n")

    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()

        if not text:
            continue

        # Detectăm titlul
        if para.alignment == WD_PARAGRAPH_ALIGNMENT.CENTER and not text.startswith("ID:"):
            current_title = text
            current_title_para_idx = i
            titles_found += 1
            print(f"\n[{titles_found}] TITLU: {text[:70]}{'...' if len(text)>70 else ''}")

        # Detectăm linia de ID
        elif text.startswith("ID:") and current_title:
            id_lines_found += 1
            old_id = text.replace("ID:", "").strip()
            print(f"  ID curent: {old_id}")

            match = find_matching_ro_file(current_title, ro_index, ro_filename_index)

            if match:
                filename, correct_id, ro_title = match

                if old_id != correct_id:
                    print(f"  >>> CORECȚIE: {old_id} -> {correct_id}")
                    print(f"      Fișier RO: {filename}")

                    para.clear()
                    run = para.add_run(f"ID: {correct_id}")

                    corrections.append({
                        'title': current_title,
                        'old_id': old_id,
                        'new_id': correct_id,
                        'ro_file': filename
                    })
                else:
                    already_ok += 1
                    print(f"  [OK] ID corect deja: {correct_id}")
            else:
                not_found += 1
                print(f"  [!!!] NU S-A GĂSIT fișier RO pentru acest titlu!")

            current_title = None

    # Salvăm documentul
    print(f"\n{'='*60}")
    print(f"Salvare document: {output_path}")
    doc.save(output_path)
    print(f"Document salvat cu succes!")

    print(f"\n{'='*60}")
    print(f"SUMAR FINAL")
    print(f"{'='*60}")
    print(f"  Titluri detectate:   {titles_found}")
    print(f"  Linii ID procesate:  {id_lines_found}")
    print(f"  ID-uri corecte deja: {already_ok}")
    print(f"  Corecții efectuate:  {len(corrections)}")
    print(f"  Negăsite (fără RO):  {not_found}")
    print(f"{'='*60}")

    return corrections

def main():
    bebe_docx = "bebe.docx"
    ro_dir = r"e:\Carte\BB\17 - Site Leadership\Principal\ro"

    if not os.path.exists(bebe_docx):
        print(f"[EROARE] Fișierul {bebe_docx} nu există!")
        return

    if not os.path.exists(ro_dir):
        print(f"[EROARE] Directorul {ro_dir} nu există!")
        return

    print("=" * 60)
    print("PASUL 1.5 - Corectare ID-uri în bebe.docx")
    print("=" * 60)

    corrections = correct_ids_in_docx(bebe_docx, ro_dir)

    if corrections:
        print(f"\n{'='*60}")
        print("LISTA CORECȚIILOR:")
        print(f"{'='*60}")
        for i, c in enumerate(corrections, 1):
            print(f"  {i:3d}. {c['title'][:45]}{'...' if len(c['title'])>45 else ''}")
            print(f"       {c['old_id']} -> {c['new_id']}  ({c['ro_file']})")

    print(f"\nProcesare completă!")
    print("Acum poți rula Pasul 2 pentru a regenera fișierele HTML cu ID-uri corecte.")

if __name__ == "__main__":
    main()