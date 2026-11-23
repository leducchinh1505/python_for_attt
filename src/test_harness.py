import os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness


def run(src, ex):
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            return harness.run_tests(src, ex)
        finally:
            os.chdir(cwd)


def stdio(printed, expected, inp=''):
    ex = {'mode': 'stdio', 'tests': [{'input': inp, 'expected': expected}]}
    return run(f'print({printed!r}, end="")', ex)[0]


def func(src, call, expected, setup=''):
    ex = {'mode': 'function', 'tests': [{'setup': setup, 'call': call, 'expected': expected}]}
    return run(src, ex)[0]

NL = chr(10)


class StdioTests(unittest.TestCase):
    def test_exact(self):
        r = stdio('8\n', '8\n')
        self.assertTrue(r['ok']); self.assertIsNone(r['note'])

    def test_spacing_punct(self):
        r = stdio('apple : 8', 'apple: 8')
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_float_int(self):
        r = stdio('8.0', '8')
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_descriptive_prefix(self):
        r = stdio('Kết quả: 8', '8')
        self.assertTrue(r['ok']); self.assertIn('chữ mô tả', r['note'])

    def test_one_line_vs_two(self):
        r = stdio('6 15', '6\n15')
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_wrong_value(self):
        self.assertFalse(stdio('9', '8')['ok'])

    def test_extra_number(self):
        self.assertFalse(stdio('8 9', '8')['ok'])

    def test_extra_value_word(self):
        self.assertFalse(stdio('True False', 'True')['ok'])

    def test_prefix_word_not_in_expected_is_accepted(self):
        # documented behaviour: 'usd' is not in expected, so it counts as descriptive text
        r = stdio('USD EUR', 'EUR')
        self.assertTrue(r['ok']); self.assertIn('chữ mô tả', r['note'])

    def test_empty_expected_empty_got(self):
        r = stdio('', '')
        self.assertTrue(r['ok'])

    def test_empty_expected_zero_got(self):
        self.assertFalse(stdio('0', '')['ok'])

    def test_empty_expected_value_word(self):
        self.assertFalse(stdio('Không tìm thấy', '')['ok'])

    def test_keys(self):
        r = stdio('8', '8')
        for k in ('ok', 'got', 'error', 'errType', 'note'):
            self.assertIn(k, r)


class FunctionTests(unittest.TestCase):
    def test_exact(self):
        r = func('def f(x):\n    return [x, 1]', 'f(2)', '[2, 1]')
        self.assertTrue(r['ok']); self.assertIsNone(r['note'])

    def test_tuple_for_list(self):
        r = func('def f(x):\n    return (x, 1)', 'f(2)', '[2, 1]')
        self.assertTrue(r['ok']); self.assertIn('list/tuple', r['note'])

    def test_wrong_value(self):
        self.assertFalse(func('def f(x):\n    return x', 'f(2)', '3')['ok'])

    def test_other_name_single_function(self):
        r = func('def g(x):\n    return x + 1', 'f(2)', '3')
        self.assertTrue(r['ok']); self.assertIn('`f`', r['note']); self.assertIn('`g`', r['note'])

    def test_other_name_two_functions(self):
        r = func('def g(x):\n    return x + 1\ndef h(x):\n    return x', 'f(2)', '3')
        self.assertFalse(r['ok']); self.assertEqual(r['errType'], 'NameError')

    def test_print_instead_of_return(self):
        r = func('def f(x):\n    print(x + 1)', 'f(2)', '3')
        self.assertTrue(r['ok']); self.assertIn('print', r['note'])

    def test_print_wrong_value(self):
        self.assertFalse(func('def f(x):\n    print(x + 5)', 'f(2)', '3')['ok'])

    def test_string_case(self):
        r = func("def f():\n    return 'bill: 2'", 'f()', "'Bill: 2'")
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_bool_vs_int(self):
        self.assertFalse(func('def f():\n    return 1', 'f()', 'True')['ok'])

    def test_keys(self):
        r = func('def f():\n    return 1', 'f()', '1')
        for k in ('ok', 'got', 'printed', 'error', 'errType', 'note'):
            self.assertIn(k, r)


class FilesPerTest(unittest.TestCase):
    def test_files_per_test(self):
        src = 'with open("d.txt", encoding="utf-8") as fh:' + chr(10) + '    print(fh.read().strip())'
        ex = {'mode': 'stdio', 'tests': [
            {'input': '', 'expected': 'A', 'files': {'d.txt': 'A'}},
            {'input': '', 'expected': 'B', 'files': {'d.txt': 'B'}},
        ]}
        self.assertEqual([r['ok'] for r in run(src, ex)], [True, True])

    def test_files_per_test_function(self):
        src = 'def f():' + chr(10) + '    with open("d.txt", encoding="utf-8") as fh:' + chr(10) + '        return fh.read()'
        ex = {'mode': 'function', 'files': {'d.txt': 'zzz'}, 'tests': [
            {'call': 'f()', 'expected': "'A'", 'files': {'d.txt': 'A'}},
            {'call': 'f()', 'expected': "'B'", 'files': {'d.txt': 'B'}},
        ]}
        self.assertEqual([r['ok'] for r in run(src, ex)], [True, True])


class FixRound1(unittest.TestCase):
    def test_noop_vs_empty_list(self):
        self.assertFalse(func('def f(): pass', 'f()', '[]')['ok'])

    def test_noop_vs_empty_string(self):
        self.assertFalse(func('def f(): pass', 'f()', "''")['ok'])

    def test_stars_wrong_shape(self):
        self.assertFalse(stdio(NL.join(['**', '**', '*']), NL.join(['***', '**', '*']))['ok'])

    def test_stars_vs_letters(self):
        self.assertFalse(stdio(NL.join('abc'), NL.join(['***', '**', '*']))['ok'])

    def test_stars_trailing_spaces(self):
        self.assertTrue(stdio(NL.join(['***  ', '**', '*  ']), NL.join(['***', '**', '*']))['ok'])

    def test_punct_strings_differ(self):
        self.assertFalse(func("def f():" + NL + "    return '?'", 'f()', "'.'")['ok'])


if __name__ == '__main__':
    unittest.main()
