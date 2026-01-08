# 🎣 Autofish - 猛兽派对自动钓鱼助手

[![Release](https://img.shields.io/github/v/release/R1ckyyyyy/Autofish?style=for-the-badge)](https://github.com/R1ckyyyyy/Autofish/releases/latest)
[![License](https://img.shields.io/github/license/R1ckyyyyy/Autofish?style=for-the-badge)](LICENSE)
[![Game](https://img.shields.io/badge/Game-猛兽派对%20Party%20Animals-blue?style=for-the-badge)](https://www.partyanimals.com/)

**🎮 专为《猛兽派对 (Party Animals)》钓鱼玩法设计的自动化辅助工具**

Autofish 是一款基于图像识别的自动钓鱼工具，拥有自动化操作、OCR 钓鱼记录、现代化 GUI 界面等特性，让你在猛兽派对中轻松享受钓鱼乐趣！

---

## ✨ 功能特性 (Features)

- **🤖 自动化操作**：自动抛竿、智能等待、循环收线，全程无需人工干预。
- **📖 OCR 钓鱼记录**：利用光学字符识别（OCR）技术，自动记录每条鱼的名称、重量、品质和垂钓时间。
- **📸 传奇鱼种自动截图**：当钓到“传说”品质的鱼时，程序会自动截图，并保存在 `screenshots` 文件夹中，方便您分享和记录。
- **🎨 现代化界面**：基于 PySide6 和 QFluentWidgets 构建，提供美观、直观的用户界面。
- **📊 数据统计**：内置统计面板，展示总数、传说数量、脱钩率等关键指标，并附带品质分布饼图。
- **👁️ 可视化调试**：开启后，程序会实时显示图像识别的匹配过程和结果，方便开发者进行调试和优化。
- **悬浮窗**：可选的迷你悬浮窗，实时显示程序状态，不遮挡游戏画面。
- **⌨️ 全局热键**：通过 F2 键轻松启动/暂停，F10 键快速截图以供调试。

---

## 📸 屏幕截图 (Screenshots)

| 钓鱼记录 | 迷你悬浮窗 | 可视化调试 |
| :---: | :---: |:---:|
| ![钓鱼记录](docs/images/records.png) | ![迷你悬浮窗](docs/images/overlay.png) | ![可视化调试](docs/images/visual_debug_20260109_013910.png) |

---

## 🚀 快速开始 (Quick Start)

1.  **下载**：前往 [Releases](https://github.com/R1ckyyyyy/Autofish/releases/latest) 页面，下载最新的 `Autofish_vX.X.X.zip` 压缩包。
2.  **解压**：将压缩包解压到您选择的任意目录。
3.  **运行**：双击 `autofish.exe` 启动程序。

---

## 📖 使用方法 (Usage)

- **启动/暂停**：按下 `F2` 键启动或暂停自动钓鱼。
- **调试截图**：按下 `F10` 键可截取当前游戏画面，用于问题排查和调试。
- **配置**：在程序主界面，您可以根据游戏内的分辨率和设置调整相关参数，以获得最佳识别效果。

---

## 🔧 工作原理 (How it Works)

Autofish 的核心是利用 **OpenCV** 进行图像识别和模板匹配。它会持续分析游戏画面，识别出抛竿提示、咬钩信号和渔获信息等关键图像。当需要记录钓鱼数据时，程序会调用 **RapidOCR** 引擎，对截图中的文字（鱼的名称、重量、品质）进行识别，并将结果保存到本地记录中。

---

## 💾 数据与截图 (Data & Screenshots)

- **钓鱼记录**：所有的钓鱼数据都以 CSV 格式保存在程序目录下的 `data/records.csv` 文件中。您可以使用 Excel 或其他表格软件打开和分析。
- **传奇截图**：钓到“传说”品质鱼类的截图会自动保存在 `screenshots` 文件夹中。
- **调试截图**：通过 `F10` 热键截取的调试图片会保存在 `debug` 文件夹中。

---

## ❤️ 致谢与许可 (Credits & License)

本项目的图像识别逻辑和部分资源参考了 [FADEDTUMI/PartyFish](https://github.com/FADEDTUMI/PartyFish) 项目，在此表示诚挚的感谢。

本项目采用 [Apache License 2.0](LICENSE) 许可证。
