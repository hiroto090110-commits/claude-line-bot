#!/usr/bin/env python3
"""
Claude LINE Bot - スマホからClaudeに依頼できるLINE Bot

使い方:
1. LINEで「動画編集アプリに○○機能追加して」と送信
2. Claudeが自動でコード生成
3. 結果をLINEで返信
"""

import os
import logging
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import anthropic

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask初期化
app = Flask(__name__)

# LINE Bot API初期化
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# Claude API初期化
claude_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# システムプロンプト（Claudeの役割を定義）
SYSTEM_PROMPT = """あなたはプログラミングアシスタントのClaudeです。
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
    return "Claude LINE Bot is running!", 200


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
    user_message = event.message.text
    logger.info(f"Received message: {user_message}")
    
    try:
        # Claude APIに質問
        response = claude_client.messages.create(
            model="claude-sonnet-4",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # Claude の返答を取得
        reply_text = response.content[0].text
        
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
