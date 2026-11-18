"""Đóng gói app.html + harness.py + data/*.json thành một file index.html duy nhất.
Dùng: py -I src/build.py
"""
import json, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DATA = os.path.join(ROOT, 'src'), os.path.join(ROOT, 'data')
read = lambda p: open(p, encoding='utf-8').read()

TOPICS = [
    ('T1', 'Kiểu dữ liệu, toán tử và chuỗi', 1, 'Giáo trình chương 2'),
    ('T2', 'Điều kiện và vòng lặp', 1, 'Giáo trình chương 4, 6'),
    ('T3', 'List, tuple và ma trận', 1, 'Giáo trình chương 3'),
    ('T4', 'Dictionary và set', 1, 'Giáo trình chương 5 (set: bổ sung)'),
    ('T5', 'Hàm và lambda', 1, 'Giáo trình chương 7'),
    ('T6', 'File và exception', 1, 'Giáo trình chương 9'),
    ('T7', 'Lớp và đối tượng (OOP)', 1, 'Giáo trình chương 8'),
    ('T8', 'Module và thư viện chuẩn', 2, 'Giáo trình chương 7.7, 8.4, 8.5'),
]

mcq = json.load(open(os.path.join(DATA, 'mcq.json'), encoding='utf-8'))
coding = json.load(open(os.path.join(DATA, 'coding.json'), encoding='utf-8'))
materials = json.load(open(os.path.join(DATA, 'materials.json'), encoding='utf-8'))
for q in mcq:
    q['code'] = q.get('code') or ''
for c in coding:
    c['files'] = c.get('files') or {}

bank = {
    'meta': {
        'generated': datetime.date.today().isoformat(),
        'note': 'Đáp án trắc nghiệm dạng đọc code và lời giải mẫu của mọi bài code đã được kiểm chứng bằng cách chạy Python thật.',
    },
    'topics': [{'id': i, 'name': n, 'priority': p, 'chapters': ch} for i, n, p, ch in TOPICS],
    'mcq': mcq, 'coding': coding, 'materials': materials,
}
bank_json = json.dumps(bank, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
harness_js = json.dumps(read(os.path.join(SRC, 'harness.py')), ensure_ascii=False).replace('</', '<\\/')

html = read(os.path.join(SRC, 'app.html'))
assert '/*__BANK__*/' in html and '/*__HARNESS__*/""' in html
html = html.replace('/*__BANK__*/', bank_json).replace('/*__HARNESS__*/""', harness_js)
out = os.path.join(ROOT, 'index.html')
open(out, 'w', encoding='utf-8').write(html)
print(f'{out}: {len(html) // 1024} KB, {len(mcq)} MCQ, {len(coding)} bài code')
