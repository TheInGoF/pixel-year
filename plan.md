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
- Konfigurierbar: Kästchengröße, Farben, Strichstärken.

## Offene Features / Ideen

- **Eigene Zeiträume (manuelles Overlay).** Lücken bei Schulferien (z. B. Schweden, Lettland —
  dort legen Kommunen die Ferien lokal fest, OpenHolidays hat keinen Datensatz; ebenso Japan)
  ließen sich mit benutzerdefinierten Datumsbereichen + Farbe füllen. Würde *jede* Lücke
  schließen und wäre allgemein nützlich (eigene Urlaube/Termine eintragen). Passt zur Overlay-Logik.
- Alternative Ferien-Quellen pro Land (nur falls es saubere APIs gibt) — eher brüchig, niedrige Prio.

## Bewusst ausgeklammert

- Strukturell andere Kalender (islamisch, hebräisch, chinesisch) — anderes Monatsraster.
- Echte CJK-Vektorschrift im PDF (statt Bild) — bräuchte MB-Font-Einbettung.
