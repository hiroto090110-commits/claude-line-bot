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
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask初期化
app = Flask(__name__)

# LINE Bot API初期化
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# Gemini API初期化
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

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
    return "Gemini LINE Bot is running! 💰 完全無料", 200


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

    logger.info(f"User ID: {user_id}")
    logger.info(f"Received message: {user_message}")

    # セキュリティチェック: 許可されたユーザーのみ処理
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        logger.warning(f"Unauthorized user attempted access: {user_id}")
        # 不正なユーザーには何も返さない（セキュリティのため）
        return

    try:
        # Gemini APIに質問
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
