from __future__ import annotations

import csv
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import scienceplots  # noqa: F401 - registers SciencePlots styles


def find_root() -> Path:
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parents[1]
    exe_dir = Path(sys.executable).resolve().parent
    candidates = [exe_dir, exe_dir.parent, exe_dir.parent.parent, Path.cwd()]
    for candidate in candidates:
        if (candidate / "示例数据").exists() or (candidate / "26lAB5").exists():
            return candidate
    return exe_dir


if getattr(sys, "frozen", False):
    ROOT = find_root()
else:
    ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPECTRA_DIR = ROOT / "示例数据" / "光谱数据"
DEFAULT_DEVICE_DIR = ROOT / "示例数据" / "器件性能_EL数据"
OUTPUT_DIR = ROOT / "web_app_outputs"

SPECTRA_CHARTS = {
    "raw_spectra": "原始光谱",
    "normalized_spectra": "归一化光谱",
    "peak_summary": "峰值柱状图",
}

DEVICE_CHARTS = {
    "jv": "J-V",
    "lv": "L-V",
    "ce_v": "电流效率-电压",
    "eqe_l": "EQE-L",
    "el_spectra": "EL 光谱",
    "cie": "CIE 坐标",
    "eff_summary": "效率汇总柱状图",
}

LINE_STYLES = {
    "solid": {"plotly": "solid", "mpl": "-"},
    "dash": {"plotly": "dash", "mpl": "--"},
    "dot": {"plotly": "dot", "mpl": ":"},
    "dashdot": {"plotly": "dashdot", "mpl": "-."},
}

MARKERS = ["circle", "square", "diamond", "triangle-up", "triangle-down", "x"]
MPL_MARKERS = {
    "circle": "o",
    "square": "s",
    "diamond": "D",
    "triangle-up": "^",
    "triangle-down": "v",
    "x": "x",
}


@dataclass
class Series:
    file: str
    sample: str
    legend: str
    color: str
    line_style: str
    marker: str
    data: dict[str, Any]


def default_folder(data_type: str) -> str:
    return str(DEFAULT_SPECTRA_DIR if data_type == "spectra" else DEFAULT_DEVICE_DIR)


def scan_txt_files(folder: str) -> list[dict[str, str]]:
    path = Path(folder)
    if not path.exists() or not path.is_dir():
        return []
    return [{"label": item.name, "value": str(item)} for item in sorted(path.glob("*.txt"))]


def detect_data_type(path: Path) -> str:
    head = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    if "Begin Processed Spectral Data" in head or "SpectraSuite" in head:
        return "spectra"
    if "Voltage(V)" in head and "Wav (nm)" in head:
        return "device"
    return "unknown"


def read_spectra(path: Path) -> dict[str, list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    in_data = False
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if "Begin Processed Spectral Data" in line:
                in_data = True
                continue
            if not in_data:
                continue
            line = line.strip()
            if not line or line.startswith(">>>>>"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                xs.append(float(parts[0]))
                ys.append(float(parts[1]))
            except ValueError:
                continue
    return {"x": xs, "y": ys}


def parse_float(value: str) -> float:
    value = value.strip()
    if not value:
        return math.nan
    try:
        return float(value)
    except ValueError:
        return math.nan


def read_device(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {
        "voltage": [],
        "j": [],
        "abs_j": [],
        "luminance": [],
        "ce": [],
        "pe": [],
        "eqe": [],
        "wavelength": [],
        "intensity": [],
        "cie": (math.nan, math.nan),
    }
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        reader = csv.reader(handle, delimiter="\t")
        next(reader, None)
        for row in reader:
            if len(row) < 12:
                continue
            values = [parse_float(item) for item in row]
            v, j, l, ce, pe, eqe = values[0], values[3], values[4], values[5], values[6], values[7]
            if all(math.isfinite(x) for x in (v, j, l, ce, pe, eqe)):
                data["voltage"].append(v)
                data["j"].append(j)
                data["abs_j"].append(abs(j))
                data["luminance"].append(l)
                data["ce"].append(ce)
                data["pe"].append(pe)
                data["eqe"].append(eqe)
            if math.isnan(data["cie"][0]) and math.isfinite(values[8]) and math.isfinite(values[9]):
                data["cie"] = (values[8], values[9])
            if math.isfinite(values[10]) and math.isfinite(values[11]):
                data["wavelength"].append(values[10])
                data["intensity"].append(values[11])
    return data


def load_series(rows: list[dict[str, Any]], data_type: str) -> list[Series]:
    series: list[Series] = []
    for row in rows:
        if not row.get("include", True):
            continue
        file_path = Path(row.get("path") or row.get("file") or "")
        if not file_path.exists():
            continue
        try:
            data = read_spectra(file_path) if data_type == "spectra" else read_device(file_path)
        except OSError:
            continue
        legend = row.get("legend") or row.get("sample") or file_path.stem
        series.append(
            Series(
                file=str(file_path),
                sample=row.get("sample") or file_path.stem,
                legend=legend,
                color=row.get("color") or "#1f77b4",
                line_style=row.get("line_style") or "solid",
                marker=row.get("marker") or "circle",
                data=data,
            )
        )
    return series


def finite_pairs(xs: list[float], ys: list[float], predicate=None) -> tuple[list[float], list[float]]:
    out_x: list[float] = []
    out_y: list[float] = []
    for x, y in zip(xs, ys):
        if not (math.isfinite(x) and math.isfinite(y)):
            continue
        if predicate and not predicate(x, y):
            continue
        out_x.append(x)
        out_y.append(y)
    return out_x, out_y


def point_key(series: Series, kind: str) -> str:
    return f"{series.file}|{kind}"


def max_point(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    pairs = [(x, y) for x, y in zip(xs, ys) if math.isfinite(x) and math.isfinite(y)]
    if not pairs:
        return None
    return max(pairs, key=lambda item: item[1])


def min_point(xs: list[float], ys: list[float]) -> tuple[float, float] | None:
    pairs = [(x, y) for x, y in zip(xs, ys) if math.isfinite(x) and math.isfinite(y)]
    if not pairs:
        return None
    return min(pairs, key=lambda item: item[1])


def normalize_ys(xs: list[float], ys: list[float], x_min=380, x_max=780) -> list[float]:
    visible = [y for x, y in zip(xs, ys) if x_min <= x <= x_max and math.isfinite(y)]
    denom = max(visible) if visible else 1.0
    if denom == 0:
        denom = 1.0
    return [y / denom for y in ys]


def operating_indices(d: dict[str, list[float]]) -> list[int]:
    result = []
    for i in range(len(d["voltage"])):
        if d["voltage"][i] >= 0 and d["j"][i] > 0 and d["luminance"][i] >= 1 and d["ce"][i] > 0 and d["eqe"][i] > 0:
            result.append(i)
    return result


def selected_xy(series: Series, data_type: str, chart_type: str) -> tuple[list[float], list[float], str, str, str]:
    d = series.data
    if data_type == "spectra":
        if chart_type == "normalized_spectra":
            xs, ys = finite_pairs(d["x"], normalize_ys(d["x"], d["y"]), lambda x, y: 380 <= x <= 780)
            return xs, ys, "Wavelength (nm)", "Normalized intensity", "Normalized spectra"
        xs, ys = finite_pairs(d["x"], d["y"], lambda x, y: 380 <= x <= 780)
        return xs, ys, "Wavelength (nm)", "Intensity (a.u.)", "Raw spectra"
    if chart_type == "jv":
        xs, ys = finite_pairs(d["voltage"], d["abs_j"], lambda x, y: y > 0)
        return xs, ys, "Voltage (V)", "|J| (mA cm^-2)", "Current density-voltage"
    if chart_type == "lv":
        xs, ys = finite_pairs(d["voltage"], d["luminance"], lambda x, y: x >= 0 and y > 0)
        return xs, ys, "Voltage (V)", "Luminance (cd m^-2)", "Luminance-voltage"
    if chart_type == "ce_v":
        indices = operating_indices(d)
        return [d["voltage"][i] for i in indices], [d["ce"][i] for i in indices], "Voltage (V)", "Current efficiency (cd A^-1)", "Current efficiency-voltage"
    if chart_type == "eqe_l":
        indices = operating_indices(d)
        return [d["luminance"][i] for i in indices], [d["eqe"][i] for i in indices], "Luminance (cd m^-2)", "EQE (%)", "EQE-luminance"
    if chart_type == "el_spectra":
        ys_norm = normalize_ys(d["wavelength"], d["intensity"])
        xs, ys = finite_pairs(d["wavelength"], ys_norm, lambda x, y: 380 <= x <= 780)
        return xs, ys, "Wavelength (nm)", "Normalized EL intensity", "Normalized EL spectra"
    if chart_type == "cie":
        x, y = d["cie"]
        return [x], [y], "CIE x", "CIE y", "CIE coordinates"
    return [], [], "", "", ""


def build_annotations(
    series_list: list[Series],
    data_type: str,
    chart_type: str,
    annotation_modes: list[str],
    annotation_positions: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    annotations = []
    for series in series_list:
        xs, ys, *_ = selected_xy(series, data_type, chart_type)
        if not xs:
            continue
        for mode in annotation_modes:
            point = max_point(xs, ys) if mode == "max" else min_point(xs, ys)
            if not point:
                continue
            key = point_key(series, mode)
            saved = annotation_positions.get(key, {})
            ax = saved.get("ax", 34 if mode == "max" else -34)
            ay = saved.get("ay", -38 if mode == "max" else 38)
            x, y = point
            label = f"{series.legend}: ({x:.3g}, {y:.3g})"
            annotations.append(
                {
                    "x": x,
                    "y": y,
                    "xref": "x",
                    "yref": "y",
                    "text": label,
                    "showarrow": True,
                    "arrowhead": 2,
                    "ax": ax,
                    "ay": ay,
                    "font": {"color": series.color, "size": 12},
                    "bordercolor": series.color,
                    "borderwidth": 1,
                    "bgcolor": "rgba(255,255,255,0.85)",
                    "name": key,
                }
            )
    return annotations


def make_plotly_figure(
    rows: list[dict[str, Any]],
    data_type: str,
    chart_type: str,
    annotation_modes: list[str] | None,
    annotation_positions: dict[str, dict[str, float]] | None,
    custom_title: str | None = None,
) -> go.Figure:
    annotation_modes = annotation_modes or []
    annotation_positions = annotation_positions or {}
    series_list = load_series(rows, data_type)
    fig = go.Figure()
    title = ""
    x_title = ""
    y_title = ""

    if chart_type in ("peak_summary", "eff_summary"):
        labels = []
        values = []
        colors = []
        for series in series_list:
            if chart_type == "peak_summary":
                xs, ys, *_ = selected_xy(series, data_type, "raw_spectra")
                point = max_point(xs, ys)
                if not point:
                    continue
                label = f"{series.legend}<br>{point[0]:.1f} nm"
                value = point[1]
                title = "Peak intensity comparison"
                y_title = "Peak intensity (a.u.)"
            else:
                xs, ys, *_ = selected_xy(series, data_type, "ce_v")
                point = max_point(xs, ys)
                if not point:
                    continue
                label = series.legend
                value = point[1]
                title = "Current efficiency maxima"
                y_title = "Current efficiency (cd A^-1)"
            labels.append(label)
            values.append(value)
            colors.append(series.color)
        fig.add_bar(x=labels, y=values, marker_color=colors, text=[f"{v:.3g}" for v in values], textposition="outside")
        fig.update_layout(title=custom_title or title, xaxis_title="", yaxis_title=y_title)
        fig.update_layout(uirevision=f"{data_type}:{chart_type}:{custom_title or title}:bar")
        return fig

    for series in series_list:
        xs, ys, x_title, y_title, title = selected_xy(series, data_type, chart_type)
        if not xs:
            continue
        mode = "lines+markers" if chart_type == "cie" else "lines"
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode=mode,
                name=series.legend,
                line={"color": series.color, "dash": LINE_STYLES.get(series.line_style, LINE_STYLES["solid"])["plotly"], "width": 2},
                marker={"symbol": series.marker, "size": 9, "color": series.color},
            )
        )

    annotations = build_annotations(series_list, data_type, chart_type, annotation_modes, annotation_positions)
    fig.update_layout(
        title=custom_title or title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        legend={"x": 1.02, "y": 1, "xanchor": "left", "yanchor": "top"},
        margin={"l": 70, "r": 180, "t": 60, "b": 65},
        annotations=annotations,
        dragmode="pan",
        uirevision=f"{data_type}:{chart_type}:{custom_title or title}",
    )
    if chart_type in ("jv", "lv"):
        fig.update_yaxes(type="log")
    if chart_type == "eqe_l":
        fig.update_xaxes(type="log")
    if chart_type in ("normalized_spectra", "el_spectra"):
        fig.update_yaxes(range=[0, 1.3])
    if chart_type in ("raw_spectra", "normalized_spectra", "el_spectra"):
        fig.update_xaxes(range=[380, 780])
    if chart_type == "cie":
        fig.update_xaxes(range=[0, 0.8])
        fig.update_yaxes(range=[0, 0.85], scaleanchor="x", scaleratio=1)
    return fig


def update_positions_from_relayout(
    current: dict[str, dict[str, float]] | None,
    relayout_data: dict[str, Any] | None,
    fig_json: dict[str, Any] | None,
) -> dict[str, dict[str, float]]:
    positions = dict(current or {})
    if not relayout_data or not fig_json:
        return positions
    annotations = fig_json.get("layout", {}).get("annotations", [])
    for key, value in relayout_data.items():
        if not key.startswith("annotations["):
            continue
        try:
            idx = int(key.split("[", 1)[1].split("]", 1)[0])
        except (ValueError, IndexError):
            continue
        if idx >= len(annotations):
            continue
        meta_key = annotations[idx].get("name")
        if not meta_key:
            continue
        positions.setdefault(meta_key, {})
        prop = key.split("].", 1)[-1]
        if prop in ("ax", "ay", "x", "y"):
            positions[meta_key][prop] = value
    return positions


def apply_science_style() -> None:
    plt.style.use(["science", "nature", "no-latex"])
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Microsoft YaHei", "SimHei", "DejaVu Sans"],
            "font.size": 7.8,
            "axes.labelsize": 8.4,
            "axes.titlesize": 9.0,
            "legend.fontsize": 7.2,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "savefig.dpi": 400,
            "axes.unicode_minus": False,
        }
    )


def mpl_annotate(ax, x: float, y: float, text: str, color: str, offset: dict[str, float] | None = None) -> None:
    offset = offset or {}
    xytext = (float(offset.get("ax", 34)) * 0.75, -float(offset.get("ay", -38)) * 0.75)
    ax.scatter([x], [y], s=15, color=color, edgecolor="white", linewidth=0.35, zorder=4)
    ax.annotate(
        text,
        xy=(x, y),
        xytext=xytext,
        textcoords="offset points",
        color=color,
        fontsize=6.6,
        arrowprops={"arrowstyle": "->", "color": color, "lw": 0.6},
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": color, "lw": 0.45, "alpha": 0.85},
    )


def export_science_figure(
    rows: list[dict[str, Any]],
    data_type: str,
    chart_type: str,
    annotation_modes: list[str] | None,
    annotation_positions: dict[str, dict[str, float]] | None,
    custom_title: str | None = None,
    file_stem: str | None = None,
    export_formats: list[str] | None = None,
) -> list[Path]:
    annotation_modes = annotation_modes or []
    annotation_positions = annotation_positions or {}
    series_list = load_series(rows, data_type)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    apply_science_style()
    stem = safe_file_stem(file_stem) if file_stem else f"{data_type}_{chart_type}"
    export_formats = export_formats or ["png", "svg", "pdf", "csv"]
    paths: list[Path] = []

    if chart_type in ("peak_summary", "eff_summary"):
        fig, ax = plt.subplots(figsize=(4.7, 3.25))
        labels, values, colors = [], [], []
        for series in series_list:
            if chart_type == "peak_summary":
                xs, ys, *_ = selected_xy(series, data_type, "raw_spectra")
                point = max_point(xs, ys)
                ylabel = "Peak intensity (a.u.)"
                title = "Peak intensity comparison"
            else:
                xs, ys, *_ = selected_xy(series, data_type, "ce_v")
                point = max_point(xs, ys)
                ylabel = "Current efficiency (cd A$^{-1}$)"
                title = "Current efficiency maxima"
            if not point:
                continue
            labels.append(series.legend)
            values.append(point[1])
            colors.append(series.color)
        bars = ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.35)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value * 1.02, f"{value:.3g}", ha="center", va="bottom", fontsize=6.8)
        ax.set_ylabel(ylabel)
        ax.set_title(custom_title or title, pad=7)
        ax.set_ylim(0, max(values) * 1.22 if values else 1)
    else:
        fig, ax = plt.subplots(figsize=(5.8, 3.65))
        title = ""
        for series in series_list:
            xs, ys, xlabel, ylabel, title = selected_xy(series, data_type, chart_type)
            if not xs:
                continue
            line_style = LINE_STYLES.get(series.line_style, LINE_STYLES["solid"])["mpl"]
            marker = MPL_MARKERS.get(series.marker, "o") if chart_type == "cie" else None
            if chart_type in ("jv", "lv"):
                ax.semilogy(xs, ys, line_style, color=series.color, lw=1.05, label=series.legend, marker=marker)
            elif chart_type == "eqe_l":
                ax.semilogx(xs, ys, line_style, color=series.color, lw=1.05, label=series.legend)
            else:
                ax.plot(xs, ys, line_style, color=series.color, lw=1.05, label=series.legend, marker=marker)
            for mode in annotation_modes:
                point = max_point(xs, ys) if mode == "max" else min_point(xs, ys)
                if not point:
                    continue
                key = point_key(series, mode)
                x, y = point
                label = f"{series.legend}: ({x:.3g}, {y:.3g})"
                mpl_annotate(ax, x, y, label, series.color, annotation_positions.get(key))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(custom_title or title, pad=7)
        if chart_type in ("normalized_spectra", "el_spectra"):
            ax.set_ylim(0, 1.32)
        if chart_type in ("raw_spectra", "normalized_spectra", "el_spectra"):
            ax.set_xlim(380, 780)
        if chart_type == "cie":
            ax.set_xlim(0, 0.8)
            ax.set_ylim(0, 0.85)
        ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5), borderaxespad=0.0)

    for ext in ("png", "svg", "pdf"):
        if ext in export_formats:
            out = OUTPUT_DIR / f"{stem}.{ext}"
            fig.savefig(out, bbox_inches="tight")
            paths.append(out)
    plt.close(fig)
    if "csv" in export_formats:
        summary_path = OUTPUT_DIR / f"{stem}_summary.csv"
        write_summary(rows, data_type, summary_path)
        paths.append(summary_path)
    return paths


def safe_file_stem(value: str | None) -> str:
    value = (value or "").strip()
    if not value:
        return "chart"
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", value)
    value = re.sub(r"\s+", "_", value)
    return value.strip("._ ") or "chart"


def write_summary(rows: list[dict[str, Any]], data_type: str, output_path: Path) -> None:
    series_list = load_series(rows, data_type)
    summaries = []
    for series in series_list:
        if data_type == "spectra":
            xs, ys, *_ = selected_xy(series, data_type, "raw_spectra")
            peak = max_point(xs, ys)
            valley = min_point(xs, ys)
            summaries.append(
                {
                    "legend": series.legend,
                    "file": series.file,
                    "peak_x": peak[0] if peak else "",
                    "peak_y": peak[1] if peak else "",
                    "min_x": valley[0] if valley else "",
                    "min_y": valley[1] if valley else "",
                }
            )
        else:
            d = series.data
            el_xs, el_ys, *_ = selected_xy(series, data_type, "el_spectra")
            peak = max_point(el_xs, el_ys)
            lv_xs, lv_ys, *_ = selected_xy(series, data_type, "lv")
            max_l = max_point(lv_xs, lv_ys)
            ce_xs, ce_ys, *_ = selected_xy(series, data_type, "ce_v")
            max_ce = max_point(ce_xs, ce_ys)
            eqe_xs, eqe_ys, *_ = selected_xy(series, data_type, "eqe_l")
            max_eqe = max_point(eqe_xs, eqe_ys)
            summaries.append(
                {
                    "legend": series.legend,
                    "file": series.file,
                    "el_peak_nm": peak[0] if peak else "",
                    "max_luminance": max_l[1] if max_l else "",
                    "max_ce": max_ce[1] if max_ce else "",
                    "max_eqe": max_eqe[1] if max_eqe else "",
                    "cie_x": d["cie"][0],
                    "cie_y": d["cie"][1],
                }
            )
    if not summaries:
        return
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
