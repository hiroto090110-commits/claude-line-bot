# Supabase セットアップガイド

## 1. Supabaseアカウント作成

1. [Supabase](https://supabase.com/) にアクセス
2. 「Start your project」をクリック
3. GitHubアカウントでサインアップ

## 2. 新規プロジェクト作成

1. ダッシュボードで「New project」をクリック
2. 以下を入力:
   - **Name**: `gemini-line-bot`
   - **Database Password**: 強力なパスワードを生成（保存必須）
   - **Region**: `Northeast Asia (Tokyo)` または `Southeast Asia (Singapore)`
   - **Pricing Plan**: `Free` （500MB、無制限API リクエスト）
3. 「Create new project」をクリック（1-2分で完了）

## 3. データベーステーブル作成

1. 左サイドバーの「Table Editor」をクリック
2. 「Create a new table」をクリック
3. 「SQL Editor」タブに移動
4. 以下のSQLを実行:

```sql
-- 会話履歴テーブル作成
CREATE TABLE conversation_history (
  id BIGSERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス作成（検索高速化）
CREATE INDEX idx_user_id ON conversation_history(user_id);
CREATE INDEX idx_created_at ON conversation_history(created_at DESC);

-- ユーザーごとの会話数を確認するビュー（オプション）
CREATE VIEW user_conversation_stats AS
SELECT
  user_id,
  COUNT(*) as message_count,
  MIN(created_at) as first_message,
  MAX(created_at) as last_message
FROM conversation_history
GROUP BY user_id;
```

## 4. API認証情報取得

1. 左サイドバーの「Settings」→「API」をクリック
2. 以下の情報をコピー:
   - **Project URL**: `https://xxxxxxxx.supabase.co`
   - **anon public key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

**重要**: `service_role key`ではなく`anon public`キーを使用します。

## 5. 環境変数設定

### ローカル開発用（`.env`ファイル）

```bash
# .envファイルに追加
SUPABASE_URL=https://xxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Render.com デプロイ用

1. Renderダッシュボードで`gemini-line-bot`サービスを選択
2. 「Environment」タブに移動
3. 「Add Environment Variable」をクリック
4. 以下を追加:
   - Key: `SUPABASE_URL`, Value: `https://xxxxxxxx.supabase.co`
   - Key: `SUPABASE_KEY`, Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
5. 「Save Changes」をクリック

## 6. テーブル確認

```sql
-- テーブル構造確認
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'conversation_history';

-- データ確認（実行後）
SELECT * FROM conversation_history ORDER BY created_at DESC LIMIT 10;

-- ユーザー別統計
SELECT * FROM user_conversation_stats;
```

## 7. セキュリティ設定（オプション）

デフォルトでは、Supabaseの`anon`キーでは全データにアクセスできます。
より厳格なセキュリティが必要な場合は、Row Level Security（RLS）を有効化:

```sql
-- RLS有効化
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;

-- すべてのユーザーが自分のデータのみ読み書き可能
CREATE POLICY "Users can manage own conversations"
ON conversation_history
FOR ALL
USING (true);  -- LINE Bot用なので全アクセス許可
```

**注意**: LINE Botでは複数ユーザーを管理するため、RLSは不要です。

## 8. トラブルシューティング

### エラー: "relation 'conversation_history' does not exist"
- SQL Editorでテーブル作成SQLを再実行

### エラー: "Invalid API key"
- `SUPABASE_KEY`が正しいか確認（`anon public`キー）
- Renderで環境変数が設定されているか確認

### 接続テスト

```python
from supabase import create_client, Client

url = "https://xxxxxxxx.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase: Client = create_client(url, key)

# テストクエリ
result = supabase.table('conversation_history').select("*").limit(1).execute()
print(result)
```

## 9. データベース容量管理

- **無料枠**: 500MB
- **現在の使用量確認**: Settings → Database → Database Size

**見積もり**:
- 1メッセージ平均 500バイト
- 500MB ÷ 500バイト = 約100万メッセージ

個人使用では容量オーバーの心配はほぼありません。

---

セットアップ完了後、次のステップ（コード実装）に進んでください。
