"""Verdict rules for a batch inspection.

This file only holds logic. It knows nothing about web pages or files.
"""

# The acceptance limits table, copied from the brief.
# Each row is: (sample size at least, major limit, minor limit)
# Rows are kept in order from smallest to largest "at least" value.
LIMITS = [
    (1, 0, 1),
    (10, 1, 3),
    (40, 3, 7),
    (150, 6, 13),
    (600, 12, 26),
]


class InvalidSampleSize(ValueError):
    """Raised when the sample size is not a whole number of at least 1."""


def select_row(sample_size):
    """Return the table row (at_least, major_limit, minor_limit) for a sample size.

    Rule R1: use the row with the largest "at least" value that is less than
    or equal to the sample size. We never blend two rows together.
    """
    # bool is technically a number in Python (True == 1), so reject it explicitly.
    if isinstance(sample_size, bool) or not isinstance(sample_size, int):
        raise InvalidSampleSize(
            f"Sample size must be a whole number, got {sample_size!r}."
        )
    # Rule R4: anything below 1 is invalid.
    if sample_size < 1:
        raise InvalidSampleSize(
            f"Sample size must be at least 1, got {sample_size}."
        )

    chosen = LIMITS[0]
    for row in LIMITS:
        if row[0] <= sample_size:
            chosen = row  # keep going; a later row may fit better
        else:
            break  # rows are in order, so no later row can fit
    return chosen


SEVERITIES = ("critical", "major", "minor")


def compute_verdict(sample_size, severities):
    """Decide ACCEPT or REJECT for an inspection.

    sample_size: a whole number, at least 1.
    severities:  a list with one entry per defect, e.g. ["major", "minor", "major"].

    Returns a dict with the verdict and the numbers behind it, so the page can
    show *why*. If the sample size is invalid this raises InvalidSampleSize and
    gives back no verdict at all (rule R4).
    """
    # Raises InvalidSampleSize for bad input, before we count anything.
    _, major_limit, minor_limit = select_row(sample_size)

    for severity in severities:
        if severity not in SEVERITIES:
            raise ValueError(f"Unknown severity: {severity!r}")

    critical = severities.count("critical")
    major = severities.count("major")
    minor = severities.count("minor")

    # Rule R2: REJECT if any of these is true. Note "greater than" (>), not ">=":
    # a count that lands exactly on the limit is still acceptable.
    rejected = critical >= 1 or major > major_limit or minor > minor_limit

    # Rule R3: otherwise ACCEPT (this includes zero defects).
    return {
        "verdict": "REJECT" if rejected else "ACCEPT",
        "critical": critical,
        "major": major,
        "minor": minor,
        "major_limit": major_limit,
        "minor_limit": minor_limit,
    }
