#!/bin/bash
# Strict add-only: no file replacement, deletion, migration or backups.
cd "$(dirname "$0")" || exit 1
printf '\n=================================================================\n'
printf ' SMuFL — Organized Collections for FontLab 8 and FontLab 9\n'
printf ' ADD ONLY • NO BACKUPS • NO OVERWRITES • NO DELETIONS\n'
printf '=================================================================\n\n'
printf ' Creates purpose-based sections including:\n'
printf ' Quick, Common, Medieval, Techniques, Microtonal, Percussion,\n'
printf ' Text & Signs, Notes & Rests, Accidentals, Tablature, etc.\n\n'
printf ' The source files are fetched directly from SMuFL-Glyphs4.\n'
printf ' Quit FontLab 8 and 9 before installing.\n\n'
if ! command -v python3 >/dev/null 2>&1; then
    printf 'ERROR: Python 3 (3.9 or newer) was not found.\n'
    read -r -p 'Press Return to close...' _
    exit 1
fi
python3 -B -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)'
if [ "$?" -ne 0 ]; then
    printf 'ERROR: Python 3.9 or later is required. No changes made.\n'
    read -r -p 'Press Return to close...' _
    exit 1
fi
printf 'Type PREVIEW to see groups and proposed additions (no files written).\n'
printf 'Type ADD to add only missing files into BOTH existing Encoding folders.\n'
printf 'Anything else cancels.\n\n'
read -r -p 'Choice: ' choice
case "$choice" in
  PREVIEW) mode=--preview ;;
  ADD) mode=--add ;;
  *) printf '\nCancelled. Nothing was changed.\n'; read -r -p 'Press Return to close...' _; exit 0 ;;
esac
printf '\nBuilding official Glyphs4 catalog...\n'
python3 -B './smufl_organized.py' "$mode"
status=$?
if [ "$status" -eq 0 ]; then
    if [ "$mode" = '--add' ]; then
        printf '\nFinished. Review the ADDED counts for each FontLab version.\n'
        printf 'Reopen FontLab 8 and 9 to inspect the new menu groups.\n'
        printf 'Older groups from previous installers will remain untouched.\n'
    else
        printf '\nPreview completed: no files have been written.\n'
    fi
else
    printf '\nAn error occurred. The program never deletes or replaces existing files.\n'
    printf 'Please send the error output rather than repeatedly running the installer.\n'
fi
read -r -p 'Press Return to close...' _
exit "$status"
