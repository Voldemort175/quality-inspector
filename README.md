# Quality Inspector

A small website for factory quality inspections. An inspector starts an inspection for a batch (batch ID and sample size), records each defect found (critical, major or minor, with a short description), sees the list of defects so far, and gets a verdict of ACCEPT or REJECT. The verdict comes from the acceptance-limits table in the brief, is recomputed from the recorded defects every time the page loads, and is shown next to a small table of each count against its limit. An invalid sample size shows a clear error and no verdict. Data is saved in a JSON file; there is no database, login or styling.

## What you need
- Git
- Python 3 (developed and tested on Python 3.13)
- Nothing else. Flask is installed by the install command below.

On macOS or Linux, use `python3` instead of `python` in every command in this file.

## Install
Clone the repository and go into its folder:

```bash
git clone https://github.com/Voldemort175/quality-inspector.git
cd quality-inspector
```

Then install the one dependency (Flask):

```bash
python -m pip install -r requirements.txt
```

## Run the website
From inside the `quality-inspector` folder:

```bash
python app.py
```

Then open http://127.0.0.1:5000 in your browser. Press Ctrl+C in the terminal to stop it.

1. **Start an inspection:** type a batch ID and a sample size (a whole number from 1 to 1,000,000).
2. **Record a defect:** pick a severity and type a short description.
3. **Defects recorded so far:** the list grows as you add defects.
4. **Verdict:** ACCEPT or REJECT, with each count shown against its limit.

The current inspection is saved in `inspection.json` in the project folder, so it survives a page refresh or a restart. Delete that file to start from a blank site. Starting a new inspection replaces the old one.

## How the verdict is calculated

The limits come from this table, using the sample size of the inspection:

| Sample size (at least) | Major limit | Minor limit |
|---|---|---|
| 1 | 0 | 1 |
| 10 | 1 | 3 |
| 40 | 3 | 7 |
| 150 | 6 | 13 |
| 600 | 12 | 26 |

**Step 1: pick the row.** Use the row with the largest "at least" value that is less than or equal to the sample size. Rows are never blended together.
- Sample size 39 uses the **10** row (limits 1 and 3).
- Sample size 40 uses the **40** row, not the 10 row (limits 3 and 7).
- Sample size 100 uses the **40** row (limits 3 and 7).
- Sample size 900 uses the **600** row (limits 12 and 26).

**Step 2: decide.** The batch is **REJECT** if any of these is true:
- there is **1 or more** critical defect, or
- the number of major defects is **greater than** the major limit, or
- the number of minor defects is **greater than** the minor limit.

Otherwise the batch is **ACCEPT**. A count that lands exactly on a limit is still acceptable (for sample size 40, 3 major defects is ACCEPT and 4 is REJECT). An inspection with no defects is ACCEPT.

**Invalid sample sizes.** A sample size below 1, above 1,000,000, or not a whole number is refused with a clear error, and no verdict is shown.

## Run the tests
From inside the `quality-inspector` folder (after the install step above):

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
