# Project Context: Autofish

## 1. 项目概述
Autofish 是一个基于 Python 的自动化钓鱼工具，专为特定游戏场景设计。它利用计算机视觉（OpenCV）识别游戏状态，通过模拟鼠标和键盘输入（PyInput/ctypes）自动执行钓鱼操作，并使用 OCR 技术记录渔获信息。项目采用 PySide6 和 QFluentWidgets 构建了现代化的图形用户界面。

## 2. 架构概览

项目遵循模块化设计，主要分为以下几个部分：

*   **GUI 层 (`src/gui/`)**: 负责用户交互、状态显示和参数配置。
*   **业务逻辑层 (`src/workers.py`)**: 包含核心的自动化工作流线程。
*   **基础设施层**:
    *   `src/vision.py`: 图像处理与识别。
    *   `src/inputs.py`: 输入模拟与监听。
    *   `src/config.py`: 配置管理与持久化。
*   **资源与配置**:
    *   `resources/`: 存放用于模板匹配的图片资源。
    *   `config/`: 存放用户配置文件 `config.json`。
    *   `data/`: 存放渔获记录 `records.csv`。

## 3. 模块详解

### 3.1 核心配置 (`src/config.py`)
*   **类**: `Config` (单例模式)
*   **职责**:
    *   加载和保存 `config/config.json`。
    *   管理多套钓鱼“预设” (Presets)，每套预设包含抛竿时间、收杆力度等参数。
    *   处理屏幕分辨率适配：根据当前屏幕分辨率自动缩放识别区域和点击坐标。
    *   提供全局设置（如快捷键、主题模式）。
*   **关键数据**: `REGIONS` 定义了屏幕上的关键识别区域（如鱼饵数量区、渔获信息区）。

### 3.2 视觉识别 (`src/vision.py`)
*   **类**: `Vision`
*   **职责**:
    *   **截图**: 使用 `mss` 进行高效屏幕截图。
    *   **模板匹配**: 加载 `resources/` 下的 PNG 图片，使用 OpenCV (`matchTemplate`) 在屏幕上查找特定图标（如抛竿提示、星星、加时文字）。
    *   **数字识别**: 针对鱼饵数量，使用模板匹配法识别数字（0-9）。
    *   **OCR**: 集成 `RapidOCR` 用于识别复杂的渔获文本信息（在 `FishingWorker` 中调用）。

### 3.3 输入控制 (`src/inputs.py`)
*   **类**: `InputController`
*   **职责**:
    *   **模拟输入**: 使用 `ctypes` 模拟鼠标点击、长按和键盘按键。包含 `add_jitter` 方法为操作增加随机抖动，模拟人类行为以降低被检测风险。
    *   **监听**: 使用 `pynput` 监听全局快捷键（默认 F2），用于启动/暂停脚本。

### 3.4 核心工作流 (`src/workers.py`)
该模块包含两个主要的 `QThread` 子类：

#### A. `FishingWorker` (主流程)
负责完整的钓鱼循环：
1.  **预检**: 检查屏幕是否存在抛竿提示或鱼饵数量，确认游戏环境。
2.  **抛竿 (`_cast_rod`)**: 识别 `F1`/`F2` 图标 -> 模拟长按鼠标抛竿。
3.  **等待咬钩 (`_wait_for_bite`)**: 持续监控鱼饵数量区域，检测到数字减少即视为咬钩。
4.  **收杆 (`_reel_in`)**: 执行“长按收线 -> 松开回气”的循环。持续检测屏幕是否出现“星星”图标，出现则停止收线。
5.  **记录 (`_record_catch`)**:
    *   截图渔获信息区域。
    *   调用 OCR 识别文字，解析鱼名、重量和品质。
    *   写入 `data/records.csv`。
    *   如果是“传说”品质，自动截图保存至 `screenshots/`。

#### B. `JiashiWorker` (加时检测)
独立线程，并行运行：
*   循环检测屏幕上是否出现“加时”相关的弹窗。
*   根据配置 (`enable_jiashi`) 自动点击“是”或“否”。

### 3.5 GUI 界面 (`src/gui/`)
*   **`MainWindow` (`main_window.py`)**: 应用程序主窗口，集成侧边导航栏，连接 Worker 信号与界面更新槽函数。
*   **`HomeInterface` (`home_interface.py`)**: 默认首页。
    *   **Dashboard**: 显示运行时间、本次捕获数、最近一条渔获。
    *   **控制**: 提供预设切换下拉框。
    *   **日志**: 实时显示 `FishingWorker` 发出的日志信息。

## 4. 核心逻辑流程图

```mermaid
graph TD
    A[启动脚本 (F2)] --> B{环境预检}
    B -- 失败 --> C[暂停并提示]
    B -- 成功 --> D[抛竿阶段]
    D --> E{检测抛竿提示}
    E -- 找到 --> F[长按鼠标抛竿]
    E -- 超时 --> D
    F --> G[等待咬钩]
    G --> H{监控鱼饵数量减少}
    H -- 减少 --> I[收杆阶段]
    H -- 超时 --> D
    I --> J[按住鼠标收线]
    J --> K[松开鼠标回气]
    K --> L{检测星星图标?}
    L -- 是 --> M[收杆完成]
    L -- 否 (循环) --> I
    M --> N[记录渔获 (OCR)]
    N --> O[保存 CSV/截图]
    O --> P[点击确认/关闭]
    P --> Q[等待循环间隔]
    Q --> D
```

## 5. 当前状态与注意事项

*   **功能状态**: 基础功能的代码逻辑已实现，包括视觉识别、自动操作和数据记录。
*   **配置**: 配置文件位于 `config/config.json`，支持自定义不同鱼竿的参数。
*   **依赖**: 强依赖于游戏窗口的分辨率和 UI 布局。虽然有缩放逻辑，但核心识别区域（Regions）可能需要根据实际游戏更新进行微调。
*   **调试**:
    *   主要通过 GUI 的日志窗口观察运行状态。
    *   `screenshots/` 目录下可能会生成调试截图（如果代码中开启了调试保存）。
*   **后续重点**:
    *   针对实际游戏画面的识别率优化（阈值调整、区域校准）。
    *   异常处理的增强（如网络波动、弹窗干扰）。

## 6. 视觉识别与区域详情 (Visual Recognition and Regions Detail)

### 6.1 坐标系统
*   **基准分辨率**: 2560 x 1440
*   **缩放逻辑**: `src/config.py` 启动时获取当前屏幕分辨率，计算 `scale_x` 和 `scale_y`。
*   **区域锚定**:
    *   **Top-Left (默认)**: 大多数区域使用标准缩放 `(x*scale_x, y*scale_y, w*scale_x, h*scale_y)`。
    *   **Bottom-Right**: `bait_count_area` (鱼饵数量) 采用右下角锚定，以适配不同宽高比的屏幕。

### 6.2 识别区域映射表 (Recognition Region Mapping Table)

| 功能 (Function) | 区域变量名 (Region Name) | 基准坐标 (Base Coords) / 范围 | 识别逻辑 (Logic) | 模板/资源 (Templates) | 备注 (Notes) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **鱼饵数量** | `bait_count_area` | `(2318, 1296, 2348, 1318)` (x1, y1, x2, y2) | 数字模板匹配 (0-9) | `0-9_grayscale.png` | 锚定右下角；支持二次扩展扫描 |
| **抛竿提示** | 全屏 (Full Screen) | - | 模板匹配 | `F1_grayscale.png`<br>`F2_grayscale.png` | 查找 F1/F2 图标 |
| **收杆/完美** | 全屏 (Full Screen) | - | 模板匹配 | `star_grayscale.png` | 收线时检测星星 |
| **加时检测** | (硬编码) `JIASHI_REGION_BASE` | `(1244, 676, 27, 28)` (Center) | 模板匹配 | `chang_grayscale.png` | 检测“长”字 |
| **加时-是** | (硬编码) `BTN_YES_BASE` | `(1390, 778)` (Point) | 点击坐标 | - | - |
| **加时-否** | (硬编码) `BTN_NO_BASE` | `(1175, 778)` (Point) | 点击坐标 | - | - |
| **渔获信息** | `catch_info_area` | `(960, 200, 640, 300)` (x, y, w, h) | OCR (RapidOCR) | - | 位于屏幕顶部中央 |

### 6.3 资源用途清单 (Resource Manifest)

位于 `resources/` 目录下的图片文件及其具体用途：

*   **数字 (0-9_grayscale.png, 0-9.png)**:
    *   **用途**: 在 `vision.get_bait_amount` 中使用，通过多重模板匹配识别当前鱼饵的剩余数量。
    *   **逻辑**: 提取 `bait_count_area` 截图 -> 灰度化 -> 逐个匹配 0-9 模板 -> 根据 x 坐标排序并组合成数字。
*   **抛竿提示 (F1/F2_grayscale.png, F1/F2.png)**:
    *   **用途**: 在抛竿阶段 (`_cast_rod`) 检测屏幕是否出现提示，确认可以抛竿。
*   **收杆提示 (star_grayscale.png, star.png)**:
    *   **用途**: 在收线阶段 (`_reel_in`) 持续检测。当“星星”出现时，意味着已经拉到合适位置（或触发完美），此时应停止收线。
*   **加时 (chang_grayscale.png, 长.png)**:
    *   **用途**: 检测是否弹出了“是否延长钓鱼时间”的对话框（识别“长”字）。
*   **其他 (shangyu.png, F.png)**:
    *   **用途**: `shangyu.png` 可能用于上鱼提示（但在代码中主要使用数字变化判断）；`F.png` 用于辅助判断（如收杆 F 键提示）。

### 6.4 已知代码差异与待修复项 (Known Issues)

在代码分析中发现了以下不一致之处，需要优先修复：

1.  **区域名称不匹配**:
    *   `src/config.py` 定义了 `"catch_info_area"`.
    *   `src/workers.py` (`FishingWorker`) 调用 `cfg.get_rect("region_fish_info")`.
    *   **风险**: `FishingWorker` 会因为找不到区域而报错。
2.  **方法缺失**:
    *   `src/workers.py` (`JiashiWorker`) 调用了 `cfg.get_center_anchored_rect(...)`.
    *   `src/config.py` 中尚未实现 `get_center_anchored_rect` 方法。
    *   **风险**: 加时检测线程会崩溃。
