# PDF Form Auto-Filler

A Claude Code **skill** for tax teams that fills repetitive PDF forms from a structured
data file (CSV/JSON), and can split a multi-form packet into individual PDFs.

## What it solves
Preparation work often means the same fields typed into dozens of near-identical PDF forms.
This skill maps a data row to form fields and produces one filled PDF per row.

## Usage
> "Fill `form-template.pdf` for every row in `clients.csv`."

## Overlap note
This overlaps with the Engineering team's **PDF Bookmark Splitter** on PDF splitting —
a good candidate for the Hub's duplicate-effort detection to flag for consolidation.
