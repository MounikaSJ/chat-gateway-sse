import unittest
from server import summarize_text, extract_delta_content_from_upstream_line


class TestUtils(unittest.TestCase):
    def test_summarize_text_caps_length(self):
        txt = "word " * 200
        out = summarize_text(txt, max_len=40)
        self.assertTrue(len(out) <= 40)
        self.assertTrue(out.endswith("..."))

    def test_summarize_text_strips_whitespace(self):
        txt = "  hello   world \n\n this   is   fine "
        out = summarize_text(txt, max_len=200)
        self.assertEqual(out, "hello world this is fine")

    def test_extract_delta_from_mock_line(self):
        line = 'data: data: {"choices":[{"delta":{"content":"<think>"}}]}'
        out = extract_delta_content_from_upstream_line(line)
        self.assertEqual(out, "<think>")

    def test_extract_done_returns_none(self):
        line = "data: data: [DONE]"
        out = extract_delta_content_from_upstream_line(line)
        self.assertIsNone(out)

    def test_ignore_non_data(self):
        line = "event: message"
        out = extract_delta_content_from_upstream_line(line)
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
