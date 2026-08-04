from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QScrollArea, QWidget, QGridLayout

from UI.fra_camera_manage import FraCameraManage


class DynamicGridWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        # 设置滚动区域属性
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 创建内容容器
        self.container = QWidget()
        self.setWidget(self.container)

        # 使用网格布局
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        # 存储子控件
        self.widgets:List[FraCameraManage] = []

        # 设置每个控件的固定宽度（包括间距）
        self.widget_width = 200  # 控件宽度
        self.widget_height = 120  # 控件高度
        self.horizontal_spacing = 15  # 水平间距

    def add_widget(self, widget):
        """添加控件"""
        # 固定控件大小
        # widget.setFixedSize(self.widget_width, self.widget_height)
        self.widgets.append(widget)
        self.update_layout()

        # 延迟10ms滚动（确保UI刷新完成）
        QTimer.singleShot(10, self.scroll_to_bottom)


    def scroll_to_bottom(self):
        """滚动到最底部（核心方法）"""
        # 方式1：操作滚动条（推荐）
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )

    #移除
    def on_item_remove(self,widget):
        self.widgets.remove(widget)
        self.update_layout()

    #清空
    def on_clear(self):
        if len(self.widgets)<=0:
            self.update_layout()
            return
        list_revemo=[]
        for item in self.widgets:
            item.setParent(None)
            list_revemo.append(item)
        for item in list_revemo:
            self.widgets.remove(item)
        list_revemo.clear()
        self.widgets.clear()
        self.update_layout()

    def update_layout(self):
        """更新布局排列"""
        # 计算可用宽度（减去边距）
        available_width = self.width() - self.grid_layout.contentsMargins().left() \
                          - self.grid_layout.contentsMargins().right()

        # 计算每行可以容纳的控件数量
        widget_total_width = self.widget_width + self.horizontal_spacing
        widgets_per_row = max(1, available_width // widget_total_width)

        # 清除布局
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        # 重新排列控件
        for i, widget in enumerate(self.widgets):
            row = i // widgets_per_row
            col = i % widgets_per_row
            self.grid_layout.addWidget(widget, row, col)

        # 强制更新容器大小
        self.container.adjustSize()

    def resizeEvent(self, event):
        """重写resizeEvent以响应窗口大小变化"""
        super().resizeEvent(event)
        self.update_layout()
