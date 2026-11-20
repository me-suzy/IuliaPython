# -*- coding: utf-8 -*-
"""
TRADUCE TOT - automat
=====================
Ruleaza tot fluxul RO -> EN, de la lista de fisiere netraduse pana la
c:\\Folder1\\fisiere_html, cu toate verificarile si corecturile:

  1  backup (ro/en html, docx, scripturi, output)    -> C:\\Folder1\\_backup_pipeline\\<data>\\
  2  muta HTML-urile vechi din output\\ deoparte     (altfel Pasul 5 le reproceseaza)
  3  Pasul 0  - corecteaza ID-urile duplicate
  4  Pasul 1A - pune lista in SPECIFIC_FILES si compileaza articole_compilate.docx
  5  extrage fiecare articol in <run>\\ro\\NN.txt
  6  traduce in <run>\\en\\NN.txt (Claude API sau manual) + validare
  7  construieste bebe.docx din traduceri
  8  Pasul 1B - rulat, apoi ID-urile verificate fata de RO; daca le strica, se restaureaza
  9  Pasul 2  - genereaza HTML-urile EN in output\\
 10  Pasul 3  - link-uri RO <-> EN; apoi repara steagul EN in fisierele RO sarite de script
 11  Pasul 4  - data si categoria din RO; verifica potrivirea cu RO-ul corect
 12  Pasul 5  - categorii + index + copiere in c:\\Folder1\\fisiere_html
 13  verificare finala + raport

Utilizare (din folderul Iulia Python):
  python "TRADUCE TOT - automat.py"                         # gaseste singur articolele RO netraduse
  python "TRADUCE TOT - automat.py" --lista fisier.txt
  python "TRADUCE TOT - automat.py" --fisiere a.html b.html  # unul sau cateva fisiere
  python "TRADUCE TOT - automat.py" --mod manual             # se opreste dupa pasul 5 ca sa traduci tu
  python "TRADUCE TOT - automat.py" --reia                    # continua ultima rulare de unde a ramas
  python "TRADUCE TOT - automat.py" --reia --pana-la docx     # opreste dupa un anumit pas

Pentru modul claude: setati o data cheia API (PowerShell):  setx ANTHROPIC_API_KEY "sk-ant-..."
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ---------------------------------------------------------------- configurare
IULIA = os.path.dirname(os.path.abspath(__file__))
RO_DIR = r'e:\Carte\BB\17 - Site Leadership\Principal\ro'
EN_DIR = r'e:\Carte\BB\17 - Site Leadership\Principal\en'
FOLDER_FINAL = r'c:\Folder1\fisiere_html'
BACKUP_ROOT = r'C:\Folder1\_backup_pipeline'
LISTA_IMPLICITA = os.path.join(os.path.dirname(IULIA), 'Schimba numerele HTML categorii in Principal 2022',
                               'articole-netraduse-in-engleza.txt')
WORK_ROOT = os.path.join(IULIA, '_traducere_claude')
OUTPUT_DIR = os.path.join(IULIA, 'output')
MODEL = 'claude-opus-5-5'

P0 = 'Pasul 0 - Incrementare $item_id Fisiere HTML 2024 RO.py'
P1A = 'Pasul 1 A - Copiaza fisiere html in docx BEBE website.py'
P1B = 'Pasul 1 B - Corecteaza ID-urile in bebe.docx.py'
P2 = 'Pasul 2 - Converteste bebe.docx in fisiere html (dupa ce ai tradus in engleza cu Google).py'
P3 = 'Pasul 3 - ADAUGA LINK-urile din RO in OUTPUT si invers (doar daca ai DATA si CATEGORIILE).py'
P4 = 'Pasul 4 - Preia DATA si Numele categoriilor din RO si le pune in fisierele noi EN.py'
P5 = 'Pasul 5 - Duce fiecare articol in fisierul categorii din care face parte si apoi in index FINAL.py'

PASI = ['backup', 'output', 'iduri', 'pasul0', 'pasul1a', 'extragere', 'traducere', 'docx',
        'pasul1b', 'pasul2', 'pasul3', 'pasul4', 'pasul5', 'verificare']


class Oprire(Exception):
    pass


def log(msg=''):
    print(msg, flush=True)
    if RUN.get('dir'):
        with open(os.path.join(RUN['dir'], 'jurnal.txt'), 'a', encoding='utf-8') as f:
            f.write(msg + '\n')


RUN = {}


def stare_salveaza():
    with open(os.path.join(RUN['dir'], 'stare.json'), 'w', encoding='utf-8') as f:
        json.dump(RUN['stare'], f, ensure_ascii=False, indent=2)


def citeste(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def scrie(p, s):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)


def ruleaza_script(nume, logname):
    """Ruleaza unul din scripturile Pasul X din folderul Iulia Python, cu log separat."""
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    lp = os.path.join(RUN['dir'], logname)
    log(f'   rulez: {nume}')
    with open(lp, 'w', encoding='utf-8') as f:
        r = subprocess.run([sys.executable, nume], cwd=IULIA, stdout=f, stderr=subprocess.STDOUT, env=env)
    if r.returncode != 0:
        raise Oprire(f'{nume} a esuat (cod {r.returncode}). Vezi {lp}')
    return citeste(lp)


def item_id(continut):
    m = re.search(r'\$item_id\s*=\s*(\d+);', continut)
    return m.group(1) if m else None


def sectiune_flags(c):
    return re.search(r'<!-- FLAGS_1 -->.*?<!-- FLAGS -->', c, re.S)


# ---------------------------------------------------------------- lista
def citeste_lista(cale):
    t = citeste(cale)
    nume = re.findall(r"['\"]([A-Za-z0-9_.\-]+\.html)['\"]", t)
    if not nume:  # format simplu: un fisier pe linie
        nume = [l.strip() for l in t.splitlines() if l.strip().endswith('.html')]
    vazute, rez = set(), []
    for n in nume:
        if n not in vazute:
            vazute.add(n); rez.append(n)
    return rez


def gaseste_netraduse():
    """Articolele RO netraduse: link-ul EN din FLAGS duce la un fisier care nu exista in en\\,
    sau la traducerea altui articol (articol nou facut prin copierea unuia vechi)."""
    rez = []
    for f in sorted(os.listdir(RO_DIR)):
        if not f.endswith('.html'):
            continue
        c = citeste(os.path.join(RO_DIR, f))
        if '<!-- ARTICOL START -->' not in c or 'class="den_articol"' not in c or '<!-- SASA-1 -->' not in c:
            continue  # nu e articol (index, categorii etc.)
        fl = sectiune_flags(c)
        m = re.search(r'neculaifantanaru\.com/en/([^"]+\.html)', fl.group(0) if fl else '')
        if not m or not os.path.exists(os.path.join(EN_DIR, m.group(1))):
            rez.append(f); continue
        efl = sectiune_flags(citeste(os.path.join(EN_DIR, m.group(1))))
        r = re.search(r'neculaifantanaru\.com/([^"/]+\.html)', efl.group(0) if efl else '')
        if r and r.group(1) != f:
            rez.append(f)
    return rez


# ---------------------------------------------------------------- pasi
def pas_iduri():
    """Da ID nou (unic) doar articolelor de tradus care au ID lipsa/duplicat/prea mare.
    Altfel Pasul 0 ar renumerota si articolul VECHI cu acelasi ID, stricandu-i perechea RO<->EN."""
    toate = {}
    for d in (RO_DIR, os.path.join(RO_DIR, 'Python Files'), EN_DIR):
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith('.html'):
                    i = item_id(citeste(os.path.join(d, f)))
                    if i:
                        toate.setdefault(i, []).append((d, f))
    # urmatorul ID liber dupa cele din RO (sub 5000, nefolosit nici in EN)
    urmator = max(int(i) for i, l in toate.items() if any(d != EN_DIR for d, _ in l) and int(i) <= 5000) + 1

    def liber(n):
        while str(n) in toate:
            n += 1
        return n
    urmator = liber(urmator)
    schimbate = 0
    for f in RUN['stare']['fisiere']:
        p = os.path.join(RO_DIR, f); c = citeste(p); i = item_id(c)
        alti = [x for x in toate.get(i, []) if not (x[0] == RO_DIR and x[1] == f)] if i else []
        if i and int(i) <= 5000 and not alti:
            continue
        if urmator > 5000:
            raise Oprire('Nu mai sunt ID-uri libere sub 5000')
        nou = f'<!-- $item_id = {urmator}; // Replace that with your rating id -->'
        if i:
            c = re.sub(r'<!--\s*\$item_id\s*=\s*\d+;.*?-->', nou, c, count=1)
        else:
            c = re.sub(r'(<html[^>]*>)', r'\1\n' + nou.replace('\\', '\\\\'), c, count=1, flags=re.I)
        scrie(p, c)
        log(f'   {f}: ID {i or "lipsa"} -> {urmator}' + (f' (era folosit si de {alti[0][1]})' if alti else ''))
        toate.setdefault(str(urmator), []).append((RO_DIR, f))
        urmator = liber(urmator + 1); schimbate += 1
    log(f'   ID-uri noi date articolelor de tradus: {schimbate}')


def pas_backup():
    b = os.path.join(BACKUP_ROOT, os.path.basename(RUN['dir']))
    for sub, src, ext in [('ro', RO_DIR, '.html'), ('en', EN_DIR, '.html'),
                          ('output_vechi', OUTPUT_DIR, '.html'), ('iulia', IULIA, ('.docx', '.py'))]:
        d = os.path.join(b, sub); os.makedirs(d, exist_ok=True)
        n = 0
        for f in os.listdir(src):
            if f.lower().endswith(ext) and os.path.isfile(os.path.join(src, f)):
                shutil.copy2(os.path.join(src, f), d); n += 1
        log(f'   backup {sub}: {n} fisiere')
    RUN['stare']['backup_dir'] = b
    log(f'   backup in: {b}')


def pas_output():
    vechi = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.html')]
    if vechi:
        d = os.path.join(IULIA, '_output_vechi_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(d, exist_ok=True)
        for f in vechi:
            shutil.move(os.path.join(OUTPUT_DIR, f), os.path.join(d, f))
        log(f'   {len(vechi)} HTML vechi mutate in {d}')
    else:
        log('   output\\ nu avea HTML-uri vechi')


def pas_pasul0():
    out = ruleaza_script(P0, 'pasul0.log')
    m = re.search(r'corectate/atribuite: (\d+)', out)
    log(f'   ID-uri corectate/atribuite: {m.group(1) if m else "?"}')


def pas_pasul1a():
    fisiere = RUN['stare']['fisiere']
    p = os.path.join(IULIA, P1A)
    s = citeste(p)
    nou = 'SPECIFIC_FILES = [\n' + ',\n'.join(f"    '{f}'" for f in fisiere) + '\n]'
    s2, n = re.subn(r'SPECIFIC_FILES = \[.*?\n\]', lambda m: nou, s, count=1, flags=re.S)
    if n != 1:
        raise Oprire('Nu am gasit SPECIFIC_FILES in Pasul 1A')
    scrie(p, s2)
    out = ruleaza_script(P1A, 'pasul1a.log')
    m = re.search(r'Găsite (\d+) din (\d+)', out)
    if not m or m.group(1) != m.group(2):
        raise Oprire('Pasul 1A nu a gasit toate fisierele. Vezi pasul1a.log')
    log(f'   articole_compilate.docx: {m.group(1)} articole')


def pas_extragere():
    from docx import Document
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    rodir = os.path.join(RUN['dir'], 'ro'); os.makedirs(rodir, exist_ok=True)

    def markup(p):
        parts, prev, buf = [], None, ''
        for r in p.runs:
            k = (bool(r.bold), bool(r.italic))
            if k != prev and buf:
                parts.append((prev, buf)); buf = ''
            prev = k; buf += r.text
        if buf:
            parts.append((prev, buf))
        s = ''
        for (b, i), t in parts:
            if i: t = f'<i>{t}</i>'
            if b: t = f'<b>{t}</b>'
            s += t
        return s.replace('\n', ' ')

    arts, cur = [], None
    for p in Document(os.path.join(IULIA, 'articole_compilate.docx')).paragraphs:
        t = p.text.strip()
        if not t:
            continue
        if p.alignment == WD_PARAGRAPH_ALIGNMENT.CENTER and not t.startswith('ID:'):
            cur = {'title': t, 'id': None, 'body': []}; arts.append(cur)
        elif t.startswith('ID:') and cur and cur['id'] is None:
            cur['id'] = t[3:].strip()
        elif cur:
            cur['body'].append(markup(p))
    if len(arts) != len(RUN['stare']['fisiere']):
        raise Oprire(f'Am extras {len(arts)} articole, lista are {len(RUN["stare"]["fisiere"])}')
    # verific ID-urile fata de fisierele RO (dupa Pasul 0)
    for n, (a, f) in enumerate(zip(arts, RUN['stare']['fisiere']), 1):
        idro = item_id(citeste(os.path.join(RO_DIR, f)))
        if a['id'] != idro:
            raise Oprire(f'ID diferit la {f}: docx={a["id"]} RO={idro}')
        with open(os.path.join(rodir, f'{n:04d}.txt'), 'w', encoding='utf-8') as fh:
            fh.write(f"TITLE: {a['title']}\nID: {a['id']}\n" + ''.join(b + '\n' for b in a['body']))
    ids = [a['id'] for a in arts]
    if len(set(ids)) != len(ids):
        raise Oprire('ID-uri duplicate intre articolele de tradus')
    log(f'   {len(arts)} articole extrase in {rodir}')


# ---------------------------------------------------------------- traducere
def citeste_txt(p):
    lines = [l.rstrip('\n') for l in open(p, encoding='utf-8') if l.strip()]
    if len(lines) < 2 or not lines[0].startswith('TITLE: ') or not lines[1].startswith('ID: '):
        raise ValueError('primele doua linii trebuie sa fie TITLE: si ID:')
    return lines[0][7:].strip(), lines[1][4:].strip(), lines[2:]


def e_bold(l):
    return l.startswith('<b>') and l.endswith('</b>')


def valideaza(ro_txt, en_txt):
    """Intoarce lista de probleme (goala daca traducerea e in regula)."""
    rt, rid, rb = ro_txt
    et, eid, eb = en_txt
    pb = []
    if rid != eid:
        pb.append(f'ID diferit ({eid} in loc de {rid})')
    if len(rb) != len(eb):
        pb.append(f'numar de paragrafe diferit: RO={len(rb)}, EN={len(eb)}')
    for i, (a, b) in enumerate(zip(rb, eb), 1):
        if b.count('<b>') != b.count('</b>') or b.count('<i>') != b.count('</i>'):
            pb.append(f'paragraful {i}: marcaje <b>/<i> neechilibrate')
        if e_bold(a) != e_bold(b):
            pb.append(f'paragraful {i}: in RO {"e" if e_bold(a) else "nu e"} bold in intregime, in EN nu se potriveste')
        if ('<i>' in a) and ('<i>' not in b):
            pb.append(f'paragraful {i}: italicul a disparut')
    if not et or '(' in et:
        pb.append('titlul EN lipseste sau contine paranteze (foloseste ":" in loc de paranteze)')
    return pb


SYSTEM_PROMPT = """You translate Romanian leadership articles (literary, first-person "scribe of the desert" style) into natural, elegant English for publication on a website. You return ONLY the translated article in exactly the same line format, nothing else.

FORMAT (strict):
- Line 1: "TITLE: <title>"   Line 2: "ID: <same id, unchanged>"
- Then exactly one output line per input paragraph line, same order, same count. Never merge, split, add or drop lines. No blank lines, no commentary, no code fences.
- Keep the inline markup <b>...</b> and <i>...</i> on the corresponding words. A line fully wrapped in <b>...</b> (or <b><i>...</i></b>) stays fully wrapped the same way. Numbered lines like "<b>1. </b>Text" keep that shape.

TITLE:
- If the Romanian title is in Latin or any language other than Romanian (e.g. "Non Nobis", "Sub Rosa", "Quo Vadis, Domine?"), keep it EXACTLY identical.
- Otherwise translate it naturally into English, in title case. Do not use parentheses in the title: "Demascarea (partea a doua)" -> "The Unmasking: Part Two".
- Near the end, the title is usually repeated in bold at the start of a paragraph (e.g. "<b>Cartea care a scris omenirea</b> rămâne...") and explained. Use the same English title there (or the identical Latin title).

CONTENT:
- Keep every Latin, Spanish, Italian, French, German, Russian (transliterated), Hebrew, Arabic or other non-Romanian expression exactly as written (e.g. <i>con una sencillez solemne</i>, "Sigillum Aureum", <i>Dei est iudicium.</i>, Zugzwang).
- Coined Romanian words (e.g. "cronoscris", "Sufletografie", "ignireziliență") become plausible English coinages ("chronoscript", "Soulography", "igniresilience"); invented non-Romanian-looking terms ("ClarisFract", "Theuria Rosthu", "Habajdir") stay unchanged.
- The recurring sentence "Și astfel, scribul din deșert a scris în cartea sa de nisip:" is always "And so, the scribe of the desert wrote in his book of sand:".
- Romanian quotation marks „...” become “...”. Keep other punctuation characters such as *asterisks* as they are.
- Translate everything else faithfully and completely, keeping the author's tone; do not summarize, censor, or add anything."""


def traduce_un_articol(client, ro_path, en_path):
    ro_txt = citeste_txt(ro_path)
    sursa = open(ro_path, encoding='utf-8').read()
    mesaje = [{'role': 'user', 'content': 'Translate this article:\n\n' + sursa}]
    ultima = None
    for incercare in range(1, 4):
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            system=SYSTEM_PROMPT,
            messages=mesaje,
            betas=['server-side-fallback-2026-07-01'],
            extra_body={'fallbacks': 'default'},
        ) as stream:
            resp = stream.get_final_message()
        if resp.stop_reason == 'refusal':
            ultima = 'modelul a refuzat cererea'
            continue
        if resp.stop_reason == 'max_tokens':
            ultima = 'raspunsul a fost taiat (max_tokens)'
            continue
        text = ''.join(b.text for b in resp.content if b.type == 'text').strip()
        text = re.sub(r'^```[a-z]*\n|\n```$', '', text).strip()
        tmp = en_path + '.tmp'
        scrie(tmp, text + '\n')
        try:
            en_txt = citeste_txt(tmp)
            pb = valideaza(ro_txt, en_txt)
        except ValueError as e:
            pb = [str(e)]
        if not pb:
            os.replace(tmp, en_path)
            return incercare
        ultima = '; '.join(pb[:6])
        mesaje = mesaje[:1] + [{'role': 'assistant', 'content': text},
                               {'role': 'user', 'content': 'Your translation has these problems: ' + ultima +
                                '. Return the full corrected translation in the exact required format.'}]
    raise Oprire(f'{os.path.basename(ro_path)}: traducere esuata dupa 3 incercari ({ultima})')


def pas_traducere():
    rodir = os.path.join(RUN['dir'], 'ro'); endir = os.path.join(RUN['dir'], 'en')
    os.makedirs(endir, exist_ok=True)
    toate = sorted(f for f in os.listdir(rodir) if f.endswith('.txt'))
    lipsa, gresite = [], []
    for f in toate:
        ep = os.path.join(endir, f)
        if os.path.exists(ep):
            try:
                pb = valideaza(citeste_txt(os.path.join(rodir, f)), citeste_txt(ep))
            except ValueError as e:
                pb = [str(e)]
            if pb:
                gresite.append((f, pb))
            continue
        lipsa.append(f)
    if RUN['mod'] == 'manual':
        if lipsa or gresite:
            for f, pb in gresite:
                log(f'   {f}: {"; ".join(pb[:4])}')
            raise Oprire(
                f'MOD MANUAL: {len(lipsa)} articole netraduse, {len(gresite)} cu probleme.\n'
                f'   Textele RO sunt in: {rodir}\n'
                f'   Puneti traducerile, cu acelasi nume de fisier, in: {endir}\n'
                f'   (acelasi format: TITLE:, ID:, apoi cate un paragraf pe linie)\n'
                f'   Apoi rulati din nou cu --reia')
        log(f'   toate cele {len(toate)} traduceri sunt prezente si valide')
        return
    for f, pb in gresite:  # le refac cu Claude
        log(f'   {f} are probleme ({"; ".join(pb[:3])}) - o retraduc')
        os.remove(os.path.join(endir, f)); lipsa.append(f)
    if not lipsa:
        log(f'   toate cele {len(toate)} traduceri sunt deja facute')
        return
    import anthropic
    client = anthropic.Anthropic(max_retries=6)
    log(f'   traduc {len(lipsa)} articole cu {MODEL} (4 in paralel)...')
    erori = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        fut = {ex.submit(traduce_un_articol, client, os.path.join(rodir, f), os.path.join(endir, f)): f for f in lipsa}
        for k, fu in enumerate(as_completed(fut), 1):
            f = fut[fu]
            try:
                n = fu.result()
                titlu = citeste_txt(os.path.join(endir, f))[0]
                log(f'   [{k}/{len(lipsa)}] {f} -> {titlu}' + (f' ({n} incercari)' if n > 1 else ''))
            except Exception as e:
                erori.append(f'{f}: {e}')
                log(f'   [{k}/{len(lipsa)}] EROARE {f}: {e}')
    if erori:
        raise Oprire(f'{len(erori)} articole nu s-au putut traduce. Rulati din nou cu --reia '
                     f'(cele reusite raman salvate).')


def pas_docx():
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    rodir = os.path.join(RUN['dir'], 'ro'); endir = os.path.join(RUN['dir'], 'en')
    tok = re.compile(r'(</?b>|</?i>)')
    doc = Document(); titluri = {}
    for f in sorted(x for x in os.listdir(rodir) if x.endswith('.txt')):
        ro_txt = citeste_txt(os.path.join(rodir, f)); en_txt = citeste_txt(os.path.join(endir, f))
        pb = valideaza(ro_txt, en_txt)
        if pb:
            raise Oprire(f'{f}: {"; ".join(pb)}')
        et, eid, eb = en_txt
        fname = re.sub(r'-+', '-', re.sub(r'[^a-z0-9\-]+', '-', _unidecode(et.lower()))).strip('-') + '.html'
        if fname in titluri:
            raise Oprire(f'Doua articole ar avea acelasi fisier EN {fname}: {titluri[fname]} si {f}')
        titluri[fname] = f
        tp = doc.add_paragraph(); tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = tp.add_run(et); r.bold = True; r.font.color.rgb = RGBColor(255, 0, 0)
        ip = doc.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = ip.add_run(f'ID: {eid}'); r.font.color.rgb = RGBColor(128, 128, 128); r.font.size = Pt(8)
        for line in eb:
            p = doc.add_paragraph(); b = i = False
            for t in tok.split(line):
                if t == '<b>': b = True
                elif t == '</b>': b = False
                elif t == '<i>': i = True
                elif t == '</i>': i = False
                elif t:
                    rr = p.add_run(t); rr.bold = b; rr.italic = i
        doc.add_paragraph()
    doc.save(os.path.join(IULIA, 'bebe.docx'))
    RUN['stare']['fisiere_en'] = titluri
    # fisiere EN care exista deja in Principal\en (vor fi suprascrise de Pasul 5)
    exista = [x for x in titluri if os.path.exists(os.path.join(EN_DIR, x))]
    RUN['stare']['en_suprascrise'] = exista
    log(f'   bebe.docx construit: {len(titluri)} articole')
    if exista:
        log(f'   ATENTIE: {len(exista)} fisiere EN cu acelasi nume exista deja in en\\ si vor fi inlocuite: '
            + ', '.join(exista[:10]))


def _unidecode(s):
    import unidecode
    return unidecode.unidecode(s)


def ids_din_bebe():
    from docx import Document
    return [p.text[3:].strip() for p in Document(os.path.join(IULIA, 'bebe.docx')).paragraphs
            if p.text.startswith('ID:')]


def pas_pasul1b():
    bebe = os.path.join(IULIA, 'bebe.docx'); copie = os.path.join(RUN['dir'], 'bebe_inainte_1B.docx')
    shutil.copy2(bebe, copie)
    corecte = [item_id(citeste(os.path.join(RO_DIR, f))) for f in RUN['stare']['fisiere']]
    ruleaza_script(P1B, 'pasul1b.log')
    dupa = ids_din_bebe()
    if dupa != corecte:
        stricate = [(f, a, b) for f, a, b in zip(RUN['stare']['fisiere'], corecte, dupa) if a != b]
        shutil.copy2(copie, bebe)
        log(f'   Pasul 1B a schimbat gresit {len(stricate)} ID-uri ({", ".join(f"{f}: {a}->{b}" for f, a, b in stricate[:5])})'
            f' - am restaurat bebe.docx cu ID-urile corecte')
    if ids_din_bebe() != corecte:
        raise Oprire('ID-urile din bebe.docx nu se potrivesc cu fisierele RO')
    log('   ID-urile din bebe.docx = ID-urile fisierelor RO')


def pas_pasul2():
    for f in os.listdir(OUTPUT_DIR):
        if f.lower().endswith('.html'):
            os.remove(os.path.join(OUTPUT_DIR, f))
    ruleaza_script(P2, 'pasul2.log')
    asteptate = set(RUN['stare']['fisiere_en'])
    gasite = {f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.html')}
    if gasite != asteptate:
        raise Oprire(f'Pasul 2: lipsesc {sorted(asteptate - gasite)[:5]}, in plus {sorted(gasite - asteptate)[:5]}')
    log(f'   {len(gasite)} fisiere HTML generate in output\\')


def perechi_pasul3():
    t = citeste(os.path.join(RUN['dir'], 'pasul3.log'))
    return re.findall(r'^  - RO: (\S+)\n  - EN: (\S+)', t, re.M)


def pas_pasul3():
    out = ruleaza_script(P3, 'pasul3.log')
    m = re.search(r'actualizate cu succes: (\d+)', out)
    log(f'   Pasul 3: perechi actualizate {m.group(1) if m else "?"}')
    perechi = dict((en, ro) for ro, en in perechi_pasul3())
    asteptat = {en: RUN['stare']['fisiere'][int(f[:4]) - 1] for en, f in RUN['stare']['fisiere_en'].items()}
    for en, ro in asteptat.items():
        if perechi.get(en) != ro:
            raise Oprire(f'Pasul 3 a legat {en} de {perechi.get(en)} in loc de {ro}')
    # repar steagul EN in fisierele RO (Pasul 3 il sare la "termeni speciali")
    rep = 0
    for en, ro in asteptat.items():
        p = os.path.join(RO_DIR, ro); c = citeste(p); m = sectiune_flags(c)
        if not m:
            raise Oprire(f'{ro} nu are sectiunea FLAGS')
        sec = m.group(0); cur = re.search(r'https://neculaifantanaru\.com/en/[^"]+', sec)
        want = 'https://neculaifantanaru.com/en/' + en
        if cur and cur.group(0) != want:
            c = c[:m.start()] + sec.replace(cur.group(0), want, 1) + c[m.end():]
            scrie(p, c); rep += 1
            log(f'   steag EN reparat in {ro}: {cur.group(0).split("/")[-1]} -> {en}')
    log(f'   steaguri EN reparate in RO: {rep}')


def pas_pasul4():
    out = ruleaza_script(P4, 'pasul4.log')
    perechi = re.findall(r'^Processing file: (\S+)\n(?:  \[Debug\].*\n)*  Found Romanian file by [^:]+: (\S+)', out, re.M)
    asteptat = {en: RUN['stare']['fisiere'][int(f[:4]) - 1] for en, f in RUN['stare']['fisiere_en'].items()}
    gasit = dict(perechi)
    for en, ro in asteptat.items():
        if gasit.get(en) != ro:
            raise Oprire(f'Pasul 4 a luat data/categoria pentru {en} din {gasit.get(en)} in loc de {ro}')
    m = re.search(r'Successfully updated files: (\d+)', out)
    log(f'   Pasul 4: {m.group(1) if m else "?"} fisiere cu data si categoria din RO')


def pas_pasul5():
    out = ruleaza_script(P5, 'pasul5.log')
    m = re.search(r'Total articles processed: (\d+)', out)
    if '[FATAL' in out:
        raise Oprire('Pasul 5 a raportat o eroare fatala. Vezi pasul5.log')
    log(f'   Pasul 5: {m.group(1) if m else "?"} articole duse in categorii si index')


def pas_verificare():
    asteptat = {en: RUN['stare']['fisiere'][int(f[:4]) - 1] for en, f in RUN['stare']['fisiere_en'].items()}
    idx = citeste(os.path.join(FOLDER_FINAL, 'index.html'))
    pb = []
    for en, ro in asteptat.items():
        pf = os.path.join(FOLDER_FINAL, en)
        if not os.path.exists(pf):
            pb.append(f'{en}: lipseste din {FOLDER_FINAL}'); continue
        c = citeste(pf); rc = citeste(os.path.join(RO_DIR, ro))
        fl, rfl = sectiune_flags(c), sectiune_flags(rc)
        if item_id(c) != item_id(rc): pb.append(f'{en}: ID {item_id(c)} diferit de RO {item_id(rc)}')
        if not fl or ('neculaifantanaru.com/' + ro) not in fl.group(0): pb.append(f'{en}: steagul RO nu duce la {ro}')
        if not fl or ('/en/' + en) not in fl.group(0): pb.append(f'{en}: steagul EN nu duce la el insusi')
        if not rfl or ('/en/' + en) not in rfl.group(0): pb.append(f'{ro}: steagul EN nu duce la {en}')
        if not re.search(r'<td class="text_dreapta">On [A-Z]', c): pb.append(f'{en}: fara data')
        if en not in idx: pb.append(f'{en}: nu apare in index.html')
    n = len(os.listdir(FOLDER_FINAL))
    rap = [f'RAPORT {datetime.now():%Y-%m-%d %H:%M}', f'Articole: {len(asteptat)}',
           f'Fisiere in {FOLDER_FINAL}: {n}', f'Backup: {RUN["stare"].get("backup_dir")}', '']
    rap += [f'{ro} -> {en}' for en, ro in sorted(asteptat.items(), key=lambda x: x[1])]
    if RUN['stare'].get('en_suprascrise'):
        rap += ['', 'Fisiere EN existente inlocuite:'] + RUN['stare']['en_suprascrise']
    rap += ['', f'Probleme: {len(pb)}'] + pb
    scrie(os.path.join(RUN['dir'], 'raport.txt'), '\n'.join(rap) + '\n')
    if pb:
        for x in pb[:20]: log('   ' + x)
        raise Oprire(f'Verificarea finala a gasit {len(pb)} probleme. Vezi raport.txt')
    log(f'   toate cele {len(asteptat)} articole sunt corecte; {n} fisiere in {FOLDER_FINAL}')


FUNCTII = dict(backup=pas_backup, output=pas_output, iduri=pas_iduri, pasul0=pas_pasul0, pasul1a=pas_pasul1a,
               extragere=pas_extragere, traducere=pas_traducere, docx=pas_docx, pasul1b=pas_pasul1b,
               pasul2=pas_pasul2, pasul3=pas_pasul3, pasul4=pas_pasul4, pasul5=pas_pasul5,
               verificare=pas_verificare)


# ---------------------------------------------------------------- cheia API (fereastra + aminitire la 30 de zile)
ZILE_VALABILITATE = 30
FISIER_DATA_CHEIE = os.path.join(os.environ.get('APPDATA', IULIA), 'TraduceTot', 'cheie_api.json')


def cheie_din_windows():
    """Cheia salvata in variabilele de mediu ale utilizatorului (HKCU\\Environment)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment') as k:
            return winreg.QueryValueEx(k, 'ANTHROPIC_API_KEY')[0]
    except OSError:
        return None


def salveaza_cheia(cheie):
    import winreg, ctypes
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, 'ANTHROPIC_API_KEY', 0, winreg.REG_SZ, cheie)
    try:  # anunta Windows ca s-au schimbat variabilele (pentru terminalele noi)
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x1A, 0, 'Environment', 2, 2000, None)
    except Exception:
        pass
    os.makedirs(os.path.dirname(FISIER_DATA_CHEIE), exist_ok=True)
    with open(FISIER_DATA_CHEIE, 'w', encoding='utf-8') as f:
        json.dump({'data_cheie': datetime.now().strftime('%Y-%m-%d')}, f)
    os.environ['ANTHROPIC_API_KEY'] = cheie


def data_cheii():
    try:
        with open(FISIER_DATA_CHEIE, encoding='utf-8') as f:
            return datetime.strptime(json.load(f)['data_cheie'], '%Y-%m-%d')
    except (OSError, KeyError, ValueError):
        return None


def cheia_merge(cheie):
    """Verifica cheia cu un apel gratuit (lista de modele)."""
    try:
        import anthropic
        anthropic.Anthropic(api_key=cheie, max_retries=1).models.list(limit=1)
        return True, ''
    except Exception as e:
        return False, f'{type(e).__name__}: {str(e)[:200]}'


def fereastra_cheie(mesaj):
    """Fereastra in care se lipeste cheia. Intoarce cheia sau None (Anulez)."""
    import tkinter as tk
    rez = {'cheie': None}
    w = tk.Tk(); w.title('Traduce tot - cheia API Anthropic'); w.attributes('-topmost', True)
    w.resizable(False, False)
    tk.Label(w, text=mesaj, justify='left', wraplength=520, padx=14, pady=10).pack(anchor='w')
    e = tk.Entry(w, width=70, show='•'); e.pack(padx=14); e.focus_set()
    vede = tk.BooleanVar(value=False)
    tk.Checkbutton(w, text='Arata cheia', variable=vede,
                   command=lambda: e.config(show='' if vede.get() else '•')).pack(anchor='w', padx=10)
    eroare = tk.Label(w, text='', fg='red', wraplength=520, padx=14); eroare.pack(anchor='w')

    def ok(_=None):
        c = e.get().strip()
        if not c.startswith('sk-ant-'):
            eroare.config(text='Cheia trebuie sa inceapa cu sk-ant-'); return
        eroare.config(text='Verific cheia...'); w.update()
        bun, err = cheia_merge(c)
        if not bun:
            eroare.config(text='Cheia nu functioneaza: ' + err); return
        rez['cheie'] = c; w.destroy()

    bt = tk.Frame(w); bt.pack(pady=10)
    tk.Button(bt, text='Salvez cheia', width=16, command=ok).pack(side='left', padx=6)
    tk.Button(bt, text='Anulez', width=16, command=w.destroy).pack(side='left', padx=6)
    w.bind('<Return>', ok)
    w.mainloop()
    return rez['cheie']


def fereastra_expirata(zile, data):
    """Intreaba ce facem cand cheia are 30+ zile. Intoarce 'noua', 'veche' sau None."""
    import tkinter as tk
    rez = {'r': None}
    w = tk.Tk(); w.title('Traduce tot - schimbati cheia API'); w.attributes('-topmost', True)
    w.resizable(False, False)
    tk.Label(w, text=f'Au trecut {zile} de zile de la ultima schimbare a cheii API ({data:%d.%m.%Y}).\n\n'
                     f'Cheia trebuie schimbata la fiecare {ZILE_VALABILITATE} de zile. Generati o cheie noua '
                     f'si introduceti-o acum.', justify='left', wraplength=480, padx=16, pady=14,
             fg='#a00000').pack()
    bt = tk.Frame(w); bt.pack(pady=10)

    def alege(x):
        rez['r'] = x; w.destroy()
    tk.Button(bt, text='Introduc cheia noua', width=20, command=lambda: alege('noua')).pack(side='left', padx=5)
    tk.Button(bt, text='Continui cu cea veche', width=20, command=lambda: alege('veche')).pack(side='left', padx=5)
    tk.Button(bt, text='Anulez', width=12, command=w.destroy).pack(side='left', padx=5)
    w.mainloop()
    return rez['r']


def asigura_cheia(forteaza=False):
    """Inainte de traducere: cere cheia daca lipseste, aminteste schimbarea dupa 30 de zile."""
    cheie = os.environ.get('ANTHROPIC_API_KEY') or cheie_din_windows()
    data = data_cheii()
    if cheie and not data:
        # cheie pusa de mana, fara data stiuta: o socotim de azi
        os.makedirs(os.path.dirname(FISIER_DATA_CHEIE), exist_ok=True)
        with open(FISIER_DATA_CHEIE, 'w', encoding='utf-8') as f:
            json.dump({'data_cheie': datetime.now().strftime('%Y-%m-%d')}, f)
        data = datetime.now()
    if cheie and not forteaza:
        zile = (datetime.now() - data).days
        if zile >= ZILE_VALABILITATE:
            alegere = fereastra_expirata(zile, data)
            if alegere is None:
                return False
            if alegere == 'veche':
                bun, err = cheia_merge(cheie)
                if bun:
                    os.environ['ANTHROPIC_API_KEY'] = cheie
                    log(f'   ATENTIE: cheia API are {zile} zile - schimbati-o cat mai curand')
                    return True
                log(f'   Cheia veche nu mai functioneaza ({err})')
            # 'noua' sau cheia veche nu merge -> cerem una noua
        else:
            os.environ['ANTHROPIC_API_KEY'] = cheie
            ramase = ZILE_VALABILITATE - zile
            log(f'   cheia API: mai sunt {ramase} zile pana la schimbare'
                + (' - pregatiti o cheie noua!' if ramase <= 3 else ''))
            return True
    mesaj = ('Lipiti aici cheia API Anthropic (incepe cu sk-ant-).\n'
             'Se salveaza in contul dumneavoastra de Windows, nu in script. Peste '
             f'{ZILE_VALABILITATE} de zile veti fi anuntat sa o schimbati.')
    noua = fereastra_cheie(mesaj)
    if not noua:
        return False
    salveaza_cheia(noua)
    log(f'   cheie API noua salvata; urmatoarea schimbare peste {ZILE_VALABILITATE} de zile '
        f'({datetime.fromtimestamp(time.time() + ZILE_VALABILITATE * 86400):%d.%m.%Y})')
    return True


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description='Traduce automat articole RO -> EN si le duce in c:\\Folder1\\fisiere_html')
    ap.add_argument('--lista', help='fisier cu lista de .html (formatul din articole-netraduse-in-engleza.txt sau unul pe linie)')
    ap.add_argument('--fisiere', nargs='+', help='nume de fisiere .html din ro\\, direct in linia de comanda')
    ap.add_argument('--mod', choices=['claude', 'manual'], default='claude')
    ap.add_argument('--reia', nargs='?', const='ULTIMA', help='continua o rulare (ultima, sau numele folderului ei)')
    ap.add_argument('--pana-la', choices=PASI, help='opreste dupa acest pas')
    ap.add_argument('--schimba-cheia', action='store_true', help='deschide fereastra pentru o cheie API noua')
    ap.add_argument('--doar-lista', action='store_true', help='afiseaza doar articolele netraduse (JSON) si iese')
    a = ap.parse_args()
    if a.doar_lista:
        print(json.dumps({'netraduse': gaseste_netraduse()}, ensure_ascii=False))
        return
    os.makedirs(WORK_ROOT, exist_ok=True)
    if a.schimba_cheia and not (a.lista or a.fisiere or a.reia):
        print('Cheia API a fost schimbata.' if asigura_cheia(True) else 'Cheia nu a fost schimbata.')
        return

    if a.reia:
        runs = sorted(d for d in os.listdir(WORK_ROOT) if d.startswith('run_'))
        nume = runs[-1] if a.reia == 'ULTIMA' and runs else a.reia
        RUN['dir'] = os.path.join(WORK_ROOT, nume)
        if not os.path.exists(os.path.join(RUN['dir'], 'stare.json')):
            sys.exit(f'Nu gasesc rularea {RUN["dir"]}')
        RUN['stare'] = json.load(open(os.path.join(RUN['dir'], 'stare.json'), encoding='utf-8'))
        log(f'\n=== Reiau rularea {nume} (pasi facuti: {", ".join(RUN["stare"]["facuti"]) or "niciunul"})')
    else:
        if a.fisiere:
            fisiere = a.fisiere
        elif a.lista:
            fisiere = citeste_lista(a.lista)
        else:
            print('Caut articolele RO netraduse in engleza...')
            fisiere = gaseste_netraduse()
            if not fisiere:
                sys.exit('Toate articolele din ro\\ sunt deja traduse in engleza. Nimic de facut.')
            print(f'Am gasit {len(fisiere)} articole netraduse:')
            for f in fisiere:
                print('   ' + f)
        if not fisiere:
            sys.exit('Lista de fisiere e goala.')
        lipsa = [f for f in fisiere if not os.path.exists(os.path.join(RO_DIR, f))]
        if lipsa:
            sys.exit('Nu exista in ro\\: ' + ', '.join(lipsa))
        RUN['dir'] = os.path.join(WORK_ROOT, 'run_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(RUN['dir'])
        RUN['stare'] = {'fisiere': fisiere, 'facuti': []}
        stare_salveaza()
        log(f'\n=== Rulare noua: {len(fisiere)} articole -> {RUN["dir"]}')
    RUN['mod'] = a.mod

    if a.mod == 'claude' and ('traducere' not in RUN['stare']['facuti'] or a.schimba_cheia):
        if not asigura_cheia(a.schimba_cheia):
            sys.exit('Fara cheie API nu pot traduce automat. Rulati din nou, sau cu --mod manual.')

    t0 = time.time()
    try:
        for i, pas in enumerate(PASI, 1):
            if pas in RUN['stare']['facuti']:
                continue
            log(f'\n[{i}/{len(PASI)}] {pas}')
            FUNCTII[pas]()
            RUN['stare']['facuti'].append(pas); stare_salveaza()
            if a.pana_la == pas:
                log(f'\nOprit dupa pasul "{pas}" (--pana-la). Continuati cu --reia.')
                return
    except Oprire as e:
        stare_salveaza()
        log(f'\nOPRIT: {e}')
        sys.exit(1)
    log(f'\nGATA in {int(time.time() - t0)}s. Fisierele sunt in {FOLDER_FINAL}. '
        f'Raport: {os.path.join(RUN["dir"], "raport.txt")}')
    log('Pasul urmator: porniti bebe-metoda-1-en-NOU.bat')


if __name__ == '__main__':
    cod = 0
    try:
        main()
    except SystemExit as e:  # mesajele sys.exit('...') apar si in jurnal, inaintea marcajului de final
        if isinstance(e.code, str):
            print(e.code, flush=True); cod = 1
        else:
            cod = e.code or 0
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout); cod = 1
    if '--sfarsit' in sys.argv or os.environ.get('TRADUCE_TOT_MARCAJ'):
        print(f'[[SFARSIT cod={cod}]]', flush=True)
    sys.exit(cod)
