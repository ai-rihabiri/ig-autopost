# Instagram リール自動投稿キット（臨床の疑問【1分解説】用）

GitHub Actions が毎日決まった時間に、`queue.csv` の次の動画を Instagram リールとして投稿します。
パソコンを起動しておく必要はありません。投稿済みの動画は `queue.csv` に自動で記録されます。

```
動画(mp4) ──▶ GitHubリリースに置く（公開URL）
queue.csv ──▶ 毎日19:00に GitHub Actions が起動 ──▶ Instagram API ──▶ リール投稿
                              └──▶ queue.csv を「posted」に更新
```

## 最初の設定（30〜60分・1回だけ）

### 1. Instagram をプロアカウントに切り替える
Instagramアプリ → プロフィール → 設定 → 「アカウントの種類とツール」→「プロアカウントに切り替える」→ **クリエイター** を選択（無料）。
※APIでの投稿はプロアカウントでしかできません。Facebookページとの連携は不要です。

### 2. Meta の開発者アプリを作ってトークンを取得
1. https://developers.facebook.com/ にログイン（Facebookアカウントが必要）→「マイアプリ」→「アプリを作成」
2. ユースケースで **「Instagramでメッセージやコンテンツを管理」**（Instagram API）を選ぶ
3. 「Instagramログインによる API 設定」を開き、**アクセストークンを生成** → 自分の Instagram アカウントを追加してログイン
4. 表示された **アクセストークン**（長期・60日）と **InstagramユーザーID** を控える
   - 権限 `instagram_business_basic` と `instagram_business_content_publish` が含まれていることを確認
   - 自分のアカウントに投稿するだけなら、アプリは開発モードのままで使えます（審査不要）

### 3. GitHub にリポジトリを作る
1. https://github.com/ でアカウント作成 → 新しいリポジトリを **Public** で作成（動画の公開URLを作るため）
2. このキットの中身（`.github` フォルダを含む全部）をアップロード
3. 動画をリリースに置く
   - かんたん：リポジトリの「Releases」→「Create a new release」→ タグ名 `videos` → mp4 をドラッグ＆ドロップ → Publish
   - まとめて：`./scripts/upload_videos.sh <mp4フォルダ>`（gh CLI）

### 4. 秘密情報と設定を登録
リポジトリの Settings → Secrets and variables → Actions

| 種類 | 名前 | 値 |
|---|---|---|
| Secret | `IG_ACCESS_TOKEN` | 手順2のアクセストークン |
| Secret | `IG_USER_ID` | 手順2のInstagramユーザーID |
| Secret | `GH_PAT` | トークン自動延長用（下記）。なくても投稿は動く |
| Variable | `MEDIA_BASE_URL` | `https://github.com/<ユーザー名>/<リポジトリ名>/releases/download/videos/` |
| Variable | `POSTS_PER_RUN` | 1回の投稿本数（省略時 1） |

`GH_PAT` は GitHub の Settings → Developer settings → Fine-grained tokens で、このリポジトリの **Secrets: Read and write** 権限を付けて作成します。
これを入れておくと、毎月1日と15日にトークンが自動延長され、60日の期限切れを防げます。

### 5. すでに投稿した動画を「投稿済み」にする
例：No.1〜120 を手動投稿済みなら
```
python scripts/mark_posted.py 1-120
```
（またはGitHub上で `queue.csv` を開き、該当行の `status` を `posted` に書き換え）

### 6. テスト
Actions →「Instagram自動投稿」→ Run workflow → `dry_run` を `1` で実行 → ログに次の投稿予定が出ればOK。
`0` で実行すると実際に1本投稿されます。

## 日々の運用
- **新しい動画を追加**：mp4 をリリース `videos` に追加 → `python scripts/build_queue.py <動画フォルダの親>` で `queue.csv` を更新してアップロード（投稿済みの記録は引き継がれます）
- **投稿時間を変える**：`.github/workflows/post.yml` の `cron`（UTC表記。日本時間19時＝`0 10 * * *`、朝7時＝`0 22 * * *`）
- **1日2本にする**：cron を2行にするか、`POSTS_PER_RUN` を 2 に
- **投稿順を変える**：`queue.csv` の行を並べ替え（上から順に投稿）

## 注意点
- Instagram APIの投稿上限は 24時間で100件です。
- GitHub の定時実行は混雑時に数分〜数十分遅れることがあります。
- キャプションは `captions.txt` の内容がそのまま使われます（ハッシュタグ込み）。
- 投稿に失敗した日は Actions のログにエラー内容が出ます（トークン期限切れ・動画URL不正が主な原因）。
