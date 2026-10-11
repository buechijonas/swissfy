from django.test import SimpleTestCase

from .numbers import compact_number


class CompactNumberTests(SimpleTestCase):
    def test_compact_number(self):
        cases = {
            0: "0",
            1: "1",
            1000: "1000",
            9999: "9999",
            10_000: "10 Tsd.",
            12_345: "12 Tsd.",
            100_000: "100 Tsd.",
            999_999: "999 Tsd.",
            1_000_000: "1M",
            1_250_000: "1.2M",
            15_000_000: "15M",
            -12_000: "-12 Tsd.",
        }
        for value, expected in cases.items():
            self.assertEqual(compact_number(value), expected)
