import sys, io, math, builtins, traceback, linecache

USER_FILE = '<bai_lam>'
TEST_FILE = '<kiem_thu>'
MAX_OUT = 20000


def _cmp(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) or isinstance(b, float):
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-6)
        return a == b
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return type(a) is type(b) and len(a) == len(b) and all(_cmp(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_cmp(a[k], b[k]) for k in a)
    return a == b


def _norm(s):
    lines = [l.rstrip() for l in s.replace('\r\n', '\n').split('\n')]
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines)


def _register(name, src):
    linecache.cache[name] = (len(src), None, src.splitlines(True), name)


def _fmt_exc(e):
    if isinstance(e, SyntaxError):
        txt = (e.text or '').strip()
        where = f'Dòng {e.lineno}: {txt}\n' if e.filename == USER_FILE else ''
        return type(e).__name__, f'{where}{type(e).__name__}: {e.msg}'
    frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == USER_FILE]
    where = f'Dòng {frames[-1].lineno}: {(frames[-1].line or "").strip()}\n' if frames else ''
    return type(e).__name__, f'{where}{type(e).__name__}: {e}'


def _prep_files(files):
    for name, content in (files or {}).items():
        with open(name, 'w', encoding='utf-8') as f:
            f.write(content)


def _exec(src, filename, ns, stdin=''):
    out = io.StringIO()
    inp = io.StringIO(stdin or '')

    def fake_input(prompt=''):
        line = inp.readline()
        if line == '':
            raise EOFError('chương trình gọi input() nhiều hơn số dòng dữ liệu nhập')
        return line.rstrip('\n').rstrip('\r')

    old = sys.stdout, sys.stdin, builtins.input
    sys.stdout, sys.stdin, builtins.input = out, inp, fake_input
    err = None
    try:
        _register(filename, src)
        exec(compile(src, filename, 'exec'), ns)
    except SystemExit:
        pass
    except BaseException as e:
        err = _fmt_exc(e)
    finally:
        sys.stdout, sys.stdin, builtins.input = old
    return out.getvalue()[:MAX_OUT], err


def run_program(src, stdin='', files=None):
    _prep_files(files)
    out, err = _exec(src, USER_FILE, {'__name__': '__main__'}, stdin)
    return {'stdout': out, 'error': err[1] if err else None, 'errType': err[0] if err else None}


def run_tests(src, ex):
    results = []
    for t in ex['tests']:
        _prep_files(ex.get('files'))
        if ex['mode'] == 'stdio':
            out, err = _exec(src, USER_FILE, {'__name__': '__main__'}, t.get('input', ''))
            ok = err is None and _norm(out) == _norm(t['expected'])
            results.append({'ok': ok, 'got': out, 'error': err[1] if err else None, 'errType': err[0] if err else None})
            continue
        ns = {'__name__': '__bai_lam__'}
        out, err = _exec(src, USER_FILE, ns)
        if err and err[0] != 'EOFError':
            results.append({'ok': False, 'got': '', 'printed': out, 'error': err[1], 'errType': err[0]})
            continue
        code = (t.get('setup') or '') + '\n__ket_qua__ = (' + t['call'] + ')\n'
        out2, err2 = _exec(code, TEST_FILE, ns)
        if err2:
            results.append({'ok': False, 'got': '', 'printed': out2, 'error': err2[1], 'errType': err2[0]})
            continue
        got = ns.get('__ket_qua__')
        try:
            exp = eval(t['expected'], {})
            ok = _cmp(got, exp)
        except Exception as e:
            ok = False
        results.append({'ok': ok, 'got': repr(got), 'printed': out2, 'error': None, 'errType': None})
    return results
