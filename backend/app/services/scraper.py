import json

from google.genai import types

from app.core.gemini import client


async def fetch_and_parse_job(url: str) -> tuple[str, dict]:
    """讓 Gemini 直接 fetch URL 並萃取職缺資訊，回傳 (raw_content, parsed_json)"""
    prompt = f"""請讀取以下職缺頁面，萃取職缺資訊並回傳 JSON。

格式：
{{
  "title": "職缺名稱",
  "company": "公司名稱",
  "required_skills": ["必要技能1", "必要技能2"],
  "bonus_skills": ["加分技能1"],
  "salary": "薪資範圍（如無則 null）",
  "location": "工作地點",
  "remote_policy": "遠端政策（全遠端/混合/不支援/未說明）",
  "culture_keywords": ["公司文化關鍵字"],
  "description": "職缺描述摘要（200字以內）"
}}

只回傳 JSON，不要其他文字。

URL: {url}"""

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(url_context=types.UrlContext())],
        ),
    )

    raw_content = response.text
    cleaned = raw_content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    parsed = json.loads(cleaned)
    return raw_content, parsed
