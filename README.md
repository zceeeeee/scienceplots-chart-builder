# scienceplots-chart-builder

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

## 环境要求

使用源码运行时，需要提前安装：

* Windows 10 / Windows 11
* Python 3.9 或更高版本
* pip

建议安装 Python 时勾选：

```text
Add Python to PATH
```

安装完成后，可以在终端中检查：

```powershell
python --version
pip --version
```

## 安装依赖

首次使用前，在项目根目录打开 PowerShell 或终端，运行：

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt
```

如果下载速度较慢，可以使用国内镜像源，例如：

```powershell
python -m pip install -r .\plotting_web_app\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 启动 Web 应用

### 方法一：双击启动

Windows 用户可以直接双击：

```text
start_plotting_app.bat
```

程序会启动本地 Web 服务，并自动打开浏览器。

如果浏览器没有自动打开，请手动访问：

```text
http://127.0.0.1:8050
```

### 方法二：命令行启动

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

## 示例数据

仓库包含 `示例数据` 文件夹：

* `示例数据/光谱数据`：纯光谱数据，适合绘制原始光谱、归一化光谱、峰值对比。
* `示例数据/器件性能_EL数据`：器件性能和 EL 光谱综合数据，适合绘制 J-V、L-V、CE-V、EQE-L、EL 光谱和 CIE 坐标。

使用时可以在 Web 界面中选择对应的示例数据文件夹，扫描 `.txt` 数据并生成图表。

## 输出文件

导出的图表和汇总表默认保存到：

```text
web_app_outputs/
```

该文件夹属于运行输出，通常不建议提交到 GitHub。

建议在 `.gitignore` 中忽略：

```gitignore
web_app_outputs/
plotting_web_app/web_app_outputs/
```

## 推荐的 `.gitignore`

```gitignore
# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual environments
.venv/
venv/
env/

# Build outputs
build/
dist/
*.spec

# App outputs
web_app_outputs/
plotting_web_app/web_app_outputs/

# Packaged files
SciencePlotsChartBuilder.zip
26IAB5.zip

# IDE
.vscode/

# OS files
.DS_Store
Thumbs.db
```

## 打包版说明

如果需要生成 Windows exe，可使用 PyInstaller。打包产物建议不要提交到主分支，而是放到 GitHub Releases。

打包命令示例：

```powershell
python -m PyInstaller --noconfirm --clean --onedir --name SciencePlotsChartBuilder --paths .\plotting_web_app --hidden-import scienceplots --collect-data scienceplots --collect-data dash --collect-data plotly .\plotting_web_app\run_app.py
```

打包完成后，可以将生成的压缩包上传到 GitHub Releases，供不想安装 Python 环境的用户下载使用。

## GitHub 上传建议

建议提交到主分支的内容：

```text
README.md
.gitignore
start_plotting_app.bat
plotting_web_app/
示例数据/
```

不建议提交到主分支的内容：

```text
build/
dist/
web_app_outputs/
SciencePlotsChartBuilder.zip
*.spec
__pycache__/
.vscode/
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
