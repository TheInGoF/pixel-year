#!/usr/bin/env python3
"""
Pixel Year -- Jahreskalender als Gitter ("Year in Pixels"), massstabsgetreu in Millimetern.

Spalten = Monate (Jan..Dez), Zeilen = Tage 1..31.
Roter Strich = Grenze Sonntag->Montag (auf der Unterkante der Sonntags-Zeile).
Unterer Rand: fette Stufenkontur entlang der gueltigen Tage; fehlende Tage offen.

Masse (Druck 1:1):
    Tageskaestchen      5 x 5  mm
    linke Tages-Spalte 10 x 5  mm
    Monatskopf-Hoehe         5  mm
    Jahreszahl-Feld    10 x 10 mm

Aufruf:
    python pixel_year.py 2027
    python pixel_year.py 2027 2028 2029
    python pixel_year.py 2027 --out meins.svg
"""
import calendar
import datetime as dt
import argparse
import os
import sys

MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

CELL_W   = 5.0
CELL_H   = 5.0
LABEL_W  = 10.0
HEADER_H = 5.0
TITLE_H  = 10.0
PAD      = 5.0

SW_OUTER = 0.6   # aeusserer Rahmen / fette Stufenkontur
SW_THICK = 0.4
SW_THIN  = 0.1   # normale Gitterlinien
MARK_COLOR = "#c30000"
MARK_W   = 0.5

# Schriftgroessen (skalieren mit der Kaestchengroesse, Basis = 5 mm)
FS_YEAR  = 9.0
FS_MONTH = 3.3
FS_DAY   = 3.0


def hex_rgb(color):
    """'#rrggbb' -> (r, g, b) als Floats 0..1 (fuer reportlab)."""
    h = color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))

N_ROWS = 31
N_COLS = 12



def easter_sunday(year):
    """Gauss-Osterformel -> date des Ostersonntags."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    mth = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * mth + 114) // 31
    day = ((h + l - 7 * mth + 114) % 31) + 1
    return dt.date(year, month, day)


# Bundesland-Codes (Argument-Flags) -> Kuerzel
BUNDESLAENDER = {
    "bw": "Baden-Wuerttemberg", "by": "Bayern", "be": "Berlin",
    "bb": "Brandenburg", "hb": "Bremen", "hh": "Hamburg",
    "he": "Hessen", "mv": "Mecklenburg-Vorpommern", "ni": "Niedersachsen",
    "nw": "Nordrhein-Westfalen", "rp": "Rheinland-Pfalz", "sl": "Saarland",
    "sn": "Sachsen", "st": "Sachsen-Anhalt", "sh": "Schleswig-Holstein",
    "th": "Thueringen",
}


def holidays_for(year, land):
    """Gesetzliche Feiertage je Bundesland -> set von date.
    land = None -> leeres set (keine Feiertage)."""
    if not land:
        return set()
    land = land.lower()
    es = easter_sunday(year)
    karfr = es - dt.timedelta(days=2)
    ostermo = es + dt.timedelta(days=1)
    himmelf = es + dt.timedelta(days=39)
    pfingstmo = es + dt.timedelta(days=50)
    fronleichnam = es + dt.timedelta(days=60)

    # Bundeseinheitliche Feiertage (ueberall)
    hs = {
        dt.date(year, 1, 1),     # Neujahr
        karfr,                   # Karfreitag
        ostermo,                 # Ostermontag
        dt.date(year, 5, 1),     # Tag der Arbeit
        himmelf,                 # Christi Himmelfahrt
        pfingstmo,               # Pfingstmontag
        dt.date(year, 10, 3),    # Tag der Deutschen Einheit
        dt.date(year, 12, 25),   # 1. Weihnachtstag
        dt.date(year, 12, 26),   # 2. Weihnachtstag
    }

    # Laenderspezifische Zusaetze
    hl3koenige = dt.date(year, 1, 6)        # Heilige Drei Koenige
    intfrauentag = dt.date(year, 3, 8)      # Internationaler Frauentag
    weltkindertag = dt.date(year, 9, 20)    # Weltkindertag (TH)
    reformationstag = dt.date(year, 10, 31)
    allerheiligen = dt.date(year, 11, 1)
    mariaehimmelf = dt.date(year, 8, 15)    # Mariae Himmelfahrt

    def busstag(y):
        # Buss- und Bettag: Mittwoch vor dem 23.11.
        d = dt.date(y, 11, 23)
        while d.weekday() != 2:  # 2 = Mittwoch
            d -= dt.timedelta(days=1)
        return d

    extra = {
        "bw": {hl3koenige, fronleichnam, allerheiligen},
        "by": {hl3koenige, fronleichnam, allerheiligen, mariaehimmelf},
        "be": {intfrauentag},
        "bb": {reformationstag},
        "hb": {reformationstag},
        "hh": {reformationstag},
        "he": {fronleichnam},
        "mv": {intfrauentag, reformationstag},
        "ni": {reformationstag},
        "nw": {fronleichnam, allerheiligen},
        "rp": {fronleichnam, allerheiligen},
        "sl": {fronleichnam, mariaehimmelf, allerheiligen},
        "sn": {reformationstag, busstag(year)},
        "st": {hl3koenige, reformationstag},
        "sh": {reformationstag},
        "th": {weltkindertag, reformationstag},
    }
    hs |= extra.get(land, set())
    return hs


# ISO 3166-2 Subdivision-Codes fuer OpenHolidays (Schulferien)
ISO_SUBDIV = {
    "bw": "DE-BW", "by": "DE-BY", "be": "DE-BE", "bb": "DE-BB",
    "hb": "DE-HB", "hh": "DE-HH", "he": "DE-HE", "mv": "DE-MV",
    "ni": "DE-NI", "nw": "DE-NW", "rp": "DE-RP", "sl": "DE-SL",
    "sn": "DE-SN", "st": "DE-ST", "sh": "DE-SH", "th": "DE-TH",
}

SCHOOL_FILL = "#ffe9a8"   # gelb fuer Schulferien


def school_holidays(year, land):
    """Schulferien via OpenHolidays API -> set von date.
    Braucht Internet. Bei Fehler: leeres set + Warnung."""
    if not land:
        return set()
    subdiv = ISO_SUBDIV.get(land.lower())
    if not subdiv:
        return set()
    import urllib.request, urllib.parse, json
    base = "https://openholidaysapi.org/SchoolHolidays"
    params = {
        "countryIsoCode": "DE",
        "subdivisionCode": subdiv,
        "languageIsoCode": "DE",
        "validFrom": f"{year}-01-01",
        "validTo": f"{year}-12-31",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    days = set()
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.load(r)
        for item in data:
            d0 = dt.date.fromisoformat(item["startDate"])
            d1 = dt.date.fromisoformat(item["endDate"])
            d = d0
            while d <= d1:
                if d.year == year:
                    days.add(d)
                d += dt.timedelta(days=1)
    except Exception as e:
        print(f"  [Warnung] Ferien konnten nicht geladen werden ({e}). "
              f"Kalender wird ohne Ferien erstellt.")
    return days


HOLIDAY_FILL = "#f4c9c9"  # dezentes Rot zum Hinterlegen der Feiertagszelle

def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def build_svg(year, weekday=6, land=None, ferien=None):
    grid_w = LABEL_W + N_COLS * CELL_W
    grid_h = HEADER_H + N_ROWS * CELL_H
    W = grid_w + 2 * PAD
    H = TITLE_H + grid_h + 2 * PAD

    x0  = PAD
    y0  = PAD + TITLE_H
    gx0 = x0 + LABEL_W
    gy0 = y0 + HEADER_H

    hols = holidays_for(year, land)
    ferien = ferien if ferien is not None else set()
    ferien = ferien if ferien is not None else set()
    holiday_cells = []
    ferien_cells = []
    for c in range(N_COLS):
        month = c + 1
        for day in range(1, days_in_month(year, month) + 1):
            d = dt.date(year, month, day)
            fx = gx0 + c * CELL_W
            fy = gy0 + (day - 1) * CELL_H
            if d in ferien:
                ferien_cells.append((fx, fy))
            if d in hols:
                holiday_cells.append((fx, fy))

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" '
             f'font-family="Arial, sans-serif">')
    s.append(f'<rect width="{W}" height="{H}" fill="white"/>')

    # Ferien (gelb) zuerst, dann Feiertage (rot) darueber -- beide unter dem Gitter
    for fx, fy in ferien_cells:
        s.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{CELL_W}" height="{CELL_H}" '
                 f'fill="{SCHOOL_FILL}"/>')
    for fx, fy in holiday_cells:
        s.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{CELL_W}" height="{CELL_H}" '
                 f'fill="{HOLIDAY_FILL}"/>')

    # Jahreszahl
    digits = list(str(year))
    span = N_COLS * CELL_W
    step = span / len(digits)
    ty = PAD + TITLE_H * 0.8
    for i, d in enumerate(digits):
        cx = gx0 + step * (i + 0.5)
        s.append(f'<text x="{cx:.2f}" y="{ty:.2f}" font-size="{FS_YEAR}" font-weight="bold" '
                 f'text-anchor="middle">{d}</text>')

    # Monatskopf-Buchstaben
    for c in range(N_COLS):
        cx = gx0 + c * CELL_W + CELL_W / 2
        cy = y0 + HEADER_H * 0.72
        s.append(f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="{FS_MONTH}" font-weight="bold" '
                 f'text-anchor="middle">{MONTHS[c]}</text>')

    # Tageszahlen links
    for r in range(N_ROWS):
        cx = x0 + LABEL_W / 2
        cy = gy0 + r * CELL_H + CELL_H * 0.72
        s.append(f'<text x="{cx:.2f}" y="{cy:.2f}" font-size="{FS_DAY}" font-weight="bold" '
                 f'text-anchor="middle">{r+1}</text>')

    # --- duenne Innen-Gitterlinien ---
    # vertikale Spaltentrenner (nur bis zum jeweils letzten gueltigen Tag der ANGRENZENDEN Zelle)
    # Wir zeichnen vertikale Linien segmentweise pro Reihe, damit unten nichts ueber die Stufe hinausragt.
    # Einfacher: vertikale Linien gehen bis max. Tag der beiden angrenzenden Spalten.
    # Label/Kopf-Trenner
    s.append(f'<line x1="{gx0}" y1="{y0}" x2="{gx0}" y2="{gy0 + 31*CELL_H}" '
             f'stroke="black" stroke-width="{SW_THIN}"/>')
    # innere vertikale Trenner zwischen Monatsspalten
    for c in range(1, N_COLS):
        left_dim  = days_in_month(year, c)      # Spalte c-1 (1-indexed = c)
        right_dim = days_in_month(year, c + 1)
        bottom_day = max(left_dim, right_dim)
        x = gx0 + c * CELL_W
        y_end = gy0 + bottom_day * CELL_H
        s.append(f'<line x1="{x}" y1="{gy0}" x2="{x}" y2="{y_end}" '
                 f'stroke="black" stroke-width="{SW_THIN}"/>')

    # horizontale Tageslinien (Unterkanten), segmentweise -> Stufen unten
    for r in range(N_ROWS):
        day = r + 1
        yb = gy0 + (r + 1) * CELL_H
        for c in range(N_COLS):
            month = c + 1
            dim = days_in_month(year, month)
            # Innenlinie nur zeichnen, wenn NACH diesem Tag noch ein Tag kommt (sonst ist es die fette Stufe)
            if day < dim:
                xleft = gx0 + c * CELL_W
                xright = xleft + CELL_W
                s.append(f'<line x1="{xleft}" y1="{yb}" x2="{xright}" y2="{yb}" '
                         f'stroke="black" stroke-width="{SW_THIN}"/>')
        # Label-Spalte (immer voll)
        if day < N_ROWS:
            s.append(f'<line x1="{x0}" y1="{yb}" x2="{gx0}" y2="{yb}" '
                     f'stroke="black" stroke-width="{SW_THIN}"/>')

    # Trennlinie unter dem Monatskopf
    s.append(f'<line x1="{x0}" y1="{gy0}" x2="{x0+grid_w}" y2="{gy0}" '
             f'stroke="black" stroke-width="{SW_THICK}"/>')

    # --- aeusserer Rahmen oben/links/rechts/Label ---
    # oben
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x0+grid_w}" y2="{y0}" '
             f'stroke="black" stroke-width="{SW_OUTER}"/>')
    # links
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{gy0 + 31*CELL_H}" '
             f'stroke="black" stroke-width="{SW_OUTER}"/>')
    # rechts (volle Hoehe, Dez hat 31 Tage)
    s.append(f'<line x1="{x0+grid_w}" y1="{y0}" x2="{x0+grid_w}" y2="{gy0 + 31*CELL_H}" '
             f'stroke="black" stroke-width="{SW_OUTER}"/>')
    # Label-Spalte Unterkante (Tag 31 existiert in der Label-Spalte immer)
    s.append(f'<line x1="{x0}" y1="{gy0+31*CELL_H}" x2="{gx0}" y2="{gy0+31*CELL_H}" '
             f'stroke="black" stroke-width="{SW_OUTER}"/>')

    # --- fette Stufenkontur unten: pro Spalte Unterkante bei dim, + vertikale Stufen ---
    for c in range(N_COLS):
        month = c + 1
        dim = days_in_month(year, month)
        x_l = gx0 + c * CELL_W
        x_r = x_l + CELL_W
        y_bottom = gy0 + dim * CELL_H
        # untere Kante der letzten gueltigen Zelle (fett)
        s.append(f'<line x1="{x_l}" y1="{y_bottom}" x2="{x_r}" y2="{y_bottom}" '
                 f'stroke="black" stroke-width="{SW_OUTER}"/>')
        # vertikale Stufenkanten zu Nachbarspalten, wo Hoehe abweicht
        # linke Kante
        left_dim = days_in_month(year, month - 1) if month > 1 else None
        if left_dim is not None and left_dim != dim:
            y_a = gy0 + min(left_dim, dim) * CELL_H
            y_b = gy0 + max(left_dim, dim) * CELL_H
            s.append(f'<line x1="{x_l}" y1="{y_a}" x2="{x_l}" y2="{y_b}" '
                     f'stroke="black" stroke-width="{SW_OUTER}"/>')
        # rechte Kante
        right_dim = days_in_month(year, month + 1) if month < 12 else None
        if right_dim is not None and right_dim != dim:
            y_a = gy0 + min(right_dim, dim) * CELL_H
            y_b = gy0 + max(right_dim, dim) * CELL_H
            s.append(f'<line x1="{x_r}" y1="{y_a}" x2="{x_r}" y2="{y_b}" '
                     f'stroke="black" stroke-width="{SW_OUTER}"/>')

    # --- Marker: Sonntag -> Unterkante der Sonntags-Zeile (Grenze So/Mo) ---
    # Am Monatsende faellt die Unterkante mit der fetten Aussenkontur zusammen -> kein Strich.
    for c in range(N_COLS):
        month = c + 1
        dim = days_in_month(year, month)
        for day in range(1, dim + 1):
            if day < dim and dt.date(year, month, day).weekday() == weekday:  # 6 = Sonntag
                r = day - 1
                cx = gx0 + c * CELL_W + CELL_W / 2
                cy = gy0 + (r + 1) * CELL_H          # UNTERKANTE der Sonntags-Zeile
                s.append(f'<line x1="{cx-CELL_W*0.34:.2f}" y1="{cy:.2f}" '
                         f'x2="{cx+CELL_W*0.34:.2f}" y2="{cy:.2f}" '
                         f'stroke="{MARK_COLOR}" stroke-width="{MARK_W}" '
                         f'stroke-linecap="round"/>')

    s.append('</svg>')
    return "\n".join(s)



def build_pdf(years, filename, weekday=6, land=None, ferien_map=None):
    """3 Kalender nebeneinander auf EINER A4-quer-Seite (mm-genau)."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import mm
    except ImportError:
        raise SystemExit(
            "FEHLER: Das Paket 'reportlab' wird fuer die PDF-Ausgabe (--pdf, --3) benoetigt,\n"
            "ist aber nicht installiert. Die SVG-Ausgabe (ohne --pdf) funktioniert ohne Zusatzpakete.\n\n"
            "Installation:\n"
            "  macOS:   pip3 install --user --break-system-packages reportlab\n"
            "  Windows: pip install reportlab")

    page_w, page_h = landscape(A4)          # 297 x 210 mm in pt
    c = canvas.Canvas(filename, pagesize=(page_w, page_h))

    cal_w = (LABEL_W + N_COLS * CELL_W)      # 70 mm bei Standard-Kaestchen 5 mm
    cal_h = (TITLE_H + HEADER_H + N_ROWS * CELL_H)  # 170 mm (ohne PAD)

    if isinstance(years, int):
        years = [years]
    n = max(1, min(len(years), 3))
    years = years[:n]

    if n * cal_w > 297 or cal_h > 210:
        print(f"  [Warnung] Bei Kaestchengroesse {CELL_W:g} mm passen {n} Kalender "
              f"({n*cal_w:.0f} x {cal_h:.0f} mm) evtl. nicht auf A4-quer (297 x 210 mm).")
    ferien_map = ferien_map or {}

    total_w = n * cal_w
    gap = (297 - total_w) / (n + 1)          # gleichmaessige Luecken
    top_y = (210 - cal_h) / 2                # vertikal zentriert

    def Y(mm_from_top):
        # SVG: y nach unten. PDF: y nach oben. Wir spiegeln.
        return (210 - mm_from_top) * mm

    for k in range(n):
        year = years[k]
        hols = holidays_for(year, land)
        ferien = ferien_map.get(year, set())
        ox = (gap + k * (cal_w + gap))       # linker Rand dieses Kalenders in mm
        oy = top_y                           # oberer Rand in mm (von oben)

        # Bezugspunkte in mm-von-oben
        title_h = TITLE_H
        gx0 = ox + LABEL_W
        head_top = oy + title_h
        gy0 = head_top + HEADER_H

        def line(x1, y1, x2, y2, w):
            c.setLineWidth(w * mm)
            c.setStrokeColorRGB(0, 0, 0)
            c.line((ox + (x1-ox))*mm if False else x1*mm, Y(y1), x2*mm, Y(y2))

        def rawline(x1, y1, x2, y2, w, rgb=(0,0,0)):
            c.setLineWidth(w * mm)
            c.setStrokeColorRGB(*rgb)
            c.line(x1*mm, Y(y1), x2*mm, Y(y2))

        # --- Ferien (gelb) zuerst ---
        c.setFillColorRGB(*hex_rgb(SCHOOL_FILL))
        for cc in range(N_COLS):
            month = cc + 1
            for day in range(1, days_in_month(year, month) + 1):
                if dt.date(year, month, day) in ferien:
                    fx = gx0 + cc * CELL_W
                    fy = gy0 + (day - 1) * CELL_H
                    c.rect(fx*mm, Y(fy + CELL_H), CELL_W*mm, CELL_H*mm, stroke=0, fill=1)
        # --- Feiertage (rot) darueber ---
        c.setFillColorRGB(*hex_rgb(HOLIDAY_FILL))
        for cc in range(N_COLS):
            month = cc + 1
            for day in range(1, days_in_month(year, month) + 1):
                if dt.date(year, month, day) in hols:
                    fx = gx0 + cc * CELL_W
                    fy = gy0 + (day - 1) * CELL_H
                    c.rect(fx*mm, Y(fy + CELL_H), CELL_W*mm, CELL_H*mm, stroke=0, fill=1)

        # --- Jahreszahl ---
        c.setFillColorRGB(0,0,0)
        digits = list(str(year))
        span = N_COLS * CELL_W
        step = span / len(digits)
        c.setFont("Helvetica-Bold", FS_YEAR*2.83)
        for i, d in enumerate(digits):
            cx = gx0 + step * (i + 0.5)
            c.drawCentredString(cx*mm, Y(oy + title_h*0.8), d)

        # --- Monatskopf ---
        c.setFont("Helvetica-Bold", FS_MONTH*2.83)
        for cc in range(N_COLS):
            cx = gx0 + cc*CELL_W + CELL_W/2
            c.drawCentredString(cx*mm, Y(head_top + HEADER_H*0.72), MONTHS[cc])

        # --- Tageszahlen ---
        c.setFont("Helvetica-Bold", FS_DAY*2.83)
        for r in range(N_ROWS):
            cx = ox + LABEL_W/2
            c.drawCentredString(cx*mm, Y(gy0 + r*CELL_H + CELL_H*0.72), str(r+1))

        # --- duenne Gitterlinien ---
        SW = SW_THIN
        # Label/Kopf vertikaler Trenner
        rawline(gx0, head_top, gx0, gy0 + 31*CELL_H, SW)
        for cc in range(1, N_COLS):
            left_dim  = days_in_month(year, cc)
            right_dim = days_in_month(year, cc+1)
            bottom = max(left_dim, right_dim)
            x = gx0 + cc*CELL_W
            rawline(x, gy0, x, gy0 + bottom*CELL_H, SW)
        # horizontale Innenlinien
        for r in range(N_ROWS):
            day = r+1
            yb = gy0 + (r+1)*CELL_H
            for cc in range(N_COLS):
                dim = days_in_month(year, cc+1)
                if day < dim:
                    xl = gx0 + cc*CELL_W
                    rawline(xl, yb, xl+CELL_W, yb, SW)
            if day < N_ROWS:
                rawline(ox, yb, gx0, yb, SW)
        # Kopf-Trennlinie
        rawline(ox, gy0, gx0 + N_COLS*CELL_W, gy0, SW_THICK)

        # --- aeusserer Rahmen ---
        grid_w = LABEL_W + N_COLS*CELL_W
        rawline(ox, head_top, ox+grid_w, head_top, SW_OUTER)             # oben
        rawline(ox, head_top, ox, gy0 + 31*CELL_H, SW_OUTER)            # links
        rawline(ox+grid_w, head_top, ox+grid_w, gy0+31*CELL_H, SW_OUTER) # rechts
        rawline(ox, gy0+31*CELL_H, gx0, gy0+31*CELL_H, SW_OUTER)        # Label unten

        # --- fette Stufenkontur unten ---
        for cc in range(N_COLS):
            month = cc+1
            dim = days_in_month(year, month)
            xl = gx0 + cc*CELL_W
            xr = xl + CELL_W
            yb = gy0 + dim*CELL_H
            rawline(xl, yb, xr, yb, SW_OUTER)
            ld = days_in_month(year, month-1) if month>1 else None
            if ld is not None and ld != dim:
                ya = gy0 + min(ld,dim)*CELL_H; yb2 = gy0 + max(ld,dim)*CELL_H
                rawline(xl, ya, xl, yb2, SW_OUTER)
            rd = days_in_month(year, month+1) if month<12 else None
            if rd is not None and rd != dim:
                ya = gy0 + min(rd,dim)*CELL_H; yb2 = gy0 + max(rd,dim)*CELL_H
                rawline(xr, ya, xr, yb2, SW_OUTER)

        # --- Sonntagsstriche (Unterkante So-Zeile), Farbe = MARK_COLOR ---
        # Am Monatsende kein Strich (faellt mit der Aussenkontur zusammen).
        for cc in range(N_COLS):
            month = cc+1
            dim = days_in_month(year, month)
            for day in range(1, dim+1):
                if day < dim and dt.date(year, month, day).weekday() == weekday:
                    cx = gx0 + cc*CELL_W + CELL_W/2
                    cy = gy0 + day*CELL_H
                    rawline(cx-CELL_W*0.34, cy, cx+CELL_W*0.34, cy, MARK_W,
                            rgb=hex_rgb(MARK_COLOR))

    c.showPage()
    c.save()

# Verzeichnis, in dem dieses Skript liegt -- dorthin wird die Ausgabe geschrieben,
# unabhaengig davon, von wo aus das Skript gestartet wird (Terminal, Doppelklick, ...).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def out_path(fn):
    """Ausgabedatei neben dem Skript ablegen.
    Ein absoluter Pfad (z.B. via --out) wird unveraendert respektiert."""
    return fn if os.path.isabs(fn) else os.path.join(SCRIPT_DIR, fn)


def norm_hex(color):
    """Validiert '#rrggbb' (auch ohne #) und liefert es mit fuehrendem '#'."""
    h = color.lstrip("#")
    if len(h) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in h):
        raise SystemExit(f"FEHLER: Ungueltige Farbe '{color}'. Erwartet: #rrggbb (z.B. #c30000).")
    return "#" + h.lower()


def apply_style(args):
    """Setzt die globalen Stil-/Mass-Konstanten anhand der CLI-Argumente.
    Die Kaestchengroesse skaliert Label, Kopf, Titel, Rand und Schrift proportional."""
    global CELL_W, CELL_H, LABEL_W, HEADER_H, TITLE_H, PAD
    global SW_OUTER, SW_THICK, SW_THIN, MARK_W, MARK_COLOR, HOLIDAY_FILL, SCHOOL_FILL
    global FS_YEAR, FS_MONTH, FS_DAY

    cell = args.cell
    if cell <= 0:
        raise SystemExit(f"FEHLER: --cell muss groesser als 0 sein (war {cell}).")
    CELL_W = CELL_H = cell
    LABEL_W = 2 * cell
    HEADER_H = cell
    TITLE_H = 2 * cell
    PAD = cell
    factor = cell / 5.0
    FS_YEAR, FS_MONTH, FS_DAY = 9.0 * factor, 3.3 * factor, 3.0 * factor

    SW_OUTER, SW_THICK, SW_THIN, MARK_W = args.sw_outer, args.sw_thick, args.sw_thin, args.mark_w
    MARK_COLOR = norm_hex(args.mark_color)
    HOLIDAY_FILL = norm_hex(args.holiday_fill)
    SCHOOL_FILL = norm_hex(args.school_fill)


def run(argv=None):
    ap = argparse.ArgumentParser(
        description="Year-Grid-Kalender (SVG oder A4-quer-PDF mit 3 Kalendern).")
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--weekday", type=int, default=6,
                    help="0=Mo ... 6=So (Default 6=Sonntag)")
    ap.add_argument("--out", default=None, help="Ausgabedatei (nur bei genau 1 Jahr)")
    ap.add_argument("--pdf", action="store_true",
                    help="A4-quer-PDF mit 3 Kalendern nebeneinander statt SVG")
    # je ein Flag pro Bundesland: --hh, --rp, --bw ...
    for code in BUNDESLAENDER:
        ap.add_argument(f"--{code}", dest="land", action="store_const", const=code,
                        help=f"Feiertage {BUNDESLAENDER[code]}")
    ap.add_argument("--3", dest="triple", action="store_true",
                    help="3 aufeinanderfolgende Jahre ab Startjahr auf 1 A4-Seite (erzwingt PDF)")
    ap.add_argument("--ferien", action="store_true",
                    help="Schulferien (OpenHolidays API, braucht Internet + Bundesland)")
    # --- Aussehen: Kaestchengroesse, Farben, Strichstaerken (Default = bisheriges Layout) ---
    g = ap.add_argument_group("Aussehen")
    g.add_argument("--cell", type=float, default=5.0, metavar="MM",
                   help="Kantenlaenge der Tageskaestchen in mm (Default 5.0; skaliert alles mit)")
    g.add_argument("--mark-color", default="#c30000", metavar="HEX",
                   help="Farbe Sonntagsstrich (Default #c30000)")
    g.add_argument("--holiday-fill", default="#f4c9c9", metavar="HEX",
                   help="Fuellfarbe Feiertage (Default #f4c9c9)")
    g.add_argument("--school-fill", default="#ffe9a8", metavar="HEX",
                   help="Fuellfarbe Schulferien (Default #ffe9a8)")
    g.add_argument("--sw-outer", type=float, default=0.6, metavar="MM",
                   help="Strichstaerke Rahmen/Stufenkontur (Default 0.6)")
    g.add_argument("--sw-thick", type=float, default=0.4, metavar="MM",
                   help="Strichstaerke Kopf-Trennlinie (Default 0.4)")
    g.add_argument("--sw-thin", type=float, default=0.1, metavar="MM",
                   help="Strichstaerke Gitterlinien (Default 0.1)")
    g.add_argument("--mark-w", type=float, default=0.5, metavar="MM",
                   help="Breite Sonntagsstrich (Default 0.5)")
    ap.set_defaults(land=None)
    args = ap.parse_args(argv)

    apply_style(args)

    land = args.land
    suffix = f"_{land}" if land else ""
    if land:
        print(f"Feiertage: {BUNDESLAENDER[land]}")
    else:
        print("Feiertage: keine (kein Bundesland angegeben)")

    def load_ferien(y):
        if not args.ferien:
            return set()
        if not land:
            print("  [Hinweis] --ferien braucht ein Bundesland (z.B. --hh). Wird ignoriert.")
            return set()
        print(f"  Lade Schulferien {BUNDESLAENDER[land]} {y} von OpenHolidays ...")
        f = school_holidays(y, land)
        if f:
            print(f"  {len(f)} Ferientage geladen.")
        return f

    if args.triple:
        # 3 aufeinanderfolgende Jahre ab dem (ersten) Startjahr, PDF erzwungen
        start = args.years[0]
        yrs = [start, start + 1, start + 2]
        ferien_map = {y: load_ferien(y) for y in yrs}
        fn = out_path(args.out if args.out else f"kalender_{yrs[0]}-{yrs[2]}{suffix}_A4.pdf")
        build_pdf(yrs, fn, weekday=args.weekday, land=land, ferien_map=ferien_map)
        print(f"geschrieben: {fn}  (A4 quer, {yrs[0]}-{yrs[2]} nebeneinander)")
        return

    for y in args.years:
        ferien = load_ferien(y)
        if args.pdf:
            fn = out_path(args.out if (args.out and len(args.years) == 1) else f"kalender_{y}{suffix}_A4.pdf")
            build_pdf([y, y, y], fn, weekday=args.weekday, land=land,
                      ferien_map={y: ferien})
            print(f"geschrieben: {fn}  (A4 quer, 3 Kalender)")
        else:
            svg = build_svg(y, args.weekday, land=land, ferien=ferien)
            fn = out_path(args.out if (args.out and len(args.years) == 1) else f"kalender_{y}{suffix}.svg")
            try:
                with open(fn, "w", encoding="utf-8") as f:
                    f.write(svg)
            except OSError as e:
                raise SystemExit(f"FEHLER: Konnte '{fn}' nicht schreiben ({e}).")
            print(f"geschrieben: {fn}  ({len(svg)} bytes)")


def main():
    # Ohne Argumente (z.B. per Doppelklick im Finder/Explorer gestartet):
    # interaktiv nach dem Jahr fragen und das Fenster am Ende offen halten,
    # damit Ausgabe/Fehler sichtbar bleiben und sich das Terminal nicht sofort schliesst.
    interactive = len(sys.argv) == 1
    if interactive:
        print("Year-Grid-Kalender")
        print(f"Ausgabe landet im Ordner: {SCRIPT_DIR}\n")
        try:
            eingabe = input(
                "Jahr(e) und Optionen eingeben\n"
                "  (z.B. '2027'  oder  '2027 --hh'  oder  '2026 --3 --hh --ferien'): ").strip()
        except EOFError:
            eingabe = ""
        argv = eingabe.split()
        if not argv:
            print("Keine Eingabe - nichts zu tun.")
            input("\nZum Schliessen Enter druecken ...")
            return
    else:
        argv = None

    try:
        run(argv)
    except SystemExit as e:
        # argparse oder unsere FEHLER-Meldungen: Text ausgeben, Fenster offen halten
        if e.code not in (0, None):
            print(e.code if isinstance(e.code, str) else f"Abbruch (Code {e.code}).")
        if interactive:
            input("\nZum Schliessen Enter druecken ...")
        return
    except Exception as e:
        print(f"\nFEHLER: {e}")
        if interactive:
            input("\nZum Schliessen Enter druecken ...")
        return

    if interactive:
        input("\nFertig. Zum Schliessen Enter druecken ...")


if __name__ == "__main__":
    main()
