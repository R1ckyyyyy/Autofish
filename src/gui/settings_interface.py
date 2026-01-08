from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (ScrollArea, SettingCardGroup, SettingCard, FluentIcon, 
                            DoubleSpinBox, SpinBox, SwitchSettingCard, Slider, BodyLabel,
                            ComboBox, PrimaryPushButton, InfoBar, InfoBarPosition)
from src.config import cfg
from src.gui.components import KeyBindingWidget

class SettingsInterface(ScrollArea):
    hotkey_changed_signal = Signal(str)
    debug_hotkey_changed_signal = Signal(str)
    theme_changed_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('settingsInterface')
        
        # Init Scroll Widget
        self.scrollWidget = QWidget()
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        
        # Init Layout
        self.vBoxLayout = QVBoxLayout(self.scrollWidget)
        self.vBoxLayout.setContentsMargins(36, 10, 36, 10)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        # 1. Preset Selection Group
        self.presetGroup = SettingCardGroup(self.tr("预设配置"), self.scrollWidget)
        self.presetCard = SettingCard(
            FluentIcon.TAG, self.tr("当前预设"), self.tr("选择一套预设进行编辑"), parent=self.presetGroup)
        self.presetComboBox = ComboBox(self.presetCard)
        self.presetComboBox.addItems(cfg.presets.keys())
        self.presetComboBox.setCurrentText(cfg.current_preset_name)
        self.presetComboBox.setFixedWidth(150)
        self.presetCard.hBoxLayout.addWidget(self.presetComboBox, 0, Qt.AlignRight)
        margins = self.presetCard.hBoxLayout.contentsMargins()
        self.presetCard.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        self.presetGroup.addSettingCard(self.presetCard)
        self.vBoxLayout.addWidget(self.presetGroup)

        # 2. Fishing Config Group
        self.fishingGroup = SettingCardGroup(self.tr("钓鱼参数配置"), self.scrollWidget)
        
        self.castTimeCard = self._create_double_spinbox_card(
            icon=FluentIcon.UPDATE, title=self.tr("抛竿时间"), content=self.tr("按下抛竿键的持续时间 (秒)"), config_key="cast_time")
        self.fishingGroup.addSettingCard(self.castTimeCard)

        self.reelInTimeCard = self._create_double_spinbox_card(
            icon=FluentIcon.SPEED_HIGH, title=self.tr("收线时间"), content=self.tr("按下收线键的持续时间 (秒)"), config_key="reel_in_time")
        self.fishingGroup.addSettingCard(self.reelInTimeCard)

        self.releaseTimeCard = self._create_double_spinbox_card(
            icon=FluentIcon.SPEED_OFF, title=self.tr("放线时间"), content=self.tr("松开按键的持续时间 (秒)"), config_key="release_time")
        self.fishingGroup.addSettingCard(self.releaseTimeCard)

        self.cycleIntervalCard = self._create_double_spinbox_card(
            icon=FluentIcon.HISTORY, title=self.tr("循环间隔"), content=self.tr("两次循环之间的等待时间 (秒)"), config_key="cycle_interval")
        self.fishingGroup.addSettingCard(self.cycleIntervalCard)
        
        self.maxPullsCard = SettingCard(FluentIcon.SYNC, self.tr("最大拉杆次数"), self.tr("单次钓鱼过程中的最大拉杆尝试次数"))
        self.maxPullsSpinBox = SpinBox(self.maxPullsCard)
        self.maxPullsSpinBox.setRange(1, 100)
        self.maxPullsCard.hBoxLayout.addWidget(self.maxPullsSpinBox, 0, Qt.AlignRight)
        margins = self.maxPullsCard.hBoxLayout.contentsMargins()
        self.maxPullsCard.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        self.fishingGroup.addSettingCard(self.maxPullsCard)
        self.vBoxLayout.addWidget(self.fishingGroup)

        # 3. Global Settings Group
        self.globalGroup = SettingCardGroup(self.tr("全局配置"), self.scrollWidget)
        
        self.hotkeyCard = SettingCard(FluentIcon.SETTING, self.tr("启动/暂停快捷键"), self.tr("设置用于启动和暂停脚本的全局快捷键。"))
        self.hotkeyLineEdit = KeyBindingWidget(self.hotkeyCard)
        self.hotkeyLineEdit.setFixedWidth(120)
        self.hotkeyCard.hBoxLayout.addWidget(self.hotkeyLineEdit, 0, Qt.AlignRight)
        margins = self.hotkeyCard.hBoxLayout.contentsMargins()
        self.hotkeyCard.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        self.globalGroup.addSettingCard(self.hotkeyCard)
        
        self.debugHotkeyCard = SettingCard(FluentIcon.DEVELOPER_TOOLS, self.tr("调试快捷键"), self.tr("设置用于触发调试功能的全局快捷键。"))
        self.debugHotkeyLineEdit = KeyBindingWidget(self.debugHotkeyCard)
        self.debugHotkeyLineEdit.setFixedWidth(120)
        self.debugHotkeyCard.hBoxLayout.addWidget(self.debugHotkeyLineEdit, 0, Qt.AlignRight)
        margins = self.debugHotkeyCard.hBoxLayout.contentsMargins()
        self.debugHotkeyCard.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        self.globalGroup.addSettingCard(self.debugHotkeyCard)
        
        self.jiashiCard = SwitchSettingCard(FluentIcon.CARE_UP_SOLID, self.tr("自动加时"), self.tr("检测到加时弹窗时自动点击'是'"))
        self.globalGroup.addSettingCard(self.jiashiCard)

        self.jitterCard = SettingCard(FluentIcon.SYNC, "时间抖动范围", "设置操作时间的随机波动百分比 (0% - 30%)")
        self.jitterSlider = Slider(Qt.Orientation.Horizontal)
        self.jitterLabel = BodyLabel("0%")
        self.jitterSlider.setRange(0, 30)
        self.jitterCard.hBoxLayout.addStretch(1)
        self.jitterCard.hBoxLayout.addWidget(self.jitterSlider)
        self.jitterCard.hBoxLayout.addSpacing(15)
        self.jitterCard.hBoxLayout.addWidget(self.jitterLabel)
        self.globalGroup.addSettingCard(self.jitterCard)

        self.themeCard = SettingCard(FluentIcon.PALETTE, self.tr("主题设置"), self.tr("选择应用的主题模式"))
        self.themeComboBox = ComboBox(self.themeCard)
        self.themeComboBox.addItems(["Light", "Dark"])
        self.themeComboBox.setFixedWidth(120)
        self.themeCard.hBoxLayout.addWidget(self.themeComboBox, 0, Qt.AlignRight)
        margins = self.themeCard.hBoxLayout.contentsMargins()
        self.themeCard.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        self.globalGroup.addSettingCard(self.themeCard)
        

        self.vBoxLayout.addWidget(self.globalGroup)

        # 4. Save Button
        self.saveButton = PrimaryPushButton(self.tr("保存设置"), self)
        self.vBoxLayout.addWidget(self.saveButton, 0, Qt.AlignRight)
        
        # 5. Load initial values and connect signals
        self._load_settings_to_ui()
        self._connect_signals()

        # Style
        self.setStyleSheet("QScrollArea {background-color: transparent; border: none;}")
        self.scrollWidget.setStyleSheet("QWidget {background-color: transparent;}")

    def _create_double_spinbox_card(self, icon, title, content, config_key):
        card = SettingCard(icon, title, content, parent=self.fishingGroup)
        spinbox = DoubleSpinBox(card)
        spinbox.setRange(0.1, 10.0)
        spinbox.setSingleStep(0.1)
        card.hBoxLayout.addWidget(spinbox, 0, Qt.AlignRight)
        margins = card.hBoxLayout.contentsMargins()
        card.hBoxLayout.setContentsMargins(margins.left(), margins.top(), 16, margins.bottom())
        
        # Convert snake_case to camelCase for attribute name
        parts = config_key.split('_')
        attr_name = parts[0] + ''.join(x.title() for x in parts[1:]) + 'SpinBox'
        setattr(self, attr_name, spinbox)
        return card

    def _connect_signals(self):
        self.presetComboBox.currentTextChanged.connect(self._load_settings_to_ui)
        self.saveButton.clicked.connect(self._save_settings_from_ui)
        self.jitterSlider.valueChanged.connect(lambda v: self.jitterLabel.setText(f"{v}%"))
        self.themeComboBox.currentTextChanged.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme):
        self.theme_changed_signal.emit(theme)

    def _load_settings_to_ui(self, preset_name_to_load=None):
        # Block signals to prevent recursive calls while updating the UI
        self.presetComboBox.blockSignals(True)

        # Determine which preset to load
        preset_name = preset_name_to_load if preset_name_to_load else self.presetComboBox.currentText()
        if not preset_name:
            preset_name = cfg.current_preset_name # Fallback to global current
        
        # Update the ComboBox to ensure it reflects the state
        self.presetComboBox.setCurrentText(preset_name)

        # Load preset-specific settings
        current_preset = cfg.presets.get(preset_name, {})
        
        self.castTimeSpinBox.setValue(current_preset.get("cast_time", 2.0))
        self.reelInTimeSpinBox.setValue(current_preset.get("reel_in_time", 2.0))
        self.releaseTimeSpinBox.setValue(current_preset.get("release_time", 1.0))
        self.cycleIntervalSpinBox.setValue(current_preset.get("cycle_interval", 0.5))
        self.maxPullsSpinBox.setValue(current_preset.get("max_pulls", 20))
        
        # Load global settings
        self.hotkeyLineEdit.setText(cfg.global_settings.get("hotkey", "F2"))
        self.debugHotkeyLineEdit.setText(cfg.global_settings.get("debug_hotkey", "F10"))
        self.jiashiCard.setChecked(cfg.global_settings.get("enable_jiashi", True))
        jitter_value = cfg.global_settings.get("jitter_range", 0)
        self.jitterSlider.setValue(jitter_value)
        self.jitterLabel.setText(f"{jitter_value}%")
        self.themeComboBox.setCurrentText(cfg.global_settings.get("theme", "Dark"))

        # Unblock signals
        self.presetComboBox.blockSignals(False)


    def _save_settings_from_ui(self):
        # Save preset-specific settings
        preset_name = self.presetComboBox.currentText()
        if preset_name in cfg.presets:
            cfg.presets[preset_name]["cast_time"] = self.castTimeSpinBox.value()
            cfg.presets[preset_name]["reel_in_time"] = self.reelInTimeSpinBox.value()
            cfg.presets[preset_name]["release_time"] = self.releaseTimeSpinBox.value()
            cfg.presets[preset_name]["cycle_interval"] = self.cycleIntervalSpinBox.value()
            cfg.presets[preset_name]["max_pulls"] = self.maxPullsSpinBox.value()
        
        # Save global settings
        new_hotkey = self.hotkeyLineEdit.text()
        if cfg.global_settings.get("hotkey") != new_hotkey:
            cfg.global_settings["hotkey"] = new_hotkey
            self.hotkey_changed_signal.emit(new_hotkey)
            
        new_debug_hotkey = self.debugHotkeyLineEdit.text()
        if cfg.global_settings.get("debug_hotkey") != new_debug_hotkey:
            cfg.global_settings["debug_hotkey"] = new_debug_hotkey
            self.debug_hotkey_changed_signal.emit(new_debug_hotkey)
            
        cfg.global_settings["enable_jiashi"] = self.jiashiCard.isChecked()
        cfg.global_settings["jitter_range"] = self.jitterSlider.value()
        cfg.global_settings["theme"] = self.themeComboBox.currentText()
        
        # Update current preset in config to match the one being edited
        cfg.load_preset(preset_name)
        
        # Save to file
        cfg.save()
        
        # Show success message
        InfoBar.success(
            title=self.tr('保存成功'),
            content=self.tr(f"配置 '{preset_name}' 及全局设置已更新。"),
            duration=2000,
            position=InfoBarPosition.TOP,
            parent=self.window()
        )


