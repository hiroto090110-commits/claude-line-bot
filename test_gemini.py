#!/usr/bin/env python3
"""
Gemini API接続テスト
google-generativeai==0.3.2 での動作確認
"""

import google.generativeai as genai

# API Key設定
GEMINI_API_KEY = "AIzaSyCj1swx-2Ap9geoNgoYJfJeX2vvW5UKv0k"

print("🔍 Gemini API接続テスト開始...")
print(f"パッケージバージョン: google-generativeai==0.3.2")
print()

try:
    # API設定
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ API Key設定完了")

    # 利用可能なモデル一覧を取得
    print("\n📋 利用可能なモデル一覧:")
    for model in genai.list_models():
        print(f"  - {model.name}")

    print("\n" + "="*60)

    # gemini-2.5-flashモデルでテスト（無料）
    print("\n🤖 gemini-2.5-flashモデルでテスト（無料）:")
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("こんにちは、簡単な自己紹介をしてください")
    print(f"✅ 成功！返答: {response.text[:100]}...")

except Exception as e:
    print(f"\n❌ エラー発生: {e}")
    print(f"エラータイプ: {type(e).__name__}")
    import traceback
    traceback.print_exc()
