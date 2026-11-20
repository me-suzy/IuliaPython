# Traduce tot - automat

Scriptul `TRADUCE TOT - automat.py` gaseste singur articolele din `Principal\ro` care nu sunt traduse in engleza,
le traduce cu Claude API si le duce prin toti pasii (Pasul 0 - Pasul 5) pana in `c:\Folder1\fisiere_html`.

## Pornire
- Dublu-click pe **TRADUCE TOT - automat.bat**.
- La final scrie `GATA` si unde este `raport.txt`. Apoi se porneste `bebe-metoda-1-en-NOU.bat`.

## Din editorul Mini Dreamweaver
- Butonul **Translate** (langa „Trimite E-mail”) cauta articolele netraduse, cere confirmarea,
  porneste scriptul prin **TRADUCE TOT - din editor.bat** si afiseaza jurnalul in timp real.
- Editorul foloseste `--doar-lista` (doar lista articolelor netraduse) si citeste jurnalul pana la marcajul `[[SFARSIT cod=N]]`.

## Cheia API
- Cheia **nu** este in acest repository si nu se scrie in script.
- La prima rulare (sau cu **Schimba cheia API.bat**) se deschide o fereastra in care se lipeste cheia.
  Se salveaza in variabila de mediu `ANTHROPIC_API_KEY` a contului Windows.
- Dupa 30 de zile apare o fereastra care cere o cheie noua.

## Optiuni (din PowerShell, in acest folder)
- `python "TRADUCE TOT - automat.py" --fisiere a.html b.html` - doar anumite fisiere
- `python "TRADUCE TOT - automat.py" --lista lista.txt` - fisierele dintr-o lista
- `python "TRADUCE TOT - automat.py" --mod manual` - se opreste dupa extragere; traducerile se pun manual
- `python "TRADUCE TOT - automat.py" --reia` - continua ultima rulare de unde a ramas
- `python "TRADUCE TOT - automat.py" --schimba-cheia` - schimba cheia API

## Ce face, pe scurt
1. backup (`ro`, `en`, docx, scripturi, output) in `C:\Folder1\_backup_pipeline\`
2. muta HTML-urile vechi din `output\`
3. da ID nou doar articolelor noi cu ID duplicat (ca Pasul 0 sa nu strice perechile vechi RO-EN)
4. Pasul 0, Pasul 1A (lista pusa automat in `SPECIFIC_FILES`)
5. extrage articolele, le traduce (titlurile si expresiile in latina sau alte limbi raman neschimbate), verifica traducerea
6. construieste `bebe.docx`, Pasul 1B (ID-urile verificate si restaurate daca 1B le strica)
7. Pasul 2, 3 (+ repara steagul EN in fisierele RO), 4 (verifica data/categoria), 5
8. verificare finala: ID, steaguri RO <-> EN, data, index

Scripturile Pasul 0 - Pasul 5 trebuie sa fie in acelasi folder cu `TRADUCE TOT - automat.py`.
