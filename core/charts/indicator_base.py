#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标基础类
提供指标配置和公共功能的基础实现
"""

from typing import Dict, Any, Tuple
from abc import abstractmethod

from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.chart.item import ChartItem


class ConfigurableIndicator:
    """可配置指标的混入类"""
    
    def get_config_dialog(self, parent: QtWidgets.QWidget) -> QtWidgets.QDialog:
        """获取配置对话框 - 子类应重写此方法"""
        dialog = QtWidgets.QMessageBox(parent)
        dialog.setText("此指标暂不支持配置")
        return dialog
    
    def apply_config(self, config: Dict[str, Any]) -> None:
        """应用配置 - 子类应重写此方法"""
        pass
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置 - 子类应重写此方法"""
        return {}
    
    def create_config_dialog(self, parent: QtWidgets.QWidget, title: str, 
                           config_items: list) -> QtWidgets.QDialog:
        """
        创建标准配置对话框
        
        Args:
            parent: 父窗口
            title: 对话框标题
            config_items: 配置项列表，格式为 [(key, label, widget, current_value), ...]
        """
        dialog = QtWidgets.QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(350, len(config_items) * 50 + 100)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        widgets = {}
        
        # 创建配置项
        for key, label, widget_type, current_value in config_items:
            if widget_type == "spinbox":
                widget = QtWidgets.QSpinBox()
                if isinstance(current_value, dict):
                    widget.setRange(current_value.get("min", 1), current_value.get("max", 200))
                    widget.setValue(current_value.get("value", 20))
                else:
                    widget.setRange(1, 200)
                    widget.setValue(current_value)
            elif widget_type == "doublespinbox":
                widget = QtWidgets.QDoubleSpinBox()
                if isinstance(current_value, dict):
                    widget.setRange(current_value.get("min", 0.1), current_value.get("max", 10.0))
                    widget.setSingleStep(current_value.get("step", 0.1))
                    widget.setValue(current_value.get("value", 2.0))
                else:
                    widget.setRange(0.1, 10.0)
                    widget.setSingleStep(0.1)
                    widget.setValue(current_value)
            elif widget_type == "lineedit":
                widget = QtWidgets.QLineEdit()
                widget.setText(str(current_value))
            elif widget_type == "checkbox":
                widget = QtWidgets.QCheckBox()
                widget.setChecked(current_value)
            else:
                continue
            
            layout.addRow(label + ":", widget)
            widgets[key] = widget
        
        # 添加说明文本
        if hasattr(self, '_get_config_help_text'):
            help_text = self._get_config_help_text()
            if help_text:
                help_label = QtWidgets.QLabel(help_text)
                help_label.setWordWrap(True)
                help_label.setStyleSheet("QLabel { color: #666; font-size: 10px; margin-top: 10px; }")
                layout.addRow(help_label)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        reset_button = QtWidgets.QPushButton("重置默认")
        ok_button = QtWidgets.QPushButton("应用")
        cancel_button = QtWidgets.QPushButton("取消")
        
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addRow(button_layout)
        
        # 连接事件
        def reset_to_defaults():
            if hasattr(self, '_get_default_config'):
                default_config = self._get_default_config()
                for key, widget in widgets.items():
                    if key in default_config:
                        value = default_config[key]
                        if isinstance(widget, QtWidgets.QSpinBox):
                            widget.setValue(value)
                        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                            widget.setValue(value)
                        elif isinstance(widget, QtWidgets.QLineEdit):
                            widget.setText(str(value))
                        elif isinstance(widget, QtWidgets.QCheckBox):
                            widget.setChecked(value)
        
        def apply_settings():
            try:
                config = {}
                for key, widget in widgets.items():
                    if isinstance(widget, QtWidgets.QSpinBox):
                        config[key] = widget.value()
                    elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                        config[key] = widget.value()
                    elif isinstance(widget, QtWidgets.QLineEdit):
                        text = widget.text().strip()
                        # 尝试解析逗号分隔的数字列表
                        if ',' in text:
                            try:
                                config[key] = [int(x.strip()) for x in text.split(',') if x.strip()]
                            except ValueError:
                                config[key] = text
                        else:
                            config[key] = text
                    elif isinstance(widget, QtWidgets.QCheckBox):
                        config[key] = widget.isChecked()
                
                self.apply_config(config)
                
                # 显示成功提示
                ok_button.setText("✓ 已应用")
                ok_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
                
                # 2秒后恢复按钮
                QtCore.QTimer.singleShot(2000, lambda: (
                    ok_button.setText("应用"),
                    ok_button.setStyleSheet("")
                ))
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(dialog, "配置失败", f"应用设置时发生错误：\n{str(e)}")
        
        reset_button.clicked.connect(reset_to_defaults)
        ok_button.clicked.connect(apply_settings)
        cancel_button.clicked.connect(dialog.reject)
        
        # 保存widgets引用供外部使用
        dialog.config_widgets = widgets
        
        return dialog
