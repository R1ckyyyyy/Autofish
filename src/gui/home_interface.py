from PySide6.QtCore import Qt, QTimer, Slot, QTime, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QTableWidgetItem, QHeaderView, QSplitter)
from PySide6.QtGui import QColor, QBrush
from qfluentwidgets import (CardWidget, TextEdit, StrongBodyLabel, TableWidget,
                            CaptionLabel, TitleLabel, SubtitleLabel, InfoBadge, InfoLevel, ComboBox, qconfig, SwitchButton)
from qfluentwidgets import FluentIcon as FIF
from src.config import cfg
from .components import QUALITY_COLORS


class HomeInterface(QWidget):
    """主页界面"""

    preset_changed_signal = Signal(str)
    toggle_overlay_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("HomeInterface")
        
        self.run_time = QTime(0, 0, 0)
        self.total_catch = 0
        self.last_fish_info = "暂无"

        self.v_box_layout = QVBoxLayout(self)
        self.v_box_layout.setContentsMargins(30, 30, 30, 30)
        self.v_box_layout.setSpacing(20)

        # 1. Banner Area
        self.init_banner()

        # Create a splitter to divide the main area
        self.main_splitter = QSplitter(Qt.Horizontal, self)
        
        # Left side widget
        self.left_widget = QWidget(self)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 15, 0) # Add right margin
        self.left_layout.setSpacing(20)

        # 2. Real-time data panel
        self.init_dashboard()
        self.left_layout.addLayout(self.dashboard_layout)

        # 3. Session records table
        self.init_session_records()
        self.left_layout.addWidget(self.session_records_container)
        self.left_layout.setStretchFactor(self.session_records_container, 1) # Allow table to expand

        # Right side widget (Log Area)
        self.init_log_area() # This now returns the container

        # Add widgets to splitter
        self.main_splitter.addWidget(self.left_widget)
        self.main_splitter.addWidget(self.log_container)
        self.main_splitter.setStretchFactor(0, 2) # Give more space to the left side initially (ratio 2:1)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: transparent;
                width: 1px;
            }
            QSplitter::handle:horizontal {
                border-right: 1px solid #3A3A3A;
            }
        """)

        self.v_box_layout.addWidget(self.main_splitter)
        
        # Timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_run_time)

    def init_banner(self):
        """初始化 Banner"""
        self.banner = CardWidget(self)
        self.banner_layout = QHBoxLayout(self.banner)
        self.banner_layout.setContentsMargins(20, 20, 20, 20)
        self.banner_layout.setSpacing(20)

        # 文本部分
        self.banner_text_layout = QVBoxLayout()
        self.banner_text_layout.setSpacing(10)
        
        self.title_label = TitleLabel("自动钓鱼助手", self.banner)
        self.instruction_label = SubtitleLabel(f"按 {cfg.hotkey} 键启动/暂停", self.banner)
        self.instruction_label.setTextColor(QColor(100, 100, 100), QColor(200, 200, 200))
        self.debug_instruction_label = SubtitleLabel(f"按 {cfg.global_settings.get('debug_hotkey', 'F10')} 键生成调试截图", self.banner)
        self.debug_instruction_label.setTextColor(QColor(100, 100, 100), QColor(200, 200, 200))

        self.banner_text_layout.addWidget(self.title_label)
        self.banner_text_layout.addWidget(self.instruction_label)
        self.banner_text_layout.addWidget(self.debug_instruction_label)
        self.banner_layout.addLayout(self.banner_text_layout)
        
        self.banner_layout.addStretch(1)

        # Overlay Switcher
        self.overlay_label = StrongBodyLabel("显示悬浮窗:", self.banner)
        self.overlay_switch = SwitchButton(self.banner)
        self.overlay_switch.checkedChanged.connect(lambda: self.toggle_overlay_signal.emit())
        self.banner_layout.addWidget(self.overlay_label)
        self.banner_layout.addWidget(self.overlay_switch)

        # Preset Switcher
        self.preset_label = StrongBodyLabel("当前预设:", self.banner)
        self.presetComboBox = ComboBox(self.banner)
        self.presetComboBox.addItems(cfg.presets.keys())
        self.presetComboBox.setCurrentText(cfg.current_preset_name)
        self.presetComboBox.setFixedWidth(120)
        self.presetComboBox.currentTextChanged.connect(self._on_preset_changed)
        
        self.banner_layout.addWidget(self.preset_label)
        self.banner_layout.addWidget(self.presetComboBox)
        
        # 状态指示
        self.status_badge = InfoBadge.custom("已停止", QColor("#8a8a8a"), QColor("#f9f9f9"))
        self.banner_layout.addWidget(self.status_badge)

        self.v_box_layout.addWidget(self.banner)

    def _on_preset_changed(self, preset_name):
        """Handle preset switching from the ComboBox."""
        if preset_name in cfg.presets:
            cfg.load_preset(preset_name)
            cfg.save()
            # 状态重置信号：如果此时脚本正在运行或暂停，我们需要通知Worker重置状态
            # 由于没有直接引用的worker，我们通过一个自定义信号或查找父窗口来通信
            # 或者更简单的，我们定义一个信号，让MainWindow去连接
            if hasattr(self, 'preset_changed_signal'):
                 self.preset_changed_signal.emit(preset_name)

    def update_hotkey_display(self, new_hotkey):
        self.instruction_label.setText(f"按 {new_hotkey} 键启动/暂停")

    def update_debug_hotkey_display(self, new_hotkey):
        self.debug_instruction_label.setText(f"按 {new_hotkey} 键生成调试截图")

    def init_dashboard(self):
        """初始化数据看板"""
        self.dashboard_layout = QGridLayout()
        self.dashboard_layout.setSpacing(20)

        # 卡片 1 - 运行时间
        self.time_card = self.create_stat_card("运行时间", "00:00:00", FIF.HISTORY)
        self.time_value_label = self.time_card.findChild(TitleLabel)
        self.dashboard_layout.addWidget(self.time_card, 0, 0)

        # 卡片 2 - 本次捕获
        self.catch_card = self.create_stat_card("本次捕获", "0", FIF.ACCEPT)
        self.catch_value_label = self.catch_card.findChild(TitleLabel)
        self.dashboard_layout.addWidget(self.catch_card, 0, 1)

        # 卡片 3 - 最近收获
        self.last_card = self.create_stat_card("最近收获", "暂无", FIF.TAG)
        self.last_value_label = self.last_card.findChild(TitleLabel)
        self.dashboard_layout.addWidget(self.last_card, 0, 2)
        
        # self.v_box_layout.addLayout(self.dashboard_layout) #<-- THIS WAS THE CULPRIT

    def init_session_records(self):
        """Initializes the session records table area."""
        self.session_records_container = QWidget(self)
        layout = QVBoxLayout(self.session_records_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = StrongBodyLabel("本次记录", self)
        layout.addWidget(header)
        
        self.session_table = TableWidget(self)
        self.session_table.setColumnCount(3)
        self.session_table.setHorizontalHeaderLabels(["鱼名", "品质", "重量 (kg)"])
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setEditTriggers(TableWidget.NoEditTriggers)
        self.session_table.setBorderVisible(True)
        self.session_table.setBorderRadius(8)
        self.session_table.setWordWrap(False)
        
        self.session_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.session_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.session_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.session_table)

    def add_record_to_session_table(self, record):
        """Adds a new catch record to the session table."""
        row_position = self.session_table.rowCount()
        self.session_table.insertRow(row_position)
        
        name_item = QTableWidgetItem(record.get('name', ''))
        quality_item = QTableWidgetItem(record.get('quality', ''))
        weight_item = QTableWidgetItem(str(record.get('weight', 0.0)))
        
        # Add color based on quality
        quality = record.get('quality', 'Standard')
        is_dark_theme = qconfig.theme.value == "Dark"
        
        if quality in QUALITY_COLORS:
            color = QUALITY_COLORS[quality][1] if is_dark_theme else QUALITY_COLORS[quality][0]
            brush = QBrush(color)
            name_item.setForeground(brush)
            quality_item.setForeground(brush)

        self.session_table.setItem(row_position, 0, name_item)
        self.session_table.setItem(row_position, 1, quality_item)
        self.session_table.setItem(row_position, 2, weight_item)
        
        self.session_table.scrollToBottom()

    def clear_session_table(self):
        """Clears all records from the session table."""
        self.session_table.setRowCount(0)


    def create_stat_card(self, title, value, icon):
        """创建统计卡片辅助函数"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 标题行
        title_row = QHBoxLayout()
        icon_widget = getattr(icon, 'icon', icon)() # Handle both FluentIcon enum or object
        
        title_label = CaptionLabel(title, card)
        title_label.setTextColor(QColor(120, 120, 120), QColor(160, 160, 160))
        title_row.addWidget(title_label)
        title_row.addStretch(1)
        
        layout.addLayout(title_row)
        
        # 数值
        value_label = TitleLabel(value, card)
        layout.addWidget(value_label)
        
        return card

    def init_log_area(self):
        """初始化日志区域"""
        # 容器
        self.log_container = QWidget(self)
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(15, 0, 0, 0) # Add left margin
        self.log_layout.setSpacing(0)

        self.log_header_label = StrongBodyLabel("运行日志", self)
        self.log_layout.addWidget(self.log_header_label)

        # 日志输出框
        self.log_output = TextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setObjectName("LogOutput")
        self.log_layout.addWidget(self.log_output)
        
        # self.v_box_layout.addWidget(self.log_container) NO LONGER ADDED HERE
        # self.v_box_layout.setStretchFactor(self.log_container, 1)

    @Slot(str)
    def update_log(self, text):
        """追加日志"""
        self.log_output.append(text)

    @Slot(str)
    def update_status(self, status):
        """更新状态"""
        # 更新 Badge
        if status == "运行中":
            self.status_badge.deleteLater()
            self.status_badge = InfoBadge.success("运行中", self.banner)
            self.banner_layout.addWidget(self.status_badge)
            
            # Start timer if not running
            if not self.timer.isActive():
                # Reset session data
                self.clear_session_table()
                self.total_catch = 0
                self.catch_value_label.setText("0")
                self.last_value_label.setText("暂无")
                
                self.run_time = QTime(0, 0, 0)
                self.time_value_label.setText("00:00:00")
                self.timer.start(1000)
                
        elif "暂停" in status:
            self.status_badge.deleteLater()
            self.status_badge = InfoBadge.warning("已暂停", self.banner)
            self.banner_layout.addWidget(self.status_badge)
            self.timer.stop()
            
        elif "停止" in status:
            self.status_badge.deleteLater()
            self.status_badge = InfoBadge.custom("已停止", QColor("#8a8a8a"), QColor("#f9f9f9"))
            self.banner_layout.addWidget(self.status_badge)
            self.timer.stop()
            
    def update_run_time(self):
        """更新运行时间显示"""
        self.run_time = self.run_time.addSecs(1)
        self.time_value_label.setText(self.run_time.toString("HH:mm:ss"))

    @Slot(dict)
    def update_catch_info(self, catch_data):
        """更新捕获数据"""
        # 更新数量
        self.total_catch += 1
        self.catch_value_label.setText(str(self.total_catch))
        
        # 更新最近一条
        name = catch_data.get('name', '未知')
        quality = catch_data.get('quality', '普通')
        self.last_value_label.setText(f"{quality} - {name}")

    def refresh_table_colors(self):
        """
        Iterate over all rows in the session table and re-apply colors based on the current theme.
        """
        is_dark_theme = qconfig.theme.value == "Dark"
        for row in range(self.session_table.rowCount()):
            quality_item = self.session_table.item(row, 1) # Quality is in column 1
            if not quality_item:
                continue
            
            quality_str = quality_item.text()
            color = None
            if quality_str in QUALITY_COLORS:
                color = QUALITY_COLORS[quality_str][1] if is_dark_theme else QUALITY_COLORS[quality_str][0]

            if color:
                brush = QBrush(color)
                # Apply to both name (col 0) and quality (col 1)
                name_item = self.session_table.item(row, 0)
                if name_item:
                    name_item.setForeground(brush)
                quality_item.setForeground(brush)

