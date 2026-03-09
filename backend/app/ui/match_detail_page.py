import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"


def match_detail_page():
    @ui.page("/match/{match_id}")
    async def page(match_id: int):
        content = page_layout("匹配分析詳情", "", "/ui/match")

        with content:
            async with httpx.AsyncClient() as client:
                mr = await client.get(f"{API}/match/{match_id}")

            if mr.status_code != 200:
                ui.label("找不到分析結果").classes("fit-subtext")
                return

            match = mr.json()

            async with httpx.AsyncClient() as client:
                jr = await client.get(f"{API}/jobs/{match['job_id']}")
            job = jr.json() if jr.status_code == 200 else {}
            parsed = job.get("parsed_json") or {}

            title = parsed.get("title") or f"職缺 #{match['job_id']}"
            company = parsed.get("company") or ""
            score = match.get("score") or 0
            score_color = "green" if score >= 7 else "orange" if score >= 4 else "red"
            badge_color = score_color

            # 返回
            with ui.row().classes("items-center gap-2"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/match")).props("flat round size=sm")
                ui.label("返回列表").classes("fit-subtext text-sm cursor-pointer").on("click", lambda: ui.navigate.to("/match"))

            # 分數 header
            with ui.card().classes("fit-card w-full"):
                with ui.row().classes("items-center justify-between p-4 w-full"):
                    with ui.column().classes("gap-1"):
                        ui.label(title).classes("fit-text text-xl font-bold")
                        if company:
                            ui.label(company).classes("fit-subtext")
                        if parsed.get("salary"):
                            ui.label(f"💰 {parsed['salary']}").classes("text-sm fit-subtext")
                    with ui.column().classes("items-end gap-1"):
                        ui.label(f"{score:.1f}").classes(f"text-5xl font-black text-{score_color}-500")
                        ui.label("/ 10").classes("fit-subtext text-sm")
                        ui.badge("適合" if score >= 7 else "普通" if score >= 4 else "不適合", color=badge_color)

            # 技能比對
            with ui.row().classes("w-full gap-4"):
                matched = match.get("matched_skills") or []
                missing = match.get("missing_skills") or []

                with ui.card().classes("fit-card flex-1"):
                    with ui.column().classes("p-4 gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("check_circle", color="green").classes("text-base")
                            ui.label(f"符合條件（{len(matched)}）").classes("fit-text font-semibold")
                        if matched:
                            for skill in matched:
                                with ui.row().classes("items-start gap-2"):
                                    ui.icon("check", color="green", size="xs").classes("flex-shrink-0 mt-0.5")
                                    ui.label(skill).classes("text-sm fit-text")
                        else:
                            ui.label("無").classes("text-sm fit-subtext")

                with ui.card().classes("fit-card flex-1"):
                    with ui.column().classes("p-4 gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("cancel", color="red").classes("text-base")
                            ui.label(f"缺少條件（{len(missing)}）").classes("fit-text font-semibold")
                        if missing:
                            for skill in missing:
                                with ui.row().classes("items-start gap-2"):
                                    ui.icon("close", color="red", size="xs").classes("flex-shrink-0 mt-0.5")
                                    ui.label(skill).classes("text-sm fit-text")
                        else:
                            ui.label("無").classes("text-sm fit-subtext")

            # 補強建議
            if match.get("suggestion"):
                with ui.card().classes("fit-card w-full"):
                    with ui.column().classes("p-4 gap-3"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("lightbulb", color="orange").classes("text-base")
                            ui.label("補強建議").classes("fit-text font-semibold")
                        ui.label(match["suggestion"]).classes("text-sm fit-subtext leading-loose whitespace-pre-wrap")

            # 求職信
            with ui.card().classes("fit-card w-full"):
                with ui.column().classes("p-4 gap-4"):
                    with ui.row().classes("items-center justify-between w-full"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("edit_note", color="blue").classes("text-base")
                            ui.label("求職信").classes("fit-text font-semibold")

                        if not match.get("cover_letter"):
                            tone_select = ui.select(["正式", "活潑"], value="正式", label="語氣").props("dense outlined").classes("w-24")

                            async def generate():
                                gen_btn.props("loading")
                                async with httpx.AsyncClient(timeout=60) as client:
                                    r = await client.post(f"{API}/generate/{match_id}", json={"tone": tone_select.value})
                                try:
                                    gen_btn.props(remove="loading")
                                    if r.status_code == 200:
                                        ui.notify("求職信生成完成！", type="positive")
                                        ui.navigate.to(f"/match/{match_id}")
                                    else:
                                        ui.notify(r.json().get("detail", "生成失敗"), type="negative")
                                except RuntimeError:
                                    pass

                            gen_btn = ui.button("生成求職信", on_click=generate).props("unelevated color=blue")

                    if match.get("cover_letter"):
                        with ui.tabs().classes("w-full") as tabs:
                            tab_zh = ui.tab("中文版")
                            tab_en = ui.tab("English")

                        with ui.tab_panels(tabs, value=tab_zh).classes("w-full"):
                            with ui.tab_panel(tab_zh):
                                cl_zh = match["cover_letter"]
                                ui.label(cl_zh).classes("fit-text leading-loose whitespace-pre-wrap").style("font-size:15px; line-height:1.9")
                                with ui.row().classes("items-center justify-between w-full mt-2"):
                                    ui.label(f"{len(cl_zh)} 字").classes("text-xs fit-subtext")
                                    ui.button("複製", icon="content_copy", on_click=lambda cl=cl_zh: ui.run_javascript(
                                        f"navigator.clipboard.writeText({repr(cl)})"
                                    )).props("flat color=blue size=sm")

                            with ui.tab_panel(tab_en):
                                cl_en = match.get("cover_letter_en") or ""
                                if cl_en:
                                    ui.label(cl_en).classes("fit-text leading-loose whitespace-pre-wrap").style("font-size:15px; line-height:1.9")
                                    with ui.row().classes("items-center justify-between w-full mt-2"):
                                        ui.label(f"{len(cl_en.split())} words").classes("text-xs fit-subtext")
                                        ui.button("Copy", icon="content_copy", on_click=lambda cl=cl_en: ui.run_javascript(
                                            f"navigator.clipboard.writeText({repr(cl)})"
                                        )).props("flat color=blue size=sm")
                                else:
                                    ui.label("尚無英文版").classes("fit-subtext text-sm")
                    else:
                        ui.label("尚未生成求職信").classes("fit-subtext text-sm")
