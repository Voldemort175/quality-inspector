"""Saving and loading the current inspection in a JSON file.

Only one inspection exists at a time. Defects can be added but never
edited or deleted (the brief says those are out of scope).
"""

import json
import os

from verdict import SEVERITIES, select_row

# By default the data file sits next to this code. Every function accepts a
# different path so that tests can use a temporary file instead.
DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inspection.json")


class NoInspectionError(Exception):
    """Raised when a defect is added before any inspection was started."""


def load_inspection(path=DEFAULT_PATH):
    """Return the saved inspection as a dict, or None if none has been started."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(inspection, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(inspection, f, indent=2)


def start_inspection(batch_id, sample_size, path=DEFAULT_PATH):
    """Start a new inspection. Replaces any earlier one.

    Raises ValueError for an empty batch ID, and InvalidSampleSize (a kind of
    ValueError) for a sample size that is not a whole number of at least 1.
    Nothing is saved if the input is bad.
    """
    batch_id = str(batch_id).strip()
    if not batch_id:
        raise ValueError("Batch ID must not be empty.")

    select_row(sample_size)  # raises InvalidSampleSize if the size is bad

    inspection = {"batch_id": batch_id, "sample_size": sample_size, "defects": []}
    _save(inspection, path)
    return inspection


def add_defect(severity, description, path=DEFAULT_PATH):
    """Record one defect on the current inspection and return the inspection.

    Raises NoInspectionError if no inspection was started, and ValueError for
    an unknown severity or an empty description.
    """
    inspection = load_inspection(path)
    if inspection is None:
        raise NoInspectionError("Start an inspection before recording defects.")

    severity = str(severity).strip().lower()
    if severity not in SEVERITIES:
        raise ValueError(f"Severity must be one of: {', '.join(SEVERITIES)}.")

    description = str(description).strip()
    if not description:
        raise ValueError("Defect description must not be empty.")

    inspection["defects"].append({"severity": severity, "description": description})
    _save(inspection, path)
    return inspection
