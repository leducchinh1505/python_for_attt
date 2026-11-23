import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness, expand_tests

NL = chr(10)


class SolutionOutput(unittest.TestCase):
    def test_stdio(self):
        ex = {'mode': 'stdio', 'solution': 'n=int(input())' + NL + 'print(n*2)', 'tests': []}
        self.assertEqual(harness.solution_output(ex['solution'], ex, {'input': '4'}), (True, '8', None))

    def test_stdio_error_rejected(self):
        ex = {'mode': 'stdio', 'solution': 'print(int(input()))', 'tests': []}
        ok, exp, why = harness.solution_output(ex['solution'], ex, {'input': 'x'})
        self.assertFalse(ok)
        self.assertIn('lỗi', why)

    def test_function(self):
        ex = {'mode': 'function', 'solution': 'def f(x): return [x, x]', 'tests': []}
        self.assertEqual(harness.solution_output(ex['solution'], ex, {'setup': '', 'call': 'f(1)'}), (True, '[1, 1]', None))

    def test_function_print_rejected(self):
        ex = {'mode': 'function', 'solution': 'def f(x):' + NL + '    print(x)' + NL + '    return x', 'tests': []}
        self.assertFalse(harness.solution_output(ex['solution'], ex, {'call': 'f(1)'})[0])

    def test_function_nan_rejected(self):
        ex = {'mode': 'function', 'solution': 'def f(): return float("nan")', 'tests': []}
        self.assertFalse(harness.solution_output(ex['solution'], ex, {'call': 'f()'})[0])

    def test_function_error_rejected(self):
        ex = {'mode': 'function', 'solution': 'def f(x): return 1/x', 'tests': []}
        self.assertFalse(harness.solution_output(ex['solution'], ex, {'call': 'f(0)'})[0])

    def test_files_per_test(self):
        src = 'print(open("d.txt", encoding="utf-8").read().strip())'
        ex = {'mode': 'stdio', 'solution': src, 'tests': []}
        self.assertEqual(harness.solution_output(src, ex, {'input': '', 'files': {'d.txt': 'Z'}}), (True, 'Z', None))


class Expand(unittest.TestCase):
    def test_stdio_expand_dedupe_cap(self):
        ex = {'id': 'a', 'mode': 'stdio', 'solution': 'print(int(input())+1)',
              'tests': [{'input': '1', 'expected': '2'}]}
        cands = [{'input': '1  '}, {'input': '2'}, {'input': 'bad'}] + [{'input': str(i)} for i in range(10, 30)]
        b, a, d = expand_tests.expand_exercise(ex, cands)
        self.assertEqual((b, a), (1, 15))
        self.assertEqual(ex['tests'][1], {'input': '2', 'expected': '3'})
        self.assertEqual(d['trùng'], 1)
        self.assertEqual(sum(d.values()), 2)

    def test_function_expand(self):
        ex = {'id': 'b', 'mode': 'function', 'solution': 'def f(x): return x*x',
              'tests': [{'setup': '', 'call': 'f(2)', 'expected': '4'}]}
        cands = [{'setup': '', 'call': 'f(2)'}, {'setup': '', 'call': 'f(3)'}]
        b, a, d = expand_tests.expand_exercise(ex, cands)
        self.assertEqual((b, a), (1, 2))
        self.assertEqual(ex['tests'][1]['expected'], '9')

    def test_expand_all_unknown_id(self):
        rows = expand_tests.expand_all([], {'zz': [{'input': ''}]})
        self.assertEqual(rows[0][0], 'zz')


if __name__ == '__main__':
    unittest.main()
