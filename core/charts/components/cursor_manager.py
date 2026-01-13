#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光标管理器
处理十字光标的显示、移动和标签更新
"""

import pyqtgraph as pg
from vnpy.trader.ui import QtCore, QtWidgets


class CursorManager:
    """
    光标管理器
    负责管理十字光标在多个plot之间的正确显示
    """

    def __init__(self, chart_widget):
        self.chart = chart_widget
        self._cursor = None
        self._x_label_plot_name = None

    def setup(self):
        """设置光标修复"""
        self._cursor = self.chart._cursor
        if not self._cursor:
            return

        self._setup_z_values()
        self._setup_mouse_moved()
        self._setup_update_label()
        self._setup_update_line()
        self._setup_update_info()
        self._setup_cursor_style()

    def _setup_z_values(self):
        """设置光标元素的z值"""
        for v_line in self._cursor._v_lines.values():
            v_line.setZValue(-1)
        for h_line in self._cursor._h_lines.values():
            h_line.setZValue(-1)

        if hasattr(self._cursor, '_x_label'):
            self._cursor._x_label.setZValue(1000)
        for y_label in self._cursor._y_labels.values():
            y_label.setZValue(1000)

    def _setup_mouse_moved(self):
        """设置鼠标移动处理"""
        chart = self.chart
        cursor = self._cursor

        def fixed_mouse_moved(evt):
            if not chart._manager.get_count():
                return

            pos = evt
            found_plot = False

            for plot_name, view in cursor._views.items():
                if plot_name in chart._plots and not chart._plots[plot_name].isVisible():
                    continue

                rect = view.sceneBoundingRect()
                if rect.contains(pos):
                    mouse_point = view.mapSceneToView(pos)
                    cursor._x = int(mouse_point.x())
                    cursor._y = mouse_point.y()
                    cursor._plot_name = plot_name
                    found_plot = True
                    break

            if not found_plot and "candle" in cursor._views:
                view = cursor._views["candle"]
                rect = view.sceneBoundingRect()
                if rect.contains(pos):
                    mouse_point = view.mapSceneToView(pos)
                    cursor._x = int(mouse_point.x())
                    cursor._y = mouse_point.y()
                    cursor._plot_name = "candle"
                    found_plot = True

            if found_plot:
                cursor._update_line()
                cursor._update_label()
                cursor.update_info()

        cursor._mouse_moved = fixed_mouse_moved

    def _setup_update_label(self):
        """设置标签更新方法"""
        chart = self.chart
        cursor = self._cursor

        # 初始化x_label所在的plot名称
        if not hasattr(cursor, '_x_label_plot_name'):
            all_plot_names = list(chart._plots.keys())
            cursor._x_label_plot_name = all_plot_names[-1] if all_plot_names else None

        def fixed_update_label():
            visible_plots = [
                name for name in chart._plots.keys() 
                if chart._plots[name].isVisible()
            ]

            if not visible_plots:
                return

            bottom_plot_name = visible_plots[-1]
            bottom_plot = chart._plots[bottom_plot_name]

            if bottom_plot_name not in cursor._views:
                return

            bottom_view = cursor._views[bottom_plot_name]
            x_label = cursor._x_label
            current_label_plot = getattr(cursor, '_x_label_plot_name', None)

            # 移动x_label到正确的plot
            if current_label_plot != bottom_plot_name:
                if current_label_plot and current_label_plot in chart._plots:
                    old_plot = chart._plots[current_label_plot]
                    try:
                        if x_label in old_plot.items:
                            old_plot.removeItem(x_label)
                    except Exception:
                        pass

                try:
                    if x_label not in bottom_plot.items:
                        bottom_plot.addItem(x_label, ignoreBounds=True)
                except Exception:
                    pass

                cursor._x_label_plot_name = bottom_plot_name
                x_label.setZValue(1000)

            axis_width = bottom_plot.getAxis("right").width()
            axis_height = bottom_plot.getAxis("bottom").height()
            axis_offset = QtCore.QPointF(axis_width, axis_height)

            bottom_right = bottom_view.mapSceneToView(
                bottom_view.sceneBoundingRect().bottomRight() - axis_offset
            )

            # 更新y轴标签
            for plot_name, label in cursor._y_labels.items():
                if plot_name not in chart._plots or not chart._plots[plot_name].isVisible():
                    label.hide()
                    continue

                if plot_name == cursor._plot_name:
                    label.setText(str(cursor._y))
                    label.show()
                    label.setPos(bottom_right.x(), cursor._y)
                else:
                    label.hide()

            # 更新x轴标签
            dt = chart._manager.get_datetime(cursor._x)
            if dt:
                x_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                x_label.setText(f"Index: {cursor._x}")
            x_label.show()
            x_label.setPos(cursor._x, bottom_right.y())
            x_label.setAnchor((0, 0))

        cursor._update_label = fixed_update_label

    def _setup_update_line(self):
        """设置线条更新方法"""
        chart = self.chart
        cursor = self._cursor

        def fixed_update_line():
            for v_line in cursor._v_lines.values():
                if hasattr(v_line, 'prepareGeometryChange'):
                    v_line.prepareGeometryChange()
                v_line.setPos(cursor._x)
                v_line.show()

            for plot_name, h_line in cursor._h_lines.items():
                if plot_name in chart._plots and chart._plots[plot_name].isVisible():
                    if plot_name == cursor._plot_name:
                        if hasattr(h_line, 'prepareGeometryChange'):
                            h_line.prepareGeometryChange()
                        h_line.setPos(cursor._y)
                        h_line.show()
                    else:
                        h_line.hide()
                else:
                    h_line.hide()

        cursor._update_line = fixed_update_line

    def _setup_update_info(self):
        """设置信息更新方法"""
        chart = self.chart
        cursor = self._cursor

        def fixed_update_info():
            buf = {}

            for item, plot in cursor._item_plot_map.items():
                item_info_text = item.get_info_text(cursor._x)
                if plot not in buf:
                    buf[plot] = item_info_text
                else:
                    if item_info_text:
                        buf[plot] += "\n\n" + item_info_text

            for plot_name, plot in chart._plots.items():
                if not plot.isVisible():
                    if plot_name in cursor._infos:
                        cursor._infos[plot_name].hide()
                    continue

                if plot not in buf:
                    continue

                plot_info_text = buf[plot]
                info = cursor._infos[plot_name]
                info.setText(plot_info_text)
                info.show()

                view = cursor._views[plot_name]
                top_left = view.mapSceneToView(view.sceneBoundingRect().topLeft())
                info.setPos(top_left)

        cursor.update_info = fixed_update_info

    def _setup_cursor_style(self):
        """设置光标样式"""
        cursor_pen = pg.mkPen(
            color=(255, 255, 255, 150), 
            width=1, 
            style=QtCore.Qt.PenStyle.DashLine
        )
        
        for v_line in self._cursor._v_lines.values():
            v_line.setPen(cursor_pen)
            v_line.setCacheMode(QtWidgets.QGraphicsItem.NoCache)
        
        for h_line in self._cursor._h_lines.values():
            h_line.setPen(cursor_pen)
            h_line.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

    def relocate_x_label(self):
        """重新定位x轴标签到最后一个可见的plot"""
        if not self._cursor or not hasattr(self._cursor, '_x_label'):
            return

        visible_plots = [
            name for name in self.chart._plots.keys() 
            if self.chart._plots[name].isVisible()
        ]

        if not visible_plots:
            return

        bottom_plot_name = visible_plots[-1]
        bottom_plot = self.chart._plots[bottom_plot_name]
        current_label_plot = getattr(self._cursor, '_x_label_plot_name', None)

        if current_label_plot == bottom_plot_name:
            self._cursor._x_label.setZValue(1000)
            self._cursor._x_label.show()
            return

        x_label = self._cursor._x_label

        if current_label_plot and current_label_plot in self.chart._plots:
            old_plot = self.chart._plots[current_label_plot]
            try:
                if x_label in old_plot.items:
                    old_plot.removeItem(x_label)
            except Exception:
                pass

        try:
            if x_label not in bottom_plot.items:
                bottom_plot.addItem(x_label, ignoreBounds=True)
        except Exception:
            pass

        self._cursor._x_label_plot_name = bottom_plot_name
        x_label.setZValue(1000)
        x_label.show()
