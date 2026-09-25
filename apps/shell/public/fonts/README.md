# Self-hosted fonts

Downloaded once by `scripts/nexus-fetch-fonts.mjs` from the subsetted woff2 files Google's font API serves; hashes are in `manifest.json`. The page must not contact Google.

| Font | Files | Licence |
|---|---|---|
| Inter (variable, latin and latin-ext) | `inter-*.woff2` | SIL Open Font License 1.1, copyright The Inter Project Authors |
| JetBrains Mono (variable, latin and latin-ext) | `jetbrains-mono-*.woff2` | SIL Open Font License 1.1, copyright The JetBrains Mono Project Authors |
| Material Symbols Outlined (subset to the glyphs the app names) | `material-symbols-outlined-icon-subset-*.woff2` | Apache License 2.0, copyright Google |

The fonts are attributed in the repository's `THIRD_PARTY_NOTICES.md` and listed in `licences/components.json`. The full licence texts still have to be added before any release.
