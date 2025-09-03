import os
import re

def update_html_files(directory):
    files_processed = 0
    files_skipped = 0
    replacements_made = {}

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
            print(f"Processing file: {filename}")
            base_name = os.path.splitext(filename)[0]
            new_image_name = f"images/{base_name}_image.jpg"

            # Verifică dacă există o imagine corespunzătoare (case sensitive)
            image_exists = any(
                os.path.exists(os.path.join(directory, "images", f"{base_name}_image.{ext}"))
                for ext in ['webp', 'jpg', 'jpeg']
            )

            if image_exists:
                print(f"Corresponding image for {filename} exists. Skipping file.")
                files_skipped += 1
                continue

            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

            # Elimină </div> imediat după <!--FINNISHDATES-->
            content, div_count = re.subn(r'(<!--FINNISHDATES-->)\s*</div>', r'\1', content)
            if div_count > 0:
                print(f"Removed extra </div> after <!--FINNISHDATES--> in {filename}")

            # Extrage conținutul titlului
            title_match = re.search(r'<title>(.*?) \| Neculai Fantanaru</title>', content)
            title_text = title_match.group(1) if title_match else ""

            # Verifică dacă secțiunea dintre <!--FINNISHDATES--> și <!-- ARTICOL START --> conține deja o imagine
            if re.search(r'<!--FINNISHDATES-->.*?<img.*?<!-- ARTICOL START -->', content, re.DOTALL):
                print(f"Exista deja inlocuirea facuta {filename}. Skipping file.")
                files_skipped += 1
                continue

            replacements = []

            # Înlocuiește toate instanțele de "icon-facebook.jpg" cu noul nume de imagine
            content, count = re.subn(r'icon-facebook\.jpg', new_image_name, content)
            if count > 0:
                replacements.append(f"Replaced 'icon-facebook.jpg' with '{new_image_name}' ({count} times)")

            # Înlocuiește toate instanțele de "[nume]_image.jpg" cu noul nume de imagine
            content, count = re.subn(r'(?:images/)?[^"/]+_image\.jpg', new_image_name, content)
            if count > 0:
                replacements.append(f"Replaced '[nume]_image.jpg' with '{new_image_name}' ({count} times)")

            # Înlocuiește toate instanțele unde "images/" lipsește din URL
            content, count = re.subn(r'(https://neculaifantanaru\.com/)(?!images/)([^"/]+_image\.jpg)',
                                     f'\\1{new_image_name}', content)
            if count > 0:
                replacements.append(f"Added 'images/' to URLs ({count} times)")


            # Înlocuiește secțiunea dintre <!--FINNISHDATES--> și <!-- ARTICOL START -->
            # Înlocuiește secțiunea dintre <!--FINNISHDATES--> și <!-- ARTICOL START -->
            content, count = re.subn(
                r'(<!--FINNISHDATES-->)(?:\s*</div>)?\s*(<!-- ARTICOL START -->)',
                f'''\\1
            \t\t\t\t\t\t    </div>
                    <div class="space-before-image"></div>
                    <div class="feature-img-wrap">
                        <img src="https://neculaifantanaru.com/{new_image_name}" alt="{title_text}" class="img-responsive">

                                            </div><br>
            \\2''',
                content,
                flags=re.DOTALL
            )
            if count > 0:
                replacements.append(f"Added new image section ({count} times)")

            if count > 0:
                replacements.append(f"Added new image section ({count} times)")

            if count > 0:
                replacements.append(f"Added new image section ({count} times)")

            if replacements:
                # Scrie conținutul actualizat înapoi în fișier
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                files_processed += 1
                replacements_made[filename] = replacements
                print(f"Updated {filename}")
                print("Acestea sunt inlocuirile facute in fisierul {filename}:")
                for i, replacement in enumerate(replacements, 1):
                    print(f"{i}. {replacement}")
            else:
                print(f"No replacements needed in {filename}")

    print("\nProcessing complete.")
    print(f"Files updated: {files_processed}")
    print(f"Files skipped: {files_skipped}")
    print("\nReplacements made:")
    for file, reps in replacements_made.items():
        print(f"\n{file}:")
        for i, rep in enumerate(reps, 1):
            print(f"{i}. {rep}")
    print("\nFiles with no replacements:")
    for filename in os.listdir(directory):
        if filename.endswith(".html") and filename not in replacements_made and filename not in skip_files:
            print(f"  {filename}")

# Actualizează această cale cu directorul care conține fișierele tale HTML
directory_path = r'c:\Folder1\fisiere_gata'
update_html_files(directory_path)
