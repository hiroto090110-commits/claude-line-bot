# Gemini LINE Bot - セットアップ手順

💰 **完全無料**（Gemini API: 月1500リクエストまで無料）

スマホからGeminiに開発依頼できるLINE Botです。

## 機能

### 1. コード生成機能
- LINEでメッセージ送信 → Geminiが自動でコード生成
- 「動画編集アプリに○○機能追加して」などの依頼に対応
- 長い返答も自動分割して送信

### 2. スケジュール機能 ✨NEW
- 自然言語でスケジュール登録（「明日14時から会議」など）
- ICS（カレンダー）ファイル自動生成
- タップするだけでiPhone/Androidカレンダーに追加可能
- グループチャット対応（@メンション必要）

### 制限事項
- **レート制限**: 1分間に5リクエストまで（Gemini無料枠）
- 短時間に複数メッセージを送ると30秒待機が必要

---

## セットアップ手順

### 1. LINE Developers アカウント作成

1. [LINE Developers Console](https://developers.line.biz/console/) にアクセス
2. LINEアカウントでログイン
3. 「新規プロバイダー作成」をクリック
4. プロバイダー名を入力（例: "MyClaude"）

### 2. Messaging API チャネル作成

1. 作成したプロバイダーを選択
2. 「新規チャネル作成」→「Messaging API」を選択
3. 以下を入力:
   - チャネル名: `Claude Bot`
   - チャネル説明: `AI開発アシスタント`
   - カテゴリ: `個人用ツール`
4. 「作成」をクリック

### 3. チャネル設定

1. 作成したチャネルの「Messaging API設定」タブに移動
2. 以下の設定を変更:
   - **応答メッセージ**: `無効`
   - **Webhook**: `有効`
   - **グループ・複数人トークへの参加**: `無効`（個人用）

3. 必要な情報を取得:
   - **Channel Secret**: 「チャネル基本設定」タブにあります
   - **Channel Access Token**: 「Messaging API設定」タブで「発行」ボタンをクリック

### 4. Anthropic API キー取得

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. 「API Keys」→「Create Key」
3. キーをコピーして保存

### 5. Render.com でデプロイ

1. [Render.com](https://render.com/) にアクセス
2. GitHubアカウントでサインアップ
3. 「New +」→「Blueprint」を選択
4. このリポジトリを接続
5. 「render.yaml」を検出したら「Apply」

6. 環境変数を設定:
   - `LINE_CHANNEL_ACCESS_TOKEN`: LINEのChannel Access Token
   - `LINE_CHANNEL_SECRET`: LINEのChannel Secret
   - `ANTHROPIC_API_KEY`: AnthropicのAPI Key

7. デプロイ完了後、URLをコピー（例: `https://claude-line-bot.onrender.com`）

### 6. LINE Webhook URL 設定

1. LINE Developers Consoleに戻る
2. 「Messaging API設定」タブ
3. **Webhook URL**に以下を入力:
   ```
   https://your-app.onrender.com/callback
   ```
4. 「検証」ボタンをクリック → 成功すればOK

### 7. 友だち追加してテスト

1. 「Messaging API設定」タブのQRコードをスキャン
2. Botを友だち追加
3. メッセージを送信:
   ```
   Pythonで簡単なWebサーバーを作成して
   ```
4. Claudeから返信が来れば成功！

---

## 使い方

### 1. コード生成機能の例

```
動画編集アプリに字幕生成機能を追加して
```

```
ポートフォリオサイトにダークモード機能を実装して
```

```
FlaskアプリにGoogle OAuth認証を組み込んで
```

**回答フォーマット**:
1. 簡潔な説明（1-2行）
2. コードブロック
3. 使い方・注意点

### 2. スケジュール機能の例

**個人チャット**:
```
明日14時から会議のスケジュール作成して
```

```
来週月曜10時〜12時でミーティング登録
```

**グループチャット**:
```
@BotName 明後日15時からプレゼン準備の予定登録
```

**回答フォーマット**:
```
📅 スケジュール登録完了

1. 会議
   2025年12月18日(水) 14:00〜15:00

📥 カレンダーに追加:
https://your-bot.com/download/xxx

※ リンクをタップするとカレンダーアプリで開きます
```

---

## トラブルシューティング

### Botが応答しない

1. Render.comのログを確認:
   - Renderダッシュボード → Logs
2. LINE Webhook URLが正しいか確認
3. 環境変数が設定されているか確認

### 「只今アクセスが集中しています」と表示される

**原因**: Gemini APIのレート制限（1分間に5リクエスト）

**対処法**:
1. **30秒待ってから再送信**
2. メッセージの送信間隔を空ける
3. グループチャットでは@メンションがある時のみ反応

**無料枠の詳細**:
- 1分間: 5リクエスト
- 1日: 1500リクエスト
- 1ヶ月: 無制限（1日制限の範囲内）

### エラーメッセージが返ってくる

- Gemini API キーが有効か確認
- API使用量が月1500リクエストを超えていないか確認

### 長い返答が途中で切れる

- LINE制限（5000文字）により自動分割されます
- 複数のメッセージに分かれて届きます

### スケジュールが正しく認識されない

- 明確な日時表現を使用（「明日14時」「12/20 15:00」など）
- 「スケジュール」「予定」などのキーワードを含める

---

## 💰 費用（完全無料）

- **LINE Messaging API**: 無料（月1000通まで）
- **Render.com**: 無料プラン（月750時間）
- **Gemini API**: **完全無料**（月1500リクエストまで）

**合計: 0円/月**（個人使用の範囲内）

---

## セキュリティ

- API Keyは環境変数で管理（`.env`ファイルは`.gitignore`済み）
- LINE署名検証でWebhook認証
- HTTPS通信のみ

---

## 開発者向け

### ローカル実行

```bash
cd /Users/he/ai-project/claude-line-bot

# 環境変数設定
export LINE_CHANNEL_ACCESS_TOKEN="your_token"
export LINE_CHANNEL_SECRET="your_secret"
export ANTHROPIC_API_KEY="your_key"

# 実行
python app.py
```

### ngrokでテスト

```bash
ngrok http 5000
# 表示されたURLをLINE Webhook URLに設定
```

---

## ライセンス

MIT License
