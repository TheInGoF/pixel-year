# Pixel Year — Feature-Plan

Doku für kommende Features. Kein Code wird vorab geändert; Umsetzung wird einzeln freigegeben.

## Bereits umgesetzt

- Gitterkalender, SVG-Download, eingebauter PDF-Generator (3× A4 quer, ohne Bibliothek).
- Internationalisierung: 6 UI-Sprachen (EN, DE, ES, FR, IT, JA), lokalisierte Monatslabels (Intl),
  **Sprache · Land · Region** unabhängig wählbar.
- Feiertage + Schulferien für 130+ Länder (OpenHolidays + Nager.Date), Regionen in Landessprache.
- Länderüblicher markierter Wochentag (Intl weekInfo).
- Zweite Jahreszählung (Ära) für Japan (令和), Taiwan (民國), Thailand (พ.ศ.) — ans gewählte
  Land gekoppelt, im Kalender (über dem Jahr) **und** als UI-Hinweis; im PDF als Bild eingebettet.
- Nicht-lateinische Labels (z. B. 1月, 令和8) auch im **PDF** (als vom Browser gerenderte Bilder).
- **Overlay 2:** zweites, unabhängiges Land/Region mit eigenen Feiertagen/Ferien; bei
  Doppelbelegung **diagonal geteilte Kästchen** (oben-links Ebene 1, unten-rechts Ebene 2).
  Standardfarben blass-grün `#c9e8c9` / blass-blau `#c9d9f4`, konfigurierbar.
- 3-Jahres-Vorschau zeigt die 3 Kalender nebeneinander; Standardjahr = heute + 1 Monat.
- **Eigene Termine („# Eigene"):** Land = „# Eigene" → zwei Textfelder (Feiertage/Ferien),
  toleranter Datums-Parser (Einzeltage + Bereiche, mehrere Formate); füllt jede Daten-Lücke.
- **Querformat (transponiert):** Tage als Spalten, Monate als Reihen; Druck als A4 **hoch**
  mit Kalendern **untereinander gestapelt**. Umschalter „Layout" (Hoch/Quer).
- Dark Mode (UI dunkel, Vorschau gedimmt, Export weiß); Auto-Speichern (localStorage);
  Live-Demo (GitHub Pages), Footer mit Repo + Ko-fi.
- **Monats-Matrix (komplett, SVG + PDF):** Layout „Monatsmatrix 3×4/4×3" — 12 echte Wochen-
  Mini-Kalender (Spalten Mo–So); Feiertage/Ferien/Overlay-2/Eigene + markierter Wochentag (rot),
  Monatsnamen & Wochentagskürzel in UI-Sprache (JA als CJK-Bilder im PDF). **PDF:** feste
  Zellgröße (5 mm, maßstabstreu), max. 2 Jahres-Matrizen pro Seite — 4×3 A4-hoch übereinander,
  3×4 A4-quer nebeneinander; „3 Jahre" fällt auf 2 zurück. **Einzelne Matrix** → kleinstes
  passendes Seitenformat (A5, bei kleiner Zelle A6), damit der ausgeschnittene Kalender locker passt.
- **Jahreszahl ausblenden** (inkl. Ära-Helper) als Option; Ära folgt Land **oder** UI-Sprache.
- Konfigurierbar: Kästchengröße, Farben, Strichstärken.

- **Wochenbeginn** (umbenannt von „markierter Wochentag"): Option wählt den Wochen-Start
  (Default Montag; landesüblich via Intl weekInfo). Matrix-Spalten + markierter/roter Tag richten
  sich danach; im Pixel-Gitter sitzt der Trennstrich am Wochenende davor (wie gehabt).
- **Jahr links** beim 4×3 (gestapelt, vertikal zentriert) statt oben — nutzt die Breite, macht
  den Block flacher; 3×4 behält das Jahr oben.

## Offene Features / Ideen

- Alternative Ferien-Quellen pro Land — nur falls es saubere, CORS-fähige APIs gibt; Regionen
  kämen je Provider unterschiedlich (Liste müsste beim Wechsel neu laden). Eher Nische, niedrige Prio.

## Bewusst ausgeklammert

- Strukturell andere Kalender (islamisch, hebräisch, chinesisch) — anderes Monatsraster.
- Echte CJK-Vektorschrift im PDF (statt Bild) — bräuchte MB-Font-Einbettung.
