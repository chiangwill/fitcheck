import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def _job_detail_dialog(parsed: dict, title: str):
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-2xl"):
        with ui.column().classes("w-full gap-4 p-2"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label(title).classes("font-bold text-lg fit-text")
                ui.button(icon="close", on_click=dialog.close).props("flat round dense")

            def section(label: str, icon: str, color: str):
                with ui.row().classes("items-center gap-2"):
                    ui.icon(icon, color=color).classes("text-base")
                    ui.label(label).classes("font-semibold fit-text text-sm uppercase tracking-wide")

            # 基本資訊
            section("基本資訊", "info", "blue")
            with ui.row().classes("gap-6 flex-wrap ml-6"):
                for label, key in [("薪資", "salary"), ("地點", "location"), ("遠端政策", "remote_policy")]:
                    val = parsed.get(key)
                    if val:
                        with ui.column().classes("gap-0.5"):
                            ui.label(label).classes("text-xs fit-subtext")
                            ui.label(val).classes("text-sm fit-text font-medium")

            ui.separator()

            # 描述
            if parsed.get("description"):
                section("職缺描述", "description", "gray")
                ui.label(parsed["description"]).classes("text-sm fit-text leading-relaxed ml-6")
                ui.separator()

            # 必要技能
            req = parsed.get("required_skills", [])
            if req:
                section("必要技能", "star", "orange")
                with ui.row().classes("gap-2 flex-wrap ml-6"):
                    for s in req:
                        ui.badge(s, color="orange").classes("text-xs")
                ui.separator()

            # 加分技能
            bonus = parsed.get("bonus_skills", [])
            if bonus:
                section("加分技能", "add_circle", "green")
                with ui.row().classes("gap-2 flex-wrap ml-6"):
                    for s in bonus:
                        ui.badge(s, color="green").classes("text-xs")
                ui.separator()

            # 文化關鍵字
            culture = parsed.get("culture_keywords", [])
            if culture:
                section("公司文化", "groups", "purple")
                with ui.row().classes("gap-2 flex-wrap ml-6"):
                    for k in culture:
                        ui.badge(k, color="purple").classes("text-xs")

    dialog.open()


def jobs_page():
    @ui.page("/jobs")
    async def page():
        content = page_layout("職缺解析", "貼入職缺 URL，AI 自動萃取結構化資訊", "/ui/jobs")

        with content:
            async def load_jobs():
                jobs_container.clear()
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{API}/jobs")
                jobs = r.json() if r.status_code == 200 else []

                with jobs_container:
                    if not jobs:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("travel_explore", size="3rem").classes("text-gray-300")
                            ui.label("尚無職缺，貼入 URL 開始解析").classes("fit-subtext")
                        return

                    for job in jobs:
                        parsed = job.get("parsed_json") or {}
                        title = parsed.get("title") or job.get("title") or "解析中..."
                        company = parsed.get("company") or job.get("company") or ""
                        is_parsed = bool(job.get("parsed_json"))

                        with ui.card().classes("w-full fit-card"):
                            with ui.row().classes("items-start justify-between w-full p-1"):
                                with ui.row().classes("items-start gap-4 flex-1"):
                                    with ui.column().classes("w-10 h-10 rounded-full bg-purple-100 items-center justify-center flex-shrink-0"):
                                        ui.icon("work", color="purple").classes("text-lg")
                                    with ui.column().classes("gap-1 flex-1"):
                                        with ui.row().classes("items-center gap-2 flex-wrap"):
                                            ui.label(title).classes("font-semibold fit-text")
                                            ui.badge(
                                                "已解析" if is_parsed else "處理中",
                                                color="green" if is_parsed else "orange",
                                            ).classes("text-xs")
                                        if company:
                                            ui.label(company).classes("text-sm fit-subtext")
                                        ui.link(job["url"], job["url"], new_tab=True).classes("text-xs text-blue-400 truncate max-w-md")

                                        if is_parsed:
                                            skills = parsed.get("required_skills", [])
                                            salary = parsed.get("salary")
                                            location = parsed.get("location", "")
                                            remote = parsed.get("remote_policy", "")
                                            with ui.row().classes("gap-4 mt-1 flex-wrap"):
                                                if salary:
                                                    ui.label(f"💰 {salary}").classes("text-xs fit-subtext")
                                                if location:
                                                    ui.label(f"📍 {location}").classes("text-xs fit-subtext")
                                                if remote:
                                                    ui.label(f"🖥 {remote}").classes("text-xs fit-subtext")
                                            if skills:
                                                with ui.row().classes("gap-1 mt-1 flex-wrap"):
                                                    for s in skills[:5]:
                                                        ui.badge(s, color="purple").classes("text-xs opacity-80")
                                                    if len(skills) > 5:
                                                        ui.label(f"+{len(skills)-5}").classes("text-xs fit-subtext")

                                if is_parsed:
                                    ui.button(
                                        "詳情",
                                        icon="open_in_full",
                                        on_click=lambda jid=job["id"]: ui.navigate.to(f"/jobs/{jid}"),
                                    ).props("flat color=purple size=sm")

            # 輸入卡片
            with ui.card().classes("w-full fit-card"):
                with ui.column().classes("p-2 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("add_link", color="purple").classes("text-xl")
                        ui.label("新增職缺").classes("font-semibold fit-text")

                    with ui.row().classes("w-full gap-3 items-start"):
                        url_input = ui.input("貼入職缺 URL").classes("flex-1").props("outlined dense")

                        async def parse_job():
                            url = url_input.value.strip()
                            if not url:
                                ui.notify("請輸入 URL", type="warning")
                                return
                            parse_btn.props("loading")
                            async with httpx.AsyncClient(timeout=60) as client:
                                r = await client.post(f"{API}/jobs/parse", json={"url": url})
                            parse_btn.props(remove="loading")
                            if r.status_code in (200, 201):
                                ui.notify("已送出，Gemini 解析中...", type="positive")
                                url_input.set_value("")
                                await load_jobs()
                            else:
                                ui.notify(f"失敗：{r.json().get('detail', r.text)}", type="negative")

                        parse_btn = ui.button("解析", icon="search", on_click=parse_job).props("color=purple unelevated")

            with ui.row().classes("items-center justify-between w-full"):
                ui.label("已解析職缺").classes("font-semibold fit-text")

            jobs_container = ui.column().classes("w-full gap-3")
            await load_jobs()
