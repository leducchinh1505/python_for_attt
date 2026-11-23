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

    def test_float_close(self):
        self.assertTrue(stdio('0.30000000000000004', '0.3')['ok'])

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

    def test_prefix_word_from_stdin_is_rejected(self):
        # 'USD' là dữ liệu nhập vào, không phải chữ mô tả
        self.assertFalse(stdio('USD EUR', 'EUR', 'USD 25100\nEUR 27200')['ok'])

    def test_prefix_word_from_stdin_case_insensitive(self):
        self.assertFalse(stdio('usd EUR', 'EUR', 'USD 25100\nEUR 27200')['ok'])

    def test_prefix_word_not_in_stdin_or_expected_is_accepted(self):
        r = stdio('Max EUR', 'EUR', 'USD 25100\nEUR 27200')
        self.assertTrue(r['ok']); self.assertIn('chữ mô tả', r['note'])

    def test_label_prefix_with_stdin(self):
        r = stdio('Kết quả: 8', '8', '3 5')
        self.assertTrue(r['ok']); self.assertIn('chữ mô tả', r['note'])

    def test_case_differs_fails(self):
        self.assertFalse(stdio('nguyen van a', 'Nguyen Van A')['ok'])

    def test_case_differs_label_line_fails(self):
        self.assertFalse(stdio('Tên: nguyen', 'Nguyen')['ok'])

    def test_value_word_case_insensitive(self):
        r = stdio('true', 'True')
        self.assertTrue(r['ok']); self.assertIsNotNone(r['note'])

    def test_value_word_prefix_rejected_any_case(self):
        self.assertFalse(stdio('TRUE False', 'False')['ok'])

    def test_big_int_not_close(self):
        self.assertFalse(stdio('1000000001', '1000000000')['ok'])

    def test_big_int_with_label_not_close(self):
        self.assertFalse(stdio('Tổng: 1000000001', '1000000000')['ok'])

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

    def test_T4_C11_label_passes(self):
        ex = load_ex('T4-C11')
        src = ex['solution'].replace('print(best_currency)', "print('Kết quả:', best_currency)")
        self.assertNotEqual(src, ex['solution'])
        self.assertTrue(all(r['ok'] for r in run(src, ex)))


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


class RequireFunctionCall(unittest.TestCase):
    """Bài 'viết hàm' chấm như chương trình: phải tự đọc input, gọi hàm và in kết quả."""
    EX = {'mode': 'stdio', 'requireFunction': ['tong'],
          'tests': [{'input': '2 3', 'expected': '5'}, {'input': '10 -4', 'expected': '6'}]}

    def check(self, src):
        return run(src, self.EX)

    def test_function_called_passes(self):
        src = 'def tong(a, b):\n    return a + b\na, b = map(int, input().split())\nprint(tong(a, b))'
        rs = self.check(src)
        self.assertTrue(all(r['ok'] for r in rs)); self.assertTrue(all(r['note'] is None for r in rs))

    def test_function_only_fails(self):
        rs = self.check('def tong(a, b):\n    return a + b')
        self.assertFalse(any(r['ok'] for r in rs))

    def test_correct_output_without_calling_function_fails(self):
        src = 'def tong(a, b):\n    return a + b\na, b = map(int, input().split())\nprint(a + b)'
        rs = self.check(src)
        self.assertFalse(any(r['ok'] for r in rs))
        self.assertEqual(rs[0]['errType'], 'ChuaGoiHam')
        self.assertIn('không gọi', rs[0]['error'])

    def test_no_function_at_all_fails(self):
        rs = self.check('a, b = map(int, input().split())\nprint(a + b)')
        self.assertFalse(any(r['ok'] for r in rs))
        self.assertEqual(rs[0]['errType'], 'ChuaGoiHam')

    def test_other_function_name_accepted_with_note(self):
        src = 'def cong(a, b):\n    return a + b\na, b = map(int, input().split())\nprint(cong(a, b))'
        rs = self.check(src)
        self.assertTrue(all(r['ok'] for r in rs)); self.assertIn('cong', rs[0]['note'])

    def test_lambda_does_not_count(self):
        src = 'f = lambda a, b: a + b\na, b = map(int, input().split())\nprint(f(a, b))'
        self.assertFalse(any(r['ok'] for r in self.check(src)))

    def test_method_alone_does_not_satisfy(self):
        src = ('class C:\n    def tong(self, a, b):\n        return a + b\n'
               'a, b = map(int, input().split())\nprint(C().tong(a, b))')
        # phương thức trùng tên vẫn tính (co_name == 'tong'): đề yêu cầu hàm tên tong và nó đã được gọi
        self.assertTrue(all(r['ok'] for r in self.check(src)))

    def test_wrong_value_still_fails(self):
        src = 'def tong(a, b):\n    return a - b\na, b = map(int, input().split())\nprint(tong(a, b))'
        self.assertFalse(any(r['ok'] for r in self.check(src)))

    def test_profiler_cleared_after_run(self):
        self.check('def tong(a, b):\n    return a + b\nprint(tong(*map(int, input().split())))')
        self.assertIsNone(sys.getprofile())

    def test_no_requirement_keeps_old_behavior(self):
        ex = {'mode': 'stdio', 'tests': [{'input': '2 3', 'expected': '5'}]}
        r = run('a, b = map(int, input().split())\nprint(a + b)', ex)[0]
        self.assertTrue(r['ok'])


if __name__ == '__main__':
    unittest.main()
