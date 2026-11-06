# Quality Inspector

A small website for factory quality inspections. An inspector starts an inspection for a batch (batch ID and sample size), records each defect found (critical, major or minor, with a short description), sees the list of defects so far, and gets a verdict of ACCEPT or REJECT. The verdict comes from the acceptance-limits table in the brief, is recomputed from the recorded defects every time the page loads, and is shown next to a small table of each count against its limit. An invalid sample size shows a clear error and no verdict. Data is saved in a JSON file; there is no database, login or styling.

## What you need
- Python 3 (developed and tested on Python 3.13)
- Nothing else. Flask is installed by the command below.

## Install
Open a terminal in the project folder (the one that contains `app.py`) and run:

```bash
python -m pip install -r requirements.txt
```

On macOS or Linux, use `python3` instead of `python` in every command in this file.

## Run the website

```bash
python app.py
```

Then open http://127.0.0.1:5000 in your browser. Press Ctrl+C in the terminal to stop it.

1. **Start an inspection:** type a batch ID and a sample size (a whole number from 1 to 1,000,000).
2. **Record a defect:** pick a severity and type a short description.
3. **Defects recorded so far:** the list grows as you add defects.
4. **Verdict:** ACCEPT or REJECT, with each count shown against its limit.

The current inspection is saved in `inspection.json` in the project folder, so it survives a page refresh or a restart. Delete that file to start from a blank site. Starting a new inspection replaces the old one.

## Run the tests

```bash
python -m unittest -v
```

This runs 41 tests, using only Python's built-in `unittest`. The tests save to temporary files, so they never touch your real `inspection.json`.

- `test_verdict.py` tests the rules: the six required cases, zero defects, invalid sample sizes, row selection, and every limit in the table.
- `test_app.py` tests the website: the same cases entered through the forms, plus error messages, saving, and escaping of typed text.

## Files

| File | What it does |
|---|---|
| `verdict.py` | The limits table and the ACCEPT/REJECT rule. Plain logic, no web code. |
| `store.py` | Saves and loads the inspection in `inspection.json`. |
| `app.py` | The Flask website. |
| `templates/index.html` | The single page. |
| `test_verdict.py`, `test_app.py` | Automated tests. |
| `DECISIONS.md` | Where the AI went wrong, what was left out, what was ambiguous, and what the tests don't cover. |
| `session-log.md` | The AI session this project was built in. |

## Time spent
Roughly 4 hours.

## AI session
Built with Claude Code. The full session is committed to this repository as [`session-log.md`](session-log.md).
