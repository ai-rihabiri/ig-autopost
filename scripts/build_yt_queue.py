"""queue.csv（Instagram用）から YouTube用の予定表 yt_queue.csv を作る／新しい動画を追記する。
すでに yt_queue.csv にある番号はそのまま残す（投稿済みの記録を消さない）。"""
import csv, os, re
CLOSING = ("📚勉強するほど稼げるセラピストになる\n"
           "AIで作った動画で副業・収益化に挑戦中。やり方・使うAI・収益化の流れはチャンネルのリンクのnoteで公開中")
def convert(row):
    cap = row['caption'].strip()
    first, *rest = cap.split('\n')
    m = re.search(r'No\.\s*(\d+)\s*(.+?)】', first)
    theme = m.group(2).strip() if m else os.path.splitext(row['video'])[0]
    body = cap.split('\n\n')[0].split('\n')[1:]
    tags = [l for l in cap.split('\n') if l.startswith('#')]
    credit = [l for l in cap.split('\n') if 'VOICEVOX' in l]
    title = f'{theme}を1分で解説【セラピスト向け】 #Shorts'
    if len(title) > 100: title = title[:100]
    desc = '\n'.join(body) + '\n\n' + CLOSING + ('\n' + '\n'.join(credit) if credit else '') + '\n\n' + (tags[-1] if tags else '') + ' #Shorts'
    return {'no': row['no'], 'video': row['video'], 'title': title.replace('<', '＜').replace('>', '＞'),
            'description': desc.replace('<', '＜').replace('>', '＞')[:4900], 'status': 'pending', 'posted_at': '', 'video_id': ''}
src = list(csv.DictReader(open('queue.csv', encoding='utf-8')))
old = {}
if os.path.exists('yt_queue.csv'):
    old = {r['no']: r for r in csv.DictReader(open('yt_queue.csv', encoding='utf-8'))}
rows = [old.get(r['no']) or convert(r) for r in src]
with open('yt_queue.csv', 'w', encoding='utf-8', newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=['no', 'video', 'title', 'description', 'status', 'posted_at', 'video_id'])
    w.writeheader(); w.writerows(rows)
print(f'YouTube予定表: {len(rows)} 件（投稿済み {sum(r["status"]=="posted" for r in rows)} 件）')
