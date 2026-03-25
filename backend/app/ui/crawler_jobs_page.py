import asyncio

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


_STATUS_DEFS = [
    ("interested", "感興趣", "blue"),
    ("applied", "已投履", "green"),
    ("rejected", "不適合", "grey"),
]


def crawler_jobs_page():
    @ui.page("/crawler-jobs")
    async def page():
        content = page_layout("爬蟲職缺", "來自 Japan Dev & Tokyo Dev 的每日職缺", "/ui/crawler-jobs")

        with content:
            # ── state ──────────────────────────────────────────────────────
            show_all = {"value": False}
            sort_by_score = {"value": False}
            current_jobs: list[dict] = []
            cached_scores: dict[str, dict] = {}
            cached_statuses: dict[str, str] = {}

            # ── controls row ───────────────────────────────────────────────
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("爬蟲職缺").classes("font-semibold fit-text")

                with ui.row().classes("items-center gap-2"):
                    sort_btn = ui.button("依評分", icon="sort").props("flat color=blue size=sm")
                    bulk_btn = ui.button("一鍵評分全部", icon="auto_awesome").props("flat color=orange size=sm")
                    toggle_btn = ui.button("顯示所有時間", icon="history").props("flat color=blue size=sm")

            # ── skills gap banner (hidden until ≥1 job scored) ────────────
            gap_banner = ui.row().classes("w-full").style("display:none")

            # ── jobs list ──────────────────────────────────────────────────
            jobs_container = ui.column().classes("w-full gap-3")

            # ── helpers ────────────────────────────────────────────────────

            def _compute_skills_gap() -> tuple[int, list[tuple[str, int]]]:
                """Return (scored_count, top_5_skills)."""
                counts: dict[str, int] = {}
                scored = 0
                for job in current_jobs:
                    data = cached_scores.get(job["id"])
                    if data is not None:
                        scored += 1
                        for skill in data.get("missing_skills") or []:
                            if isinstance(skill, str):
                                counts[skill] = counts.get(skill, 0) + 1
                return scored, sorted(counts.items(), key=lambda x: -x[1])[:5]

            def _refresh_gap_banner() -> None:
                gap_banner.clear()
                scored, top = _compute_skills_gap()
                if scored == 0 or not top:
                    gap_banner.style("display:none")
                    return
                gap_banner.style("")
                with gap_banner:
                    with ui.card().classes("w-full fit-card px-4 py-3"):
                        with ui.column().classes("gap-1"):
                            ui.label("📊 Skills Gap 分析").classes("font-semibold fit-text text-sm")
                            items = " · ".join(
                                f"{skill} 缺少於 {cnt}/{scored} 職缺"
                                for skill, cnt in top
                            )
                            ui.label(items).classes("text-xs fit-subtext")

            def _sorted_jobs() -> list[dict]:
                if not sort_by_score["value"]:
                    return list(current_jobs)

                def _key(job: dict):
                    data = cached_scores.get(job["id"])
                    if data and data.get("score") is not None:
                        return (0, -data["score"])
                    return (1, 0)  # unscored → bottom

                return sorted(current_jobs, key=_key)

            # ── load_jobs ──────────────────────────────────────────────────

            async def load_jobs() -> None:
                jobs_container.clear()
                gap_banner.style("display:none")
                current_jobs.clear()
                cached_scores.clear()
                cached_statuses.clear()

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

                current_jobs.extend(jobs)

                if jobs:
                    ids = [j["id"] for j in jobs]
                    ids_csv = ",".join(ids)
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            scores_r, statuses_r = await asyncio.gather(
                                client.post(f"{API}/crawler-jobs/scores", json={"ids": ids}),
                                client.get(f"{API}/crawler-jobs/statuses", params={"ids": ids_csv}),
                                return_exceptions=True,
                            )
                        if isinstance(scores_r, Exception):
                            print(f"[crawler-jobs] preload scores failed: {scores_r}")
                        elif scores_r.status_code == 200:
                            cached_scores.update(scores_r.json())
                        if isinstance(statuses_r, Exception):
                            print(f"[crawler-jobs] preload statuses failed: {statuses_r}")
                        elif statuses_r.status_code == 200:
                            cached_statuses.update(statuses_r.json())
                    except Exception as e:
                        print(f"[crawler-jobs] preload failed: {e}")

                with jobs_container:
                    if not jobs:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("work_off", size="3rem").classes("text-gray-300")
                            label = "沒有歷史職缺" if show_all["value"] else "最近 7 天沒有新職缺"
                            ui.label(label).classes("fit-subtext")
                        return

                    for job in _sorted_jobs():
                        _render_job_card(job)

                _refresh_gap_banner()

            # ── _render_job_card ───────────────────────────────────────────

            def _render_job_card(job: dict) -> None:
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

                                # ── status chips ──────────────────────────
                                status_row = ui.row().classes("gap-1 mt-2")
                                current_status = {"value": cached_statuses.get(supabase_id)}

                                def _rebuild_chips(sid: str, row: ui.row, status_ref: dict) -> None:
                                    row.clear()
                                    with row:
                                        for val, label, color in _STATUS_DEFS:
                                            active = status_ref["value"] == val
                                            btn = ui.button(label).props(
                                                f"color={color} size=xs {'unelevated' if active else 'flat outline'}"
                                            )

                                            def _make_handler(v=val, s=sid, r=row, sr=status_ref):
                                                async def _handler():
                                                    # toggle off if already selected
                                                    sr["value"] = v if sr["value"] != v else None
                                                    _rebuild_chips(s, r, sr)
                                                    new_status = sr["value"]
                                                    if new_status:
                                                        try:
                                                            async with httpx.AsyncClient(timeout=5) as c:
                                                                await c.patch(
                                                                    f"{API}/crawler-jobs/{s}/status",
                                                                    json={"status": new_status},
                                                                )
                                                            cached_statuses[s] = new_status
                                                        except Exception:
                                                            pass
                                                    else:
                                                        try:
                                                            async with httpx.AsyncClient(timeout=5) as c:
                                                                await c.delete(f"{API}/crawler-jobs/{s}/status")
                                                            cached_statuses.pop(s, None)
                                                        except Exception:
                                                            pass
                                                return _handler

                                            btn.on_click(_make_handler())

                                _rebuild_chips(supabase_id, status_row, current_status)

                        # Right: score display + button
                        with ui.column().classes("items-end gap-2 min-w-24"):
                            score_display = ui.column().classes("items-end gap-1")

                            # Show pre-loaded cached score immediately
                            preloaded = cached_scores.get(supabase_id)
                            if preloaded:
                                score_val = preloaded.get("score") or 0
                                col = _score_color(score_val)
                                with score_display:
                                    with ui.row().classes("items-baseline gap-1"):
                                        ui.label(f"{score_val:.1f}").classes(f"font-black text-2xl text-{col}-500")
                                        ui.label("/ 10").classes("fit-subtext text-xs")
                                    missing = preloaded.get("missing_skills") or []
                                    if missing:
                                        ui.label(f"缺：{', '.join(missing[:3])}").classes("text-xs fit-subtext text-right")
                                    ui.label("（已快取）").classes("text-xs fit-subtext")

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
                                            score = data.get("score") if data.get("score") is not None else 0
                                            color = _score_color(score)
                                            with ui.row().classes("items-baseline gap-1"):
                                                ui.label(f"{score:.1f}").classes(f"font-black text-2xl text-{color}-500")
                                                ui.label("/ 10").classes("fit-subtext text-xs")
                                            missing = data.get("missing_skills") or []
                                            if missing:
                                                ui.label(f"缺：{', '.join(missing[:3])}").classes("text-xs fit-subtext text-right")
                                            if data.get("cached"):
                                                ui.label("（已快取）").classes("text-xs fit-subtext")
                                            cached_scores[sid] = data
                                            _refresh_gap_banner()
                                        elif r.status_code == 404 and "active 履歷" in r.text:
                                            ui.notify("請先設定 active 履歷", type="warning")
                                        elif r.status_code == 422:
                                            ui.label("頁面無法解析").classes("text-xs text-red-400")
                                        elif r.status_code == 500:
                                            try:
                                                detail = r.json().get("detail", "")
                                            except Exception:
                                                detail = ""
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

            # ── button handlers (defined after helpers/render fn) ──────────

            async def toggle_all() -> None:
                show_all["value"] = not show_all["value"]
                toggle_btn.set_text("顯示最近 7 天" if show_all["value"] else "顯示所有時間")
                await load_jobs()

            toggle_btn.on_click(toggle_all)

            async def toggle_sort() -> None:
                sort_by_score["value"] = not sort_by_score["value"]
                sort_btn.set_text("依日期" if sort_by_score["value"] else "依評分")
                jobs_container.clear()
                with jobs_container:
                    for job in _sorted_jobs():
                        _render_job_card(job)

            sort_btn.on_click(toggle_sort)

            async def bulk_score() -> None:
                if not current_jobs:
                    return
                total = len(current_jobs)
                success = 0
                fail = 0
                bulk_btn.set_enabled(False)
                ui.notify(
                    f"⚠️ 批量評分將消耗約 {total} 次 Gemini 每日配額",
                    type="warning",
                    timeout=5000,
                )
                for i, job in enumerate(current_jobs):
                    sid = job["id"]
                    bulk_btn.set_text(f"Scoring {i + 1}/{total}…")
                    try:
                        async with httpx.AsyncClient(timeout=60) as client:
                            r = await client.post(f"{API}/crawler-jobs/{sid}/score")
                        if r.status_code == 200:
                            success += 1
                            cached_scores[sid] = r.json()
                        else:
                            fail += 1
                    except Exception:
                        fail += 1
                    if i < total - 1:
                        await asyncio.sleep(4)

                bulk_btn.set_text("一鍵評分全部")
                bulk_btn.set_enabled(True)
                if fail:
                    ui.notify(f"{success}/{total} 成功，{fail} 失敗", type="warning")
                else:
                    ui.notify(f"全部 {success} 個評分完成！", type="positive")
                _refresh_gap_banner()
                jobs_container.clear()
                with jobs_container:
                    for job in _sorted_jobs():
                        _render_job_card(job)

            bulk_btn.on_click(bulk_score)

            await load_jobs()
