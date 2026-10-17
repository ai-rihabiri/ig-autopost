"""yt_queue.csv の次の動画を YouTube にショートとしてアップロードする。
必要なシークレット: YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN"""
import csv, json, os, sys, datetime, urllib.request, urllib.parse
E = os.environ
DRY = E.get('DRY_RUN', '0') == '1'
PRIVACY = E.get('YT_PRIVACY', 'private')          # public / unlisted / private
N = int(E.get('POSTS_PER_RUN', '1'))
BASE = E['MEDIA_BASE_URL'].rstrip('/') + '/'

def http(url, data=None, headers={}, method=None):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=600) as r: return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        sys.exit(f'エラー {e.code}: {body[:1500]}')

def access_token():
    data = urllib.parse.urlencode({'client_id': E['YT_CLIENT_ID'], 'client_secret': E['YT_CLIENT_SECRET'],
                                   'refresh_token': E['YT_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode()
    _, _, b = http('https://oauth2.googleapis.com/token', data, {'Content-Type': 'application/x-www-form-urlencoded'})
    return json.loads(b)['access_token']

def upload(tok, row):
    _, _, video = http(BASE + urllib.parse.quote(row['video']))
    meta = {'snippet': {'title': row['title'], 'description': row['description'], 'categoryId': '27',
                        'defaultLanguage': 'ja', 'defaultAudioLanguage': 'ja',
                        'tags': [t.lstrip('#') for t in row['description'].split() if t.startswith('#')][:15]},
            'status': {'privacyStatus': PRIVACY, 'selfDeclaredMadeForKids': False, 'containsSyntheticMedia': True}}
    _, h, _ = http('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
                   json.dumps(meta).encode(), {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json; charset=UTF-8',
                   'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(len(video))}, 'POST')
    loc = h.get('Location') or h.get('location')
    _, _, b = http(loc, video, {'Content-Type': 'video/mp4'}, 'PUT')
    return json.loads(b)


JST = datetime.timezone(datetime.timedelta(hours=9))
def due_now(rows):
    """定時実行のとき：今日の予定時刻（毎日0〜14分ずらす）のうち過ぎた数より、今日の投稿数が少なければ投稿する。
    GitHubの定時実行が抜けても、次の実行で取り戻せる。"""
    import hashlib
    slots = [s.strip() for s in os.environ.get('SLOTS', '').split(',') if s.strip()]
    if not slots: return True
    now = datetime.datetime.now(JST); today = now.strftime('%Y-%m-%d')
    due = 0
    for s in slots:
        h, m = map(int, s.split(':'))
        off = int(hashlib.md5(f'{today}{s}'.encode()).hexdigest(), 16) % 15
        if now >= now.replace(hour=h, minute=m, second=0, microsecond=0) + datetime.timedelta(minutes=off): due += 1
    times = [r['posted_at'] for r in rows if r['posted_at'][:10] == today]
    print(f'今日の予定: {due}/{len(slots)} 本が時刻を過ぎています。今日の投稿済み: {len(times)} 本')
    if len(times) >= due: return False
    gap = int(os.environ.get('MIN_GAP_MIN', '50'))
    if times:
        last = datetime.datetime.strptime(max(times), '%Y-%m-%d %H:%M').replace(tzinfo=JST)
        if now - last < datetime.timedelta(minutes=gap):
            print(f'前回の投稿から{gap}分たっていないので、次の実行で投稿します'); return False
    return True

rows = list(csv.DictReader(open('yt_queue.csv', encoding='utf-8')))
if E.get('SCHEDULED') == '1' and not due_now(rows): print('今は投稿の時間ではありません'); sys.exit(0)
todo = [r for r in rows if r['status'] != 'posted'][:N]
if not todo: print('予定表の動画はすべて投稿済みです'); sys.exit(0)
if DRY:
    for r in todo: print('【確認のみ】', r['video'], '\n', r['title'], '\n', r['description'])
    sys.exit(0)
tok = access_token()
for r in todo:
    res = upload(tok, r)
    r['status'] = 'posted'; r['video_id'] = res['id']
    r['posted_at'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
    print(f"投稿しました: No.{r['no']} {r['title']} → https://youtube.com/shorts/{res['id']}（公開設定: {res['status']['privacyStatus']}）")
    with open('yt_queue.csv', 'w', encoding='utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
