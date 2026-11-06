"""Automated tests for the verdict rules. Run with: python -m unittest -v"""

import unittest

from verdict import InvalidSampleSize, compute_verdict, select_row


class RequiredCases(unittest.TestCase):
    """The six cases listed in the brief."""

    def test_1_size_40_three_major_is_accept(self):
        result = compute_verdict(40, ["major"] * 3)
        self.assertEqual(result["verdict"], "ACCEPT")

    def test_2_size_40_four_major_is_reject(self):
        result = compute_verdict(40, ["major"] * 4)
        self.assertEqual(result["verdict"], "REJECT")

    def test_3_size_39_three_major_is_reject(self):
        # 39 uses the 10 row (major limit 1), not the 40 row.
        result = compute_verdict(39, ["major"] * 3)
        self.assertEqual(result["verdict"], "REJECT")

    def test_4_size_149_six_major_is_reject(self):
        # 149 still uses the 40 row (major limit 3), not the 150 row.
        result = compute_verdict(149, ["major"] * 6)
        self.assertEqual(result["verdict"], "REJECT")

    def test_5_size_150_six_major_is_accept(self):
        result = compute_verdict(150, ["major"] * 6)
        self.assertEqual(result["verdict"], "ACCEPT")

    def test_6_size_60_one_critical_is_reject(self):
        result = compute_verdict(60, ["critical"])
        self.assertEqual(result["verdict"], "REJECT")


class ZeroDefects(unittest.TestCase):
    def test_no_defects_is_accept(self):
        # Rule R3: zero defects is ACCEPT, not blank and not an error.
        result = compute_verdict(40, [])
        self.assertEqual(result["verdict"], "ACCEPT")


class InvalidInput(unittest.TestCase):
    def test_sample_size_below_1_gives_error_and_no_verdict(self):
        # Rule R4: refuse to produce a verdict, and do not crash in some other way.
        for bad_size in (0, -1, -100):
            with self.subTest(sample_size=bad_size):
                with self.assertRaises(InvalidSampleSize):
                    compute_verdict(bad_size, [])

    def test_non_whole_number_sample_size_is_invalid(self):
        for bad_size in (12.5, "40", None, True):
            with self.subTest(sample_size=bad_size):
                with self.assertRaises(InvalidSampleSize):
                    compute_verdict(bad_size, [])

    def test_unknown_severity_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_verdict(40, ["huge"])


class RowSelection(unittest.TestCase):
    """Rule R1: use the row with the largest 'at least' value <= sample size."""

    def test_rows_chosen_from_the_brief(self):
        expected = {
            1: 1,
            9: 1,
            10: 10,
            39: 10,
            40: 40,  # exactly on a row start uses that row, not the one below
            100: 40,
            149: 40,
            150: 150,
            599: 150,
            600: 600,
            900: 600,
        }
        for size, row_start in expected.items():
            with self.subTest(sample_size=size):
                self.assertEqual(select_row(size)[0], row_start)


class ExactLimitEdges(unittest.TestCase):
    """Rule R2: 'greater than', so landing exactly on a limit is still OK."""

    def test_minor_exactly_on_limit_is_accept(self):
        self.assertEqual(compute_verdict(40, ["minor"] * 7)["verdict"], "ACCEPT")

    def test_minor_one_over_limit_is_reject(self):
        self.assertEqual(compute_verdict(40, ["minor"] * 8)["verdict"], "REJECT")

    def test_size_1_allows_one_minor_but_no_major(self):
        self.assertEqual(compute_verdict(1, ["minor"])["verdict"], "ACCEPT")
        self.assertEqual(compute_verdict(1, ["major"])["verdict"], "REJECT")

    def test_result_includes_counts_and_limits(self):
        result = compute_verdict(40, ["major"] * 4 + ["minor"])
        self.assertEqual(result["major"], 4)
        self.assertEqual(result["minor"], 1)
        self.assertEqual(result["critical"], 0)
        self.assertEqual(result["major_limit"], 3)
        self.assertEqual(result["minor_limit"], 7)


class EveryLimitInTheTable(unittest.TestCase):
    """Check every number in the brief's table, not just the row boundaries.

    The expected numbers below are typed in again from the brief, on purpose.
    They are a second, independent copy of the table. If someone mistypes a
    limit in verdict.py, this test will disagree with it and fail.
    """

    # sample size at least: (major limit, minor limit)
    BRIEF_TABLE = {
        1: (0, 1),
        10: (1, 3),
        40: (3, 7),
        150: (6, 13),
        600: (12, 26),
    }

    def test_major_limit_of_every_row(self):
        for size, (major_limit, _) in self.BRIEF_TABLE.items():
            with self.subTest(sample_size=size, major_limit=major_limit):
                on_limit = compute_verdict(size, ["major"] * major_limit)
                over_limit = compute_verdict(size, ["major"] * (major_limit + 1))
                self.assertEqual(on_limit["verdict"], "ACCEPT")  # exactly on is fine
                self.assertEqual(over_limit["verdict"], "REJECT")  # one over is not

    def test_minor_limit_of_every_row(self):
        for size, (_, minor_limit) in self.BRIEF_TABLE.items():
            with self.subTest(sample_size=size, minor_limit=minor_limit):
                on_limit = compute_verdict(size, ["minor"] * minor_limit)
                over_limit = compute_verdict(size, ["minor"] * (minor_limit + 1))
                self.assertEqual(on_limit["verdict"], "ACCEPT")
                self.assertEqual(over_limit["verdict"], "REJECT")

    def test_limits_hold_across_the_whole_row_not_just_its_first_size(self):
        # Last size before the next row starts, plus one size far above the table.
        last_size_of_row = {1: 9, 10: 39, 40: 149, 150: 599, 600: 5000}
        for row_start, size in last_size_of_row.items():
            major_limit, minor_limit = self.BRIEF_TABLE[row_start]
            with self.subTest(sample_size=size):
                self.assertEqual(
                    compute_verdict(size, ["major"] * major_limit)["verdict"], "ACCEPT"
                )
                self.assertEqual(
                    compute_verdict(size, ["major"] * (major_limit + 1))["verdict"],
                    "REJECT",
                )
                self.assertEqual(
                    compute_verdict(size, ["minor"] * minor_limit)["verdict"], "ACCEPT"
                )
                self.assertEqual(
                    compute_verdict(size, ["minor"] * (minor_limit + 1))["verdict"],
                    "REJECT",
                )


if __name__ == "__main__":
    unittest.main()
