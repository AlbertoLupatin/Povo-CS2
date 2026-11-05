import random
import unittest

from tools.vmap_delimiters import matching_brace, matching_bracket


class VmapDelimiterTests(unittest.TestCase):
    def test_quoted_delimiters_escaped_quotes_and_multiline_values(self):
        body = r'"key" "brace } bracket ] escaped \" still quoted {" { "x" "\\" }'
        for left, right, match in (('{', '}', matching_brace), ('[', ']', matching_bracket)):
            text = 'prefix' + left + body + right + ' trailing "unfinished'
            self.assertEqual(match(text, 6), len(text) - len(' trailing "unfinished') - 1)
        self.assertEqual(matching_brace('{ "a\\\nb" "}" }', 0), len('{ "a\\\nb" "}" }') - 1)

    def test_rejects_unbalanced_input_with_callers_exception_type(self):
        class ParseError(RuntimeError):
            pass
        for text in ('{ "unterminated }', '{ { }', '{ "escape\\'):
            with self.assertRaises(ParseError):
                matching_brace(text, 0, error_type=ParseError)
        with self.assertRaises(ValueError):
            matching_bracket('[ []', 0)

    def test_nested_generated_documents_ignore_delimiters_inside_strings(self):
        rng = random.Random(9413)
        def document(depth, left, right):
            parts = ['"' + ''.join(rng.choice(('a', '{', '}', '[', ']', '\\\\', '\\"', '\n')) for _ in range(20)) + '"']
            if depth:
                parts.extend(document(depth - 1, left, right) for _ in range(rng.randrange(1, 4)))
            return left + ' '.join(parts) + right
        for left, right, match in (('{', '}', matching_brace), ('[', ']', matching_bracket)):
            for _ in range(100):
                value = document(3, left, right)
                self.assertEqual(match(value + ' ignored', 0), len(value) - 1)
