import os
import re
import shutil

ro_directory = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\ro'
en_directory = r'c:\Folder1\fisiere_gata'

def get_ro_filename(en_content):
   match = re.search(r'<li><a cunt_code="\+40" href="https://neculaifantanaru\.com/(.*?)\.html"', en_content)
   return match.group(1) if match else None

def get_image_url(content):
   img_match = re.search(r'<img src="(https://neculaifantanaru\.com/images/.*?_image\.jpg)"', content)
   return img_match.group(1) if img_match else None

def process_files():
   print("Start procesare fișiere...")

   for en_file in os.listdir(en_directory):
       if not en_file.endswith('.html'):
           continue

       print(f"\nProcesare: {en_file}")
       en_file_path = os.path.join(en_directory, en_file)

       try:
           with open(en_file_path, 'r', encoding='utf-8') as f:
               en_content = f.read()

           ro_filename = get_ro_filename(en_content)
           if not ro_filename:
               print(f"Nu s-a găsit link-ul RO în {en_file}")
               continue

           ro_file_path = os.path.join(ro_directory, f"{ro_filename}.html")
           if not os.path.exists(ro_file_path):
               print(f"Fișierul RO nu există: {ro_file_path}")
               continue

           print(f"Fișier RO găsit: {ro_filename}.html")

           with open(ro_file_path, 'r', encoding='utf-8') as f:
               ro_content = f.read()

           image_url = get_image_url(ro_content)
           if not image_url:
               print(f"Nu s-a găsit URL-ul imaginii în {ro_filename}.html")
               continue

           print(f"URL imagine găsit: {image_url}")

           # Înlocuiește imaginea în fișierul EN
           new_en_content = re.sub(
               r'<img src="https://neculaifantanaru\.com/images/.*?_image\.jpg"',
               f'<img src="{image_url}"',
               en_content
           )

           with open(en_file_path, 'w', encoding='utf-8') as f:
               f.write(new_en_content)

           print(f"Imagine actualizată în {en_file}")

       except Exception as e:
           print(f"Eroare la procesarea {en_file}: {str(e)}")

   print("\nProcesare terminată")

def copy_output_files():
    """Copiază fișierele din folderul output în folderul en din Principal (păstrează originalele)"""
    source_dir = r'e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Iulia Python\output'
    target_dir = r'e:\Carte\BB\17 - Site Leadership\Principal\en'

    print("\nCopiere fișiere din output în Principal/en...")

    # Verifică existența directoarelor
    if not os.path.exists(source_dir):
        print(f"Directorul sursă nu există: {source_dir}")
        return False

    if not os.path.exists(target_dir):
        print(f"Directorul țintă nu există: {target_dir}")
        return False

    # Contoare pentru statistici
    total_files = 0
    copied_files = 0
    error_files = 0

    for filename in os.listdir(source_dir):
        if not filename.endswith('.html'):
            continue

        total_files += 1
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)

        try:
            # Verifică dacă fișierul există deja la destinație
            if os.path.exists(target_path):
                print(f"Fișierul există deja la destinație, se suprascrie: {filename}")

            # Copiază fișierul la destinație (păstrează originalul)
            shutil.copy2(source_path, target_path)
            print(f"Fișier copiat cu succes: {filename}")
            copied_files += 1

        except Exception as e:
            print(f"Eroare la copierea fișierului {filename}: {str(e)}")
            error_files += 1

    print(f"\nRezultat copiere din output în Principal/en:")
    print(f"- Total fișiere procesate: {total_files}")
    print(f"- Fișiere copiate cu succes: {copied_files}")
    print(f"- Fișiere cu erori: {error_files}")

    return True

def copy_fisiere_gata():
    """Copiază fișierele din folderul fisiere_gata în folderul en din Principal 2022 (păstrează originalele)"""
    source_dir = r'c:\Folder1\fisiere_gata'
    target_dir = r'e:\Carte\BB\17 - Site Leadership\Principal 2022\en'

    print("\nCopiere fișiere în Principal 2022/en...")

    # Verifică existența directoarelor
    if not os.path.exists(source_dir):
        print(f"Directorul sursă nu există: {source_dir}")
        return False

    if not os.path.exists(target_dir):
        print(f"Directorul țintă nu există: {target_dir}")
        # Încercăm să creăm directorul țintă
        try:
            os.makedirs(target_dir)
            print(f"Directorul țintă a fost creat: {target_dir}")
        except Exception as e:
            print(f"Nu s-a putut crea directorul țintă: {str(e)}")
            return False

    # Contoare pentru statistici
    total_files = 0
    copied_files = 0
    error_files = 0

    for filename in os.listdir(source_dir):
        if not filename.endswith('.html'):
            continue

        total_files += 1
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)

        try:
            # Verifică dacă fișierul există deja la destinație
            if os.path.exists(target_path):
                print(f"Fișierul există deja la destinație, se suprascrie: {filename}")

            # Copiază fișierul la destinație (păstrează originalul)
            shutil.copy2(source_path, target_path)
            print(f"Fișier copiat cu succes în directorul local: {filename}")
            copied_files += 1

        except Exception as e:
            print(f"Eroare la procesarea fișierului {filename}: {str(e)}")
            error_files += 1

    print(f"\nRezultat procesare din fisiere_gata:")
    print(f"- Total fișiere procesate: {total_files}")
    print(f"- Fișiere copiate în director local: {copied_files}")
    print(f"- Fișiere cu erori: {error_files}")

    return True

if __name__ == "__main__":
    # Prima etapă - procesarea fișierelor conform codului original
    process_files()

    # A doua etapă - copierea fișierelor din output în Principal/en (păstrează originalele)
    copy_output_files()

    # A treia etapă - copierea fișierelor din fisiere_gata în Principal 2022/en (păstrează originalele)
    copy_fisiere_gata()

    print("\nToate operațiunile au fost finalizate!")