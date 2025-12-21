#!/usr/bin/env python3
"""
Gemini LINE Bot - スマホからGeminiに依頼できるLINE Bot

💰 費用: 完全無料（Gemini API無料枠: 月1500リクエスト）

使い方:
1. LINEで「動画編集アプリに○○機能追加して」と送信
2. Geminiが自動でコード生成
3. 結果をLINEで返信
"""

import os
import logging
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, request, abort, send_file
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
from supabase import create_client, Client

# スケジュール機能（一時凍結）
# from schedule_parser import parse_schedule
# from ics_generator import generate_ics, format_event_message

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask初期化
app = Flask(__name__)

# 一時ファイル用ディレクトリ
TEMP_DIR = Path(__file__).parent / "temp"
TEMP_DIR.mkdir(exist_ok=True)

# LINE Bot API初期化
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# Gemini API初期化（無料: gemini-2.5-flash）
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

# Supabase初期化（会話履歴永続化）
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = None

if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
else:
    logger.warning("SUPABASE_URL or SUPABASE_KEY not set. Conversation history will not be saved.")

# セキュリティ: 許可されたユーザーIDのみ使用可能
# 環境変数 ALLOWED_USER_IDS にカンマ区切りで設定（例: "U1234,U5678"）
# 空の場合は全ユーザー許可（初回セットアップ用）
allowed_users_str = os.environ.get('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS = [uid.strip() for uid in allowed_users_str.split(',') if uid.strip()]

# 会話履歴設定
MAX_HISTORY_MESSAGES = 20  # Geminiに渡す最新会話数（10往復分）

# システムプロンプト（Geminiの役割を定義）
SYSTEM_PROMPT = """AIアシスタントとして質問に回答します。

回答方針:
- 要点を簡潔に述べる
- 詳細が必要な場合は「詳しく教えて」と指示を受けてから提供
- 中立的な立場を維持

制約: 3000文字以内
"""


def get_conversation_history(user_id: str, limit: int = MAX_HISTORY_MESSAGES) -> list:
    """
    データベースから会話履歴を取得

    Args:
        user_id: LINEユーザーID
        limit: 取得する最新メッセージ数

    Returns:
        会話履歴のリスト [{'role': 'ユーザー', 'content': '...'}]
    """
    if not supabase:
        logger.warning("Supabase not initialized. Returning empty history.")
        return []

    try:
        # 最新のメッセージをlimit件取得（降順→昇順に変換）
        response = supabase.table('conversation_history') \
            .select('role, content') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()

        # 降順で取得したので、古い順に並び替え
        history = list(reversed(response.data))

        logger.info(f"Retrieved {len(history)} messages for user {user_id}")
        return history

    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        return []


def save_conversation(user_id: str, role: str, content: str):
    """
    会話をデータベースに保存

    Args:
        user_id: LINEユーザーID
        role: 'ユーザー' または 'アシスタント'
        content: メッセージ内容
    """
    if not supabase:
        logger.warning("Supabase not initialized. Conversation not saved.")
        return

    try:
        supabase.table('conversation_history').insert({
            'user_id': user_id,
            'role': role,
            'content': content
        }).execute()

        logger.debug(f"Saved {role} message for user {user_id}")

    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")


@app.route("/")
def home():
    """ヘルスチェック"""
    # 環境変数チェック
    env_status = {
        "LINE_CHANNEL_ACCESS_TOKEN": "✅" if os.environ.get('LINE_CHANNEL_ACCESS_TOKEN') else "❌",
        "LINE_CHANNEL_SECRET": "✅" if os.environ.get('LINE_CHANNEL_SECRET') else "❌",
        "GEMINI_API_KEY": "✅" if os.environ.get('GEMINI_API_KEY') else "❌",
    }
    status_text = " | ".join([f"{k}: {v}" for k, v in env_status.items()])
    return f"Gemini LINE Bot is running! 💰 完全無料<br>汎用会話 + @メンション対応<br><br>環境変数: {status_text}", 200


@app.route("/download/<file_id>")
def download_ics(file_id):
    """ICSファイルダウンロード"""
    try:
        file_path = TEMP_DIR / f"{file_id}.ics"

        if not file_path.exists():
            abort(404)

        # ファイルをダウンロード
        return send_file(
            file_path,
            mimetype='text/calendar',
            as_attachment=True,
            download_name='schedule.ics'
        )

    except Exception as e:
        logger.error(f"Download error: {e}", exc_info=True)
        abort(500)


@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhookコールバック"""
    # 署名検証
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """LINEメッセージ受信時の処理"""
    user_id = event.source.user_id
    user_message = event.message.text

    # グループチャットの場合、メンションをチェック
    source_type = event.source.type
    if source_type == 'group' or source_type == 'room':
        # グループ内では@メンションがある場合のみ反応
        if '@' not in user_message:
            return
        # メンション部分を削除
        user_message = user_message.split(maxsplit=1)[-1] if len(user_message.split()) > 1 else user_message

    # 会話の識別子を生成（グループごとに会話を分別）
    if source_type == 'user':
        # 個人チャット: user_idをそのまま使う
        conversation_id = user_id
    elif source_type == 'group':
        # グループチャット: group_idを使う
        conversation_id = event.source.group_id
    elif source_type == 'room':
        # 複数人トーク: room_idを使う
        conversation_id = event.source.room_id
    else:
        conversation_id = user_id

    logger.info(f"User ID: {user_id}")
    logger.info(f"Source type: {source_type}")
    logger.info(f"Conversation ID: {conversation_id}")
    logger.info(f"Received message: {user_message}")

    # セキュリティチェック: 許可されたユーザーのみ処理
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        logger.warning(f"Unauthorized user attempted access: {user_id}")
        # 不正なユーザーには何も返さない（セキュリティのため）
        return

    try:
        # スケジュール機能は一時凍結
        # 全てのメッセージをGeminiとの汎用会話として処理

        # データベースから会話履歴を取得（グループごとに分別）
        history = get_conversation_history(conversation_id, MAX_HISTORY_MESSAGES)

        # 過去の会話履歴をテキスト化
        history_text = ""
        if history:
            history_text = "\n\n過去の会話:\n"
            for msg in history:
                history_text += f"{msg['role']}: {msg['content']}\n"

        # Gemini対話
        full_prompt = f"{SYSTEM_PROMPT}{history_text}\n\n最新の質問: {user_message}"
        response = gemini_model.generate_content(full_prompt)

        # Gemini の返答を取得
        reply_text = response.text

        # 会話履歴をデータベースに保存（グループごとに分別）
        save_conversation(conversation_id, 'ユーザー', user_message)
        save_conversation(conversation_id, 'アシスタント', reply_text)

        logger.info(f"Saved conversation for conversation_id {conversation_id}")

        # LINE文字数制限（5000文字）を考慮して分割
        if len(reply_text) > 4500:
            # 長い場合は分割して送信
            parts = split_message(reply_text, 4500)
            for part in parts:
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text=part)
                )
        else:
            # LINEで返信
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

        logger.info("Reply sent successfully")

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

        # Gemini APIレート制限エラーの特別処理
        if "ResourceExhausted" in str(type(e)) or "429" in str(e):
            error_message = "⏳ 只今アクセスが集中しています。\n\n" \
                          "Gemini APIの無料枠（1分間に5リクエスト）に達しました。\n" \
                          "30秒ほど待ってから再度お試しください。"
        else:
            error_message = f"エラーが発生しました:\n{str(e)}"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_message)
        )


def split_message(text, max_length=4500):
    """長いメッセージを分割"""
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break

        # 改行で分割を試みる
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    return parts


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
