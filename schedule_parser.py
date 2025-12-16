#!/usr/bin/env python3
"""
スケジュール解析モジュール - Gemini APIで自然言語→構造化データ
"""

import json
import logging
from datetime import datetime, timedelta
import pytz
import google.generativeai as genai

logger = logging.getLogger(__name__)

# 日本時間のタイムゾーン
JST = pytz.timezone('Asia/Tokyo')

def parse_schedule(message: str, gemini_model) -> dict:
    """
    自然言語のスケジュールをGeminiで解析して構造化データに変換

    Args:
        message: ユーザーメッセージ (例: "明日14時から会議")
        gemini_model: Geminiモデルインスタンス

    Returns:
        {
            "success": bool,
            "events": [
                {
                    "title": str,
                    "start_datetime": str (ISO8601),
                    "end_datetime": str (ISO8601),
                    "description": str (optional)
                }
            ],
            "error": str (if success=False)
        }
    """

    # 現在時刻 (JST)
    now = datetime.now(JST)

    # Geminiに送るプロンプト
    prompt = f"""以下のメッセージからスケジュール情報を抽出してJSON形式で返してください。

現在時刻: {now.strftime('%Y年%m月%d日(%a) %H:%M')} (日本時間)

メッセージ: {message}

以下のJSON形式で返してください（JSON以外の説明文は不要）:
{{
  "events": [
    {{
      "title": "イベントタイトル",
      "start_datetime": "2025-12-17T14:00:00+09:00",
      "end_datetime": "2025-12-17T15:00:00+09:00",
      "description": "詳細説明（省略可）"
    }}
  ]
}}

ルール:
1. 日時は ISO8601 形式 (YYYY-MM-DDTHH:MM:SS+09:00) で返す
2. 終了時刻が指定されていない場合は開始から1時間後とする
3. 「明日」「来週」などの相対日時は現在時刻から計算する
4. 複数のイベントがある場合は配列に含める
5. スケジュール情報が含まれていない場合は events を空配列にする
"""

    try:
        # Gemini APIで解析
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()

        # JSON部分を抽出（マークダウンのコードブロックを除去）
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        # JSONパース
        parsed = json.loads(response_text)

        if not parsed.get("events"):
            return {
                "success": False,
                "error": "スケジュール情報が見つかりませんでした"
            }

        # 日時のバリデーション
        for event in parsed["events"]:
            try:
                datetime.fromisoformat(event["start_datetime"])
                datetime.fromisoformat(event["end_datetime"])
            except Exception as e:
                return {
                    "success": False,
                    "error": f"日時の形式が不正です: {e}"
                }

        return {
            "success": True,
            "events": parsed["events"]
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nResponse: {response_text}")
        return {
            "success": False,
            "error": "スケジュール情報の解析に失敗しました"
        }
    except Exception as e:
        logger.error(f"Schedule parsing error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"エラーが発生しました: {str(e)}"
        }
