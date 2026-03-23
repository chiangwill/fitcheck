import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def _resume_detail_dialog(parsed: dict, version_name: str):
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
        with ui.column().classes("w-full gap-4 p-2"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(f"履歷解析結果 — {version_name}").classes("font-bold text-lg fit-text")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense")

            # 摘要
            if parsed.get("summary"):
                ui.label(parsed["summary"]).classes("text-sm fit-subtext leading-relaxed p-3 rounded-lg bg-blue-50")

            with ui.row().classes("gap-1 items-center"):
                ui.icon("work_history", color="blue")
                ui.label("工作經驗").classes("font-semibold fit-text")
                yoe = parsed.get("years_of_experience")
                if yoe is not None:
                    ui.badge(f"{yoe} 年", color="blue").classes("text-xs")

            work = parsed.get("work_history", [])
            if work:
                for job in work:
                    with ui.card().classes("w-full fit-card"):
                        with ui.column().classes("p-3 gap-1"):
                            with ui.row().classes("items-center justify-between"):
                                ui.label(job.get("title", "")).classes("font-semibold fit-text text-sm")
                                ui.label(job.get("duration", "")).classes("text-xs fit-subtext")
                            ui.label(job.get("company", "")).classes("text-sm text-blue-600")
                            bullets = job.get("bullets") or []
                            if not bullets and job.get("description"):
                                bullets = [l.strip().lstrip("-•· ") for l in job["description"].splitlines() if l.strip()]
                            if bullets:
                                with ui.column().classes("gap-0.5 mt-1"):
                                    for bullet in bullets:
                                        with ui.row().classes("items-start gap-1.5"):
                                            ui.label("·").classes("text-xs fit-subtext flex-shrink-0")
                                            ui.label(bullet).classes("text-xs fit-subtext leading-relaxed")
            else:
                ui.label("無工作經歷資料").classes("text-xs fit-subtext ml-6")

            ui.separator()

            # 技能
            with ui.row().classes("gap-1 items-center"):
                ui.icon("build", color="green")
                ui.label("技能").classes("font-semibold fit-text")

            skills = parsed.get("skills", [])
            if skills:
                with ui.row().classes("gap-2 flex-wrap ml-6"):
                    for s in skills:
                        ui.badge(s, color="green").classes("text-xs")
            else:
                ui.label("無技能資料").classes("text-xs fit-subtext ml-6")

            ui.separator()

            # 學歷
            with ui.row().classes("gap-1 items-center"):
                ui.icon("school", color="purple")
                ui.label("學歷").classes("font-semibold fit-text")

            education = parsed.get("education", [])
            if education:
                for edu in education:
                    with ui.row().classes("items-center gap-3 ml-6"):
                        with ui.column().classes("gap-0.5"):
                            ui.label(f"{edu.get('school', '')}").classes("text-sm fit-text font-medium")
                            ui.label(f"{edu.get('degree', '')} · {edu.get('major', '')} · {edu.get('year', '')}").classes("text-xs fit-subtext")
            else:
                ui.label("無學歷資料").classes("text-xs fit-subtext ml-6")

    dialog.open()


def resume_page():
    @ui.page("/resume")
    async def page():
        content = page_layout("履歷管理", "上傳或編輯你的履歷，支援多版本切換", "/ui/resume")

        with content:
            async def load_versions():
                versions_container.clear()
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{API}/resume/versions")
                resumes = r.json() if r.status_code == 200 else []

                with versions_container:
                    if not resumes:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("description", size="3rem").classes("text-gray-300")
                            ui.label("尚無履歷，請上傳你的第一份履歷").classes("fit-subtext")
                        return

                    for resume in resumes:
                        parsed = resume.get("parsed_json") or {}
                        with ui.card().classes("w-full fit-card"):
                            with ui.row().classes("items-center justify-between w-full p-1"):
                                with ui.row().classes("items-center gap-4"):
                                    with ui.column().classes("w-10 h-10 rounded-full bg-blue-100 items-center justify-center"):
                                        ui.icon("description", color="blue").classes("text-lg")
                                    with ui.column().classes("gap-0.5"):
                                        with ui.row().classes("items-center gap-2"):
                                            ui.label(resume["version_name"]).classes("font-semibold fit-text")
                                            if resume["is_active"]:
                                                ui.badge("active", color="green").classes("text-xs")
                                        ui.label(f"建立於 {resume['created_at'][:10]}").classes("text-xs fit-subtext")
                                        if parsed:
                                            yoe = parsed.get("years_of_experience")
                                            skills = parsed.get("skills", [])
                                            with ui.row().classes("items-center gap-3 mt-0.5"):
                                                if yoe is not None:
                                                    ui.label(f"{yoe} 年經驗").classes("text-xs fit-subtext")
                                                if skills:
                                                    with ui.row().classes("gap-1 flex-wrap"):
                                                        for s in skills[:4]:
                                                            ui.badge(s, color="blue").classes("text-xs opacity-70")
                                                        if len(skills) > 4:
                                                            ui.label(f"+{len(skills)-4}").classes("text-xs fit-subtext")

                                with ui.row().classes("gap-2 items-center"):
                                    if parsed:
                                        ui.button(
                                            "詳情",
                                            icon="open_in_full",
                                            on_click=lambda p=parsed, v=resume["version_name"]: _resume_detail_dialog(p, v),
                                        ).props("flat color=blue size=sm")
                                    if not resume["is_active"]:
                                        async def set_active(rid=resume["id"]):
                                            async with httpx.AsyncClient() as client:
                                                await client.put(f"{API}/resume/active/{rid}")
                                            await load_versions()
                                            try:
                                                ui.notify("已切換 active 履歷", type="positive")
                                            except RuntimeError:
                                                pass
                                        ui.button("設為 active", on_click=set_active).props("flat color=green size=sm")

                                    async def delete_resume(rid=resume["id"]):
                                        async with httpx.AsyncClient() as client:
                                            await client.delete(f"{API}/resume/{rid}")
                                        await load_versions()
                                        try:
                                            ui.notify("已刪除", type="warning")
                                        except RuntimeError:
                                            pass
                                    ui.button(icon="delete", on_click=delete_resume).props("flat color=red size=sm round")

            # 上傳卡片
            with ui.card().classes("w-full fit-card"):
                with ui.column().classes("p-2 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("upload_file", color="blue").classes("text-xl")
                        ui.label("上傳履歷 PDF").classes("font-semibold fit-text")

                    version_input = ui.input("版本名稱（例如：後端版）").classes("w-full").props("outlined dense")

                    async def handle_upload(e):
                        if not version_input.value.strip():
                            ui.notify("請輸入版本名稱", type="warning")
                            return
                        content_bytes = await e.file.read()
                        async with httpx.AsyncClient(timeout=30) as client:
                            r = await client.post(
                                f"{API}/resume/upload",
                                params={"version_name": version_input.value},
                                files={"file": (e.file.name, content_bytes, "application/pdf")},
                            )
                        if r.status_code == 201:
                            ui.notify("上傳成功，AI 解析中...", type="positive")
                            version_input.set_value("")
                            await load_versions()
                        else:
                            ui.notify(f"上傳失敗：{r.text}", type="negative")

                    ui.upload(
                        label="點擊或拖曳 PDF 至此",
                        on_upload=handle_upload,
                        auto_upload=True,
                    ).props("accept=.pdf flat bordered").classes("w-full")

            with ui.row().classes("items-center justify-between w-full"):
                ui.label("所有版本").classes("font-semibold fit-text")

            versions_container = ui.column().classes("w-full gap-3")
            await load_versions()
