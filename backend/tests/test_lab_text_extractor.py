"""Teste extragere lab — limită text și warnings."""
import unittest

from services.lab_text_extractor import MAX_LAB_TEXT_CHARS, extract_lab_values_from_text


class TestLabTextExtractor(unittest.TestCase):
    def test_truncates_long_text(self):
        text = "Hemoglobină 13.5 g/dL\n" + ("x" * (MAX_LAB_TEXT_CHARS + 1000))
        out = extract_lab_values_from_text(text)
        self.assertTrue(out.get("truncated"))
        self.assertTrue(any("trunchiat" in (w.get("message") or "").lower() for w in out.get("warnings") or []))

    def test_out_of_range_hemoglobin_warning(self):
        out = extract_lab_values_from_text("Hemoglobină 99 g/dL")
        self.assertEqual(out.get("hemoglobin"), 99.0)
        warnings = out.get("warnings") or []
        self.assertTrue(any(w.get("key") == "hemoglobin" and w.get("low_confidence") for w in warnings))

    def test_normal_value_no_clinical_warning(self):
        out = extract_lab_values_from_text("Hemoglobină 13.2 g/dL")
        self.assertEqual(out.get("hemoglobin"), 13.2)
        hem_warnings = [w for w in (out.get("warnings") or []) if w.get("key") == "hemoglobin"]
        self.assertEqual(len(hem_warnings), 0)


if __name__ == "__main__":
    unittest.main()
