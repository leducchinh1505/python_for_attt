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
    """Chấm output theo chuẩn thi đấu: so từng token (tách theo khoảng trắng) giống hệt."""
    def test_exact(self):
        r = stdio('8' + NL, '8' + NL)
        self.assertTrue(r['ok']); self.assertIsNone(r['note'])

    def test_whitespace_and_trailing_lines_ignored(self):
        r = stdio('  apple:   8  ' + NL * 3, 'apple: 8')
        self.assertTrue(r['ok']); self.assertIsNone(r['note'])

    def test_one_line_vs_two(self):
        self.assertTrue(stdio('6 15', '6' + NL + '15')['ok'])

    def test_punctuation_matters(self):
        self.assertFalse(stdio('apple : 8', 'apple: 8')['ok'])

    def test_float_vs_int_fails(self):
        self.assertFalse(stdio('8.0', '8')['ok'])

    def test_float_noise_accepted_with_note(self):
        r = stdio('0.30000000000000004', '0.3')
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_float_far_fails(self):
        self.assertFalse(stdio('0.31', '0.3')['ok'])

    def test_descriptive_label_fails(self):
        self.assertFalse(stdio('Kết quả: 8', '8')['ok'])

    def test_wrong_value(self):
        self.assertFalse(stdio('9', '8')['ok'])

    def test_extra_number(self):
        self.assertFalse(stdio('8 9', '8')['ok'])

    def test_case_matters(self):
        self.assertFalse(stdio('nguyen van a', 'Nguyen Van A')['ok'])
        self.assertFalse(stdio('true', 'True')['ok'])

    def test_big_int_exact(self):
        self.assertFalse(stdio('1000000001', '1000000000')['ok'])

    def test_empty_expected_empty_got(self):
        self.assertTrue(stdio('', '')['ok'])

    def test_empty_expected_zero_got(self):
        self.assertFalse(stdio('0', '')['ok'])

    def test_stars_shape(self):
        shape = NL.join(['***', '**', '*'])
        self.assertTrue(stdio(shape, shape)['ok'])
        self.assertFalse(stdio(NL.join(['**', '**', '*']), shape)['ok'])

    def test_keys(self):
        r = stdio('8', '8')
        for k in ('ok', 'got', 'error', 'errType', 'note'):
            self.assertIn(k, r)


class NoFunctionRequirement(unittest.TestCase):
    """Chỉ chấm output: không quan tâm có viết hàm hay không."""
    EX = {'mode': 'stdio', 'tests': [{'input': '2 3', 'expected': '5'}, {'input': '10 -4', 'expected': '6'}]}

    def test_program_without_function_passes(self):
        rs = run('a, b = map(int, input().split())' + NL + 'print(a + b)', self.EX)
        self.assertTrue(all(r['ok'] and r['note'] is None for r in rs))

    def test_program_with_function_passes(self):
        src = NL.join(['def tong(a, b):', '    return a + b', 'print(tong(*map(int, input().split())))'])
        self.assertTrue(all(r['ok'] for r in run(src, self.EX)))

    def test_function_only_prints_nothing_so_fails(self):
        src = NL.join(['def tong(a, b):', '    return a + b'])
        self.assertFalse(any(r['ok'] for r in run(src, self.EX)))

    def test_requirefunction_field_is_ignored(self):
        ex = {**self.EX, 'requireFunction': ['tong']}
        rs = run('a, b = map(int, input().split())' + NL + 'print(a + b)', ex)
        self.assertTrue(all(r['ok'] for r in rs))


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

    def test_string_case_fails(self):
        self.assertFalse(func("def f():\n    return 'bill: 2'", 'f()', "'Bill: 2'")['ok'])

    def test_string_punct_spacing(self):
        r = func("def f():\n    return 'Bill : 2'", 'f()', "'Bill: 2'")
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_string_value_word_case(self):
        r = func("def f():\n    return 'true'", 'f()', "'True'")
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_print_case_fails(self):
        self.assertFalse(func("def f():\n    print('nguyen')", 'f()', "'Nguyen'")['ok'])

    def test_big_int_string(self):
        self.assertFalse(func("def f():\n    return '1000000001'", 'f()', "'1000000000'")['ok'])

    def test_alias_note_kept_on_failure(self):
        r = func('def g(x):\n    return x', 'f(2)', '3')
        self.assertFalse(r['ok']); self.assertIn('`g`', r['note'])

    def test_alias_note_kept_on_error(self):
        r = func('def g(x):\n    return 1 / 0', 'f(2)', '3')
        self.assertFalse(r['ok']); self.assertEqual(r['errType'], 'ZeroDivisionError'); self.assertIn('`g`', r['note'])

    def test_no_note_on_plain_failure(self):
        self.assertIsNone(func('def f(x):\n    return x', 'f(2)', '3')['note'])

    def test_bool_vs_int(self):
        self.assertFalse(func('def f():\n    return 1', 'f()', 'True')['ok'])

    def test_keys(self):
        r = func('def f():\n    return 1', 'f()', '1')
        for k in ('ok', 'got', 'printed', 'error', 'errType', 'note'):
            self.assertIn(k, r)


def load_ex(ex_id):
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, 'data', 'coding.json'), encoding='utf-8') as fh:
        data = json.load(fh)
    exs = data if isinstance(data, list) else data.get('exercises', data)
    return next(e for e in exs if e['id'] == ex_id)


class FixFinal(unittest.TestCase):
    def test_T1_C02_identity_fails(self):
        ex = load_ex('T1-C02')
        bad = run('def standardize_name(raw_name):\n    return raw_name', ex)
        self.assertLess(sum(r['ok'] for r in bad), len(ex['tests']) // 2)
        good = run(ex['solution'], ex)
        self.assertTrue(all(r['ok'] and r['note'] is None for r in good))

    def test_T4_C11_running_max_fails(self):
        ex = load_ex('T4-C11')
        src = NL.join([
            'n = int(input())', 'mx = -1',
            'for _ in range(n):', '    p = input().split()',
            '    if int(p[1]) > mx:', '        mx = int(p[1])', "        print(p[0], end=' ')",
        ])
        self.assertFalse(all(r['ok'] for r in run(src, ex)))
        good = run(ex['solution'], ex)
        self.assertTrue(all(r['ok'] and r['note'] is None for r in good))

    def test_T4_C11_label_fails_strict(self):
        ex = load_ex('T4-C11')
        src = ex['solution'].replace('print(best_currency)', "print('Kết quả:', best_currency)")
        self.assertNotEqual(src, ex['solution'])
        self.assertFalse(all(r['ok'] for r in run(src, ex)))


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


class InputLines(unittest.TestCase):
    """Mỗi dòng dữ liệu nhập là một lần input(), kể cả dòng trống."""
    def test_empty_input_is_one_empty_line(self):
        ex = {'mode': 'stdio', 'tests': [{'input': '', 'expected': '0'}]}
        r = run('s = input()\nprint(len(s))', ex)[0]
        self.assertTrue(r['ok'], r)

    def test_trailing_empty_line(self):
        ex = {'mode': 'stdio', 'tests': [{'input': '0\n', 'expected': '0 []'}]}
        r = run('n = int(input())\nds = input().split()\nprint(n, ds)', ex)[0]
        self.assertTrue(r['ok'], r)

    def test_reading_past_end_is_eof(self):
        ex = {'mode': 'stdio', 'tests': [{'input': '5', 'expected': '5'}]}
        r = run('a = input()\nb = input()\nprint(a)', ex)[0]
        self.assertFalse(r['ok']); self.assertEqual(r['errType'], 'EOFError')


if __name__ == '__main__':
    unittest.main()
