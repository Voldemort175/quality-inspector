"""The Quality Inspector website: one page with a few forms.

Run with:  python app.py   then open http://127.0.0.1:5000
"""

import re

from flask import Flask, redirect, render_template, url_for, request

import store
from verdict import MAX_SAMPLE_SIZE, InvalidSampleSize, compute_verdict, too_large_message

app = Flask(__name__)
# Where the inspection is saved. Tests change this to a temporary file.
app.config["DATA_PATH"] = store.DEFAULT_PATH


def parse_sample_size(text):
    """Turn the text typed in the form into a whole number.

    Anything that is not a plain whole number (empty, "abc", "12.5") is invalid.
    A number below 1 is caught later by the verdict rules (rule R4).
    """
    text = (text or "").strip()
    if not re.fullmatch(r"-?\d+", text):
        raise InvalidSampleSize(f"Sample size must be a whole number, got {text!r}.")

    # Python refuses to convert a string of more than 4300 digits into a number
    # (it raises its own confusing error), so we look at the length first.
    # Leading zeros are dropped so "0000040" still counts as 40.
    is_negative = text.startswith("-")
    digits = text.lstrip("-").lstrip("0")
    if len(digits) > len(str(MAX_SAMPLE_SIZE)):
        if is_negative:
            raise InvalidSampleSize("Sample size must be at least 1.")
        raise InvalidSampleSize(too_large_message())

    value = int(digits) if digits else 0
    return -value if is_negative else value


def show_page(error=None, status=200):
    """Draw the page from whatever is saved right now.

    The verdict is recomputed here, from the defects recorded so far, every
    time the page is drawn.
    """
    inspection = store.load_inspection(app.config["DATA_PATH"])
    result = None
    if inspection is not None:
        severities = [d["severity"] for d in inspection["defects"]]
        try:
            result = compute_verdict(inspection["sample_size"], severities)
        except InvalidSampleSize as problem:
            # Rule R4: no verdict for an invalid sample size, just say why.
            error = error or str(problem)
    page = render_template(
        "index.html",
        inspection=inspection,
        result=result,
        error=error,
        severities=("critical", "major", "minor"),
    )
    return page, status


@app.get("/")
def index():
    return show_page()


@app.post("/start")
def start():
    try:
        sample_size = parse_sample_size(request.form.get("sample_size"))
        store.start_inspection(
            request.form.get("batch_id"), sample_size, app.config["DATA_PATH"]
        )
    except ValueError as problem:  # InvalidSampleSize is a kind of ValueError
        return show_page(error=f"Inspection not started. {problem}", status=400)
    return redirect(url_for("index"))


@app.post("/defect")
def defect():
    try:
        store.add_defect(
            request.form.get("severity"),
            request.form.get("description"),
            app.config["DATA_PATH"],
        )
    except (ValueError, store.NoInspectionError) as problem:
        return show_page(error=f"Defect not recorded. {problem}", status=400)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run()
