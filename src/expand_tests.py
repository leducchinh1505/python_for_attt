"""Thêm test vào bài code; expected được tính từ lời giải mẫu.
Dùng: py -I -X utf8 src/expand_tests.py data/coding.json CANDIDATES.json [--write]
CANDIDATES.json: {"<id bài>": [{"input": "..."} | {"setup": "...", "call": "...", "files": {...}}, ...]}
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness  # noqa: E402

TARGET = 15


def _key(ex, t):
    files = json.dumps(t.get('files') or {}, sort_keys=True)
    if ex['mode'] == 'stdio':
        inp = '\n'.join(l.rstrip() for l in t.get('input', '').split('\n'))
        return ('stdio', inp, files)
    return ('function', t.get('setup') or '', t['call'], files)


def expand_exercise(ex, candidates, target=TARGET):
    """Nối candidate hợp lệ vào ex['tests'] (sửa tại chỗ) tới khi đủ target.
    Trả (số test trước, số test sau, {lý do: số lượng bị bỏ})."""
    before = len(ex['tests'])
    seen = {_key(ex, t) for t in ex['tests']}
    dropped = {}
    for c in candidates:
        if len(ex['tests']) >= target:
            break
        k = _key(ex, c)
        if k in seen:
            dropped['trùng'] = dropped.get('trùng', 0) + 1
            continue
        ok, expected, reason = harness.solution_output(ex['solution'], ex, c)
        if not ok:
            dropped[reason] = dropped.get(reason, 0) + 1
            continue
        seen.add(k)
        ex['tests'].append({**c, 'expected': expected})
    return before, len(ex['tests']), dropped


def expand_all(coding, cands, target=TARGET):
    rows = []
    byid = {e['id']: e for e in coding}
    for eid, cs in cands.items():
        if eid not in byid:
            rows.append((eid, None, None, {'không có bài này': 1}))
            continue
        b, a, d = expand_exercise(byid[eid], cs, target)
        rows.append((eid, b, a, d))
    return rows


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    sys.stdout.reconfigure(encoding='utf-8')
    path, cpath = args[0], args[1]
    coding = json.load(open(path, encoding='utf-8'))
    cands = json.load(open(cpath, encoding='utf-8'))
    for eid, b, a, d in expand_all(coding, cands):
        why = '; '.join(f'{r} x{n}' for r, n in d.items())
        if b is None:
            print(f'{eid}: bỏ qua ({why})')
        else:
            print(f'{eid}: {b} -> {a} test' + (f' (bỏ: {why})' if why else ''))
    if '--write' in sys.argv:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(coding, f, ensure_ascii=False, indent=1)
        print('đã ghi', path)
    else:
        print('(chưa ghi; thêm --write để ghi)')
