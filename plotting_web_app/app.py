from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, State, callback_context, dash_table, dcc, html, no_update

from chart_core import (
    DEFAULT_SPECTRA_DIR,
    DEVICE_CHARTS,
    LINE_STYLES,
    MARKERS,
    SPECTRA_CHARTS,
    default_folder,
    detect_data_type,
    export_science_figure,
    make_plotly_figure,
    scan_txt_files,
    update_positions_from_relayout,
)


COLOR_PALETTE = ["#b91c1c", "#ef4444", "#f97316", "#16a34a", "#2563eb", "#7c3aed", "#111827"]


def chart_options(data_type: str) -> list[dict[str, str]]:
    source = SPECTRA_CHARTS if data_type == "spectra" else DEVICE_CHARTS
    return [{"label": label, "value": value} for value, label in source.items()]


def default_chart(data_type: str) -> str:
    return "normalized_spectra" if data_type == "spectra" else "el_spectra"


def default_title(data_type: str, chart_type: str) -> str:
    labels = SPECTRA_CHARTS if data_type == "spectra" else DEVICE_CHARTS
    return labels.get(chart_type, "Chart")


def make_row(file_path: str, index: int, data_type: str) -> dict:
    path = Path(file_path)
    sample = path.stem
    detected = detect_data_type(path)
    return {
        "sample": sample,
        "legend": sample,
        "color": COLOR_PALETTE[index % len(COLOR_PALETTE)],
        "line_style": "solid",
        "marker": MARKERS[index % len(MARKERS)],
        "file": path.name,
        "path": str(path),
        "detected": detected,
        "status": "OK" if detected in (data_type, "unknown") else f"可能是 {detected}",
    }


def open_folder_dialog(initial_dir: str | None = None) -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        selected = filedialog.askdirectory(
            title="选择数据文件夹",
            initialdir=initial_dir if initial_dir and Path(initial_dir).exists() else str(Path.home()),
            mustexist=True,
        )
    finally:
        root.destroy()
    return selected or None


app = Dash(__name__)
app.title = "SciencePlots Chart Builder"

TABLE_COLUMNS = [
    {"name": "样品名", "id": "sample", "editable": True},
    {"name": "图例文字", "id": "legend", "editable": True},
    {"name": "颜色", "id": "color", "editable": True},
    {"name": "线型", "id": "line_style", "presentation": "dropdown", "editable": True},
    {"name": "Marker", "id": "marker", "presentation": "dropdown", "editable": True},
    {"name": "文件", "id": "file"},
    {"name": "完整路径", "id": "path"},
    {"name": "识别", "id": "detected"},
    {"name": "状态", "id": "status"},
]

TABLE_DROPDOWNS = {
    "line_style": {"options": [{"label": key, "value": key} for key in LINE_STYLES.keys()]},
    "marker": {"options": [{"label": key, "value": key} for key in MARKERS]},
}

DEFAULT_EXPORT_FORMATS = ["png", "svg", "pdf", "csv"]

app.layout = html.Div(
    [
        dcc.Store(id="annotation-store", data={}),
        html.Div(
            [
                html.H1("SciencePlots Chart Builder"),
                html.P("本地科研制图工具：选择文件、编辑图例和线条属性、拖动标注位置，然后导出 SciencePlots 学术图。"),
            ],
            className="header",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("数据类型"),
                                dcc.RadioItems(
                                    id="data-type",
                                    options=[
                                        {"label": "光谱数据", "value": "spectra"},
                                        {"label": "器件性能 + EL 数据", "value": "device"},
                                    ],
                                    value="spectra",
                                ),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("数据文件夹"),
                                dcc.Input(id="folder-input", value=str(DEFAULT_SPECTRA_DIR), type="text", debounce=True),
                                html.Div(
                                    [
                                        html.Button("选择文件夹", id="choose-folder", n_clicks=0),
                                        html.Button("扫描文件夹", id="scan-button", n_clicks=0, className="secondary-button"),
                                    ],
                                    className="button-row",
                                ),
                                html.Div(id="scan-status", className="status"),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("可添加文件"),
                                dcc.Dropdown(id="available-files", multi=True, placeholder="选择一个或多个 .txt 文件"),
                                html.Div(
                                    [
                                        html.Button("添加到列表", id="add-files", n_clicks=0),
                                        html.Button("清空文件列表", id="clear-files", n_clicks=0, className="secondary-button"),
                                    ],
                                    className="button-row",
                                ),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("图表类型"),
                                dcc.Dropdown(id="chart-type", options=chart_options("spectra"), value=default_chart("spectra"), clearable=False),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("图表标题"),
                                dcc.Input(id="chart-title", value=default_title("spectra", default_chart("spectra")), type="text", debounce=False),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("标注"),
                                dcc.Checklist(
                                    id="annotation-modes",
                                    options=[
                                        {"label": "最高点", "value": "max"},
                                        {"label": "最低点", "value": "min"},
                                    ],
                                    value=["max"],
                                ),
                                html.Div("提示：预览图中的标注可以直接拖动；导出会尽量使用拖动后的偏移。", className="hint"),
                            ],
                            className="control-block",
                        ),
                        html.Div(
                            [
                                html.Label("导出文件名"),
                                dcc.Input(id="export-filename", value="chart", type="text", debounce=False),
                                html.Label("导出类型", className="inline-label"),
                                dcc.Checklist(
                                    id="export-formats",
                                    options=[
                                        {"label": "PNG", "value": "png"},
                                        {"label": "SVG", "value": "svg"},
                                        {"label": "PDF", "value": "pdf"},
                                        {"label": "CSV", "value": "csv"},
                                    ],
                                    value=DEFAULT_EXPORT_FORMATS,
                                    inline=True,
                                ),
                                html.Button("导出当前图表", id="export-button", n_clicks=0),
                                html.Div(id="export-status", className="status pre-wrap"),
                            ],
                            className="control-block",
                        ),
                    ],
                    className="sidebar",
                ),
                html.Div(
                    [
                        html.H2("样品文件列表"),
                        dash_table.DataTable(
                            id="sample-table",
                            columns=TABLE_COLUMNS,
                            data=[],
                            editable=True,
                            row_deletable=True,
                            dropdown=TABLE_DROPDOWNS,
                            style_table={"overflowX": "auto", "maxHeight": "310px", "overflowY": "auto"},
                            style_cell={
                                "fontFamily": "Arial",
                                "fontSize": 13,
                                "padding": "7px",
                                "minWidth": 90,
                                "maxWidth": 360,
                                "whiteSpace": "normal",
                                "textAlign": "left",
                            },
                            style_cell_conditional=[
                                {"if": {"column_id": "path"}, "minWidth": "420px", "maxWidth": "680px"},
                                {"if": {"column_id": "color"}, "width": "95px", "fontFamily": "Consolas"},
                                {"if": {"column_id": "line_style"}, "width": "90px"},
                                {"if": {"column_id": "marker"}, "width": "120px"},
                            ],
                            style_header={"fontWeight": "700", "backgroundColor": "#f3f4f6"},
                        ),
                        html.H2("交互预览"),
                        dcc.Graph(
                            id="preview-graph",
                            figure=make_plotly_figure([], "spectra", "normalized_spectra", ["max"], {}, default_title("spectra", "normalized_spectra")),
                            config={
                                "displaylogo": False,
                                "scrollZoom": True,
                                "editable": True,
                                "edits": {"annotationPosition": True, "legendPosition": True},
                            },
                            style={"height": "650px"},
                        ),
                    ],
                    className="main",
                ),
            ],
            className="app-grid",
        ),
    ]
)


app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body { margin: 0; font-family: Arial, Helvetica, sans-serif; background: #f6f7f9; color: #1f2937; }
            .header { padding: 22px 28px 10px; background: #ffffff; border-bottom: 1px solid #e5e7eb; }
            h1 { margin: 0 0 6px; font-size: 26px; letter-spacing: 0; }
            h2 { margin: 18px 0 10px; font-size: 17px; letter-spacing: 0; }
            p { margin: 0; color: #5b6472; }
            .app-grid { display: grid; grid-template-columns: 340px minmax(0, 1fr); gap: 18px; padding: 18px 22px 28px; }
            .sidebar, .main { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; }
            .control-block { margin-bottom: 18px; }
            label { display: block; font-size: 13px; font-weight: 700; margin-bottom: 7px; color: #374151; }
            .inline-label { margin-top: 12px; }
            input[type="text"] { width: 100%; box-sizing: border-box; padding: 8px 9px; border: 1px solid #d1d5db; border-radius: 6px; }
            button { border: 1px solid #111827; background: #111827; color: white; border-radius: 6px; padding: 8px 11px; margin-top: 8px; cursor: pointer; }
            button:hover { background: #374151; }
            .secondary-button { margin-left: 8px; background: #ffffff; color: #111827; }
            .secondary-button:hover { background: #f3f4f6; }
            .button-row { display: flex; flex-wrap: wrap; gap: 0; align-items: center; }
            .status { margin-top: 8px; color: #4b5563; font-size: 12px; line-height: 1.45; }
            .hint { margin-top: 8px; color: #6b7280; font-size: 12px; line-height: 1.45; }
            .pre-wrap { white-space: pre-wrap; }
            @media (max-width: 980px) { .app-grid { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


@app.callback(
    Output("folder-input", "value"),
    Output("chart-type", "options"),
    Output("chart-type", "value"),
    Output("chart-title", "value"),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("data-type", "value"),
    prevent_initial_call=True,
)
def switch_data_type(data_type):
    chart_type = default_chart(data_type)
    return default_folder(data_type), chart_options(data_type), chart_type, default_title(data_type, chart_type), {}


@app.callback(
    Output("chart-title", "value", allow_duplicate=True),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("chart-type", "value"),
    State("data-type", "value"),
    prevent_initial_call=True,
)
def reset_title_on_chart_change(chart_type, data_type):
    return default_title(data_type, chart_type), {}


@app.callback(
    Output("folder-input", "value", allow_duplicate=True),
    Output("scan-status", "children", allow_duplicate=True),
    Input("choose-folder", "n_clicks"),
    State("folder-input", "value"),
    prevent_initial_call=True,
)
def choose_folder(_n_clicks, current_folder):
    selected = open_folder_dialog(current_folder)
    if not selected:
        return no_update, "未选择新文件夹；仍可手动输入路径。"
    return selected, f"已选择文件夹：{selected}"


@app.callback(
    Output("available-files", "options"),
    Output("scan-status", "children"),
    Input("scan-button", "n_clicks"),
    Input("folder-input", "value"),
)
def scan_folder(_n_clicks, folder):
    options = scan_txt_files(folder or "")
    if not options:
        return [], "没有找到 .txt 文件，或文件夹不存在。"
    return options, f"找到 {len(options)} 个 .txt 文件。"


@app.callback(
    Output("sample-table", "data"),
    Output("available-files", "value"),
    Output("annotation-store", "data", allow_duplicate=True),
    Input("add-files", "n_clicks"),
    Input("clear-files", "n_clicks"),
    State("available-files", "value"),
    State("sample-table", "data"),
    State("data-type", "value"),
    prevent_initial_call=True,
)
def edit_file_list(_add_clicks, _clear_clicks, selected_files, rows, data_type):
    trigger = callback_context.triggered[0]["prop_id"].split(".")[0] if callback_context.triggered else ""
    if trigger == "clear-files":
        return [], [], {}
    if not selected_files:
        return no_update, no_update, no_update
    rows = rows or []
    existing = {row.get("path") for row in rows}
    next_rows = list(rows)
    for file_path in selected_files:
        if file_path in existing:
            continue
        next_rows.append(make_row(file_path, len(next_rows), data_type))
    return next_rows, [], {}


@app.callback(
    Output("annotation-store", "data", allow_duplicate=True),
    Input("preview-graph", "relayoutData"),
    State("annotation-store", "data"),
    State("preview-graph", "figure"),
    prevent_initial_call=True,
)
def remember_annotation_positions(relayout_data, current, figure):
    return update_positions_from_relayout(current, relayout_data, figure)


@app.callback(
    Output("preview-graph", "figure"),
    Input("sample-table", "data"),
    Input("data-type", "value"),
    Input("chart-type", "value"),
    Input("chart-title", "value"),
    Input("annotation-modes", "value"),
    Input("annotation-store", "data"),
)
def update_preview(rows, data_type, chart_type, chart_title, annotation_modes, annotation_store):
    return make_plotly_figure(rows or [], data_type, chart_type, annotation_modes or [], annotation_store or {}, chart_title)


@app.callback(
    Output("export-status", "children"),
    Input("export-button", "n_clicks"),
    State("sample-table", "data"),
    State("data-type", "value"),
    State("chart-type", "value"),
    State("chart-title", "value"),
    State("export-filename", "value"),
    State("export-formats", "value"),
    State("annotation-modes", "value"),
    State("annotation-store", "data"),
    prevent_initial_call=True,
)
def export_current_chart(_n_clicks, rows, data_type, chart_type, chart_title, export_filename, export_formats, annotation_modes, annotation_store):
    if not rows:
        return "请先添加至少一个文件。"
    if not export_formats:
        return "请至少选择一种导出类型。"
    try:
        paths = export_science_figure(
            rows,
            data_type,
            chart_type,
            annotation_modes or [],
            annotation_store or {},
            custom_title=chart_title,
            file_stem=export_filename,
            export_formats=export_formats,
        )
    except Exception as exc:  # noqa: BLE001 - shown to local user
        return f"导出失败：{exc}"
    rendered = [str(path) for path in paths]
    return "已导出：\n" + "\n".join(rendered)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
