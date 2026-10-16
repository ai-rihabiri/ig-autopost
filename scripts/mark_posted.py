"""すでに手動で投稿した動画を「投稿済み」にする。例: python scripts/mark_posted.py 1-120 135 140"""
import csv, sys
nums = set()
for a in sys.argv[1:]:
    if '-' in a: x, y = map(int, a.split('-')); nums |= set(range(x, y + 1))
    else: nums.add(int(a))
rows = list(csv.DictReader(open('queue.csv', encoding='utf-8')))
for r in rows:
    if int(r['no']) in nums and r['status'] != 'posted': r['status'] = 'posted'; r['posted_at'] = 'manual'
with open('queue.csv', 'w', encoding='utf-8', newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'投稿済み: {sum(r["status"]=="posted" for r in rows)} 件 / 残り: {sum(r["status"]!="posted" for r in rows)} 件')
