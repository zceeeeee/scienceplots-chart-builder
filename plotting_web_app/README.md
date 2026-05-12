# SciencePlots Chart Builder

本地 Web 科研制图工具，用于处理两类 `.txt` 实验数据，并导出符合论文/PPT 使用习惯的 SciencePlots 图表。

## 支持的数据类型

- 光谱数据：SpectraSuite 导出的波长-强度数据。
- 器件性能 + EL 数据：包含 `Voltage(V)`, `J`, `L`, `Cur Eff`, `EQE`, `CIE`, `Wav`, `Intensity` 等列的器件测试数据。

## 运行方式

在项目根目录执行：

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt
python .\plotting_web_app\run_app.py
```

程序会自动打开浏览器。如果没有自动打开，请访问终端里显示的本地地址，通常是：

```text
http://127.0.0.1:8050
```

Windows 下也可以运行：

```powershell
.\start_plotting_app.ps1
```

## 主要功能

- 切换数据类型：光谱数据 / 器件性能 + EL 数据。
- 通过“选择文件夹”打开本机文件夹选择窗口，也可手动输入路径。
- 扫描文件夹中的 `.txt` 数据文件。
- 从文件列表添加数据，可在样品表中删除或一键清空。
- 编辑样品名、图例文字、线条颜色、线型和 marker。
- 编辑图表标题。
- 支持最高点和最低点标注。
- Plotly 预览图中的标注可拖动。
- 导出前可编辑文件名，并选择 `PNG / SVG / PDF / CSV` 中的一种或多种格式。

## 支持的图表

光谱数据：

- 原始光谱
- 归一化光谱
- 峰值柱状图

器件性能 + EL 数据：

- J-V
- L-V
- CE-V
- EQE-L
- EL 光谱
- CIE 坐标
- 效率汇总柱状图

## 输出目录

```text
web_app_outputs/
```

## 注意

- 网页预览使用 Plotly，最终导出使用 Matplotlib + SciencePlots，两者视觉效果会有轻微差异。
- 拖动标注后，程序会记录标注偏移，并尽量映射到 SciencePlots 导出图中。
- 第一版暂未加入重复样品均值/标准差、平滑、背景扣除和模板管理。
