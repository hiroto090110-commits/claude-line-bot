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

# スケジュール機能
from schedule_parser import parse_schedule
from ics_generator import generate_ics, format_event_message

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

# セキュリティ: 許可されたユーザーIDのみ使用可能
# 環境変数 ALLOWED_USER_IDS にカンマ区切りで設定（例: "U1234,U5678"）
# 空の場合は全ユーザー許可（初回セットアップ用）
allowed_users_str = os.environ.get('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS = [uid.strip() for uid in allowed_users_str.split(',') if uid.strip()]

# システムプロンプト（Geminiの役割を定義）
SYSTEM_PROMPT = """あなたはプログラミングアシスタントです。
ユーザーからの開発依頼に対して、完全なコードを生成して返します。

回答の形式:
1. 簡潔な説明（1-2行）
2. コードブロック（必要に応じて）
3. 使い方・注意点（簡潔に）

制約:
- 回答は3000文字以内（LINE制限）
- コードは実装可能な完全な形で提供
- 専門用語は必要最小限に
"""


@app.route("/")
def home():
    """ヘルスチェック"""
    return "Gemini LINE Bot is running! 💰 完全無料 + スケジュール機能", 200


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

    logger.info(f"User ID: {user_id}")
    logger.info(f"Source type: {source_type}")
    logger.info(f"Received message: {user_message}")

    # セキュリティチェック: 許可されたユーザーのみ処理
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        logger.warning(f"Unauthorized user attempted access: {user_id}")
        # 不正なユーザーには何も返さない（セキュリティのため）
        return

    try:
        # スケジュール関連キーワード検出
        schedule_keywords = ['スケジュール', '予定', 'カレンダー', '登録', '作成']
        is_schedule_request = any(keyword in user_message for keyword in schedule_keywords)

        if is_schedule_request:
            # スケジュール解析
            logger.info("Parsing schedule...")
            result = parse_schedule(user_message, gemini_model)

            if result['success']:
                events = result['events']

                # ICSファイル生成
                ics_data = generate_ics(events)

                # 一時ファイルに保存
                file_id = str(uuid.uuid4())
                file_path = TEMP_DIR / f"{file_id}.ics"
                file_path.write_bytes(ics_data)

                # ダウンロードURL生成
                download_url = f"https://{request.host}/download/{file_id}"

                # フォーマット済みメッセージ + ダウンロードリンク
                event_message = format_event_message(events)
                reply_text = f"{event_message}\n📥 カレンダーに追加:\n{download_url}\n\n※ リンクをタップするとカレンダーアプリで開きます"

                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )

                logger.info(f"Schedule created: {file_id}")
            else:
                # スケジュール解析失敗
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=result['error'])
                )

        else:
            # 通常のGemini対話
            full_prompt = f"{SYSTEM_PROMPT}\n\nユーザーの質問: {user_message}"
            response = gemini_model.generate_content(full_prompt)

            # Gemini の返答を取得
            reply_text = response.text

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
