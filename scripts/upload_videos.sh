#!/bin/bash
# 動画をGitHubリリース「videos」にまとめてアップロード（gh CLI が必要: https://cli.github.com/）
# 使い方: ./scripts/upload_videos.sh <mp4が入ったフォルダ>
set -e
DIR="$1"; [ -d "$DIR" ] || { echo "フォルダを指定してください"; exit 1; }
gh release view videos >/dev/null 2>&1 || gh release create videos --title "videos" --notes "投稿用動画の置き場"
find "$DIR" -name 'T*.mp4' -print0 | xargs -0 -n 20 gh release upload videos --clobber
echo "完了。MEDIA_BASE_URL は https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/download/videos/ です"
