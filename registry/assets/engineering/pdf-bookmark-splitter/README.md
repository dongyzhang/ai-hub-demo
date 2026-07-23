# PDF Bookmark Splitter

A Claude Code **skill** that splits a large PDF into one file per top-level bookmark.

## What it solves
Teams routinely receive 200+ page PDFs (reports, filings, appendices) that need to be
broken into per-section files. This skill reads the PDF outline and emits one PDF per
bookmark, named after the bookmark title.

## Usage
Drop the skill into `.claude/skills/`, then ask Claude Code:

> "Split `report.pdf` by its bookmarks."

## How it works
- Reads the PDF outline tree.
- Maps each top-level bookmark to a page range.
- Writes `NN - <Bookmark Title>.pdf` for each range.

## Notes
Contains no client material — works on any PDF you point it at.
