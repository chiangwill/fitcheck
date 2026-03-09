import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def job_detail_page():
    @ui.page("/jobs/{job_id}")
    async def page(job_id: int):
        content = page_layout("職缺詳情", "", "/ui/jobs")

        with content:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{API}/jobs/{job_id}")

            if r.status_code != 200:
                ui.label("找不到職缺").classes("fit-subtext")
                return

            job = r.json()
            parsed = job.get("parsed_json") or {}

            title = parsed.get("title") or job.get("title") or "未知職缺"
            company = parsed.get("company") or job.get("company") or ""

            # 返回按鈕
            with ui.row().classes("items-center gap-2"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/jobs")).props("flat round size=sm")
                ui.label("返回列表").classes("fit-subtext text-sm cursor-pointer").on("click", lambda: ui.navigate.to("/jobs"))

            if not parsed:
                with ui.card().classes("fit-card p-6 items-center gap-3"):
                    ui.icon("hourglass_empty", size="2rem").classes("text-gray-300")
                    ui.label("職缺尚在解析中，請稍後再試").classes("fit-subtext")
                return

            # Header card
            with ui.card().classes("fit-card w-full"):
                with ui.column().classes("p-4 gap-3"):
                    with ui.row().classes("items-start justify-between w-full"):
                        with ui.column().classes("gap-1"):
                            ui.label(title).classes("fit-text text-2xl font-bold")
                            if company:
                                ui.label(company).classes("fit-subtext text-base")
                            ui.link(job["url"], job["url"], new_tab=True).classes("text-blue-400 text-sm")

                        async def start_analysis():
                            async with httpx.AsyncClient(timeout=60) as client:
                                r = await client.post(f"{API}/match/{job_id}")
                            if r.status_code == 201:
                                match_id = r.json()["id"]
                                ui.navigate.to(f"/match/{match_id}")
                            else:
                                ui.notify(r.json().get("detail", "分析失敗"), type="negative")

                        ui.button("開始匹配分析", icon="analytics", on_click=start_analysis).props("unelevated color=blue")

                    # 基本資訊 chips
                    with ui.row().classes("gap-3 flex-wrap mt-1"):
                        for icon, val, color in [
                            ("payments",      parsed.get("salary"),        "green"),
                            ("location_on",   parsed.get("location"),      "blue"),
                            ("computer",      parsed.get("remote_policy"), "purple"),
                        ]:
                            if val:
                                with ui.row().classes(f"items-center gap-1.5 px-3 py-1.5 rounded-full bg-{color}-50"):
                                    ui.icon(icon, color=color).classes("text-sm")
                                    ui.label(val).classes(f"text-sm text-{color}-700 font-medium")

            # 職缺描述
            if parsed.get("description"):
                with ui.card().classes("fit-card w-full"):
                    with ui.column().classes("p-4 gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("description", color="gray").classes("text-base")
                            ui.label("職缺描述").classes("fit-text font-semibold")
                        ui.label(parsed["description"]).classes("fit-subtext text-sm leading-relaxed")

            # 技能區塊
            with ui.row().classes("w-full gap-4"):
                req_skills = parsed.get("required_skills", [])
                bonus_skills = parsed.get("bonus_skills", [])

                if req_skills:
                    with ui.card().classes("fit-card flex-1"):
                        with ui.column().classes("p-4 gap-3"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("star", color="orange").classes("text-base")
                                ui.label("必要技能").classes("fit-text font-semibold")
                            with ui.row().classes("gap-2 flex-wrap"):
                                for s in req_skills:
                                    ui.badge(s, color="orange").classes("text-xs px-2 py-1")

                if bonus_skills:
                    with ui.card().classes("fit-card flex-1"):
                        with ui.column().classes("p-4 gap-3"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("add_circle", color="green").classes("text-base")
                                ui.label("加分技能").classes("fit-text font-semibold")
                            with ui.row().classes("gap-2 flex-wrap"):
                                for s in bonus_skills:
                                    ui.badge(s, color="green").classes("text-xs px-2 py-1")

            # 文化關鍵字
            culture = parsed.get("culture_keywords", [])
            if culture:
                with ui.card().classes("fit-card w-full"):
                    with ui.column().classes("p-4 gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("groups", color="purple").classes("text-base")
                            ui.label("公司文化").classes("fit-text font-semibold")
                        with ui.row().classes("gap-2 flex-wrap"):
                            for k in culture:
                                ui.badge(k, color="purple").classes("text-xs px-2 py-1")
