# Plotting Web App

一个面向实验数据的本地 Web 科研制图工具。应用使用 Dash + Plotly 提供交互式预览，使用 Matplotlib + SciencePlots 导出适合论文和 PPT 的静态图表。

## 功能概览

- 支持两类数据：
  - 光谱数据：SpectraSuite 导出的波长-强度 `.txt` 文件。
  - 器件性能 + EL 数据：包含电压、电流密度、亮度、效率、CIE 和 EL 光谱的 `.txt` 文件。
- 支持选择文件夹、扫描 `.txt` 数据、添加/删除/清空文件列表。
- 可编辑样品名、图例文字、线条颜色、线型、marker 和图表标题。
- 可标注最高点/最低点，标注可在预览图中拖动。
- 可导出 `PNG / SVG / PDF / CSV`。

## 项目结构

```text
plotting_web_app/
  app.py              # Dash Web 界面
  chart_core.py       # 数据解析、预览图生成、SciencePlots 导出
  run_app.py          # 推荐启动入口，会自动打开浏览器
  requirements.txt    # Python 依赖
  README.md           # 应用说明

示例数据/
  光谱数据/             # SpectraSuite 光谱 txt 示例
  器件性能_EL数据/      # 器件性能 + EL txt 示例

start_plotting_app.ps1 # Windows 启动脚本
```

## 安装依赖

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt
```

## 启动 Web 应用

推荐方式：

```powershell
python .\plotting_web_app\run_app.py
```

或在 Windows PowerShell 中运行：

```powershell
.\start_plotting_app.ps1
```

启动后会自动打开浏览器。如果没有自动打开，请访问终端中显示的地址，通常是：

```text
http://127.0.0.1:8050
```

## 示例数据

仓库包含 `示例数据` 文件夹：

- `示例数据/光谱数据`：纯光谱数据，适合绘制原始光谱、归一化光谱、峰值对比。
- `示例数据/器件性能_EL数据`：器件性能和 EL 光谱综合数据，适合绘制 J-V、L-V、CE-V、EQE-L、EL 光谱和 CIE 坐标。

## 打包版说明

如果需要生成 Windows exe，可使用 PyInstaller。打包产物建议不要提交到主分支，而是放到 GitHub Releases。

```powershell
python -m PyInstaller --noconfirm --clean --onedir --name SciencePlotsChartBuilder --paths .\plotting_web_app --hidden-import scienceplots --collect-data scienceplots --collect-data dash --collect-data plotly .\plotting_web_app\run_app.py
```

## 输出

导出的图表和汇总表默认保存到：

```text
web_app_outputs/
```
