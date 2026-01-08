from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableWidgetItem, QLabel, QHBoxLayout, QFrame, QToolTip
from PySide6.QtGui import QColor, QBrush, Qt, QPainter, QCursor
from PySide6.QtCore import Qt as QtCoreQt, QMargins
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QPieSlice
from qfluentwidgets import TableWidget, ComboBox, CardWidget, BodyLabel, TitleLabel, FluentIcon, qconfig, SegmentedWidget, InfoBadge, setTheme, Theme
from datetime import datetime
import csv
import os
from collections import Counter
from .components import QUALITY_COLORS
from src.config import cfg

class NumericTableWidgetItem(QTableWidgetItem):
    """
    Custom TableWidgetItem to ensure proper sorting for numeric columns (Weight).
    """
    def __lt__(self, other):
        try:
            return float(self.text()) < float(other.text())
        except ValueError:
            return super().__lt__(other)

class RecordsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('recordsInterface')
        
        # --- Main Layout ---
        self.vBoxLayout = QVBoxLayout(self)

        # --- Top Controls ---
        top_controls_layout = QHBoxLayout()
        self.view_switcher = SegmentedWidget(self)
        self.view_switcher.addItem('history', '历史统计')
        self.view_switcher.addItem('today', '今日统计')
        self.view_switcher.setCurrentItem('history')
        self.view_switcher.currentItemChanged.connect(self._on_view_changed)
        top_controls_layout.addWidget(self.view_switcher)
        top_controls_layout.addStretch(1)
        self.filter_combo = ComboBox()
        self.filter_combo.addItems(['全部品质', '标准', '非凡', '稀有', '史诗', '传说'])
        self.filter_combo.currentTextChanged.connect(self._filter_table)
        self.filter_combo.setFixedWidth(150)
        top_controls_layout.addWidget(QLabel("筛选品质:"))
        top_controls_layout.addWidget(self.filter_combo)
        self.vBoxLayout.addLayout(top_controls_layout)

        # --- Dashboard (Statistics) ---
        self.dashboard_layout_row1 = QHBoxLayout()
        self.dashboard_layout_row1.setSpacing(15)
        self.total_card = self._create_stat_card("总数", "0", FluentIcon.CALENDAR)
        self.today_card = self._create_stat_card("今日捕获", "0", FluentIcon.BASKETBALL)
        self.legendary_card = self._create_stat_card("传说数量", "0", FluentIcon.TAG)
        self.unhook_rate_card = self._create_stat_card("脱钩率", "0.00%", FluentIcon.REMOVE_FROM)
        self.dashboard_layout_row1.addWidget(self.total_card)
        self.dashboard_layout_row1.addWidget(self.today_card)
        self.dashboard_layout_row1.addWidget(self.legendary_card)
        self.dashboard_layout_row1.addWidget(self.unhook_rate_card)

        self.vBoxLayout.addLayout(self.dashboard_layout_row1)


        # --- Bottom Layout (Table + Chart) ---
        bottom_layout = QHBoxLayout()

        # Table
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['时间', '名称', '重量', '品质'])
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        bottom_layout.addWidget(self.table, 3) # Table takes 3/5 of space

        # Pie Chart
        self._init_pie_chart()
        bottom_layout.addWidget(self.chart_view, 2) # Chart takes 2/5 of space

        self.vBoxLayout.addLayout(bottom_layout)

        # --- Data Storage ---
        self.all_records = []
        self.current_qualities_in_view = [] # To refresh chart theme
        self._load_data()

    def _init_pie_chart(self):
        """Initializes the pie chart component."""
        self.pie_series = QPieSeries()
        self.pie_series.setHoleSize(0.35)

        chart = QChart()
        chart.addSeries(self.pie_series)
        chart.setTitle("品质分布")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        is_dark_theme = qconfig.theme.value == "Dark"
        chart.setTheme(QChart.ChartTheme.ChartThemeDark if is_dark_theme else QChart.ChartTheme.ChartThemeLight)
        
        self.chart_view = QChartView(chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

    def _on_view_changed(self, item):
        """Handle view change between Today and History"""
        self._update_stats_and_table()

    def _create_stat_card(self, title, value, icon):
        """Helper to create a more appealing stat card"""
        card = CardWidget(self)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        
        icon_label = QLabel()
        icon_label.setPixmap(icon.icon(color=qconfig.themeColor.value).pixmap(28, 28))
        
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(10, 0, 0, 0)
        
        title_label = BodyLabel(title, card)
        value_label = TitleLabel(value, card)
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(value_label)
        text_layout.setSpacing(0)
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout)
        layout.addStretch(1)
        
        card.value_label = value_label
        
        return card

    def _load_data(self):
        """Load data from CSV and populate table"""
        self.all_records = []
        
        data_path = cfg._get_base_path() / 'data' / 'records.csv'
        if not data_path.exists():
            self._update_stats_and_table()
            return

        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None) # Skip header
                
                for row in reader:
                    if len(row) >= 4:
                        self.all_records.append({
                            'timestamp': row[0],
                            'name': row[1],
                            'quality': row[2],
                            'weight': row[3]
                        })
        except Exception as e:
            print(f"Error loading records: {e}")
        
        # Reverse records to show newest first by default
        self.all_records.reverse()
        self._update_stats_and_table()

    def _populate_table(self, records_to_display):
        """Populate the table with a given list of records"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        
        for record in records_to_display:
            self._add_row_to_table(
                record['timestamp'],
                record['name'],
                record['quality'],
                record['weight']
            )
        self.table.setSortingEnabled(True)

    def _add_row_to_table(self, timestamp, name, quality, weight):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        items = [
            QTableWidgetItem(str(timestamp)),
            QTableWidgetItem(str(name)),
            NumericTableWidgetItem(str(weight)), # Use Numeric for weight
            QTableWidgetItem(str(quality))
        ]
        
        # Determine color based on quality and theme
        quality_str = str(quality)
        is_dark_theme = qconfig.theme.value == "Dark"
        color = None
        if quality_str in QUALITY_COLORS:
            color = QUALITY_COLORS[quality_str][1] if is_dark_theme else QUALITY_COLORS[quality_str][0]

        # Apply color to all items in the row
        if color:
            brush = QBrush(color)
            for item in items:
                item.setForeground(brush)

        for col_index, item in enumerate(items):
            self.table.setItem(row_count, col_index, item)
    
    def _update_stats_and_table(self):
        """
        Central function to update stats and table based on the current view (Today/History).
        """
        current_view_item = self.view_switcher.currentItem()
        if not current_view_item:
             return
        current_view = current_view_item.text()
        
        today_str = datetime.now().strftime("%Y-%m-%d")

        if current_view == '今日统计':
            display_records = [r for r in self.all_records if r['timestamp'].startswith(today_str)]
        else: # History
            display_records = self.all_records

        # --- Update Stats ---
        total_records = len(self.all_records)
        today_records = [r for r in self.all_records if r['timestamp'].startswith(today_str)]
        
        total_count = len(display_records)
        today_count = len(today_records)
        
        all_qualities = [r['quality'] for r in self.all_records]
        
        # Calculate unhook stats based on the current view
        total_attempts = len(display_records)
        unhook_count = [r['name'] for r in display_records].count('鱼跑了')
        unhook_rate = (unhook_count / total_attempts) * 100 if total_attempts > 0 else 0.0

        # Calculate quality stats based on the current view
        self.current_qualities_in_view = [r['quality'] for r in display_records]
        legendary_count = self.current_qualities_in_view.count('传说')
        epic_count = self.current_qualities_in_view.count('史诗')
        rare_count = self.current_qualities_in_view.count('稀有')
        
        total_fish_caught = total_attempts - unhook_count
        if total_fish_caught > 0:
            legendary_perc = (legendary_count / total_fish_caught) * 100
            epic_perc = (epic_count / total_fish_caught) * 100
            rare_perc = (rare_count / total_fish_caught) * 100
        else:
            legendary_perc = epic_perc = rare_perc = 0.0


        # Update labels
        self.total_card.value_label.setText(str(total_records))
        self.today_card.value_label.setText(str(today_count))
        self.legendary_card.value_label.setText(str(legendary_count))
        self.unhook_rate_card.value_label.setText(f"{unhook_rate:.2f}%")

        # --- Update Table and Chart ---
        self._populate_table(display_records)
        self._update_pie_chart(self.current_qualities_in_view)
        self._filter_table() # Re-apply current filter

    def _update_pie_chart(self, qualities):
        """Updates the pie chart with the given quality data."""
        self.pie_series.clear()
        
        quality_counts = Counter(qualities)
        total_fish_caught = sum(quality_counts.values())

        if total_fish_caught == 0:
            return
        
        is_dark_theme = qconfig.theme.value == "Dark"
        
        for quality, count in quality_counts.items():
            if quality in QUALITY_COLORS:
                slice_color = QUALITY_COLORS[quality][1] if is_dark_theme else QUALITY_COLORS[quality][0]
                
                # The slice label is just the quality name, for the legend.
                pie_slice = QPieSlice(quality, count)
                pie_slice.setColor(slice_color)
                
                # Store data needed for tooltip
                pie_slice.setProperty("count", count)
                pie_slice.setProperty("total_count", total_fish_caught)
                pie_slice.setProperty("quality_name", quality)
                
                # Connect hover effect
                pie_slice.hovered.connect(self._handle_slice_hover)
                
                self.pie_series.append(pie_slice)

    def _handle_slice_hover(self, state):
        """Explode slice and show tooltip on hover."""
        pie_slice = self.sender()
        if not isinstance(pie_slice, QPieSlice):
            return

        # Explode/un-explode the slice
        pie_slice.setExploded(state)
        
        if state:
            # Calculate tooltip text
            count = pie_slice.property("count")
            total_count = pie_slice.property("total_count")
            quality = pie_slice.property("quality_name")
            percentage = (count / total_count) * 100 if total_count > 0 else 0
            
            tooltip_text = f"{quality}\n数量: {count}\n占比: {percentage:.2f}%"
            
            # Show tooltip at cursor position
            QToolTip.showText(QCursor.pos(), tooltip_text)
        else:
            # Hide tooltip
            QToolTip.hideText()

    def _filter_table(self, text=None):
        """Filter rows based on quality"""
        if text is None:
            text = self.filter_combo.currentText()
        
        filter_quality = text
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3) # Quality column
            if not item: continue
            
            if filter_quality == '全部品质':
                self.table.setRowHidden(row, False)
            else:
                if filter_quality in item.text():
                    self.table.setRowHidden(row, False)
                else:
                    self.table.setRowHidden(row, True)

    def add_record(self, record: dict):
        """
        添加一条记录到表格 (Called by worker signal)
        """
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record['timestamp'] = now_ts
        
        # Add to the beginning of the list to show newest first
        self.all_records.insert(0, record)
        
        # Refresh everything
        self._update_stats_and_table()
        self.table.scrollToTop()
            
    def refresh_table_colors(self):
        """
        Iterate over all rows and re-apply colors based on the current theme.
        Also, refresh the chart theme.
        """
        is_dark_theme = qconfig.theme.value == "Dark"
        
        # Refresh chart
        self.chart_view.chart().setTheme(QChart.ChartTheme.ChartThemeDark if is_dark_theme else QChart.ChartTheme.ChartThemeLight)
        self._update_pie_chart(self.current_qualities_in_view)

        # Refresh table
        for row in range(self.table.rowCount()):
            quality_item = self.table.item(row, 3) # Quality is in column 3
            if not quality_item:
                continue
            
            quality_str = quality_item.text()
            color = None
            if quality_str in QUALITY_COLORS:
                color = QUALITY_COLORS[quality_str][1] if is_dark_theme else QUALITY_COLORS[quality_str][0]

            if color:
                brush = QBrush(color)
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setForeground(brush)
