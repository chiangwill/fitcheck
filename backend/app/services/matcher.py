import json

from app.core.gemini import generate


async def analyze_match(resume_text: str, job: dict) -> dict:
    prompt = f"""你是一個求職顧問，請分析以下履歷與職缺的匹配程度。

職缺資訊：
{json.dumps(job, ensure_ascii=False, indent=2)}

履歷內容：
{resume_text}

請回傳以下 JSON 格式的分析結果：
{{
  "score": 數字（1.0 到 10.0，代表整體適合度）,
  "matched_skills": ["符合的技能或條件1", "符合的技能或條件2"],
  "missing_skills": ["缺少的技能或條件1", "缺少的技能或條件2"],
  "suggestion": "具體補強建議（繁體中文，300字以內）"
}}

評分標準：
- 10分：完全符合所有要求
- 7-9分：符合大部分要求，少數缺口
- 4-6分：符合部分要求，有明顯缺口
- 1-3分：不太符合，差距較大

只回傳 JSON，不要其他文字。"""

    response = await generate(prompt)
    cleaned = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)
