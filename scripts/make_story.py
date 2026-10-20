"""直前に投稿したリールから、ストーリー用の動画（冒頭15秒＋noteへの案内画面）を作る。
作ったら stories/ に保存し、ファイル名を story_target.txt に書く。対象がなければ何もしない。"""
import csv, datetime, os, subprocess, urllib.request, urllib.parse
JST = datetime.timezone(datetime.timedelta(hours=9))
BASE = os.environ['MEDIA_BASE_URL'].rstrip('/') + '/'
CLIP = float(os.environ.get('STORY_CLIP_SEC', '15'))
END = 4.5
rows = list(csv.DictReader(open('queue.csv', encoding='utf-8')))
now = datetime.datetime.now(JST)
cand = [r for r in rows if r['status'] == 'posted' and not r.get('story_id') and r['posted_at'][:2] == '20'
        and now - datetime.datetime.strptime(r['posted_at'], '%Y-%m-%d %H:%M').replace(tzinfo=JST) < datetime.timedelta(hours=3)]
if not cand: print('ストーリーにする新しいリールはありません'); raise SystemExit(0)
r = max(cand, key=lambda x: x['posted_at'])
src = '/tmp/src.mp4'; urllib.request.urlretrieve(BASE + urllib.parse.quote(r['video']), src)
os.makedirs('stories', exist_ok=True)
out = 'stories/' + r['video'].replace('.mp4', '_story.mp4')
fc = (f"[0:v]fps=30,setsar=1,fade=t=out:st={CLIP-0.4}:d=0.4,format=yuv420p[v0];"
      f"[1:v]scale=1080:1920,fps=30,setsar=1,fade=t=in:st=0:d=0.4,format=yuv420p[v1];"
      f"[0:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=out:st={CLIP-1.2}:d=1.2[a0];"
      f"[2:a]aformat=channel_layouts=stereo[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]")
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-t', str(CLIP), '-i', src, '-loop', '1', '-t', str(END), '-i', 'scripts/story_end.png',
                '-f', 'lavfi', '-t', str(END), '-i', 'anullsrc=r=48000:cl=stereo', '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
open('story_target.txt', 'w').write(r['no'] + '\t' + out)
print('ストーリー動画を作成:', out)
