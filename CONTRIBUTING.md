# Contributing

Bug reports and documentation improvements are welcome. When reporting an installation issue, include your FontLab version, Python version, whether `PREVIEW` succeeded, the exact Terminal output, and your non-sensitive destination directory names. Do not upload proprietary font files or private user-data folders.

Changes to the installer should preserve the add-only contract: never overwrite, delete, rename, or modify existing encoding files. New behavior that writes FontLab preferences must not be introduced without explicit consent and tested rollback protections.