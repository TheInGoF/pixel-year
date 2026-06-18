#!/usr/bin/env python3
"""
Vorbereitung fuer Pixel Year International:
Zieht von der OpenHolidays-API alle Laender, deren Regionen (Subdivisions) und
Amtssprachen -- und VALIDIERT pro Land, dass auch wirklich Feiertagsdaten
abrufbar sind. Ergebnis: catalog.json (Datenbasis fuer Land-/Region-/Sprachauswahl).

Aufruf:
    python3 tools/build_catalog.py [JAHR]   # JAHR = Testjahr fuer die Validierung

Braucht Internet. Schreibt catalog.json neben die HTML/das Skript.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import datetime as dt

BASE = "https://openholidaysapi.org"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "..", "catalog.json")


def get(path, **params):
    url = path if path.startswith("http") else BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def name_map(name_list):
    """OpenHolidays-Namen [{language, text}] -> {lang: text}."""
    return {n["language"]: n["text"] for n in (name_list or []) if "text" in n}


def flatten_subdivisions(subs):
    """Top-Level + verschachtelte children flach als Liste von {code, name(EN), shortName}."""
    out = []

    def walk(items):
        for s in items or []:
            nm = name_map(s.get("name"))
            out.append({
                "code": s.get("code") or s.get("isoCode"),
                "shortName": s.get("shortName"),
                "name": nm.get("EN") or nm.get("DE") or next(iter(nm.values()), s.get("code")),
            })
            walk(s.get("children"))
    walk(subs)
    # Duplikate (gleicher Code) entfernen, Reihenfolge wahren
    seen, uniq = set(), []
    for s in out:
        if s["code"] and s["code"] not in seen:
            seen.add(s["code"]); uniq.append(s)
    return uniq


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().year
    vf, vt = f"{year}-01-01", f"{year}-12-31"
    print(f"OpenHolidays-Katalog fuer Validierungsjahr {year}\n")

    try:
        countries = get("/Countries", languageIsoCode="EN")
    except Exception as e:
        raise SystemExit(f"FEHLER: /Countries nicht erreichbar ({e}). Internet pruefen.")

    print(f"{len(countries)} Laender von der API gemeldet. Validiere Feiertagsdaten ...\n")
    print(f"{'Land':<26} {'ISO':<5} {'Feiertage':>9}  {'Regionen':>8}  Sprachen")
    print("-" * 70)

    catalog, ok_count, total_subs = [], 0, 0
    for c in sorted(countries, key=lambda x: x.get("isoCode", "")):
        iso = c.get("isoCode")
        names = name_map(c.get("name"))
        langs = c.get("officialLanguages") or []
        en_name = names.get("EN") or names.get("DE") or iso

        # 1) Regionen
        try:
            subs = flatten_subdivisions(get("/Subdivisions", countryIsoCode=iso, languageIsoCode="EN"))
        except Exception:
            subs = []

        # 2) Validierung: kommen wirklich Feiertage zurueck?
        holiday_count, holidays_ok = 0, False
        try:
            hols = get("/PublicHolidays", countryIsoCode=iso, languageIsoCode="EN",
                       validFrom=vf, validTo=vt)
            holiday_count = len(hols)
            holidays_ok = holiday_count > 0
        except Exception:
            holidays_ok = False

        # 3) Schulferien vorhanden? (nur Indikator, nicht zwingend)
        school_ok = False
        try:
            sch = get("/SchoolHolidays", countryIsoCode=iso, languageIsoCode="EN",
                      validFrom=vf, validTo=vt)
            school_ok = len(sch) > 0
        except Exception:
            school_ok = False

        if holidays_ok:
            ok_count += 1
        total_subs += len(subs)

        flag = "OK " if holidays_ok else "-- "
        print(f"{en_name[:25]:<26} {iso:<5} {holiday_count:>6} {flag}  {len(subs):>8}  {','.join(langs)}")

        catalog.append({
            "iso": iso,
            "names": names,
            "officialLanguages": langs,
            "holidaysOk": holidays_ok,
            "holidayCount": holiday_count,
            "schoolHolidaysOk": school_ok,
            "subdivisions": subs,
        })
        time.sleep(0.15)  # hoeflich zur API

    # Nur Laender mit validierten Feiertagsdaten behalten
    usable = [c for c in catalog if c["holidaysOk"]]
    payload = {
        "source": "openholidaysapi.org",
        "validationYear": year,
        "countryCount": len(usable),
        "countries": usable,
    }
    with open(os.path.normpath(OUT), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    all_langs = sorted({l for c in usable for l in c["officialLanguages"]})
    with_school = sum(1 for c in usable if c["schoolHolidaysOk"])
    print("\n" + "=" * 70)
    print(f"Validiert (Feiertage abrufbar): {len(usable)} / {len(countries)} Laender")
    print(f"davon mit Schulferien-Daten:    {with_school}")
    print(f"Regionen insgesamt:             {total_subs}")
    print(f"Amtssprachen (ISO) gesamt:      {len(all_langs)} -> {', '.join(all_langs)}")
    print(f"geschrieben: {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
