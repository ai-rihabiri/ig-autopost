"""queue.csv の次の未投稿動画を Instagram リールとして投稿する。
環境変数:
  IG_ACCESS_TOKEN  (必須) アクセストークン
  IG_USER_ID       (任意) InstagramユーザーID。未設定なら自動取得（Instagramログイン方式のみ）
  IG_LOGIN         instagram(既定) または facebook
  MEDIA_BASE_URL   動画が公開されているURLの頭（例: GitHubリリースの .../releases/download/videos/）
  POSTS_PER_RUN    1回の実行で投稿する本数（既定1）
  DRY_RUN          1 なら投稿せず内容だけ表示
"""
import csv, os, sys, time, datetime, json
import urllib.request, urllib.parse, urllib.error

TOKEN = os.environ.get('IG_ACCESS_TOKEN', '')
LOGIN = os.environ.get('IG_LOGIN', 'instagram').lower()
HOST = os.environ.get('TEST_HOST') or 'https://graph.instagram.com' if LOGIN == 'instagram' else 'https://graph.facebook.com'
VER = os.environ.get('GRAPH_VERSION', '').strip('/')
BASE = HOST + ('/' + VER if VER else '')
MEDIA_BASE = os.environ.get('MEDIA_BASE_URL', '')
DRY = os.environ.get('DRY_RUN') == '1'
N = int(os.environ.get('POSTS_PER_RUN', '1'))
QUEUE = os.environ.get('QUEUE_FILE', 'queue.csv')

def call(method, path, params=None, headers=None, data=None, url=None):
    params = dict(params or {}); 
    if not url: params['access_token'] = TOKEN
    u = url or f'{BASE}/{path}'
    body = None
    if method == 'GET': u += '?' + urllib.parse.urlencode(params)
    elif data is not None: body = data
    else: body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(u, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=600) as r: return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        raise SystemExit(f'APIエラー {e.code} {path}: {e.read().decode()[:800]}')

def resolve(url):
    """GitHubリリースなどのリダイレクトをたどって最終URLを返す（Meta側の取得失敗を防ぐ）"""
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=60) as r: return r.geturl()
    except Exception: return url

def wait(cid):
    for i in range(30):
        st = call('GET', cid, {'fields': 'status_code,status'})
        sc = st.get('status_code'); print('  処理状況:', sc)
        if sc == 'FINISHED': return
        if sc in ('ERROR', 'EXPIRED'): raise SystemExit(f'動画の処理に失敗しました: {st}')
        time.sleep(20)
    raise SystemExit('処理が10分以内に終わりませんでした')

def publish(row, uid):
    cap = row['caption']
    if True:
        if not MEDIA_BASE: raise SystemExit('MEDIA_BASE_URL が未設定です')
        p = {'media_type': 'REELS', 'video_url': resolve(MEDIA_BASE + urllib.parse.quote(row['video'])), 'caption': cap, 'share_to_feed': 'true'}
        if os.environ.get('AI_LABEL', '1') == '1': p['is_ai_generated'] = 'true'
        cid = call('POST', f'{uid}/media', p)['id']
    print('  コンテナ作成:', cid); wait(cid)
    return call('POST', f'{uid}/media_publish', {'creation_id': cid})['id']


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

def main():
    rows = list(csv.DictReader(open(QUEUE, encoding='utf-8')))
    if os.environ.get('SCHEDULED') == '1' and os.path.exists('scripts/PAUSE'): print('一時停止中（scripts/PAUSE があります）'); return
    if os.environ.get('SCHEDULED') == '1' and not due_now(rows): print('今は投稿の時間ではありません'); return
    todo = [r for r in rows if r['status'] != 'posted'][:N]
    if not todo: print('投稿待ちの動画はありません'); return
    if DRY:
        for r in todo: print(f'[DRY RUN] No.{r["no"]} {r["video"]}\n{r["caption"][:120]}…'); 
        return
    if not TOKEN: raise SystemExit('IG_ACCESS_TOKEN が未設定です')
    uid = os.environ.get('IG_USER_ID') or call('GET', 'me', {'fields': 'user_id,username'}).get('user_id')
    lim = call('GET', f'{uid}/content_publishing_limit', {'fields': 'quota_usage'})
    print('24時間以内のAPI投稿数:', lim)
    for r in todo:
        print(f'▶ No.{r["no"]} {r["video"]} を投稿します')
        r['media_id'] = publish(r, uid); r['status'] = 'posted'
        r['posted_at'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M')
        print('  投稿完了 media_id =', r['media_id'])
        with open(QUEUE, 'w', encoding='utf-8', newline='') as fp:
            w = csv.DictWriter(fp, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

if __name__ == '__main__': main()
