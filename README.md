# scienceplots-chart-builder

一个面向实验数据的本地 Web 科研制图工具。应用使用 Dash + Plotly 提供交互式预览，使用 Matplotlib + SciencePlots 导出适合论文和 PPT 的静态图表。

本项目提供两种使用方式：

- **一键启动版**：适合普通用户，不需要配置 Python 环境，下载 zip 后解压运行。
- **源码版**：适合开发者或需要修改代码的用户，需要安装 Python 依赖后运行。

## 功能概览

- 支持两类数据：
  - 光谱数据：SpectraSuite 导出的波长-强度 `.txt` 文件。
  - 器件性能 + EL 数据：包含电压、电流密度、亮度、效率、CIE 和 EL 光谱的 `.txt` 文件。
- 支持选择文件夹、扫描 `.txt` 数据、添加/删除/清空文件列表。
- 可编辑样品名、图例文字、线条颜色、线型、marker 和图表标题。
- 可标注最高点/最低点，标注可在预览图中拖动。
- 可导出 `PNG / SVG / PDF / CSV`。

## 一键启动版下载

如果不想配置 Python 环境，推荐使用一键启动版。

### 使用方法

1. 打开本仓库的 **Releases** 页面。
2. 下载最新版本中的：

```text
SciencePlotsChartBuilder.zip
```

3. 解压压缩包。
4. 双击其中的启动程序。
5. 程序会启动本地 Web 服务，并自动打开浏览器。

如果浏览器没有自动打开，请手动访问：

```text
http://127.0.0.1:8050
```

### 注意事项

- 首次启动可能较慢，请等待几秒。
- 如果 Windows 出现安全提示，可以选择“更多信息”后继续运行。
- 这是本地 Web 应用，数据在本机处理。
- 导出的图表和汇总表会保存到程序指定的输出文件夹。

## 源码版使用方法

如果你想查看源码、修改程序或自行开发，可以下载源码版。

### 环境要求

使用源码运行时，需要提前安装：

- Windows 10 / Windows 11
- Python 3.9 或更高版本
- pip

### 安装依赖

首次使用前，在项目根目录打开 PowerShell 或终端，运行：

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt
```

### 启动 Web 应用

#### 方法一：双击启动

Windows 用户可以直接双击：

```text
start_plotting_app.bat
```

程序会启动本地 Web 服务，并自动打开浏览器。

如果浏览器没有自动打开，请手动访问：

```text
http://127.0.0.1:8050
```

#### 方法二：命令行启动

也可以在项目根目录运行：

```powershell
python .\plotting_web_app\run_app.py
```

或者：

```powershell
python .\plotting_web_app\app.py
```

启动成功后，终端通常会显示：

```text
Dash is running on http://127.0.0.1:8050/
```

然后在浏览器访问：

```text
http://127.0.0.1:8050
```

## 项目结构

```text
scienceplots-chart-builder/
  README.md
  .gitignore
  start_plotting_app.bat

  plotting_web_app/
    app.py              # Dash Web 界面
    chart_core.py       # 数据解析、预览图生成、SciencePlots 导出
    run_app.py          # 推荐启动入口，会自动打开浏览器
    requirements.txt    # Python 依赖
    README.md           # 应用说明

  示例数据/
    光谱数据/             # SpectraSuite 光谱 txt 示例
    器件性能_EL数据/      # 器件性能 + EL txt 示例
```

## 示例数据

仓库包含 `示例数据` 文件夹：

- `示例数据/光谱数据`：纯光谱数据，适合绘制原始光谱、归一化光谱、峰值对比。
- `示例数据/器件性能_EL数据`：器件性能和 EL 光谱综合数据，适合绘制 J-V、L-V、CE-V、EQE-L、EL 光谱和 CIE 坐标。

使用时可以在 Web 界面中选择对应的示例数据文件夹，扫描 `.txt` 数据并生成图表。

## 输出文件

导出的图表和汇总表默认保存到：

```text
web_app_outputs/
```
## 常见问题

### 1. 双击 `start_plotting_app.bat` 后窗口闪退

可能是依赖没有安装。请先在项目根目录运行：

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt
```

然后再双击启动脚本。

### 2. 提示 `python` 不是内部或外部命令

说明 Python 没有正确加入系统 PATH。

可以重新安装 Python，并勾选：

```text
Add Python to PATH
```

或者尝试使用：

```powershell
py .\plotting_web_app\run_app.py
```

### 3. 页面打不开

确认终端中是否出现类似信息：

```text
Dash is running on http://127.0.0.1:8050/
```

如果出现了，请在浏览器手动打开：

```text
http://127.0.0.1:8050
```

### 4. 端口被占用

如果 `8050` 端口被其他程序占用，请关闭之前启动的程序窗口，或者在终端中按：

```text
Ctrl + C
```

停止旧的 Dash 服务后重新启动。

### 5. 一键启动版和源码版有什么区别？

一键启动版适合直接使用，通常不需要安装 Python 和依赖。

源码版适合查看代码、修改程序或二次开发，需要先安装 Python 依赖。