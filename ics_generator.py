#!/usr/bin/env python3
"""
ICS (iCalendar) ファイル生成モジュール
"""

import uuid
from datetime import datetime
from icalendar import Calendar, Event
import pytz

def generate_ics(events: list) -> bytes:
    """
    イベントリストからICSファイルを生成

    Args:
        events: [
            {
                "title": str,
                "start_datetime": str (ISO8601),
                "end_datetime": str (ISO8601),
                "description": str (optional)
            }
        ]

    Returns:
        bytes: ICSファイルの内容
    """

    # カレンダーオブジェクト作成
    cal = Calendar()
    cal.add('prodid', '-//Gemini LINE Bot//Schedule//JP')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    cal.add('x-wr-calname', 'LINEスケジュール')
    cal.add('x-wr-timezone', 'Asia/Tokyo')

    # イベントを追加
    for event_data in events:
        event = Event()

        # タイトル
        event.add('summary', event_data['title'])

        # 開始・終了時刻
        start_dt = datetime.fromisoformat(event_data['start_datetime'])
        end_dt = datetime.fromisoformat(event_data['end_datetime'])
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)

        # 詳細説明
        if 'description' in event_data and event_data['description']:
            event.add('description', event_data['description'])

        # UID (一意識別子)
        event.add('uid', f'{uuid.uuid4()}@gemini-line-bot')

        # 作成日時
        event.add('dtstamp', datetime.now(pytz.timezone('Asia/Tokyo')))
        event.add('created', datetime.now(pytz.timezone('Asia/Tokyo')))
        event.add('last-modified', datetime.now(pytz.timezone('Asia/Tokyo')))

        # ステータス
        event.add('status', 'CONFIRMED')
        event.add('transp', 'OPAQUE')

        cal.add_component(event)

    return cal.to_ical()


def format_event_message(events: list) -> str:
    """
    イベントリストをLINEメッセージ用にフォーマット

    Args:
        events: イベントリスト

    Returns:
        str: フォーマット済みメッセージ
    """
    if not events:
        return "スケジュールが見つかりませんでした"

    lines = ["📅 スケジュール登録完了\n"]

    for i, event in enumerate(events, 1):
        start_dt = datetime.fromisoformat(event['start_datetime'])
        end_dt = datetime.fromisoformat(event['end_datetime'])

        # 日時フォーマット
        if start_dt.date() == end_dt.date():
            # 同じ日
            date_str = start_dt.strftime('%Y年%m月%d日(%a)')
            time_str = f"{start_dt.strftime('%H:%M')}〜{end_dt.strftime('%H:%M')}"
        else:
            # 複数日
            date_str = f"{start_dt.strftime('%Y年%m月%d日(%a)')} 〜 {end_dt.strftime('%m月%d日(%a)')}"
            time_str = f"{start_dt.strftime('%H:%M')}〜{end_dt.strftime('%H:%M')}"

        lines.append(f"{i}. {event['title']}")
        lines.append(f"   {date_str} {time_str}")

        if 'description' in event and event['description']:
            lines.append(f"   {event['description']}")
        lines.append("")

    return "\n".join(lines)
