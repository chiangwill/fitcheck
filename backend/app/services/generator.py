import asyncio

from app.core.gemini import generate


async def _generate_zh(resume_text: str, job: dict, tone: str) -> str:
    prompt = f"""你是一個專業的求職顧問，請根據以下履歷和職缺資訊，生成一封客製化的求職信。

語氣：{tone}（正式 = 專業正式；活潑 = 親切有個性）

職缺資訊：
- 職缺名稱：{job.get('title', '')}
- 公司名稱：{job.get('company', '')}
- 必要技能：{', '.join(job.get('required_skills', []))}
- 職缺描述：{job.get('description', '')}

履歷內容：
{resume_text}

要求：
- 繁體中文
- 300-500 字
- 開頭說明應徵職位
- 中段對應職缺需求強調自身經驗
- 結尾表達期待面試機會
- 直接輸出求職信內容，不要額外說明"""
    return await generate(prompt)


async def _generate_en(resume_text: str, job: dict, tone: str) -> str:
    tone_desc = "professional and formal" if tone == "正式" else "friendly and personable"
    prompt = f"""You are a professional career consultant. Based on the resume and job information below, write a customized cover letter.

Tone: {tone_desc}

Job Information:
- Position: {job.get('title', '')}
- Company: {job.get('company', '')}
- Required Skills: {', '.join(job.get('required_skills', []))}
- Job Description: {job.get('description', '')}

Resume:
{resume_text}

Requirements:
- Write in English
- 300-500 words
- Opening: state the position you're applying for
- Body: highlight relevant experience matching the job requirements
- Closing: express enthusiasm and request for an interview
- Output only the cover letter content, no extra explanation"""
    return await generate(prompt)


async def generate_cover_letter(resume_text: str, job: dict, tone: str = "正式") -> tuple[str, str]:
    """回傳 (中文版, 英文版)"""
    zh, en = await asyncio.gather(
        _generate_zh(resume_text, job, tone),
        _generate_en(resume_text, job, tone),
    )
    return zh, en
