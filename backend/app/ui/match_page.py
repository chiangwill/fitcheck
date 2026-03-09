import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def match_page():
    @ui.page("/match")
    async def page():
        content = page_layout("匹配分析", "分析履歷與職缺的契合度，生成客製化求職信", "/ui/match")

        with content:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{API}/jobs")
            jobs = [j for j in (r.json() if r.status_code == 200 else []) if j.get("parsed_json")]

            async def load_matches():
                matches_container.clear()
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{API}/match")
                matches = r.json() if r.status_code == 200 else []

                async with httpx.AsyncClient() as client:
                    jr = await client.get(f"{API}/jobs")
                jobs_map = {j["id"]: j for j in (jr.json() if jr.status_code == 200 else [])}

                with matches_container:
                    if not matches:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("analytics", size="3rem").classes("text-gray-300")
                            ui.label("尚無分析紀錄").classes("fit-subtext")
                        return

                    for match in matches:
                        job = jobs_map.get(match["job_id"], {})
                        parsed = job.get("parsed_json") or {}
                        title = parsed.get("title") or f"職缺 #{match['job_id']}"
                        company = parsed.get("company") or ""
                        score = match.get("score") or 0

                        score_color = "text-green-600" if score >= 7 else "text-orange-500" if score >= 4 else "text-red-500"
                        badge_color = "green" if score >= 7 else "orange" if score >= 4 else "red"

                        with ui.card().classes("w-full fit-card"):
                            with ui.column().classes("p-2 gap-4 w-full"):
                                # Header
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.column().classes("gap-0.5"):
                                        ui.label(title).classes("font-semibold fit-text text-lg")
                                        if company:
                                            ui.label(company).classes("text-sm fit-subtext")
                                    with ui.row().classes("items-center gap-3"):
                                        ui.button("詳情", icon="open_in_full", on_click=lambda mid=match["id"]: ui.navigate.to(f"/match/{mid}")).props("flat color=blue size=sm")
                                    with ui.row().classes("items-center gap-3"):
                                        ui.label(f"{score:.1f}").classes(f"text-3xl font-black {score_color}")
                                        with ui.column().classes("gap-0"):
                                            ui.label("/ 10").classes("text-xs fit-subtext")
                                            ui.badge("適合" if score >= 7 else "普通" if score >= 4 else "不適合", color=badge_color).classes("text-xs")

                                ui.separator()

                                # Skills
                                with ui.row().classes("gap-6 w-full"):
                                    with ui.column().classes("flex-1 gap-2"):
                                        ui.label("符合條件").classes("text-xs font-semibold text-green-700 uppercase tracking-wide")
                                        for skill in (match.get("matched_skills") or []):
                                            with ui.row().classes("items-start gap-1.5"):
                                                ui.icon("check_circle", color="green", size="xs").classes("mt-0.5 flex-shrink-0")
                                                ui.label(skill).classes("text-sm fit-text")

                                    with ui.column().classes("flex-1 gap-2"):
                                        ui.label("缺少條件").classes("text-xs font-semibold text-red-600 uppercase tracking-wide")
                                        for skill in (match.get("missing_skills") or []):
                                            with ui.row().classes("items-start gap-1.5"):
                                                ui.icon("cancel", color="red", size="xs").classes("mt-0.5 flex-shrink-0")
                                                ui.label(skill).classes("text-sm fit-text")

                                if match.get("suggestion"):
                                    with ui.expansion("補強建議").classes("w-full"):
                                        with ui.column().classes("gap-2 px-2"):
                                            ui.label(match["suggestion"]).classes("text-sm fit-subtext leading-relaxed whitespace-pre-wrap")

                                ui.separator()

                                # 求職信
                                if match.get("cover_letter"):
                                    with ui.expansion("📄 求職信").classes("w-full"):
                                        with ui.column().classes("gap-3 px-2"):
                                            with ui.tabs().classes("w-full") as tabs:
                                                tab_zh = ui.tab("中文版")
                                                tab_en = ui.tab("English")
                                            with ui.tab_panels(tabs, value=tab_zh).classes("w-full"):
                                                with ui.tab_panel(tab_zh):
                                                    cl_zh = match["cover_letter"]
                                                    with ui.column().classes("gap-3"):
                                                        ui.label(cl_zh).classes("fit-text leading-loose whitespace-pre-wrap").style("font-size:15px; line-height:1.9")
                                                        with ui.row().classes("items-center justify-between w-full"):
                                                            ui.label(f"{len(cl_zh)} 字").classes("text-xs fit-subtext")
                                                            ui.button(
                                                                "複製",
                                                                icon="content_copy",
                                                                on_click=lambda cl=cl_zh: ui.run_javascript(
                                                                    f"navigator.clipboard.writeText({repr(cl)})"
                                                                ),
                                                            ).props("flat color=blue size=sm")
                                                with ui.tab_panel(tab_en):
                                                    cl_en = match.get("cover_letter_en") or ""
                                                    if cl_en:
                                                        with ui.column().classes("gap-3"):
                                                            ui.label(cl_en).classes("fit-text leading-loose whitespace-pre-wrap").style("font-size:15px; line-height:1.9")
                                                            with ui.row().classes("items-center justify-between w-full"):
                                                                ui.label(f"{len(cl_en.split())} words").classes("text-xs fit-subtext")
                                                                ui.button(
                                                                    "Copy",
                                                                    icon="content_copy",
                                                                    on_click=lambda cl=cl_en: ui.run_javascript(
                                                                        f"navigator.clipboard.writeText({repr(cl)})"
                                                                    ),
                                                                ).props("flat color=blue size=sm")
                                                    else:
                                                        ui.label("尚無英文版").classes("fit-subtext text-sm")
                                else:
                                    with ui.row().classes("items-center gap-3"):
                                        ui.icon("edit_note", color="blue").classes("text-lg")
                                        ui.label("尚未生成求職信").classes("text-sm fit-subtext")
                                        tone_select = ui.select(
                                            ["正式", "活潑"], value="正式", label="語氣"
                                        ).props("dense outlined").classes("w-24")

                                        async def gen_cover_letter(mid=match["id"], ts=tone_select):
                                            try:
                                                gen_btn.props("loading")
                                            except Exception:
                                                pass
                                            async with httpx.AsyncClient(timeout=60) as client:
                                                r = await client.post(
                                                    f"{API}/generate/{mid}",
                                                    json={"tone": ts.value},
                                                )
                                            try:
                                                gen_btn.props(remove="loading")
                                                if r.status_code == 200:
                                                    ui.notify("求職信生成完成！", type="positive")
                                                    await load_matches()
                                                else:
                                                    ui.notify(f"失敗：{r.json().get('detail', r.text)}", type="negative")
                                            except RuntimeError:
                                                pass

                                        gen_btn = ui.button("生成求職信", on_click=gen_cover_letter).props("unelevated color=blue size=sm")

            # 觸發分析
            with ui.card().classes("w-full fit-card"):
                with ui.column().classes("p-2 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("add_chart", color="green").classes("text-xl")
                        ui.label("新增匹配分析").classes("font-semibold fit-text")

                    if not jobs:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("info", color="orange")
                            ui.label("請先到「職缺解析」頁面新增至少一個職缺").classes("text-sm fit-subtext")
                    else:
                        job_options = {
                            f"{(j.get('parsed_json') or {}).get('title', '未知')}  ·  {(j.get('parsed_json') or {}).get('company', '')}": j["id"]
                            for j in jobs
                        }
                        with ui.row().classes("w-full gap-3 items-center"):
                            job_select = ui.select(list(job_options.keys()), label="選擇職缺").classes("flex-1").props("outlined dense")

                            async def run_match():
                                if not job_select.value:
                                    ui.notify("請選擇職缺", type="warning")
                                    return
                                job_id = job_options[job_select.value]
                                try:
                                    match_btn.props("loading")
                                except Exception:
                                    pass
                                async with httpx.AsyncClient(timeout=60) as client:
                                    r = await client.post(f"{API}/match/{job_id}")
                                try:
                                    match_btn.props(remove="loading")
                                except Exception:
                                    pass
                                if r.status_code == 201:
                                    ui.notify("分析完成！", type="positive")
                                    await load_matches()
                                else:
                                    ui.notify(f"失敗：{r.json().get('detail', r.text)}", type="negative")

                            match_btn = ui.button("開始分析", icon="play_arrow", on_click=run_match).props("unelevated color=green")

            # 紀錄
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("分析紀錄").classes("font-semibold fit-text")

            matches_container = ui.column().classes("w-full gap-4")
            await load_matches()
