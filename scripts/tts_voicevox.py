"""VOICEVOXエンジン（GitHub Actions内で起動）で tts/jobs.json の文章を音声にする。
jobs.json: [{"out": "tts/out/xxx.wav", "text": "...", "speaker": "青山龍星", "style": "ノーマル", "speed": 1.1, "pitch": 0, "intonation": 1.1}]"""
import json, os, time, urllib.request, urllib.parse
B = 'http://127.0.0.1:50021'
for i in range(120):
    try: urllib.request.urlopen(B + '/version', timeout=5); break
    except Exception: time.sleep(3)
sp = json.load(urllib.request.urlopen(B + '/speakers'))
ids = {(s['name'], st['name']): st['id'] for s in sp for st in s['styles']}
uuid = {s['name']: s['speaker_uuid'] for s in sp}
open('tts/speakers.txt', 'w', encoding='utf-8').write('\n'.join(f'{n}\t{s}\t{i}' for (n, s), i in sorted(ids.items(), key=lambda x: x[1])))
import subprocess, sys
JOBS = sys.argv[1] if len(sys.argv) > 1 else 'tts/jobs.json'
for j in json.load(open(JOBS, encoding='utf-8')):
    if j['out'].endswith('.mp3') and os.path.exists(j['out']): continue
    sid = j.get('id') or ids[(j['speaker'], j.get('style', 'ノーマル'))]
    q = json.load(urllib.request.urlopen(urllib.request.Request(B + '/audio_query?' + urllib.parse.urlencode({'text': j['text'], 'speaker': sid}), method='POST')))
    q['speedScale'] = j.get('speed', 1.1); q['pitchScale'] = j.get('pitch', 0); q['intonationScale'] = j.get('intonation', 1.0)
    q['prePhonemeLength'] = .05; q['postPhonemeLength'] = .1
    w = urllib.request.urlopen(urllib.request.Request(B + '/synthesis?speaker=' + str(sid), data=json.dumps(q).encode(), headers={'Content-Type': 'application/json'})).read()
    os.makedirs(os.path.dirname(j['out']), exist_ok=True)
    if j['out'].endswith('.mp3'):
        open('/tmp/t.wav', 'wb').write(w); subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/t.wav', '-b:a', '96k', j['out']], check=True)
    else: open(j['out'], 'wb').write(w)
    print('ok', j['out'], sid, flush=True)

used = sorted({j['speaker'] for j in json.load(open(JOBS, encoding='utf-8')) if 'speaker' in j})
for n in used:
    info = json.load(urllib.request.urlopen(B + '/speaker_info?' + urllib.parse.urlencode({'speaker_uuid': uuid[n]})))
    open(f'tts/policy_{n}.md', 'w', encoding='utf-8').write(info.get('policy', ''))
    print('policy saved', n)
