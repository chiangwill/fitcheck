from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from nicegui import ui

from app.database import create_tables
from app.models.crawler_job_status import CrawlerJobStatus  # noqa: F401 — registers model on Base.metadata
from app.routers import applications as applications_router
from app.routers import crawler_jobs as crawler_jobs_router
from app.routers import generate as generate_router
from app.routers import jobs as jobs_router
from app.routers import match as match_router
from app.routers import resume as resume_router
from app.ui import register_pages
from app.ui.common import THEME_CSS, sidebar

API = "http://localhost:8000"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="FitCheck", lifespan=lifespan)

app.include_router(resume_router.router)
app.include_router(jobs_router.router)
app.include_router(match_router.router)
app.include_router(generate_router.router)
app.include_router(applications_router.router)
app.include_router(crawler_jobs_router.router)


@ui.page("/")
async def index():
    ui.add_css(THEME_CSS)
    sidebar("/ui")

    async with httpx.AsyncClient() as client:
        rr = await client.get(f"{API}/resume/versions")
        jr = await client.get(f"{API}/jobs")
        mr = await client.get(f"{API}/match")
        ar = await client.get(f"{API}/applications")

    resumes = rr.json() if rr.status_code == 200 else []
    jobs = jr.json() if jr.status_code == 200 else []
    matches = mr.json() if mr.status_code == 200 else []
    applications = ar.json() if ar.status_code == 200 else []

    active_resume = next((r for r in resumes if r["is_active"]), None)
    recent_matches = sorted(matches, key=lambda m: m["created_at"], reverse=True)[:3]
    jobs_map = {j["id"]: j for j in jobs}

    with ui.column().classes("fit-page w-full"):
        # Header
        with ui.row().classes("fit-header w-full items-center justify-between px-8 py-5"):
            with ui.column().classes("gap-0"):
                ui.label("✦ FitCheck").classes("fit-text text-xl font-black")
                ui.label("求職進度總覽").classes("fit-subtext text-xs")

        with ui.column().classes("w-full p-8 gap-8"):
            # 歡迎語
            greeting = f"目前使用：{active_resume['version_name']}" if active_resume else "尚未設定 active 履歷"
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-1"):
                    ui.label("你好 👋").classes("fit-text text-2xl font-bold")
                    ui.label(greeting).classes("fit-subtext text-sm")
                ui.button("前往分析", icon="play_arrow", on_click=lambda: ui.navigate.to("/match")).props("unelevated color=blue")

            # Stats
            stats = [
                ("description",    "履歷版本",  len(resumes),      "blue",   "/ui/resume"),
                ("travel_explore", "已解析職缺", len(jobs),        "purple", "/ui/jobs"),
                ("analytics",      "匹配分析",  len(matches),     "green",  "/ui/match"),
                ("send",           "投遞紀錄",  len(applications), "orange", "/ui/applications"),
            ]
            with ui.row().classes("w-full gap-4 flex-wrap"):
                for icon, label, count, color, path in stats:
                    with ui.element("a").props(f'href="{path}"').style("text-decoration:none; flex:1; min-width:160px"):
                        with ui.column().classes("stat-card p-5 gap-3"):
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.icon(icon, color=color).classes("text-2xl")
                                ui.label(str(count)).classes(f"text-3xl font-black text-{color}-500")
                            ui.label(label).classes("fit-subtext text-sm font-medium")

            # 最近匹配
            with ui.column().classes("w-full gap-3"):
                ui.label("最近分析").classes("fit-text font-semibold")
                if not recent_matches:
                    with ui.column().classes("fit-card p-8 items-center gap-3"):
                        ui.icon("analytics", size="2.5rem").classes("text-gray-300")
                        ui.label("還沒有分析紀錄").classes("fit-subtext text-sm")
                        ui.button("開始第一次分析", on_click=lambda: ui.navigate.to("/match")).props("flat color=blue size=sm")
                else:
                    for match in recent_matches:
                        job = jobs_map.get(match["job_id"], {})
                        parsed = job.get("parsed_json") or {}
                        title = parsed.get("title") or f"職缺 #{match['job_id']}"
                        company = parsed.get("company") or ""
                        score = match.get("score") or 0
                        color = "green" if score >= 7 else "orange" if score >= 4 else "red"

                        with ui.element("a").props(f'href="/ui/match/{match["id"]}"').style("text-decoration:none; width:100%"):
                            with ui.row().classes("fit-card px-5 py-4 items-center justify-between w-full").style("transition: box-shadow .15s").on(
                                "mouseenter", lambda e, el=None: None
                            ):
                                with ui.row().classes("items-center gap-4"):
                                    with ui.column().classes(f"w-9 h-9 rounded-full bg-{color}-100 items-center justify-center"):
                                        ui.icon("analytics", color=color).classes("text-base")
                                    with ui.column().classes("gap-0.5"):
                                        ui.label(title).classes("fit-text font-semibold text-sm")
                                        if company:
                                            ui.label(company).classes("fit-subtext text-xs")
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(f"{score:.1f}").classes(f"font-black text-xl text-{color}-500")
                                    ui.label("/ 10").classes("fit-subtext text-xs")


register_pages()

ui.run_with(app, mount_path="/ui", storage_secret="fitcheck_secret")
