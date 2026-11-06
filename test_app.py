"""Tests that use the website the way a person would: submit forms, read the page.

Run with: python -m unittest -v
Every test saves to its own temporary file, so real data is never touched.
"""

import os
import re
import tempfile
import unittest

import app as app_module


class WebsiteTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        app_module.app.config["DATA_PATH"] = os.path.join(
            self.temp_dir.name, "inspection.json"
        )
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    # --- small helpers that "click the buttons" ---

    def start(self, batch_id, sample_size):
        return self.client.post(
            "/start", data={"batch_id": batch_id, "sample_size": str(sample_size)}
        )

    def add_defect(self, severity, description="something wrong"):
        return self.client.post(
            "/defect", data={"severity": severity, "description": description}
        )

    def page(self):
        return self.client.get("/").get_data(as_text=True)

    def verdict_on_page(self):
        """Return 'ACCEPT' / 'REJECT' as shown on the page, or None if no verdict."""
        match = re.search(r'id="verdict">(\w+)<', self.page())
        return match.group(1) if match else None

    def run_case(self, sample_size, severities):
        """Start an inspection, record the defects, and return the verdict shown."""
        self.start("B-1", sample_size)
        for severity in severities:
            self.add_defect(severity)
        return self.verdict_on_page()


class RequiredCasesThroughTheWebsite(WebsiteTestCase):
    """The six cases from the brief, entered through the forms."""

    def test_1_size_40_three_major_is_accept(self):
        self.assertEqual(self.run_case(40, ["major"] * 3), "ACCEPT")

    def test_2_size_40_four_major_is_reject(self):
        self.assertEqual(self.run_case(40, ["major"] * 4), "REJECT")

    def test_3_size_39_three_major_is_reject(self):
        self.assertEqual(self.run_case(39, ["major"] * 3), "REJECT")

    def test_4_size_149_six_major_is_reject(self):
        self.assertEqual(self.run_case(149, ["major"] * 6), "REJECT")

    def test_5_size_150_six_major_is_accept(self):
        self.assertEqual(self.run_case(150, ["major"] * 6), "ACCEPT")

    def test_6_size_60_one_critical_is_reject(self):
        self.assertEqual(self.run_case(60, ["critical"]), "REJECT")


class ZeroDefectsThroughTheWebsite(WebsiteTestCase):
    def test_no_defects_is_accept(self):
        self.assertEqual(self.run_case(40, []), "ACCEPT")
        self.assertIn("No defects recorded", self.page())


class InvalidInputThroughTheWebsite(WebsiteTestCase):
    def test_sample_size_zero_shows_error_and_no_verdict(self):
        response = self.start("B-1", 0)
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)  # refused, but no crash
        self.assertIn("Sample size must be at least 1", html)
        self.assertNotIn('id="verdict"', html)
        self.assertIsNone(self.verdict_on_page())

    def test_sample_size_that_is_not_a_whole_number_is_refused(self):
        for bad in ("abc", "12.5", ""):
            with self.subTest(sample_size=bad):
                response = self.start("B-1", bad)
                self.assertEqual(response.status_code, 400)
                self.assertIn("whole number", response.get_data(as_text=True))
                self.assertIsNone(self.verdict_on_page())

    def test_huge_sample_size_shows_the_too_large_message(self):
        # 10353 digits: the exact situation that used to show Python's own
        # "Exceeds the limit (4300 digits) for integer string conversion" error.
        for digits in (10353, 4301, 4300, 8):
            with self.subTest(digits=digits):
                response = self.start("B-1", "9" * digits)
                html = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 400)
                self.assertIn(
                    "Inspection not started. Sample size is too large (maximum 1,000,000).",
                    html,
                )
                self.assertNotIn("integer string conversion", html)
                self.assertNotIn("4300", html)
                self.assertIsNone(self.verdict_on_page())

    def test_one_over_the_maximum_is_refused_and_the_maximum_is_allowed(self):
        response = self.start("B-1", "1000001")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Sample size is too large (maximum 1,000,000)", response.get_data(as_text=True))

        response = self.start("B-1", "1000000")
        self.assertEqual(response.status_code, 302)  # accepted, redirected to the page
        self.assertIn("1000000", self.page())

    def test_huge_negative_number_says_at_least_1(self):
        response = self.start("B-1", "-" + "9" * 10353)
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Sample size must be at least 1", html)
        self.assertNotIn("integer string conversion", html)

    def test_very_long_number_made_of_leading_zeros_is_still_just_40(self):
        self.assertEqual(self.start("B-1", "0" * 10000 + "40").status_code, 302)
        self.assertIn("sample size <strong>40</strong>", self.page())
        for _ in range(3):
            self.add_defect("major")
        self.assertEqual(self.verdict_on_page(), "ACCEPT")  # 3 majors, size 40

    def test_empty_batch_id_is_refused(self):
        response = self.start("   ", 40)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Batch ID must not be empty", response.get_data(as_text=True))

    def test_defect_before_starting_is_refused(self):
        response = self.add_defect("major")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Start an inspection", response.get_data(as_text=True))

    def test_bad_defect_is_refused_and_not_recorded(self):
        self.start("B-1", 40)
        self.assertEqual(self.add_defect("huge").status_code, 400)
        self.assertEqual(self.add_defect("major", "   ").status_code, 400)
        self.assertIn("No defects recorded", self.page())


class ListAndPersistence(WebsiteTestCase):
    def test_fresh_site_says_no_inspection_started(self):
        self.assertIn("No inspection started yet", self.page())
        self.assertIsNone(self.verdict_on_page())

    def test_defects_are_listed_in_order(self):
        self.start("B-7", 40)
        self.add_defect("minor", "dent")
        self.add_defect("major", "crack")
        html = self.page()
        self.assertIn("B-7", html)
        self.assertLess(html.index("minor: dent"), html.index("major: crack"))

    def test_data_survives_a_new_client(self):
        # Like refreshing the page, or restarting the server: it reads the file.
        self.start("B-7", 40)
        self.add_defect("major", "crack")
        fresh_client = app_module.app.test_client()
        html = fresh_client.get("/").get_data(as_text=True)
        self.assertIn("major: crack", html)

    def test_defect_text_is_escaped_not_run_as_html(self):
        self.start("B-1", 40)
        self.add_defect("minor", "<b>bold</b>")
        html = self.page()
        self.assertNotIn("<b>bold</b>", html)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", html)


if __name__ == "__main__":
    unittest.main()
