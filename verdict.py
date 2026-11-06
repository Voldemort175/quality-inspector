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
