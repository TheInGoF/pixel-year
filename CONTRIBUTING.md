# Contributing to Pixel Year

Thanks for helping out! Pixel Year is a single-file, vanilla **HTML/JS** app — no build step,
no framework, no dependencies. Open `pixel-year.html` in a browser and you're running it.

## Translations are especially welcome 🌍

The UI is available in **27 languages**. Six were written/checked by hand
(**en, de, fr, it, es, ja**); the other **21 were machine-translated and not yet reviewed by a
native speaker**:

> bg · hr · cs · da · nl · et · fi · el · hu · ga · lv · lt · mt · pl · pt · ro · sk · sl · sv · lb · nb

If one of these is your language, please fix anything that sounds off — even a single label helps.

**How to fix a translation**

1. Open [`i18n.js`](i18n.js) and find your language object (e.g. `pl: { … }`).
2. Edit the **values** only. Keep:
   - the **keys** unchanged,
   - placeholders intact: `{name}` `{year}` `{cell}` `{max}` `{err}`,
   - the leading `# ` on `customCountry` and the date examples / line breaks in `customHint`,
   - `"Year in Pixels"` in English.
3. All languages must have the **same set of keys**. Quick check:
   ```bash
   node -e 'const I=require("./i18n.js");const n=Object.keys(I.en).length;console.log(Object.entries(I).filter(([l,o])=>Object.keys(o).length!==n))'
   ```
   (Empty output = all consistent.)
4. Open a Pull Request, or just open a **Translation issue** with your suggestions.

> Note: month/day names in the calendar grid are **not** translated by hand — they come from the
> browser's `Intl` locale data, so they're already correct per language.

## Code / bugs / features

- The app is `pixel-year.html`. UI strings live in `i18n.js`, the country list in `countries.js`
  (generated from `catalog.json` by `tools/build_catalog.py`).
- Holiday data comes live from the **OpenHolidays** and **Nager.Date** APIs.
- Keep it **dependency-free** and offline-friendly (the grid/SVG must work without internet;
  only holiday/region data is fetched online).
- The printed output (SVG / PDF) must stay **true to scale in millimetres** and **pure white** —
  screen-only styling (e.g. dark mode) must never change the export.
- Syntax check before a PR:
  ```bash
  node -e 'const fs=require("fs");new Function([...fs.readFileSync("pixel-year.html","utf8").matchAll(/<script>([\s\S]*?)<\/script>/g)].pop()[1]);console.log("OK")'
  ```
- For larger changes, please open an issue first to discuss.

## License

By contributing you agree that your contributions are licensed under the project's
**GNU GPL-3.0** (see [LICENSE](LICENSE)).
