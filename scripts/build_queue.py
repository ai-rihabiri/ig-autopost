"""captions.txt と mp4 から投稿キュー(queue.csv)を作る。
使い方: python scripts/build_queue.py <動画フォルダの親> [--out queue.csv]
各フォルダの T{No}_*.mp4 と captions.txt の【… No.N …】ブロックを番号で突き合わせます。"""
import csv, glob, os, re, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out', default='queue.csv'); a = ap.parse_args()
caps, files, covers = {}, {}, {}
for cf in glob.glob(os.path.join(a.root, '**', 'captions.txt'), recursive=True):
    for blk in re.split(r'\n\s*\n(?=【)', open(cf, encoding='utf-8').read().strip()):
        m = re.search(r'No\.(\d+)', blk.splitlines()[0])
        if m: caps[int(m.group(1))] = blk.strip()
for f in glob.glob(os.path.join(a.root, '**', 'T*.mp4'), recursive=True):
    m = re.match(r'T(\d+)_', os.path.basename(f))
    if m:
        n = int(m.group(1)); files[n] = os.path.basename(f)
old = {}
if os.path.exists(a.out):
    for r in csv.DictReader(open(a.out, encoding='utf-8')): old[r['no']] = r
rows = []
for n in sorted(files):
    if n not in caps: print(f'! No.{n}: キャプションが見つかりません', file=sys.stderr); continue
    o = old.get(str(n), {})
    rows.append({'no': n, 'video': files[n], 'caption': caps[n],
                 'status': o.get('status', 'pending'), 'posted_at': o.get('posted_at', ''), 'media_id': o.get('media_id', '')})
with open(a.out, 'w', encoding='utf-8', newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=['no', 'video', 'caption', 'status', 'posted_at', 'media_id']); w.writeheader(); w.writerows(rows)
print(f'{len(rows)} 件を {a.out} に書き出しました（posted 済み {sum(r["status"]=="posted" for r in rows)} 件）')
