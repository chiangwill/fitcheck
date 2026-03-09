import io
import json

import pdfplumber

from app.core.gemini import generate


def extract_text_from_pdf(file_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


async def parse_resume_to_structured(raw_text: str) -> dict:
    prompt = f"""請將以下履歷內容解析成結構化 JSON，格式如下：
{{
  "skills": ["技能1", "技能2"],
  "years_of_experience": 數字,
  "work_history": [
    {{"company": "公司名", "title": "職稱", "duration": "時間", "bullets": ["工作內容條列1", "工作內容條列2"]}}
  ],
  "education": [
    {{"school": "學校", "degree": "學歷", "major": "科系", "year": "畢業年份"}}
  ],
  "summary": "簡短摘要"
}}

只回傳 JSON，不要其他文字。

履歷內容：
{raw_text}"""

    response = await generate(prompt)
    # 移除可能的 markdown code block
    cleaned = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)
