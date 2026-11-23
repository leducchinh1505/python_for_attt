"""Kiểm chứng ngân hàng câu hỏi bằng cách chạy Python thật.
- Câu "output": chạy code (2 lần, để bắt code không tất định) và so với phương án đáp án.
- Câu "replace": thay "___" bằng từng phương án; chỉ phương án đáp án được in ra đúng "expect".
- Bài code: lời giải mẫu phải qua mọi test; code khởi đầu (starter) không được qua hết test.
Dùng: py -I src/verify.py data   (thêm --json để in danh sách vấn đề dạng JSON)
"""
import json, os, re, subprocess, sys, tempfile, collections
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")


def run_snippet(code):
    """Chạy code trong thư mục tạm. Trả (kind, giá trị, stdout): kind 'OK' hoặc 'EXC' (giá trị = tên exception)."""
    with tempfile.TemporaryDirectory() as d:
        try:
            p = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', code], capture_output=True, text=True, cwd=d,
                               encoding='utf-8', timeout=10, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
        except subprocess.TimeoutExpired:
            return ('EXC', 'Timeout', '')
    if p.returncode != 0:
        lines = [l for l in p.stderr.strip().splitlines() if l.strip()]
        return ('EXC', lines[-1].split(':')[0].strip() if lines else 'Error', p.stdout)
    return ('OK', p.stdout.rstrip('\n'), p.stdout)


def norm(s):
    return '\n'.join(l.rstrip() for l in str(s).split('\n')).strip()


def fill(code, opt):
    """Thay ___ bằng phương án; phương án nhiều dòng được thụt lề theo dòng chứa ___."""
    line = next(l for l in code.split('\n') if '___' in l)
    indent = line[:len(line) - len(line.lstrip())]
    return code.replace('___', opt.replace('\n', '\n' + indent), 1)


def check_mcq(q):
    out = []
    opts = q['options']
    if len(opts) != 4 or len(set(opts)) != 4:
        out.append('phải có 4 phương án khác nhau')
    if not (0 <= q.get('answer', -1) < len(opts)):
        return out + ['answer ngoài phạm vi']
    if re.search(r'(đáp án|phương án|câu|chọn)\s*[ABCD]\b', q.get('explanation', '') + q.get('hint', ''), re.I):
        out.append('giải thích nhắc chữ cái phương án (sẽ sai khi xáo trộn)')
    if q['type'] == 'output' and q.get('code'):
        k1, got, stdout = run_snippet(q['code'])
        k2, got2, _ = run_snippet(q['code'])
        if (k1, got) != (k2, got2):
            out.append('code cho kết quả khác nhau giữa 2 lần chạy')
        if k1 == 'EXC' and stdout:
            out.append(f'in ra output trước khi lỗi {got}')
        want = opts[q['answer']]
        if norm(got) != norm(want):
            match = [i for i, o in enumerate(opts) if norm(o) == norm(got)]
            out.append(f"đáp án ghi {q['answer']}={want!r}, chạy thật ra {got!r}, khớp phương án {match}")
    elif q['type'] == 'replace':
        code, expect = q.get('code', ''), q.get('expect')
        if code.count('___') != 1 or expect is None:
            return out + ['câu replace cần đúng một ___ trong code và trường expect']
        ok = []
        for o in opts:
            k, got, _ = run_snippet(fill(code, o))
            ok.append(k == 'OK' and norm(got) == norm(expect))
        if ok.count(True) != 1 or not ok[q['answer']]:
            out.append(f"các phương án in đúng expect: {[i for i, x in enumerate(ok) if x]}, đáp án ghi {q['answer']}")
        orig = re.search(r'`([^`]+)`', q['question'])
        if 'ban đầu' in q['question'] and orig:
            k, got, _ = run_snippet(fill(code, orig.group(1)))
            if not (k == 'OK' and norm(got) == norm(expect)):
                out.append(f'code gốc trong đề không in ra expect (ra {got!r})')
            if orig.group(1).strip() in [o.strip() for o in opts]:
                out.append('code gốc nằm trong phương án')
    return out


def check_code(ex):
    out = []
    if not 10 <= len(ex['tests']) <= 15:
        out.append(f"cần 10–15 test (đang có {len(ex['tests'])})")
    with tempfile.TemporaryDirectory() as d:
        cwd = os.getcwd()
        os.chdir(d)
        try:
            res = harness.run_tests(ex['solution'], ex)
            res0 = harness.run_tests(ex.get('starter') or 'pass', ex)
        finally:
            os.chdir(cwd)
    for i, r in enumerate(res):
        if not r['ok']:
            out.append(f"test {i} sai với lời giải mẫu -> got={r['got']!r} err={r['error']!r} test={ex['tests'][i]}")
        elif r.get('note'):
            out.append(f"test {i}: expected không khớp chặt với lời giải mẫu (note: {r['note']})")
    if res0 and all(r['ok'] for r in res0):
        out.append('code khởi đầu đã qua hết test')
    if ex['mode'] != 'stdio':
        out.append('bài code phải là chương trình tự đọc input và in kết quả (mode stdio)')
    if ex.get('requireFunction'):
        out.append('trường requireFunction không còn dùng (chỉ chấm output)')
    return out


def verify(mcq, coding, workers=8):
    problems = {}
    ids = collections.Counter(q['id'] for q in mcq) + collections.Counter(c['id'] for c in coding)
    for k, v in ids.items():
        if v > 1:
            problems.setdefault(k, []).append('id trùng')
    with ThreadPoolExecutor(workers) as ex:
        for q, p in zip(mcq, ex.map(check_mcq, mcq)):
            if p:
                problems.setdefault(q['id'], []).extend(p)
    for c in coding:  # harness chạy trong tiến trình hiện tại (đổi cwd), nên chạy tuần tự
        p = check_code(c)
        if p:
            problems.setdefault(c['id'], []).extend(p)
    return problems


if __name__ == '__main__':
    data = sys.argv[1]
    mcq = json.load(open(os.path.join(data, 'mcq.json'), encoding='utf-8'))
    coding = json.load(open(os.path.join(data, 'coding.json'), encoding='utf-8'))
    problems = verify(mcq, coding)
    if '--json' in sys.argv:
        print(json.dumps(problems, ensure_ascii=False, indent=1))
    else:
        print('\n'.join(f'{k}: {m}' for k, ms in problems.items() for m in ms) or 'TẤT CẢ ĐỀU ĐÚNG')
    n = sum(len(v) for v in problems.values())
    types = collections.Counter(q['type'] for q in mcq)
    print(f"-- {len(mcq)} câu trắc nghiệm ({', '.join(f'{k} {v}' for k, v in sorted(types.items()))}), {len(coding)} bài code, {n} vấn đề")
