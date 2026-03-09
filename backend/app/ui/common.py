from nicegui import ui

MENU_ITEMS = [
    ("home",           "首頁",     "/ui"),
    ("description",    "履歷管理", "/ui/resume"),
    ("travel_explore", "職缺解析", "/ui/jobs"),
    ("analytics",      "匹配分析", "/ui/match"),
    ("send",           "投遞追蹤", "/ui/applications"),
]

THEME_CSS = """
:root {
    --bg-page:    #f1f5f9;
    --bg-card:    #ffffff;
    --bg-header:  #ffffff;
    --text-main:  #1e293b;
    --text-sub:   #64748b;
    --border:     #e2e8f0;
    --accent:     #2563eb;
}
.body--dark {
    --bg-page:    #0f172a;
    --bg-card:    #1e293b;
    --bg-header:  #1e293b;
    --text-main:  #f1f5f9;
    --text-sub:   #94a3b8;
    --border:     #334155;
    --accent:     #3b82f6;
}
.fit-page    { background: var(--bg-page);   min-height: 100vh; }
.fit-card    { background: var(--bg-card);   border: 1px solid var(--border); border-radius: 12px; }
.fit-header  { background: var(--bg-header); border-bottom: 1px solid var(--border); }
.fit-text    { color: var(--text-main); }
.fit-subtext { color: var(--text-sub); }
.fit-divider { border-color: var(--border); }

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition: transform .15s, box-shadow .15s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }
.sidebar-item {
    border-radius: 8px;
    transition: background .15s;
    text-decoration: none;
}
.sidebar-active { background: rgba(59,130,246,.15) !important; }
.body--dark .sidebar-active { background: rgba(59,130,246,.25) !important; }
"""


def _inject_theme():
    ui.add_css(THEME_CSS)


def sidebar(active: str = ""):
    _inject_theme()

    with ui.left_drawer(fixed=True, value=True).classes("bg-gray-900 pt-5 pb-4").style("border-right: 1px solid #1e293b"):
        with ui.column().classes("px-3 gap-1 w-full"):
            with ui.row().classes("items-center px-2 mb-5"):
                ui.label("✦ FitCheck").classes("text-lg font-black text-white")

            for icon, label, path in MENU_ITEMS:
                is_active = active == path
                with ui.element("a").props(f'href="{path}"').classes(
                    f"sidebar-item w-full {'sidebar-active' if is_active else ''}"
                ).style("text-decoration:none"):
                    with ui.row().classes("items-center gap-3 px-3 py-2.5 w-full").style(
                        f"color: {'#93c5fd' if is_active else '#94a3b8'}"
                    ):
                        ui.icon(icon).classes("text-lg")
                        ui.label(label).classes("text-sm font-medium")


def page_layout(title: str, subtitle: str, active_path: str):
    sidebar(active_path)
    with ui.column().classes("fit-page w-full"):
        with ui.row().classes("fit-header w-full items-center px-8 py-5").style("gap:12px"):
            with ui.column().classes("gap-0.5 flex-1"):
                ui.label(title).classes("fit-text text-xl font-bold")
                ui.label(subtitle).classes("fit-subtext text-sm")
        return ui.column().classes("w-full p-8 gap-6")
