from nicegui import ui

MENU_ITEMS = [
    ("home",           "首頁",     "/ui"),
    ("description",    "履歷管理", "/ui/resume"),
    ("travel_explore", "職缺解析", "/ui/jobs"),
    ("radar",          "爬蟲職缺", "/ui/crawler-jobs"),
    ("analytics",      "匹配分析", "/ui/match"),
    ("send",           "投遞追蹤", "/ui/applications"),
]

THEME_CSS = """
:root {
    --bg-page:    #f7f6f3;
    --bg-card:    #ffffff;
    --bg-sidebar: #f7f6f3;
    --text-main:  #37352f;
    --text-sub:   #9b9a97;
    --text-muted: #c4c4c0;
    --border:     #e9e9e7;
    --accent:     #2383e2;
}
.body--dark {
    --bg-page:    #191919;
    --bg-card:    #252525;
    --bg-sidebar: #1f1f1f;
    --text-main:  #e9e9e7;
    --text-sub:   #787774;
    --text-muted: #4a4a47;
    --border:     #2f2f2f;
    --accent:     #529cca;
}

.fit-page    { background: var(--bg-page); min-height: 100vh; }
.fit-card    { background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; }
.fit-header  { background: var(--bg-card); border-bottom: 1px solid var(--border); }
.fit-text    { color: var(--text-main); }
.fit-subtext { color: var(--text-sub); }
.fit-muted   { color: var(--text-muted); }
.fit-divider { border-color: var(--border); }

.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    transition: background 0.1s;
}
.stat-card:hover { background: rgba(0,0,0,0.03); }
.body--dark .stat-card:hover { background: rgba(255,255,255,0.04); }

.sidebar-item {
    border-radius: 4px;
    transition: background 0.1s;
    text-decoration: none;
}
.sidebar-item:hover { background: rgba(0,0,0,0.06); }
.body--dark .sidebar-item:hover { background: rgba(255,255,255,0.06); }
.sidebar-active { background: rgba(0,0,0,0.08) !important; }
.body--dark .sidebar-active { background: rgba(255,255,255,0.08) !important; }
"""


def _inject_theme():
    ui.add_css(THEME_CSS)


def sidebar(active: str = ""):
    _inject_theme()

    with ui.left_drawer(fixed=True, value=True).style(
        "background: var(--bg-sidebar); border-right: 1px solid var(--border); padding: 20px 0 16px;"
    ):
        with ui.column().classes("px-3 gap-0.5 w-full"):
            with ui.row().classes("items-center px-2 mb-6"):
                ui.label("✦ FitCheck").classes("text-base font-bold fit-text")

            for icon, label, path in MENU_ITEMS:
                is_active = active == path
                with ui.element("a").props(f'href="{path}"').classes(
                    f"sidebar-item w-full {'sidebar-active' if is_active else ''}"
                ).style("text-decoration:none"):
                    with ui.row().classes("items-center gap-2.5 px-2 py-1.5 w-full"):
                        ui.icon(icon).classes("text-base").style(
                            f"color: {'var(--text-main)' if is_active else 'var(--text-sub)'}"
                        )
                        ui.label(label).classes("text-sm font-medium").style(
                            f"color: {'var(--text-main)' if is_active else 'var(--text-sub)'}"
                        )


def page_layout(title: str, subtitle: str, active_path: str):
    sidebar(active_path)
    with ui.column().classes("fit-page w-full"):
        content = ui.column().classes("w-full px-10 py-8 gap-6")
        with content:
            with ui.column().classes("gap-0.5 mb-2"):
                ui.label(title).classes("fit-text text-2xl font-bold")
                if subtitle:
                    ui.label(subtitle).classes("fit-subtext text-sm")
        return content
