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


if __name__ == "__main__":
    unittest.main()
