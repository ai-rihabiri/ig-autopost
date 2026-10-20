"""story_target.txt の動画をストーリーズに投稿し、queue.csv の story_id に記録する。"""
import csv, os, sys, time, json, urllib.request, urllib.parse
sys.path.insert(0, 'scripts')
import post_reel as P
if not os.path.exists('story_target.txt'): raise SystemExit(0)
no, path = open('story_target.txt').read().strip().split('\t')
url = os.environ['STORY_BASE_URL'].rstrip('/') + '/' + urllib.parse.quote(path)
uid = os.environ.get('IG_USER_ID')
cid = P.call('POST', f'{uid}/media', {'media_type': 'STORIES', 'video_url': url})['id']
print('コンテナ作成:', cid); P.wait(cid)
sid = P.call('POST', f'{uid}/media_publish', {'creation_id': cid})['id']
rows = list(csv.DictReader(open('queue.csv', encoding='utf-8')))
keys = list(rows[0].keys())
if 'story_id' not in keys: keys.append('story_id')
for r in rows:
    r.setdefault('story_id', '')
    if r['no'] == no: r['story_id'] = sid
with open('queue.csv', 'w', encoding='utf-8', newline='') as fp:
    w = csv.DictWriter(fp, fieldnames=keys); w.writeheader(); w.writerows(rows)
print('ストーリー投稿完了 No.', no, sid)
