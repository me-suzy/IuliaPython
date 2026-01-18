import os
import re
from pathlib import Path

def extract_item_id(file_content):
    """Extrage ID-ul articolului din comentariul HTML."""
    patterns = [
        r'<!-- \$item_id = (\d+); // .*? -->',
        r'<!-- item_id = (\d+); -->',
        r'<!-- id: (\d+) -->'
    ]

    for pattern in patterns:
        match = re.search(pattern, file_content)
        if match:
            return match.group(1)
    return None

def extract_flags_section(file_content):
    """Extrage secțiunea FLAGS din conținutul fișierului."""
    pattern = r'<!-- FLAGS_1 -->(.*?)<!-- FLAGS -->'
    match = re.search(pattern, file_content, re.DOTALL)
    if match:
        return match.group(0), match.group(1)
    return None, None

def extract_language_link(flags_content, language):
    """Extrage link-ul specific unei limbi din secțiunea FLAGS."""
    # Pattern-uri multiple pentru a face față diferitelor formate
    patterns = []

    if language == 'ro':
        patterns = [
            r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*?><img[^>]*?title="ro"[^>]*?></a>',
            r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*?title="ro"[^>]*?><img[^>]*?></a>',
            r'<a href="https://neculaifantanaru\.com/([^"]+)"[^>]*?><img[^>]*?alt="ro"[^>]*?></a>'
        ]
    elif language == 'en':
        patterns = [
            r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*?><img[^>]*?title="en"[^>]*?></a>',
            r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*?title="en"[^>]*?><img[^>]*?></a>',
            r'<a href="https://neculaifantanaru\.com/en/([^"]+)"[^>]*?><img[^>]*?alt="en"[^>]*?></a>'
        ]

    # Încercăm toate pattern-urile
    for pattern in patterns:
        matches = re.finditer(pattern, flags_content)
        for match in matches:
            # Găsim întreaga secțiune <a>...</a>
            start_idx = match.start()
            end_text = flags_content[start_idx:]
            tag_end = end_text.find('</a>')
            if tag_end != -1:
                end_idx = start_idx + tag_end + 4
                return flags_content[start_idx:end_idx]

    # Căutare avansată pentru cazuri speciale
    # Această abordare caută tag-uri <a> care conțin atât URL-ul corect cât și text/imagini specifice limbii
    if language == 'ro':
        match = re.search(r'<a [^>]*?href="https://neculaifantanaru\.com/[^"]*?"[^>]*?>.*?flag_lang_ro\.jpg.*?</a>', flags_content, re.DOTALL)
        if match:
            return match.group(0)
    elif language == 'en':
        match = re.search(r'<a [^>]*?href="https://neculaifantanaru\.com/en/[^"]*?"[^>]*?>.*?flag_lang_en\.jpg.*?</a>', flags_content, re.DOTALL)
        if match:
            return match.group(0)

    return None

def extract_filename_from_url(url_tag, language):
    """Extrage numele fișierului din tag-ul URL."""
    if language == 'ro':
        pattern = r'href="https://neculaifantanaru\.com/([^"]+)"'
    else:  # 'en'
        pattern = r'href="https://neculaifantanaru\.com/en/([^"]+)"'

    match = re.search(pattern, url_tag)
    if match:
        return match.group(1)
    return None

def is_special_term(ro_filename, en_filename):
    """
    Determină dacă perechea de URL-uri conține un termen special/străin care ar trebui păstrat.
    """
    # Elimină extensia .html
    ro_base = os.path.splitext(ro_filename)[0]
    en_base = os.path.splitext(en_filename)[0]

    # Caz 1: URL-uri identice - clar un termen special
    if ro_base == en_base:
        return True

    # Caz 2: Termeni foarte scurți (un singur cuvânt) - posibil termen special
    ro_parts = ro_base.split('-')
    en_parts = en_base.split('-')

    # Lista de cuvinte de legătură - doar acestea sunt codificate explicit
    stop_words = ['a', 'an', 'the', 'and', 'or', 'but', 'if', 'when', 'while', 'as',
                  'in', 'on', 'at', 'of', 'to', 'for', 'with', 'by', 'about', 'against',
                  'before', 'after', 'during', 'without', 'through', 'throughout', 'within',
                  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'am',
                  's', 'd', 't', 'll', 've', 're', 'm',
                  'si', 'sau', 'dar', 'daca', 'cand', 'ca', 'pe', 'la', 'de', 'cu', 'prin',
                  'pentru', 'fara', 'despre', 'inainte', 'dupa', 'in', 'din', 'spre',
                  'este', 'sunt', 'era', 'fi', 'fost', 'fiind', 'e']

    # Filtrăm cuvintele de legătură pentru a obține cuvintele de conținut
    ro_content = [w for w in ro_parts if w.lower() not in stop_words and len(w) > 2]
    en_content = [w for w in en_parts if w.lower() not in stop_words and len(w) > 2]

    # Cazul URL-urilor scurte, cu un singur cuvânt
    if len(ro_parts) == 1 and len(ro_parts[0]) < 10 and ro_parts[0].lower() not in stop_words:
        return True

    if len(en_parts) == 1 and len(en_parts[0]) < 10 and en_parts[0].lower() not in stop_words:
        return True

    # Caz special pentru hikmah/wisdom - ambele sunt scurte dar complet diferite
    # Dacă ambele URL-uri sunt simple și scurte (un singur cuvânt sau două), verificăm caracteristicile lor
    if len(ro_parts) <= 2 and len(en_parts) <= 2:
        # Detectăm caracteristici de termen străin în oricare dintre termeni
        for word in ro_parts + en_parts:
            # Verifică pentru caracteristici neobișnuite (litere rare în cuvinte europene standard)
            if ('k' in word.lower() and 'h' in word.lower()) or 'q' in word.lower() or word.lower().startswith('x'):
                return True

            # Verifică pentru modele de consoane specifice limbilor străine
            consonant_groups = ['kh', 'hk', 'mk', 'km', 'tz', 'zk', 'gh']
            if any(group in word.lower() for group in consonant_groups):
                return True

    # Caz 3: Verifică pentru termeni comuni dar cu terminații diferite (initium/initiation)
    # Extrage rădăcinile cuvintelor (primele 4 litere pentru cuvinte de minim 6 litere)
    ro_stems = [word[:4] for word in ro_parts if len(word) >= 6 and word.lower() not in stop_words]
    en_stems = [word[:4] for word in en_parts if len(word) >= 6 and word.lower() not in stop_words]

    common_stems = set(ro_stems) & set(en_stems)

    # Dacă avem o rădăcină comună dar URL-urile sunt diferite structural, probabil e un termen special
    if common_stems and abs(len(ro_parts) - len(en_parts)) > 3:
        # Verifică dacă rădăcina comună pare a fi un termen neobișnuit/străin
        for stem in common_stems:
            # Rădăcini care par latine, grecești sau străine (verifică terminații neobișnuite)
            matching_ro_words = [w for w in ro_parts if w.startswith(stem)]
            matching_en_words = [w for w in en_parts if w.startswith(stem)]

            for word in matching_ro_words + matching_en_words:
                # Verifică dacă cuvântul are caracteristici de termen străin
                if (word.endswith('um') or word.endswith('us') or word.endswith('is') or
                    word.endswith('ae') or word.endswith('os') or
                    ('k' in word and 'w' not in word)):  # Caracteristici neobișnuite pentru cuvinte românești
                    return True

    # Caz 4: Cazul special pentru URL-uri foarte diferite ca structură dar cu conținut similar
    # Filtrăm pentru cazuri precum "memoria-harenae" vs "harena-s-memory"

    # Diferență extremă în numărul de cuvinte de conținut
    if (len(ro_content) == 1 and len(en_content) >= 4) or (len(en_content) == 1 and len(ro_content) >= 4):
        return True

    # Prevenim cazul cu ID 346 care este o traducere normală dar cu structură diferită
    # Pentru o traducere normală, chiar dacă structura e diferită, numărul de cuvinte semnificative
    # nu ar trebui să difere prea mult
    if abs(len(ro_content) - len(en_content)) <= 2:
        return False

    # Cazul implicit - nu este un termen special
    return False

def update_flags_section(file_content, ro_link, en_link, special_term=False):
    """Actualizează secțiunea FLAGS cu noile link-uri."""
    # Extragem secțiunea FLAGS
    flags_section, flags_content = extract_flags_section(file_content)
    if not flags_section or not flags_content:
        return file_content, False

    # Facem o copie a conținutului original pentru a verifica dacă au fost făcute modificări
    original_flags_content = flags_content
    updated_flags_content = flags_content

    # Actualizăm link-ul RO, dacă este furnizat
    if ro_link:
        # ro_link poate fi fie un URL complet (string), fie un tag HTML complet
        # Extragem URL-ul - dacă e tag HTML, îl extragem; altfel îl folosim direct
        if ro_link.startswith('<a '):
            # Este un tag HTML - extragem URL-ul
            url_match = re.search(r'href="([^"]+)"', ro_link)
            if url_match:
                new_url = url_match.group(1)
            else:
                new_url = None
        elif ro_link.startswith('https://'):
            # Este deja un URL complet
            new_url = ro_link
        else:
            # Presupunem că e nume fișier și construim URL-ul
            new_url = f'https://neculaifantanaru.com/{ro_link}'
        
        if new_url:
            # Pattern simplu: găsim href-ul RO și îl înlocuim direct
            # Folosim regex pentru a găsi și înlocui doar href-ul, nu întregul tag
            pattern = r'(<a [^>]*?href=")https://neculaifantanaru\.com/[^"]*?("[^>]*?><img[^>]*?flag_lang_ro\.jpg[^>]*?></a>)'
            
            # DEBUG: Verificăm dacă pattern-ul se potrivește
            match = re.search(pattern, updated_flags_content, re.DOTALL)
            if match:
                old_href = match.group(0)
                # Extragem URL-ul vechi pentru comparație
                old_url_match = re.search(r'href="(https://neculaifantanaru\.com/[^"]+)"', old_href)
                old_url = old_url_match.group(1) if old_url_match else None
                
                print(f"    [DEBUG] Pattern găsit!")
                print(f"    [DEBUG] Old URL: {old_url}")
                print(f"    [DEBUG] New URL: {new_url}")
                
                # Verificăm dacă URL-urile sunt diferite
                if old_url and old_url == new_url:
                    print(f"    [DEBUG] URL-urile sunt identice - nu e nevoie de înlocuire")
                else:
                    replacement = r'\1' + new_url + r'\2'
                    updated_flags_content = re.sub(pattern, replacement, updated_flags_content, count=1)
                    print(f"    [DEBUG] Înlocuire efectuată - URL-urile erau diferite")
            else:
                print(f"    [DEBUG] Pattern NU s-a potrivit! Căutăm alte variante...")
                # Încercăm o variantă mai simplă - doar href-ul
                simple_pattern = r'(href=")https://neculaifantanaru\.com/[^"]*?("[^>]*?><img[^>]*?flag_lang_ro\.jpg)'
                simple_match = re.search(simple_pattern, updated_flags_content, re.DOTALL)
                if simple_match:
                    old_simple = simple_match.group(0)
                    old_url_match = re.search(r'href="(https://neculaifantanaru\.com/[^"]+)"', old_simple)
                    old_url = old_url_match.group(1) if old_url_match else None
                    
                    print(f"    [DEBUG] Pattern simplu găsit!")
                    print(f"    [DEBUG] Old URL: {old_url}")
                    print(f"    [DEBUG] New URL: {new_url}")
                    
                    if old_url and old_url == new_url:
                        print(f"    [DEBUG] URL-urile sunt identice - nu e nevoie de înlocuire")
                    else:
                        replacement = r'\1' + new_url + r'\2'
                        updated_flags_content = re.sub(simple_pattern, replacement, updated_flags_content, count=1)
                        print(f"    [DEBUG] Înlocuire efectuată cu pattern simplu")
                else:
                    print(f"    [DEBUG] NICIUN pattern nu s-a potrivit pentru RO link!")

    # Actualizăm link-ul EN, dacă este furnizat și nu este un termen special
    if en_link and not special_term:
        # Pattern-uri multiple pentru link-ul EN
        en_patterns = [
            r'<a [^>]*?href="https://neculaifantanaru\.com/en/[^"]*?"[^>]*?>.*?flag_lang_en\.jpg.*?</a>',
            r'<a [^>]*?title="en"[^>]*?href="https://neculaifantanaru\.com/en/[^"]*?"[^>]*?>.*?</a>',
            r'<a [^>]*?href="https://neculaifantanaru\.com/en/[^"]*?"[^>]*?title="en"[^>]*?>.*?</a>'
        ]

        for pattern in en_patterns:
            match = re.search(pattern, updated_flags_content, re.DOTALL)
            if match:
                updated_flags_content = updated_flags_content.replace(match.group(0), en_link)
                break

    # Verificăm dacă s-au făcut modificări
    if original_flags_content == updated_flags_content:
        return file_content, False

    # Reconstruim secțiunea FLAGS
    updated_flags_section = f'<!-- FLAGS_1 -->{updated_flags_content}<!-- FLAGS -->'

    # Înlocuim secțiunea veche cu cea nouă
    return file_content.replace(flags_section, updated_flags_section), True

def process_files(ro_dir, output_dir):
    """Procesează toate fișierele și face schimbul de flags."""
    # Dicționare pentru a asocia ID-urile cu fișierele
    ro_files = {}
    output_files = {}
    special_terms = []

    # Indexăm fișierele RO după ID - stocăm lista de fișiere pentru fiecare ID
    print("\nIndexare fișiere RO...")
    ro_file_count = 0
    for filename in os.listdir(ro_dir):
        if not filename.endswith('.html'):
            continue

        ro_file_count += 1
        # Afișăm numele fișierului în timp real
        print(f"  Indexare RO #{ro_file_count}: {filename}")

        file_path = os.path.join(ro_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                item_id = extract_item_id(content)
                if item_id:
                    ro_file_data = {
                        'path': file_path,
                        'filename': filename,
                        'content': content
                    }
                    # Stocăm lista de fișiere pentru fiecare ID (pentru cazurile cu ID duplicat)
                    if item_id not in ro_files:
                        ro_files[item_id] = []
                    ro_files[item_id].append(ro_file_data)
                    print(f"    - ID găsit: {item_id}")
                else:
                    print(f"    - Niciun ID găsit")
        except Exception as e:
            print(f"    - Eroare la citirea fișierului: {e}")

    print(f"Total: {ro_file_count} fișiere RO verificate, {len(ro_files)} ID-uri unice.\n")

    # Indexăm fișierele OUTPUT după ID
    print(f"Indexare fișiere OUTPUT din {output_dir}...")
    output_file_count = 0
    for filename in os.listdir(output_dir):
        if not filename.endswith('.html'):
            continue

        output_file_count += 1
        # Afișăm numele fișierului în timp real
        print(f"  Indexare OUTPUT #{output_file_count}: {filename}")

        file_path = os.path.join(output_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                item_id = extract_item_id(content)
                if item_id:
                    output_files[item_id] = {
                        'path': file_path,
                        'filename': filename,
                        'content': content
                    }
                    print(f"    - ID găsit: {item_id}")
                else:
                    print(f"    - Niciun ID găsit")
        except Exception as e:
            print(f"    - Eroare la citirea fișierului: {e}")

    print(f"Total: {output_file_count} fișiere OUTPUT verificate, {len(output_files)} cu ID-uri valide.\n")
    print(f"Rezumat: {len(ro_files)} fișiere RO și {len(output_files)} fișiere OUTPUT cu ID-uri.")

    # Găsim perechile de fișiere și facem schimbul de flags
    print("\nProcesare perechi de fișiere...\n")
    processed_pairs = 0
    failed_pairs = 0

    # Adăugat: afișare număr de perechi
    common_ids = set(ro_files.keys()) & set(output_files.keys())
    print(f"S-au găsit {len(common_ids)} perechi de fișiere cu același ID.")

    # Procesăm fiecare fișier OUTPUT
    for item_id, output_file in output_files.items():
        output_filename_base = os.path.splitext(output_file['filename'])[0]
        
        ro_file = None
        
        print(f"  [DEBUG] Căutăm fișier RO pentru OUTPUT: {output_filename_base} (ID: {item_id})")
        
        # Extragem link-ul RO din OUTPUT pentru verificare (necesar pentru toate metodele)
        output_flags_section_temp, output_flags_content_temp = extract_flags_section(output_file['content'])
        ro_link_in_output = None
        ro_filename_in_output = None
        if output_flags_content_temp:
            ro_link_in_output = extract_language_link(output_flags_content_temp, 'ro')
            if ro_link_in_output:
                ro_filename_in_output = extract_filename_from_url(ro_link_in_output, 'ro')
        
        # METODA PRINCIPALĂ: Folosim ID-ul pentru a găsi fișierul RO corect
        # Aceasta este metoda cea mai sigură, pentru că ID-urile ar trebui să fie sincronizate
        if item_id in ro_files and len(ro_files[item_id]) > 0:
            ro_file = ro_files[item_id][0]
            print(f"  [DEBUG] GĂSIT: Fișier RO prin ID: {ro_file['filename']} (ID: {item_id})")
        
        # METODA SECUNDARĂ: Dacă nu am găsit prin ID, căutăm printre TOATE fișierele RO unul care are link-ul EN către numele fișierului OUTPUT
        # Chiar dacă majoritatea link-urilor EN sunt greșite, unele pot fi corecte
        # IMPORTANT: Verificăm și dacă link-ul RO din fișierul RO găsit se potrivește cu numele fișierului RO
        # pentru a evita potrivirile false cauzate de link-uri EN greșite
        if not ro_file:
            ro_file_found_by_en_link = False
            for id_key, all_ro_files in ro_files.items():
                for candidate_ro_file in all_ro_files:
                    candidate_flags_section, candidate_flags_content = extract_flags_section(candidate_ro_file['content'])
                if candidate_flags_content:
                    candidate_en_link = extract_language_link(candidate_flags_content, 'en')
                    if candidate_en_link:
                        candidate_en_filename = extract_filename_from_url(candidate_en_link, 'en')
                        if candidate_en_filename:
                            candidate_en_filename_base = os.path.splitext(candidate_en_filename)[0]
                            if candidate_en_filename_base == output_filename_base:
                                # Găsit un fișier RO cu link-ul EN către OUTPUT
                                # Verificăm dacă link-ul RO din acest fișier RO se potrivește cu link-ul RO din OUTPUT
                                candidate_ro_link = extract_language_link(candidate_flags_content, 'ro')
                                if candidate_ro_link:
                                    candidate_ro_filename = extract_filename_from_url(candidate_ro_link, 'ro')
                                    if candidate_ro_filename and ro_filename_in_output:
                                        candidate_ro_filename_base = os.path.splitext(candidate_ro_filename)[0]
                                        ro_filename_in_output_base = os.path.splitext(ro_filename_in_output)[0]
                                        if candidate_ro_filename_base == ro_filename_in_output_base:
                                            # Link-ul RO se potrivește - acesta este fișierul RO corect!
                                            ro_file = candidate_ro_file
                                            ro_file_found_by_en_link = True
                                            print(f"  [DEBUG] GĂSIT: Fișier RO prin potrivire link EN + verificare link RO: {ro_file['filename']} (ID: {id_key})")
                                            break
                                        else:
                                            # Link-ul RO nu se potrivește - continuăm căutarea
                                            print(f"  [DEBUG] Fișier RO găsit prin link EN dar link-ul RO nu se potrivește: {candidate_ro_file['filename']} (link RO: {candidate_ro_filename_base}, link RO din OUTPUT: {ro_filename_in_output_base})")
                                            continue
                                    else:
                                        # Nu avem link RO pentru verificare - folosim acest fișier RO
                                        ro_file = candidate_ro_file
                                        ro_file_found_by_en_link = True
                                        print(f"  [DEBUG] GĂSIT: Fișier RO prin potrivire link EN (fără verificare link RO): {ro_file['filename']} (ID: {id_key})")
                                        break
                                else:
                                    # Nu avem link RO în fișierul RO - folosim acest fișier RO
                                    ro_file = candidate_ro_file
                                    ro_file_found_by_en_link = True
                                    print(f"  [DEBUG] GĂSIT: Fișier RO prin potrivire link EN (fără link RO în fișier): {ro_file['filename']} (ID: {id_key})")
                                    break
                if ro_file_found_by_en_link:
                    break
            if ro_file_found_by_en_link:
                break
        
        # METODA SUPLIMENTARĂ 1: Folosim link-ul RO din OUTPUT pentru a găsi fișierul RO corect
        # (chiar dacă link-ul RO din OUTPUT poate fi greșit, uneori poate fi corect)
        if not ro_file and ro_filename_in_output:
            ro_filename_in_output_base = os.path.splitext(ro_filename_in_output)[0]
            print(f"  [DEBUG] Căutăm fișier RO prin link-ul RO din OUTPUT: {ro_filename_in_output_base}")
            
            for id_key, all_ro_files in ro_files.items():
                for candidate_ro_file in all_ro_files:
                    candidate_filename_base = os.path.splitext(candidate_ro_file['filename'])[0]
                    if candidate_filename_base == ro_filename_in_output_base:
                        # Găsit un fișier RO cu numele care se potrivește cu link-ul RO din OUTPUT
                        # Verificăm dacă link-ul EN din acest fișier RO se potrivește cu numele fișierului OUTPUT
                        candidate_flags_section, candidate_flags_content = extract_flags_section(candidate_ro_file['content'])
                        if candidate_flags_content:
                            candidate_en_link = extract_language_link(candidate_flags_content, 'en')
                            if candidate_en_link:
                                candidate_en_filename = extract_filename_from_url(candidate_en_link, 'en')
                                if candidate_en_filename:
                                    candidate_en_filename_base = os.path.splitext(candidate_en_filename)[0]
                                    if candidate_en_filename_base == output_filename_base:
                                        # Link-ul EN se potrivește - acesta este fișierul RO corect!
                                        ro_file = candidate_ro_file
                                        print(f"  [DEBUG] GĂSIT: Fișier RO prin link RO din OUTPUT + verificare link EN: {ro_file['filename']} (ID: {id_key})")
                                        break
                        if ro_file:
                            break
                if ro_file:
                    break
        
        # METODA SUPLIMENTARĂ 2: Dacă nu am găsit prin link-ul EN cu verificare link RO,
        # colectăm toate fișierele RO care au link-ul EN către OUTPUT și le sortăm
        # după cât de bine se potrivesc (dacă link-ul RO din fișierul RO se potrivește cu numele fișierului RO)
        if not ro_file:
            candidates = []
            for id_key, all_ro_files in ro_files.items():
                for candidate_ro_file in all_ro_files:
                    candidate_flags_section, candidate_flags_content = extract_flags_section(candidate_ro_file['content'])
                    if candidate_flags_content:
                        candidate_en_link = extract_language_link(candidate_flags_content, 'en')
                        if candidate_en_link:
                            candidate_en_filename = extract_filename_from_url(candidate_en_link, 'en')
                            if candidate_en_filename:
                                candidate_en_filename_base = os.path.splitext(candidate_en_filename)[0]
                                if candidate_en_filename_base == output_filename_base:
                                    # Verificăm dacă link-ul RO din fișierul RO se potrivește cu numele fișierului RO
                                    candidate_ro_link = extract_language_link(candidate_flags_content, 'ro')
                                    candidate_ro_filename = None
                                    if candidate_ro_link:
                                        candidate_ro_filename = extract_filename_from_url(candidate_ro_link, 'ro')
                                    
                                    candidate_filename_base = os.path.splitext(candidate_ro_file['filename'])[0]
                                    score = 0
                                    if candidate_ro_filename:
                                        candidate_ro_filename_base = os.path.splitext(candidate_ro_filename)[0]
                                        # Dacă link-ul RO se potrivește cu numele fișierului RO, este mai probabil să fie corect
                                        if candidate_ro_filename_base == candidate_filename_base:
                                            score = 2
                                        elif ro_filename_in_output and os.path.splitext(ro_filename_in_output)[0] == candidate_ro_filename_base:
                                            score = 1
                                    
                                    candidates.append({
                                        'file': candidate_ro_file,
                                        'id': id_key,
                                        'score': score,
                                        'ro_filename': candidate_ro_filename
                                    })
            
            # Sortăm candidații după scor (cel mai mare scor este cel mai bun)
            if candidates:
                candidates.sort(key=lambda x: x['score'], reverse=True)
                ro_file = candidates[0]['file']
                print(f"  [DEBUG] GĂSIT: Fișier RO prin sortare candidați: {ro_file['filename']} (ID: {candidates[0]['id']}, scor: {candidates[0]['score']})")
        
        # FALLBACK FINAL: Dacă tot nu am găsit, eroare
        if not ro_file:
            print(f"  - EȘEC: Nu s-a găsit niciun fișier RO pentru OUTPUT {output_file['filename']}")
            failed_pairs += 1
            continue
        
        # Procesăm perechea găsită
        print(f"Procesare pereche ID {item_id}:")
        print(f"  - RO: {ro_file['filename']}")
        print(f"  - EN: {output_file['filename']}")

        # Extragem secțiunile FLAGS
        ro_flags_section, ro_flags_content = extract_flags_section(ro_file['content'])
        output_flags_section, output_flags_content = extract_flags_section(output_file['content'])

        if not ro_flags_section or not output_flags_section:
            print(f"  - EȘEC: Nu s-a găsit secțiunea FLAGS în unul sau ambele fișiere. Se continuă.")
            failed_pairs += 1
            continue

        # Extragem link-urile specifice
        ro_link_in_ro = extract_language_link(ro_flags_content, 'ro')
        en_link_in_output = extract_language_link(output_flags_content, 'en')

        if not ro_link_in_ro:
            print(f"  - EȘEC: Nu s-a găsit link-ul RO în fișierul RO.")
            failed_pairs += 1
            continue

        if not en_link_in_output:
            print(f"  - EȘEC: Nu s-a găsit link-ul EN în fișierul OUTPUT.")
            failed_pairs += 1
            continue

        # Extragem numele fișierelor din link-uri
        ro_filename = extract_filename_from_url(ro_link_in_ro, 'ro')
        en_filename = extract_filename_from_url(en_link_in_output, 'en')

        if not ro_filename or not en_filename:
            print(f"  - EȘEC: Nu s-au putut extrage numele fișierelor din link-uri.")
            failed_pairs += 1
            continue

        # Verificăm dacă este un termen special
        is_special = is_special_term(ro_filename, en_filename)
        if is_special:
            special_terms.append({
                'id': item_id,
                'ro_file': ro_file['filename'],
                'en_file': output_file['filename'],
                'ro_url': ro_filename,
                'en_url': en_filename
            })
            print(f"  - SPECIAL: Termen special detectat! Se păstrează link-ul în EN.")

        # Construim link-ul EN corect bazat pe numele REAL al fișierului EN din OUTPUT
        en_filename_for_url = output_file['filename']  # Numele real: ex. "how-do-you-turn-disappointment-into-the-strength-to-move-forward.html"
        en_url_correct = f'https://neculaifantanaru.com/en/{en_filename_for_url}'
        
        # Construim tag-ul HTML complet pentru link-ul EN corect
        # Folosim tag-ul EN existent din OUTPUT ca template, dar înlocuim href-ul cu cel corect
        en_link_correct = en_link_in_output  # Folosim tag-ul existent ca template
        if en_link_correct:
            # Înlocuim href-ul cu cel corect
            en_link_correct = re.sub(
                r'href="https://neculaifantanaru\.com/en/[^"]*"',
                f'href="{en_url_correct}"',
                en_link_correct
            )
        
        # DEBUG: Verificăm ce link EN există în fișierul RO înainte
        en_link_current_in_ro = extract_language_link(ro_flags_content, 'en')
        if en_link_current_in_ro:
            en_filename_current_in_ro = extract_filename_from_url(en_link_current_in_ro, 'en')
            print(f"  [DEBUG] Link EN curent în RO: {en_filename_current_in_ro}")
            print(f"  [DEBUG] Link EN corect (din OUTPUT): {en_filename_for_url}")
            if en_filename_current_in_ro == en_filename_for_url:
                print(f"  [DEBUG] Link-urile EN sunt identice - nu e nevoie de modificare")
            else:
                print(f"  [DEBUG] Link-urile EN DIFERĂ - va încerca înlocuirea")
        
        # Actualizăm conținutul fișierului RO - întotdeauna înlocuim link-ul EN cu cel corect
        ro_updated_content, ro_modified = update_flags_section(ro_file['content'], None, en_link_correct, is_special)
        
        # FORȚĂM întotdeauna înlocuirea link-ului EN în RO - chiar dacă funcția raportează că nu e nevoie
        # Facem înlocuirea manual pentru a fi siguri că link-ul EN este corect
        ro_flags_section_new, ro_flags_content_new = extract_flags_section(ro_updated_content)
        if ro_flags_content_new and not is_special:
            # Înlocuim direct href-ul EN
            en_patterns = [
                r'(<a [^>]*?href=")https://neculaifantanaru\.com/en/[^"]*?("[^>]*?><img[^>]*?flag_lang_en\.jpg[^>]*?></a>)',
                r'(<a [^>]*?href=")https://neculaifantanaru\.com/en/[^"]*?("[^>]*?title="en"[^>]*?><img[^>]*?></a>)'
            ]
            for pattern in en_patterns:
                ro_flags_content_new_forced = re.sub(pattern, r'\1' + en_url_correct + r'\2', ro_flags_content_new, count=1)
                if ro_flags_content_new_forced != ro_flags_content_new:
                    ro_flags_section_new = f'<!-- FLAGS_1 -->{ro_flags_content_new_forced}<!-- FLAGS -->'
                    ro_updated_content = ro_updated_content.replace(ro_flags_section, ro_flags_section_new)
                    ro_modified = True
                    print(f"  [DEBUG] Înlocuire forțată efectuată pentru link-ul EN în RO")
                    break
            if not ro_modified:
                print(f"  [DEBUG] Link-ul EN este deja corect (după forțare)")
                ro_modified = True  # Marchează ca modificat pentru a salva fișierul

        # Construim URL-ul RO corect bazat pe numele REAL al fișierului RO (nu pe link-ul din FLAGS care poate fi vechi)
        ro_filename_for_url = ro_file['filename']  # Numele real: ex. "stiinta-de-care-se-leaga-numele-meu.html"
        ro_url_correct = f'https://neculaifantanaru.com/{ro_filename_for_url}'
        
        # DEBUG: Verificăm ce link RO există în fișierul OUTPUT înainte
        ro_link_current = extract_language_link(output_flags_content, 'ro')
        if ro_link_current:
            ro_filename_current = extract_filename_from_url(ro_link_current, 'ro')
            print(f"  [DEBUG] Link RO curent în OUTPUT: {ro_filename_current}")
            print(f"  [DEBUG] Link RO corect (din fișier): {ro_filename_for_url}")
            if ro_filename_current == ro_filename_for_url:
                print(f"  [DEBUG] Link-urile sunt identice - nu e nevoie de modificare")
            else:
                print(f"  [DEBUG] Link-urile DIFERĂ - va încerca înlocuirea")
        
        # FORȚĂM ÎNTOTDEAUNA înlocuirea link-ului RO - pentru a fi siguri că este corect
        # Actualizăm conținutul fișierului OUTPUT - întotdeauna înlocuim link-ul RO cu cel corect bazat pe numele fișierului
        print(f"  [DEBUG] Apel update_flags_section cu ro_url_correct: {ro_url_correct}")
        output_updated_content, output_modified = update_flags_section(output_file['content'], ro_url_correct, None, is_special)
        print(f"  [DEBUG] update_flags_section returnează output_modified: {output_modified}")
        
        # FORȚĂM întotdeauna înlocuirea - chiar dacă funcția raportează că nu e nevoie
        # Facem înlocuirea manual pentru a fi siguri că link-ul RO este corect
        output_flags_section_new, output_flags_content_new = extract_flags_section(output_updated_content)
        if output_flags_content_new:
            # Înlocuim direct href-ul RO
            pattern = r'(<a [^>]*?href=")https://neculaifantanaru\.com/[^"]*?("[^>]*?><img[^>]*?flag_lang_ro\.jpg[^>]*?></a>)'
            replacement = r'\1' + ro_url_correct + r'\2'
            output_flags_content_new_forced = re.sub(pattern, replacement, output_flags_content_new, count=1)
            if output_flags_content_new_forced != output_flags_content_new:
                output_flags_section_new = f'<!-- FLAGS_1 -->{output_flags_content_new_forced}<!-- FLAGS -->'
                output_updated_content = output_updated_content.replace(output_flags_section, output_flags_section_new)
                output_modified = True
                print(f"  [DEBUG] Înlocuire forțată efectuată pentru link-ul RO")
            else:
                print(f"  [DEBUG] Link-ul RO este deja corect (după forțare)")
                output_modified = True  # Marchează ca modificat pentru a salva fișierul

        # Verificăm dacă s-au făcut modificări
        if not ro_modified and not output_modified:
            print(f"  - IGNORAT: Nu au fost necesare modificări.")
            continue

        # Salvăm fișierele actualizate
        try:
            with open(ro_file['path'], 'w', encoding='utf-8') as f:
                f.write(ro_updated_content)
            print(f"  - Fișierul RO actualizat cu succes.")
        except Exception as e:
            print(f"  - Eroare la salvarea fișierului RO: {e}")
            failed_pairs += 1
            continue

        try:
            with open(output_file['path'], 'w', encoding='utf-8') as f:
                f.write(output_updated_content)
            print(f"  - Fișierul OUTPUT actualizat cu succes.")
        except Exception as e:
            print(f"  - Eroare la salvarea fișierului OUTPUT: {e}")
            failed_pairs += 1
            continue

        print(f"  - SUCCES: Ambele fișiere au fost actualizate.")
        processed_pairs += 1

    return processed_pairs, failed_pairs, special_terms

def main():
    # Definim directoarele
    ro_dir = r'e:\Carte\BB\17 - Site Leadership\Principal\ro'
    output_dir = r'e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\output'

    # Verificăm dacă directoarele există
    if not os.path.exists(ro_dir):
        print(f"Directorul RO nu există: {ro_dir}")
        return

    if not os.path.exists(output_dir):
        print(f"Directorul OUTPUT nu există: {output_dir}")
        return

    # Procesăm fișierele
    print("Începere procesare fișiere...")
    processed_pairs, failed_pairs, special_terms = process_files(ro_dir, output_dir)

    # Afișăm rezultatul
    print(f"\nRezultat final:")
    print(f"- Perechi de fișiere actualizate cu succes: {processed_pairs}")
    print(f"- Perechi de fișiere cu erori: {failed_pairs}")

    # Afișăm termenii speciali
    if special_terms:
        print(f"\nTermeni speciali detectați ({len(special_terms)}):")
        print("-" * 80)
        for term in special_terms:
            print(f"ID: {term['id']}")
            print(f"RO: {term['ro_file']} -> URL: {term['ro_url']}")
            print(f"EN: {term['en_file']} -> URL: {term['en_url']}")
            print("-" * 80)

    print("\nProcesare completă!")

if __name__ == "__main__":
    main()