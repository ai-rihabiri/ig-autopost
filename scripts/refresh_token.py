"""Instagramログイン方式の長期トークン(60日)を延長して表示する。GitHub Actions では secrets を更新する。"""
import os, json, urllib.request, urllib.parse
t = os.environ['IG_ACCESS_TOKEN']
u = 'https://graph.instagram.com/refresh_access_token?' + urllib.parse.urlencode({'grant_type': 'ig_refresh_token', 'access_token': t})
r = json.loads(urllib.request.urlopen(u, timeout=60).read())
print('有効期限(秒):', r.get('expires_in'))
open(os.environ.get('OUT', 'new_token.txt'), 'w').write(r['access_token'])
