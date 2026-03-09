import httpx
from nicegui import ui

from app.ui.common import page_layout

API = "http://localhost:8000"

STATUS_CONFIG = {
    "pending":      ("等待中",  "gray",   "schedule"),
    "applied":      ("已投遞",  "blue",   "send"),
    "interviewing": ("面試中",  "orange", "groups"),
    "offer":        ("已錄取",  "green",  "celebration"),
    "rejected":     ("未錄取",  "red",    "cancel"),
}


def applications_page():
    @ui.page("/applications")
    async def page():
        content = page_layout("投遞追蹤", "記錄每一份投遞的狀態與面試心得", "/ui/applications")

        with content:
            async def load_apps():
                container.clear()
                async with httpx.AsyncClient() as client:
                    ar = await client.get(f"{API}/applications")
                    jr = await client.get(f"{API}/jobs")
                applications = ar.json() if ar.status_code == 200 else []
                jobs_map = {j["id"]: j for j in (jr.json() if jr.status_code == 200 else [])}

                with container:
                    if not applications:
                        with ui.column().classes("items-center py-12 gap-3"):
                            ui.icon("send", size="3rem").classes("text-gray-300")
                            ui.label("尚無投遞紀錄").classes("fit-subtext")
                        return

                    for app in applications:
                        job = jobs_map.get(app["job_id"], {})
                        parsed = job.get("parsed_json") or {}
                        title = parsed.get("title") or f"職缺 #{app['job_id']}"
                        company = parsed.get("company") or ""
                        status = app["status"]
                        label, color, icon = STATUS_CONFIG.get(status, (status, "gray", "help"))

                        with ui.card().classes("w-full fit-card"):
                            with ui.column().classes("p-2 gap-4 w-full"):
                                # Header
                                with ui.row().classes("items-center justify-between w-full"):
                                    with ui.row().classes("items-center gap-3"):
                                        with ui.column().classes(f"w-10 h-10 rounded-full bg-{color}-100 items-center justify-center"):
                                            ui.icon(icon, color=color).classes("text-lg")
                                        with ui.column().classes("gap-0.5"):
                                            ui.label(title).classes("font-semibold fit-text")
                                            if company:
                                                ui.label(company).classes("text-sm fit-subtext")
                                    with ui.column().classes("items-end gap-1"):
                                        ui.badge(label, color=color)
                                        if app.get("applied_at"):
                                            ui.label(f"投遞：{app['applied_at'][:10]}").classes("text-xs fit-subtext")

                                ui.separator()

                                # 狀態流
                                steps = list(STATUS_CONFIG.keys())
                                with ui.row().classes("gap-1 flex-wrap"):
                                    for s in steps:
                                        s_label, s_color, _ = STATUS_CONFIG[s]
                                        is_current = s == status
                                        ui.badge(s_label, color=s_color if is_current else "gray").classes(
                                            "cursor-pointer opacity-100" if is_current else "cursor-pointer opacity-40"
                                        )

                                # 更新狀態
                                with ui.row().classes("items-center gap-3 flex-wrap"):
                                    status_select = ui.select(
                                        {k: v[0] for k, v in STATUS_CONFIG.items()},
                                        value=status,
                                        label="更新狀態",
                                    ).props("dense outlined").classes("w-36")

                                    async def update_status(aid=app["id"], ss=status_select):
                                        async with httpx.AsyncClient() as client:
                                            await client.put(f"{API}/applications/{aid}", json={"status": ss.value})
                                        ui.notify("狀態已更新", type="positive")
                                        await load_apps()

                                    ui.button("更新狀態", on_click=update_status).props("unelevated color=blue size=sm")

                                    async def delete_app(aid=app["id"]):
                                        async with httpx.AsyncClient() as client:
                                            await client.delete(f"{API}/applications/{aid}")
                                        ui.notify("已刪除", type="warning")
                                        await load_apps()

                                    ui.button(icon="delete", on_click=delete_app).props("flat color=red size=sm round")

                                # 備註
                                notes_input = ui.textarea(
                                    label="備註（面試心得、聯絡窗口、薪資談判等）",
                                    value=app.get("notes") or "",
                                ).classes("w-full").props("outlined dense rows=2")

                                async def save_notes(aid=app["id"], ni=notes_input):
                                    async with httpx.AsyncClient() as client:
                                        await client.put(f"{API}/applications/{aid}", json={"notes": ni.value})
                                    ui.notify("備註已儲存", type="positive")

                                ui.button("儲存備註", icon="save", on_click=save_notes).props("flat color=gray size=sm")

            # 新增
            with ui.card().classes("w-full fit-card"):
                with ui.column().classes("p-2 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("add_task", color="blue").classes("text-xl")
                        ui.label("新增投遞紀錄").classes("font-semibold fit-text")

                    async with httpx.AsyncClient() as client:
                        jr = await client.get(f"{API}/jobs")
                    all_jobs = jr.json() if jr.status_code == 200 else []

                    if not all_jobs:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("info", color="orange")
                            ui.label("請先到「職缺解析」頁面新增至少一個職缺").classes("text-sm fit-subtext")
                    else:
                        job_options = {
                            f"{(j.get('parsed_json') or {}).get('title', '未知')}  ·  {(j.get('parsed_json') or {}).get('company', '')}": j["id"]
                            for j in all_jobs
                        }
                        with ui.row().classes("w-full gap-3 items-center"):
                            job_select = ui.select(list(job_options.keys()), label="選擇職缺").classes("flex-1").props("outlined dense")

                            async def add_application():
                                if not job_select.value:
                                    ui.notify("請選擇職缺", type="warning")
                                    return
                                job_id = job_options[job_select.value]
                                async with httpx.AsyncClient() as client:
                                    r = await client.post(f"{API}/applications", json={"job_id": job_id})
                                if r.status_code == 201:
                                    ui.notify("已新增投遞紀錄", type="positive")
                                    await load_apps()
                                else:
                                    ui.notify("新增失敗", type="negative")

                            ui.button("新增", icon="add", on_click=add_application).props("unelevated color=blue")

            # 列表
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("所有投遞").classes("font-semibold fit-text")

            container = ui.column().classes("w-full gap-3")
            await load_apps()
