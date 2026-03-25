import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def _score_color(score: float) -> str:
    if score >= 7:
        return "green"
    if score >= 4:
        return "orange"
    return "red"


def _source_label(source: str) -> tuple[str, str]:
    """Return (label, color) for a job source."""
    if source == "japan_dev":
        return "Japan Dev", "blue"
    if source == "tokyo_dev":
        return "Tokyo Dev", "teal"
    return source, "grey"


def crawler_jobs_page():
    @ui.page("/crawler-jobs")
    async def page():
        content = page_layout("爬蟲職缺", "來自 Japan Dev & Tokyo Dev 的每日職缺", "/ui/crawler-jobs")

        with content:
            show_all = {"value": False}
            jobs_container = ui.column().classes("w-full gap-3")

            async def load_jobs():
                jobs_container.clear()
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        r = await client.get(
                            f"{API}/crawler-jobs",
                            params={"all_time": str(show_all["value"]).lower()},
                        )
                    if r.status_code == 503:
                        with jobs_container:
                            with ui.card().classes("w-full fit-card"):
                                with ui.column().classes("p-4 items-center gap-3"):
                                    ui.icon("cloud_off", size="2rem").classes("text-red-400")
                                    ui.label("無法連線至 Supabase").classes("font-semibold fit-text")
                                    ui.label("請確認 SUPABASE_URL / SUPABASE_KEY 設定是否正確").classes("text-sm fit-subtext")
                        return
                    jobs = r.json() if r.status_code == 200 else []
                except Exception as e:
                    with jobs_container:
                        with ui.card().classes("w-full fit-card"):
                            with ui.column().classes("p-4 items-center gap-3"):
                                ui.icon("cloud_off", size="2rem").classes("text-red-400")
                                ui.label("連線失敗").classes("font-semibold fit-text")
                                ui.label(str(e)).classes("text-xs fit-subtext")
                    return

                with jobs_container:
                    if not jobs:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("work_off", size="3rem").classes("text-gray-300")
                            label = "沒有歷史職缺" if show_all["value"] else "最近 7 天沒有新職缺"
                            ui.label(label).classes("fit-subtext")
                        return

                    for job in jobs:
                        _render_job_card(job)

            def _render_job_card(job: dict):
                supabase_id = job["id"]
                title = job.get("title") or "（無標題）"
                company = job.get("company") or ""
                source_label, source_color = _source_label(job.get("source", ""))
                skills: list[str] = job.get("skills") or []
                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")
                location = job.get("location") or ""
                remote = job.get("remote_level") or ""
                url = job.get("url", "")

                salary_str = ""
                if salary_min and salary_max:
                    salary_str = f"¥{salary_min:,}–{salary_max:,}"
                elif salary_min:
                    salary_str = f"¥{salary_min:,}+"

                score_state = {"data": None}

                with ui.card().classes("w-full fit-card"):
                    with ui.row().classes("items-start justify-between w-full p-1"):
                        # Left: job info
                        with ui.row().classes("items-start gap-4 flex-1"):
                            with ui.column().classes("w-10 h-10 rounded-full bg-blue-100 items-center justify-center flex-shrink-0"):
                                ui.icon("work", color="blue").classes("text-lg")

                            with ui.column().classes("gap-1 flex-1"):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    ui.label(title).classes("font-semibold fit-text")
                                    ui.badge(source_label, color=source_color).classes("text-xs")

                                if company:
                                    ui.label(company).classes("text-sm fit-subtext")

                                ui.link(url, url, new_tab=True).classes("text-xs text-blue-400 truncate max-w-md")

                                with ui.row().classes("gap-4 mt-1 flex-wrap"):
                                    if salary_str:
                                        ui.label(f"💰 {salary_str}").classes("text-xs fit-subtext")
                                    if location:
                                        ui.label(f"📍 {location}").classes("text-xs fit-subtext")
                                    if remote:
                                        ui.label(f"🖥 {remote}").classes("text-xs fit-subtext")

                                if skills:
                                    with ui.row().classes("gap-1 mt-1 flex-wrap"):
                                        for s in skills[:6]:
                                            ui.badge(s, color="purple").classes("text-xs opacity-80")
                                        if len(skills) > 6:
                                            ui.label(f"+{len(skills) - 6}").classes("text-xs fit-subtext")

                        # Right: score button + result
                        with ui.column().classes("items-end gap-2 min-w-24"):
                            score_display = ui.column().classes("items-end gap-1")
                            score_btn = ui.button("評分", icon="analytics").props("color=blue unelevated size=sm")

                            async def on_score(
                                sid=supabase_id,
                                btn=score_btn,
                                display=score_display,
                            ):
                                btn.props("loading")
                                btn.set_enabled(False)
                                try:
                                    async with httpx.AsyncClient(timeout=60) as client:
                                        r = await client.post(f"{API}/crawler-jobs/{sid}/score")

                                    display.clear()
                                    with display:
                                        if r.status_code == 200:
                                            data = r.json()
                                            score = data.get("score") or 0
                                            color = _score_color(score)
                                            with ui.row().classes("items-baseline gap-1"):
                                                ui.label(f"{score:.1f}").classes(f"font-black text-2xl text-{color}-500")
                                                ui.label("/ 10").classes("fit-subtext text-xs")
                                            missing = data.get("missing_skills") or []
                                            if missing:
                                                ui.label(f"缺：{', '.join(missing[:3])}").classes("text-xs fit-subtext text-right")
                                            if data.get("cached"):
                                                ui.label("（已快取）").classes("text-xs fit-subtext")
                                        elif r.status_code == 404 and "active 履歷" in r.text:
                                            ui.notify("請先設定 active 履歷", type="warning")
                                        elif r.status_code == 422:
                                            ui.label("頁面無法解析").classes("text-xs text-red-400")
                                        elif r.status_code == 500:
                                            detail = r.json().get("detail", "")
                                            if "429" in detail or "rate" in detail.lower():
                                                ui.label("Gemini 超過每日限額").classes("text-xs text-orange-400")
                                            else:
                                                ui.label("評分失敗，請稍後再試").classes("text-xs text-red-400")
                                        else:
                                            ui.label("評分失敗").classes("text-xs text-red-400")
                                except Exception:
                                    with display:
                                        ui.label("連線失敗").classes("text-xs text-red-400")
                                finally:
                                    btn.props(remove="loading")
                                    btn.set_enabled(True)

                            score_btn.on_click(on_score)

            # Controls row
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("爬蟲職缺").classes("font-semibold fit-text")
                async def toggle_all():
                    show_all["value"] = not show_all["value"]
                    toggle_btn.set_text("顯示最近 7 天" if show_all["value"] else "顯示所有時間")
                    await load_jobs()

                toggle_btn = ui.button(
                    "顯示所有時間",
                    icon="history",
                    on_click=toggle_all,
                ).props("flat color=blue size=sm")

            await load_jobs()
