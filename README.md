# 🎣 Autofish - 猛兽派对自动钓鱼助手

[![Release](https://img.shields.io/github/v/release/R1ckyyyyy/Autofish?style=for-the-badge)](https://github.com/R1ckyyyyy/Autofish/releases/latest)
[![License](https://img.shields.io/github/license/R1ckyyyyy/Autofish?style=for-the-badge)](LICENSE)
[![Game](https://img.shields.io/badge/Game-猛兽派对%20Party%20Animals-blue?style=for-the-badge)](https://www.partyanimals.com/)

**🎮 专为《猛兽派对 (Party Animals)》钓鱼玩法设计的自动化辅助工具**

Autofish 是一款基于图像识别的自动钓鱼工具，拥有自动化操作、OCR 钓鱼记录、现代化 GUI 界面等特性，让你在猛兽派对中轻松享受钓鱼乐趣！

---

---

## ✨ 核心功能 (Core Features)

### 📊 智能钓鱼记录与统计
Autofish 不仅能自动钓鱼，还能通过 OCR 技术精准识别并记录每一条渔获的详细信息，包括鱼的名称、重量、品质和垂钓时间。所有数据都会被整齐地记录下来，方便您随时回顾和分析。

此外，程序内置了强大的数据统计面板，让您对自己的钓鱼成果一目了然。您可以轻松查看总渔获数量、传说品质鱼类的数量、脱钩率等关键指标，并通过直观的饼图了解不同品质鱼类的分布情况。

![钓鱼记录与统计](docs/images/records.png)

### 👁️ 可视化调试模式
对于开发者和高级用户，我们提供了强大的可视化调试功能。开启此模式后，Autofish 会在游戏画面上实时展示其图像识别的过程和结果。

您可以清晰地看到程序正在匹配哪些图像、识别的精确区域以及当前的决策状态。这不仅极大地简化了调试过程，也让您能更直观地了解 Autofish 的工作原理，并根据需要进行调整和优化。

![可视化调试](docs/images/visual_debug_20260109_013910.png)

### - 迷你悬浮窗
为了让您在享受自动化钓鱼的便利时，仍能随时掌握程序状态，我们设计了简约而不失功能的迷你悬浮窗。

这个悬浮窗会以最不打扰的方式驻留在游戏窗口的边缘，实时显示当前是“工作中”还是“休息中”，以及本次运行的钓鱼次数。您可以随时了解程序动态，而无需切出游戏或打开主界面。

![迷你悬浮窗](docs/images/overlay.png)

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
- **调试截图**：通过 `F10` 热键截取的调试图片会保存在 `debug_screenshots` 文件夹中。

---

## ❤️ 致谢与许可 (Credits & License)

本项目的图像识别逻辑和部分资源参考了 [FADEDTUMI/PartyFish](https://github.com/FADEDTUMI/PartyFish) 项目，在此表示诚挚的感谢。

本项目采用 [Apache License 2.0](LICENSE) 许可证。
