# SOX Sample Selector

A Claude Code **subagent** that turns a control population into a defensible SOX 404 test
sample.

## What it solves
Sample selection needs to be consistent, reproducible, and documented for review. This
agent applies a stated sampling method (attribute/random/interval), records the seed and
rationale, and outputs a workpaper-ready selection.

## Output
- The selected sample rows.
- A methodology note (population size, method, confidence, seed).
- A reviewer summary.

## Confidentiality
Ships with **synthetic** sample data only. Point it at your own (non-client) population to try it.
