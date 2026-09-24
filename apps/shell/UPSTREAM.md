# Upstream and strip log

This folder is a stripped fork of **God's Eye View** by Bilawal Sidhu, <https://github.com/bilawalsidhu/gods-eye-view>, imported at commit **`f01b6a5`** ("fix(ui): stop panel glows from adding scrollbars to the narrow-screen rails (#699)"). Its MIT licence is in `LICENSE`. The MIT grant covers the source code only; upstream states that its third-party data and assets are excluded. See `THIRD_PARTY_NOTICES.md` at the repository root.

Plan: `docs/superpowers/plans/2026-09-24-m5-visual-shell.md`. Branch: `m5-shell`. Each step below is one commit.

## What was left out of the import (deviations from "unmodified")

- `.git`, `node_modules`, `build`: not source.
- `docs/` (69 MB of demonstration GIFs and pages) and `.github/`: not needed to run or strip the app.
- `src/data/`, `public/models/`, `public/events/` are **on disk but ignored by git** (`.gitignore` here). They are upstream's bundled datasets, 3D models and event media, whose licences are not cleared for this repository. The app still needs them to start until the strip steps that own them remove the code that reads them; each such step deletes its files. They never enter git history.

## Step log

| Step | What changed | Tests | Smoke | Notes |
|---|---|---|---|---|
| A1 | Imported the reference code unmodified (apart from the exclusions above) | not yet run | not yet run | 961 tracked files |
