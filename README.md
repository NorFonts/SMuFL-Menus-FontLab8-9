# SMuFL for FontLab 8 & 9

**Organized SMuFL encoding collections for FontLab 8 and FontLab 9 (macOS).**

This independent FontLab adaptation takes inspiration from [SMuFL-Glyphs4 by Shinianqi](https://github.com/Shinianqi/SMuFL-Glyphs4) and uses its published SMuFL classification metadata. It generates native `.enc` files grouped by musical function, to help music-font designers browse related glyphs in FontLab's **Encoding** menu.

> **Status: experimental / community project.** The menu has been inspected in FontLab 8; end-to-end operation across FontLab 8 and FontLab 9 installations is not fully verified. Review the preview before installing.

## Features

- Based on approximately **2,940 glyph definitions** from the upstream project.
- **23 music-oriented groups** and approximately **203 encoding collections** (the exact generated count depends on source version and duplicate consolidation).
- Groups for common notation, clefs, notes and rests, accidentals, microtonal music, medieval notation, percussion, techniques, text and signs, and more.
- Uses **Unicode-style glyph names** such as `uniE050` and `uniE0A4` (extended names `uXXXXX` where appropriate).
- **Add-only** `.enc` creation: existing files are skipped, never replaced.
- `PREVIEW` mode shows planned changes without writing files.

## Requirements

- macOS, FontLab 8 and/or FontLab 9.
- Python **3.9+** available as `python3`.
- Internet access to download the source JSON metadata at runtime.
- Existing FontLab Encoding directories.

## Install

1. Quit FontLab 8 and 9.
2. Extract the project ZIP or clone the repository.
3. Double-click **`Add Organized SMuFL to FontLab 8 and 9.command`** (or launch it in Terminal).
4. Enter **`PREVIEW`** and inspect the planned groups, files, and paths.
5. If the result looks right, run the command again and enter **`ADD`**.
6. Reopen FontLab and find the sections in the **Encoding selector**.

Default destination folders:

```text
~/Library/Application Support/FontLab/FontLab 8/Encoding/
~/Library/Application Support/FontLab/FontLab 9/Encoding/
```

You can generate a preview directly in Terminal:

```bash
python3 smufl_organized.py --preview
```

For available command-line options:

```bash
python3 smufl_organized.py --help
```

## Important safety behavior

The existing generator uses exclusive creation for encoding files. It **never overwrites, renames, deletes, or backs up** existing encoding files, and does not edit FontLab preferences or the application bundles. It refuses to install if destination directories do not satisfy its checks. Previous SMuFL encodings remain visible and must be reviewed separately if you choose to remove them manually. Never run old experimental installers or uninstallers as part of this process.

This does **not** restore missing older custom encodings, and it does **not** automatically add items to FontLab's left-hand **Bookmarks** sidebar. It only generates Encoding menu entries. FontLab matches the generated glyph names against those in the opened font; fonts using canonical SMuFL names will need a different mapping.

## Data and credits

The generator downloads JSON metadata from `Shinianqi/SMuFL-Glyphs4` rather than embedding those JSON files in this repository. The metadata is based on the [SMuFL specification](https://www.smufl.org/).

See [NOTICE.md](NOTICE.md) for source attribution and third-party licensing. This repository is a **separate FontLab adaptation**, not an official Glyphs 4 plugin or a W3C/SMuFL endorsed product.

## License

The original adaptation code in this repository is offered under [Apache License 2.0](LICENSE). Third-party content retains its own copyright and license terms; refer to [NOTICE.md](NOTICE.md).