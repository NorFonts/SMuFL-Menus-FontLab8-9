# Attribution and third-party notices

**FontLab adaptation developed by Nor Eddine Bahha — [NorFonts](https://norfont.com/).**

**SMuFL for FontLab 8 & 9** is an independent FontLab encoding-list generator adapted from publicly available SMuFL classification metadata.

## Upstream classification data

- Project: [Shinianqi/SMuFL-Glyphs4](https://github.com/Shinianqi/SMuFL-Glyphs4)
- Upstream author/maintainer: Shinianqi
- Runtime sources used by this generator: `data/upstream/glyphnames.json`, `data/upstream/classes.json`, `data/upstream/ranges.json`, and `data/layout/legacy.json` from the upstream `main` branch.
- Upstream project states Apache-2.0 licensing for its exporter and certain generated metadata. Some other optional/reference data in the upstream repository has different licensing (e.g. OFL-1.1). Consult [the upstream LICENSE and NOTICE](https://github.com/Shinianqi/SMuFL-Glyphs4) for the applicable licenses and attribution.

The upstream data is downloaded at runtime; the JSON files are **not bundled** in this repository. The generator's source-data validation prevents unexpected metadata layouts from being installed, but an update to upstream `main` could change the resulting lists.

## Standard Music Font Layout

SMuFL (Standard Music Font Layout) provides the glyph specification and metadata reference used by the music notation community: https://www.smufl.org/ and https://github.com/w3c-cg/smufl.

## Independence

This FontLab adaptation is not affiliated with, maintained by, or endorsed by Shinianqi, Glyphs, FontLab, or the W3C Music Notation Community Group. Third-party names and materials remain with their respective owners.