from PySide6.QtCore import Qt, Signal, QPoint, QRect
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtGui import QMouseEvent, QPixmap, QPainter, QPainterPath, QColor, QPen
import os

class OverlayWindow(QWidget):
    """
    一个悬浮窗，用于显示实时状态和提供快捷操作。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置窗口无边框、总在最前、工具窗口类型
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 主框架，用于设置圆角和背景色
        main_frame = QFrame(self)
        main_frame.setObjectName("mainFrame")
        
        # --- 头像部分 ---
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.setObjectName("avatarLabel")
        self.avatar_label.setScaledContents(True) # 允许内容缩放以支持高清图
        
        # 加载头像
        avatar_path = os.path.join("resources", "avatar.png")
        if not os.path.exists(avatar_path):
             # 如果没有avatar.png，尝试使用favicon.ico
             avatar_path = os.path.join("resources", "favicon.ico")

        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path)
            # 处理头像：居中裁剪 + 圆角方形 + 高清边框
            self.avatar_label.setPixmap(self._process_avatar(pixmap, 50))
        
        # --- 文字信息部分 ---
        # 第一行：状态
        self.status_label = QLabel("状态: 准备中")
        self.status_label.setObjectName("statusLabel")
        
        # 第二行：统计
        self.fish_count_label = QLabel("总计: 0")
        self.fish_count_label.setObjectName("countLabel")

        # 文字布局 (垂直)
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2) # 两行文字靠紧一点
        text_layout.setContentsMargins(0, 5, 0, 5) # 上下微调
        text_layout.addWidget(self.status_label)
        text_layout.addWidget(self.fish_count_label)
        text_layout.setAlignment(Qt.AlignVCenter) # 垂直居中

        # 主内容布局 (水平: 头像 + 文字)
        content_layout = QHBoxLayout(main_frame)
        content_layout.setContentsMargins(10, 5, 15, 5) # 左侧少一点，右侧多一点留白
        content_layout.setSpacing(10) # 头像和文字的间距
        content_layout.addWidget(self.avatar_label)
        content_layout.addLayout(text_layout)
        
        # 设置窗口的主布局
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(main_frame)
        self.layout().setContentsMargins(0, 0, 0, 0)
        
        # 应用QSS样式
        self.apply_stylesheet()

        # 用于窗口拖动
        self._drag_start_position = None

    def _process_avatar(self, pixmap, size):
        """
        处理头像：
        1. 居中裁剪为正方形
        2. 绘制圆角方形 (Squircle)
        3. 绘制边框
        4. 使用2倍分辨率渲染以保证高清
        """
        # 渲染参数
        ratio = 2.0 # 高清倍率
        render_size = int(size * ratio)
        radius = int(12 * ratio) # 圆角半径 (12px * 2 = 24px)
        border_width = int(2.5 * ratio) # 边框宽度 (2.5px * 2 = 5px)
        border_color = QColor("#E6D2B4")

        # 1. 居中裁剪正方形
        img_size = pixmap.size()
        min_side = min(img_size.width(), img_size.height())
        x = (img_size.width() - min_side) // 2
        y = (img_size.height() - min_side) // 2
        
        # 复制并缩放到渲染尺寸
        square_pixmap = pixmap.copy(x, y, min_side, min_side)
        scaled_pixmap = square_pixmap.scaled(render_size, render_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # 2. 准备画布
        result_pixmap = QPixmap(render_size, render_size)
        result_pixmap.fill(Qt.transparent)
        
        painter = QPainter(result_pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 定义绘制路径 (考虑边框的一半宽度，防止被切掉)
        # QRectF 参数: x, y, width, height
        # 内缩半个边框宽，确保边框完整画在画布内
        rect_margin = border_width / 2.0
        draw_rect = QRect(0, 0, render_size, render_size).adjusted(
            int(rect_margin), int(rect_margin), -int(rect_margin), -int(rect_margin)
        )
        
        path = QPainterPath()
        path.addRoundedRect(draw_rect, radius, radius)
        
        # 3. 绘制图片 (使用 Clip Path)
        painter.save()
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.restore()
        
        # 4. 绘制边框
        pen = QPen(border_color, border_width)
        # 边框应该画在形状的轮廓上
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        
        painter.end()
        
        return result_pixmap

    def apply_stylesheet(self):
        """应用QSS样式"""
        style = """
            #mainFrame {
                background-color: rgba(255, 245, 215, 0.9); /* 暖黄色背景，90%不透明 */
                border-radius: 30px; /* 整体大圆角 */
                border: 3px solid rgba(230, 210, 180, 0.95); /* 整体边框 */
            }
            QLabel {
                font-family: "YouYuan", "Microsoft YaHei", "SimHei", sans-serif; /* 优先使用幼圆 */
                font-weight: bold;
            }
            #statusLabel {
                color: #5C4033; /* 深棕色文字 */
                font-size: 16px;
            }
            #countLabel {
                color: #8C6A51; /* 浅棕色文字 */
                font-size: 12px;
            }
            #avatarLabel {
                background-color: transparent;
                /* 边框和圆角已在图片中绘制，此处不再设置，以免重复或不贴合 */
            }
        """
        self.setStyleSheet(style)

    def update_status(self, status: str):
        """更新状态标签"""
        # 简化状态显示，去掉"状态: "前缀，让显示更紧凑
        display_text = status
        if "状态: " in status:
             display_text = status.replace("状态: ", "")
             
        # 特殊状态处理
        if "等待咬钩" in display_text:
            display_text = "等待咬钩..."
        elif "上鱼了" in display_text:
            display_text = "上鱼啦！"
        elif "鱼跑了" in display_text:
            display_text = "哎呀跑了!"
        elif "未检测到游戏" in display_text or "环境检查失败" in display_text:
             display_text = "找不到游戏"
        elif "没有鱼饵" in display_text:
            display_text = "没鱼饵啦!"
        elif "鱼桶" in display_text and "满" in display_text:
            display_text = "鱼桶满啦!"
        elif "抛竿" in display_text:
            display_text = "正在抛竿..."
        elif "记录" in display_text:
            display_text = "正在记录..."
        elif "暂停" in display_text:
            display_text = "休息中 zZ"
        
        self.status_label.setText(display_text)

    def update_fish_count(self, count: int):
        """更新钓鱼计数标签"""
        self.fish_count_label.setText(f"已钓: {count}条")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_start_position:
            self.move(event.globalPosition().toPoint() - self._drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_start_position = None
        event.accept()
