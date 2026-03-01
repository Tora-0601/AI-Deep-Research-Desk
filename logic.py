from datetime import date
from database import Database, Request
from gemini_service import get_gemini_service


def list_requests(db: Database) -> list[Request]:
    """Get all requests."""
    return db.list_requests()


def get_request(db: Database, index: int) -> Request:
    """Get a single request by index."""
    return db.get_request(index)


def create_prompt(title: str, deadline: str, topic: str, api_key: str = None) -> str:
    """Gemini API を使用してディープリサーチ用のプロンプトを生成"""
    if not api_key:
        return (
            "あなたはリサーチ担当です。\n"
            f"タイトル: {title or '（未入力）'}\n"
            f"納期: {deadline or '（未入力）'}\n"
            f"調査したい内容: {topic or '（未入力）'}\n"
            "日本語で要点と根拠を簡潔にまとめてください。"
        )
    
    try:
        gemini = get_gemini_service()
        success, auth_msg = gemini.authenticate(api_key)
        
        if not success:
            return (
                "あなたはリサーチ担当です。\n"
                f"タイトル: {title or '（未入力）'}\n"
                f"納期: {deadline or '（未入力）'}\n"
                f"調査したい内容: {topic or '（未入力）'}\n"
                "日本語で要点と根拠を簡潔にまとめてください。"
            )
        
        generation_prompt = f"""
以下の情報に基づいて、ディープリサーチ用の詳細なプロンプトを日本語で作成してください。

【調査情報】
- タイトル: {title}
- 納期: {deadline}
- 調査したい内容: {topic}

【要件】
- 日本語で記述
- 具体的で実行可能な指示を含む
- 調査範囲を明確に定義
- 期待される出力形式を指定
- 信頼性の高い情報源の参照を促す

【プロンプト】に続けてプロンプトを作成してください。
"""
        
        result = gemini.research(generation_prompt)
        
        if "【プロンプト】" in result:
            prompt = result.split("【プロンプト】")[1].strip()
        else:
            prompt = result
        
        return prompt
    
    except Exception as e:
        return (
            "あなたはリサーチ担当です。\n"
            f"タイトル: {title or '（未入力）'}\n"
            f"納期: {deadline or '（未入力）'}\n"
            f"調査したい内容: {topic or '（未入力）'}\n"
            "日本語で要点と根拠を簡潔にまとめてください。"
        )


def compose_mail_body(request: Request) -> str:
    """Create a mail body from a request."""
    lines = [
        f"タイトル: {request.title}",
        f"依頼者: {request.requester}",
        f"日付: {request.date}",
    ]
    if request.deadline:
        lines.append(f"納期: {request.deadline}")
    if request.email:
        lines.append(f"メール: {request.email}")
    lines.append("")
    lines.append("レポート:")
    lines.append(request.report)
    if request.correction:
        lines.append("")
        lines.append("修正依頼:")
        lines.append(request.correction)
    return "\n".join(lines)


def execute_research(prompt: str, api_key: str) -> tuple[bool, str]:
    """Gemini API を使用してディープリサーチを実行"""
    if not api_key or api_key.strip() == "":
        return False, "❌ API キーを入力してください。"
    
    gemini = get_gemini_service()
    success, auth_msg = gemini.authenticate(api_key)
    
    if not success:
        return False, auth_msg
    
    report = gemini.research(prompt)
    
    if report.startswith("❌"):
        return False, report
    
    return True, report


def submit_request(
    db: Database,
    title: str,
    requester: str,
    deadline: str,
    topic: str,
    email: str,
    prompt: str,
    api_key: str,
) -> tuple[Request, bool, str]:
    """Create a request, execute research, and store it."""
    success, report = execute_research(prompt, api_key)
    
    request = Request(
        date=date.today().strftime("%Y/%m/%d"),
        title=title or "無題",
        requester=requester or email or "受講者",
        email=email,
        deadline=deadline,
        topic=topic,
        prompt=prompt,
        report=report if success else "エラー: " + report,
        correction="",
    )
    
    db.add_request(request)
    
    return request, success, report