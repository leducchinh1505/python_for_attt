"""Kiểm chứng ngân hàng câu hỏi: chạy code của câu trắc nghiệm dạng output
và chạy lời giải mẫu của bài code qua chính bộ chấm (harness) của app.
Dùng: py -I verify.py <thu_muc_data>
"""
import json, os, subprocess, sys, tempfile, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness  # noqa: E402
sys.stdout.reconfigure(encoding="utf-8")

data = sys.argv[1]
mcq = json.load(open(os.path.join(data, 'mcq.json'), encoding='utf-8'))
coding = json.load(open(os.path.join(data, 'coding.json'), encoding='utf-8'))
problems = []


def run_snippet(code):
    p = subprocess.run([sys.executable, '-I', '-X', 'utf8', '-c', code], capture_output=True, text=True,
                       encoding='utf-8', timeout=10, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
    if p.returncode != 0:
        last = [l for l in p.stderr.strip().splitlines() if l.strip()][-1]
        return ('EXC', last.split(':')[0].strip(), p.stdout)
    return ('OK', p.stdout.rstrip('\n'), p.stdout)


ids = collections.Counter(q['id'] for q in mcq) + collections.Counter(c['id'] for c in coding)
for k, v in ids.items():
    if v > 1:
        problems.append(f'{k}: id trùng')

for q in mcq:
    opts = q['options']
    if len(opts) != 4 or len(set(opts)) != 4:
        problems.append(f"{q['id']}: phải có 4 phương án khác nhau")
    if q['type'] != 'output' or not q.get('code'):
        continue
    kind, got, stdout = run_snippet(q['code'])
    if kind == 'EXC' and stdout:
        problems.append(f"{q['id']}: in ra output trước khi lỗi {got}")
    want = opts[q['answer']]
    norm = lambda s: '\n'.join(l.rstrip() for l in s.split('\n')).strip()
    if norm(got) != norm(want):
        match = [i for i, o in enumerate(opts) if norm(o) == norm(got)]
        problems.append(f"{q['id']}: đáp án ghi {q['answer']}={want!r}, chạy thật ra {got!r}, khớp phương án {match}")

for ex in coding:
    with tempfile.TemporaryDirectory() as d:
        cwd = os.getcwd()
        os.chdir(d)
        try:
            res = harness.run_tests(ex['solution'], ex)
        finally:
            os.chdir(cwd)
    bad = [i for i, r in enumerate(res) if not r['ok']]
    if len(ex['tests']) < 4:
        problems.append(f"{ex['id']}: chỉ có {len(ex['tests'])} test")
    for i in bad:
        problems.append(f"{ex['id']}: test {i} sai với lời giải mẫu -> got={res[i]['got']!r} err={res[i]['error']!r} test={ex['tests'][i]}")

print('\n'.join(problems) if problems else 'TẤT CẢ ĐỀU ĐÚNG')
print(f'-- {len(mcq)} câu trắc nghiệm, {len(coding)} bài code, {len(problems)} vấn đề')
