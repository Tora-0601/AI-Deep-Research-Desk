"""Gemini API を使用したリサーチ実行モジュール"""

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import Optional

class GeminiService:
    """Gemini API を使用してディープリサーチを実行"""
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.model = None
        
        # 安全性設定（エラー回避のため全解除）
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    
    def authenticate(self, api_key: str) -> tuple[bool, str]:
        """Gemini API キーで認証"""
        try:
            if not api_key or api_key.strip() == "":
                return False, "❌ API キーが入力されていません。"
            
            genai.configure(api_key=api_key.strip())
            self.api_key = api_key.strip()
            
            try:
                # 本命: 高性能かつ標準API対応
                self.model = genai.GenerativeModel('gemini-2.5-pro')
            except:
                try:
                    # 対抗: 高速版
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                except:
                    # 安定版: 確実に動く2.0
                    self.model = genai.GenerativeModel('gemini-2.0-flash')

            # テスト送信
            try:
                response = self.model.generate_content("Hello")
                if response:
                    return True, f"✅ 認証成功！\n   🤖 使用モデル: {self.model.model_name}"
                else:
                    return False, "❌ 応答が空でした。"
            
            except Exception as e:
                print(f"DEBUG: {self.model.model_name} failed. Switching to backup.")
                try:
                    self.model = genai.GenerativeModel('gemini-2.0-flash')
                    response = self.model.generate_content("Hello")
                    return True, f"✅ 認証成功 (バックアップモデル使用)\n   🤖 使用モデル: {self.model.model_name}"
                except Exception as e2:
                    return False, f"❌ 認証エラー: {str(e2)}"

        except Exception as e:
            return False, f"❌ 接続エラー: {str(e)}"
    
    def research(self, prompt: str) -> str:
        """
        Gemini を使用してディープリサーチを実行（検索なし）
        """
        if not self.api_key or not self.model:
            return "❌ エラー: API キーが認証されていません。"
        
        # AIに「レポートを書くプロ」として振る舞わせる指示（検索の記述は削除）
        research_instructions = """
        あなたはプロの「リサーチ・アナリスト」です。
        ユーザーの質問に対して、あなたの持つ豊富な知識を駆使し、
        詳細かつ正確な情報を整理してレポートを作成してください。

        【出力形式】
        ・見出しを使用した読みやすいレポート形式
        ・最後にあなたの考察（まとめ）を入れる

        【ユーザーの依頼】
        """
        
        full_prompt = research_instructions + prompt
        
        try:
            # 元のモデルをそのまま使ってテキスト生成（toolsの設定は削除）
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8192,
                    temperature=0.7,
                ),
                safety_settings=self.safety_settings
            )
            
            return response.text
        
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "429" in error_msg:
                return "❌ エラー: API の利用制限に達しました。"
            else:
                return f"❌ リサーチ実行エラー: {str(e)}"


# --- ここから下はクラスの外なので、一番左に寄せます ---
_gemini_service: Optional[GeminiService] = None

def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service

def reset_gemini_service():
    global _gemini_service
    _gemini_service = None