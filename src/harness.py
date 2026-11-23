import sys, io, math, re, builtins, traceback, linecache

USER_FILE = '<bai_lam>'
TEST_FILE = '<kiem_thu>'
MAX_OUT = 20000
VALUE_WORDS = {'true', 'false', 'none', 'yes', 'no', 'có', 'không', 'đúng', 'sai'}
_TOKEN_RE = re.compile(r'-?\d+(?:\.\d+)?|[^\W\d_]+')
_NUM_RE = re.compile(r'-?\d+(?:\.\d+)?\Z')
_CALL_RE = re.compile(r'^\s*([A-Za-z_]\w*)\s*\(')


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


def _cmp_loose(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return _cmp(a, b)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(_cmp_loose(x, y) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a == b or (bool(_tokens(b)) and _toks_eq(_tokens(a), _tokens(b)))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_cmp_loose(a[k], b[k]) for k in a)
    if isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
        return a == b
    return a == b


def _tokens(s):
    return _TOKEN_RE.findall(s)


def _tok_eq(a, b):
    if _NUM_RE.match(a) and _NUM_RE.match(b):
        if '.' not in a and '.' not in b:
            return int(a) == int(b)
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-6)
    if a == b:
        return True
    # Chữ phân biệt hoa/thường, trừ các từ giá trị (True/true, None/none, ...).
    return a.lower() == b.lower() and a.lower() in VALUE_WORDS


def _toks_eq(xs, ys):
    return len(xs) == len(ys) and all(_tok_eq(x, y) for x, y in zip(xs, ys))


def _match_stdout(got, expected, stdin=''):
    if _norm(got) == _norm(expected):
        return True, None
    gt, et = _tokens(got), _tokens(expected)
    if et and _toks_eq(gt, et):
        return True, 'Đúng giá trị; khác cách trình bày (khoảng trắng/dấu câu).'
    g_lines = [l for l in _norm(got).split(chr(10)) if l.strip()]
    e_lines = [l for l in _norm(expected).split(chr(10)) if l.strip()]
    if not e_lines or len(g_lines) != len(e_lines):
        return False, None
    e_all = {w.lower() for w in et}
    in_all = {w.lower() for w in _tokens(stdin or '')}
    for gl, el in zip(g_lines, e_lines):
        g, e = _tokens(gl), _tokens(el)
        if not e:
            if gl.rstrip() != el.rstrip():
                return False, None
            continue
        if _toks_eq(g, e):
            continue
        k = len(g) - len(e)
        if k <= 0 or not _toks_eq(g[k:], e):
            return False, None
        prefix = g[:k]
        if any(_NUM_RE.match(w) or w.lower() in VALUE_WORDS or w.lower() in e_all or w.lower() in in_all
               for w in prefix):
            return False, None
    return True, 'Đúng giá trị; có thêm chữ mô tả trước kết quả.'


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
        _prep_files(t.get('files'))
        if ex['mode'] == 'stdio':
            out, err = _exec(src, USER_FILE, {'__name__': '__main__'}, t.get('input', ''))
            match_ok, note = _match_stdout(out, t['expected'], t.get('input', ''))
            ok = err is None and match_ok
            results.append({'ok': ok, 'got': out, 'error': err[1] if err else None, 'errType': err[0] if err else None,
                            'note': note if ok else None})
            continue
        ns = {'__name__': '__bai_lam__'}
        out, err = _exec(src, USER_FILE, ns)
        if err and err[0] != 'EOFError':
            results.append({'ok': False, 'got': '', 'printed': out, 'error': err[1], 'errType': err[0], 'note': None})
            continue
        notes = []
        alias = None
        m = _CALL_RE.match(t['call'])
        if m and m.group(1) not in ns and not hasattr(builtins, m.group(1)):
            want = m.group(1)
            mine = [(k, v) for k, v in ns.items()
                    if isinstance(v, type(_cmp)) and v.__code__.co_filename == USER_FILE]
            if len(mine) == 1:
                alias = (want, mine[0][0], mine[0][1])
                ns[want] = mine[0][1]
        code = (t.get('setup') or '') + '\n__ket_qua__ = (' + t['call'] + ')\n'
        out2, err2 = _exec(code, TEST_FILE, ns)
        alias_note = None
        if alias and ns.get(alias[0]) is alias[2]:
            alias_note = f'Tên hàm khác đề (đề yêu cầu `{alias[0]}`), đã chấm bằng hàm `{alias[1]}`.'
            notes.append(alias_note)
        if err2:
            results.append({'ok': False, 'got': '', 'printed': out2, 'error': err2[1], 'errType': err2[0],
                            'note': alias_note})
            continue
        got = ns.get('__ket_qua__')
        ok = False
        try:
            exp = eval(t['expected'], {})
            if _cmp(got, exp):
                ok = True
            elif _cmp_loose(got, exp):
                ok = True
                notes.append('Đúng giá trị; khác kiểu list/tuple hoặc cách viết chuỗi.')
            elif got is None and exp is not None:
                pt = _tokens(out2)
                if pt and (_toks_eq(pt, _tokens(str(exp))) or _toks_eq(pt, _tokens(repr(exp)))):
                    ok = True
                    notes.append('Hàm dùng print thay vì return; được chấp nhận, nhưng đề yêu cầu trả về (return) giá trị.')
        except Exception:
            ok = False
        # Test sai vẫn giữ ghi chú tên hàm để học sinh biết hàm nào đã được gọi.
        note = (' '.join(notes) or None) if ok else alias_note
        results.append({'ok': ok, 'got': repr(got), 'printed': out2, 'error': None, 'errType': None, 'note': note})
    return results


def solution_output(src, ex, test):
    """Chạy lời giải qua một test (chưa có expected) để lấy giá trị thật.
    Trả (ok, expected_str, reason); ok False thì expected_str None và reason nêu lý do.
    expected_str đã được chấm lại và phải khớp chặt (ok, không note). Chạy trong thư mục tạm."""
    import os, tempfile
    base = {k: v for k, v in ex.items() if k != 'tests'}
    probe = {k: v for k, v in test.items() if k != 'expected'}
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as d:
        os.chdir(d)
        try:
            r = run_tests(src, {**base, 'tests': [{**probe, 'expected': 'None'}]})[0]
            if r['error']:
                return False, None, f"lời giải bị lỗi: {r['error']}"
            if ex['mode'] == 'stdio':
                expected = _norm(r['got'])
            else:
                if r.get('printed', '').strip():
                    return False, None, 'lời giải có in ra màn hình'
                expected = r['got']
            r2 = run_tests(src, {**base, 'tests': [{**probe, 'expected': expected}]})[0]
        finally:
            os.chdir(cwd)
    if not r2['ok']:
        return False, None, f'giá trị trả về không eval lại được hoặc không bằng nhau: {expected}'
    if r2['note']:
        return False, None, f'expected không khớp chặt với lời giải (note: {r2["note"]})'
    return True, expected, None
