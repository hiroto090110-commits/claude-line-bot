# Gemini LINE Bot - セットアップ手順

💰 **完全無料**（Gemini API: 月1500リクエストまで無料）

スマホからGeminiと自由に会話できるLINE Botです。

## 機能

### 1. 汎用会話機能
- LINEでメッセージ送信 → Geminiが自然な日本語で応答
- 質問、雑談、プログラミング相談など幅広く対応
- 長い返答も自動分割して送信

### 2. グループチャット対応
- グループでは@メンション時のみ反応
- 個人チャットでは常時応答

### 3. 会話履歴機能（メモリベース）
- 過去10往復（20メッセージ）の会話を記憶
- 文脈を考慮した自然な会話が可能
- **注意**: 再デプロイ時や15分以上の非アクティブで履歴はリセット

### 制限事項
- **レート制限**: 1分間に5リクエストまで（Gemini無料枠）
- 短時間に複数メッセージを送ると30秒待機が必要
- **履歴保持**: メモリベース（再起動で消去）

### 凍結中の機能
- ~~スケジュール機能~~（一時凍結）

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

### 1. 汎用会話の例

**質問・相談**:
```
Pythonでファイルを読み書きする方法を教えて
```

```
今日の夕食何がいいかな？
```

**コード生成**:
```
動画編集アプリに字幕生成機能を追加して
```

```
FlaskアプリにGoogle OAuth認証を組み込んで
```

### 2. グループチャットでの使い方

グループでは**@メンション**をつけた時のみ反応します：

```
@BotName こんにちは
```

```
@BotName Pythonでリスト操作する方法を教えて
```

個人チャットでは@メンションは不要で、常に応答します。

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

### 会話履歴が突然リセットされる

**原因**:
- Renderの無料プランでは15分以上非アクティブでアプリが停止
- 再デプロイ時にメモリがクリア

**対処法**:
- 会話を続ける際は15分以内に次のメッセージを送信
- 長時間空く場合は「前回の会話の続きだけど...」と明示

### 過去の会話を覚えていない

- 最新10往復（20メッセージ）のみ保持
- それ以前の会話は自動削除されます
- 重要な情報は再度伝えてください

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
