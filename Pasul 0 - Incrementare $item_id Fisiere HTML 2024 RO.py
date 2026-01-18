import os
import re
from collections import defaultdict

# Configuration
folders_to_scan = [
    r'e:\Carte\BB\17 - Site Leadership\Principal\ro',
    r'e:\Carte\BB\17 - Site Leadership\Principal\ro\Python Files'
]
tracking_dir = r'e:\Carte\BB\17 - Site Leadership\Principal\ro'
MAX_ID = 5000

# Folders for find and replace cleanup
cleanup_folders = [
    r'e:\Carte\BB\17 - Site Leadership\Principal\ro',
    r'e:\Carte\BB\17 - Site Leadership\Principal\en'
]

def safe_print(text):
    """Handle special characters when printing"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode('utf-8', errors='replace').decode('utf-8'))

def find_and_update_tracking_file(directory, new_id):
    """Update or create the tracking file"""
    try:
        pattern = re.compile(r'4-+am ajuns la \d+$')
        tracking_file = None

        for filename in os.listdir(directory):
            if pattern.search(filename):
                tracking_file = os.path.join(directory, filename)
                break

        if tracking_file:
            old_name = os.path.basename(tracking_file)
            new_name = re.sub(r'\d+$', str(new_id), old_name)
            os.rename(tracking_file, os.path.join(directory, new_name))
            safe_print(f"Fișierul de tracking actualizat: {old_name} -> {new_name}")
        else:
            new_name = f"4---------------------------am ajuns la {new_id}"
            with open(os.path.join(directory, new_name), 'w') as f:
                f.write(f"Ultimul ID folosit: {new_id}")
            safe_print(f"Fișier de tracking creat: {new_name}")

    except Exception as e:
        safe_print(f"Eroare la actualizarea fișierului de tracking: {str(e)}")

def cleanup_paragraph_spacing():
    """Remove whitespace after <p class="text_obisnuit"> and <p class="text_obisnuit2"> tags"""
    safe_print("\n" + "="*50)
    safe_print("CURĂȚARE SPAȚII DUPĂ TAG-URI PARAGRAF")
    safe_print("="*50)

    pattern = re.compile(r'(<p class="text_obisnuit2?"[^>]*>)\s+')
    total_files_processed = 0
    total_replacements = 0

    for folder in cleanup_folders:
        if not os.path.exists(folder):
            safe_print(f"ATENȚIE: Folderul nu există: {folder}")
            continue

        safe_print(f"\nProcesez folderul: {folder}")
        folder_files_processed = 0
        folder_replacements = 0

        try:
            for filename in os.listdir(folder):
                if filename.lower().endswith('.html'):
                    file_path = os.path.join(folder, filename)

                    # AFIȘARE ÎN TIMP REAL
                    safe_print(f"  Procesez: {filename}")

                    try:
                        # Read file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='latin-1') as f:
                                content = f.read()
                        except Exception as e:
                            safe_print(f"    ✗ Eroare la citirea fișierului: {str(e)}")
                            continue

                    # Apply regex replacement
                    new_content, count = pattern.subn(r'\1', content)

                    if count > 0:
                        try:
                            # Write back to file
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            safe_print(f"    ✓ {count} înlocuiri efectuate")
                            folder_replacements += count
                        except Exception as e:
                            safe_print(f"    ✗ Eroare la scrierea fișierului: {str(e)}")
                    else:
                        safe_print(f"    - Nicio modificare necesară")

                    folder_files_processed += 1

        except Exception as e:
            safe_print(f"Eroare la procesarea folderului {folder}: {str(e)}")

        safe_print(f"  Folder completat: {folder_files_processed} fișiere, {folder_replacements} înlocuiri")
        total_files_processed += folder_files_processed
        total_replacements += folder_replacements

    safe_print("\n" + "="*50)
    safe_print("REZUMAT CURĂȚARE SPAȚII:")
    safe_print("="*50)
    safe_print(f"Total fișiere procesate: {total_files_processed}")
    safe_print(f"Total înlocuiri efectuate: {total_replacements}")
    safe_print("="*50)

def process_files():
    # Data structures
    all_files = []
    filename_counts = defaultdict(list)
    duplicate_names = defaultdict(list)
    id_to_files = defaultdict(list)
    files_without_id = []
    duplicate_ids = defaultdict(list)
    out_of_range_ids = []

    # First pass: Find all HTML files
    safe_print("\n=== SCANARE FIȘIERE ===")
    for folder in folders_to_scan:
        safe_print(f"\nScanare folder: {os.path.basename(folder)}")
        for filename in os.listdir(folder):
            if filename.lower().endswith('.html'):
                full_path = os.path.join(folder, filename)
                all_files.append(full_path)
                filename_counts[filename].append(full_path)
                safe_print(f" - Găsit: {filename}")

    # Check for duplicate filenames
    for name, paths in filename_counts.items():
        if len(paths) > 1:
            duplicate_names[name] = paths

    # Second pass: Analyze IDs
    safe_print("\n=== ANALIZĂ ID-URI ===")
    id_pattern = re.compile(r'<!-- \s*\$item_id\s*=\s*(\d+);.*?-->')

    safe_print("Se analizează următoarele fișiere:")
    for file_path in all_files:
        filename = os.path.basename(file_path)
        safe_print(f" - Analiză ID pentru: {filename}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()

        matches = id_pattern.findall(content)
        if not matches:
            files_without_id.append(filename)
            safe_print("   ! Fișierul nu conține ID")
            continue

        file_id = int(matches[0])
        id_to_files[file_id].append(filename)
        safe_print(f"   ID găsit: {file_id}")

        if file_id > MAX_ID:
            out_of_range_ids.append((filename, file_id))
            safe_print(f"   ! ATENȚIE: ID depășește limita maximă ({MAX_ID})")

        # Check if this ID is duplicate (we'll know after full scan)
        if len(id_to_files[file_id]) > 1:
            safe_print(f"   ! ATENȚIE: ID duplicat (mai apare în: {id_to_files[file_id][0]})")

    # Find duplicate IDs
    for file_id, files in id_to_files.items():
        if len(files) > 1:
            duplicate_ids[file_id] = files

    # Generate the exact report format requested
    safe_print("\n" + "="*50)
    safe_print("REZULTATE ANALIZĂ:")
    safe_print("="*50)
    safe_print(f"Total fișiere HTML găsite: {len(all_files)}")
    safe_print(f"Fișiere fără ID: {len(files_without_id)}")
    safe_print(f"Fișiere cu ID-uri peste limită ({MAX_ID}): {len(out_of_range_ids)}")
    safe_print(f"ID-uri duplicate: {len(duplicate_ids)}")
    safe_print("="*50)

    # Files without ID
    if files_without_id:
        safe_print("\nFIȘIERE FĂRĂ ID:")
        for i, filename in enumerate(sorted(files_without_id), 1):
            safe_print(f"{i}. {filename}")

    # Duplicate IDs
    if duplicate_ids:
        safe_print("\nID-URI DUPLICATE:")
        for i, (file_id, files) in enumerate(sorted(duplicate_ids.items()), 1):
            safe_print(f"{i}. ID {file_id} este folosit în {len(files)} fișiere:")
            for j, filename in enumerate(sorted(files), 1):
                safe_print(f"   {j}. {filename}")

    # Duplicate filenames
    if duplicate_names:
        safe_print("\nS-au detectat urmatoarele fisiere cu acelasi nume:")
        for name, paths in duplicate_names.items():
            safe_print(f"\nNume duplicat: {name}")
            for path in paths:
                safe_print(f" - {path}")

    # Determine if we need to reset IDs
    needs_reset = bool(files_without_id or out_of_range_ids or duplicate_ids)

    if needs_reset:
        safe_print("\nS-au detectat probleme cu ID-urile care necesită corectare.")
    else:
        safe_print("\nNu s-au detectat probleme cu ID-urile. ID-urile existente vor fi păstrate.")

    # Process files to fix problematic IDs and assign IDs to files without ID
    safe_print("\n=== CORECTARE ID-URI ===")
    
    # Find the maximum existing ID to start assigning new IDs from
    max_existing_id = 0
    if id_to_files:
        max_existing_id = max(id_to_files.keys())
    
    # Track which IDs are already used (for files that keep their IDs)
    used_ids = set()
    
    # First pass: Keep valid IDs for files that don't have problems
    all_files_sorted = sorted(all_files, key=lambda x: os.path.basename(x).lower())
    
    # Build a map of filename to file info
    file_info = {}
    for file_path in all_files_sorted:
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        matches = id_pattern.findall(content)
        existing_id = int(matches[0]) if matches else None
        
        # Determine if this file has problems
        has_problem = (
            existing_id is None or  # No ID
            existing_id > MAX_ID or  # Out of range
            (existing_id in duplicate_ids and filename in duplicate_ids[existing_id])  # Duplicate ID
        )
        
        file_info[file_path] = {
            'filename': filename,
            'content': content,
            'existing_id': existing_id,
            'has_problem': has_problem
        }
        
        # Mark ID as used if it's valid and not a duplicate
        if existing_id and not has_problem and existing_id not in duplicate_ids:
            used_ids.add(existing_id)
    
    # Second pass: Fix problematic files
    current_id = 1
    files_fixed = 0
    files_kept = 0
    
    for file_path in all_files_sorted:
        info = file_info[file_path]
        filename = info['filename']
        existing_id = info['existing_id']
        has_problem = info['has_problem']
        content = info['content']
        
        if has_problem:
            # Find next available ID
            while current_id in used_ids or current_id > MAX_ID:
                current_id += 1
            
            id_comment = f'<!-- $item_id = {current_id}; // Replace that with your rating id -->'
            
            # If file had no ID, add it
            if existing_id is None:
                # Find a good place to insert the ID (after <html> tag)
                html_match = re.search(r'(<html[^>]*>)', content, re.IGNORECASE)
                if html_match:
                    insert_pos = html_match.end()
                    new_content = content[:insert_pos] + '\n' + id_comment + content[insert_pos:]
                else:
                    # Try to insert at the beginning
                    new_content = id_comment + '\n' + content
            else:
                # Replace existing ID
                new_content = re.sub(
                    r'<!-- \s*\$item_id\s*=\s*\d+;.*?-->',
                    id_comment,
                    content
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            if existing_id:
                safe_print(f"  {filename}: ID corectat {existing_id} -> {current_id}")
            else:
                safe_print(f"  {filename}: ID atribuit {current_id}")
            
            used_ids.add(current_id)
            current_id += 1
            files_fixed += 1
        else:
            # Keep existing ID
            safe_print(f"  {filename}: ID păstrat {existing_id}")
            files_kept += 1

    # Update tracking file with the new maximum ID
    if used_ids:
        new_max_id = max(used_ids)
    else:
        new_max_id = current_id - 1 if current_id > 1 else 0
    find_and_update_tracking_file(tracking_dir, new_max_id)

    safe_print("\n" + "="*50)
    safe_print("REZUMAT FINAL:")
    safe_print("="*50)
    safe_print(f"Total fișiere procesate: {len(all_files)}")
    safe_print(f"Fișiere cu ID-uri păstrate: {files_kept}")
    safe_print(f"Fișiere cu ID-uri corectate/atribuite: {files_fixed}")
    safe_print(f"Ultimul ID folosit: {new_max_id}")
    safe_print("="*50)

    # NEW: Run paragraph spacing cleanup after ID processing
    cleanup_paragraph_spacing()

if __name__ == "__main__":
    process_files()