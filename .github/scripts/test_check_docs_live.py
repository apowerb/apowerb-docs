"""Tests du temoin de check_docs_live.py.

    python3 -m unittest discover -s .github/scripts
"""
import unittest

from check_docs_live import prose, visible_text


class WitnessMatchesRenderedPage(unittest.TestCase):
    def test_inline_code_followed_by_punctuation(self):
        # Retirer `<code>` laisse un espace avant la virgule, que le markdown
        # n'a pas : faux rouge du 23/09 sur guides/workflows (e4c5e02).
        page = visible_text("<p>Use <code>x</code>, y</p>")
        self.assertIn(prose("Use `x`, y"), page)

    def test_every_closing_punctuation(self):
        for mark in ",.;:!?)]":
            with self.subTest(mark=mark):
                page = visible_text(f"<p>see <code>x</code>{mark} y</p>")
                self.assertIn(prose(f"see `x`{mark} y"), page)

    def test_inline_code_after_opening_bracket(self):
        page = visible_text("<p>the flag (<code>x</code>) and [<code>y</code>]</p>")
        self.assertIn(prose("the flag (`x`) and [`y`]"), page)

    def test_other_differences_still_fail(self):
        page = visible_text("<p>Use <code>x</code>, y</p>")
        self.assertNotIn(prose("Use `x`, z"), page)
        self.assertNotIn(prose("Use `x`,y"), page)
        self.assertNotIn(prose("Use `x`y"), page)


if __name__ == "__main__":
    unittest.main()
