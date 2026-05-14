#!/usr/bin/env python3
"""
TIFF调色板转RGB - GUI版本
"""

import multiprocessing as mp
import os
import sys
import time
from multiprocessing import shared_memory, freeze_support
from typing import Tuple, List
import traceback

import numpy as np
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QSpinBox,
    QFileDialog, QMessageBox, QGroupBox, QProgressBar, QStyleFactory
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QTextCursor, QColor, QFont, QPalette

# 添加Cython模块路径
sys.path.append('.')
try:
    from palette_processor_cy import process_palette_block
except ImportError:
    print("警告: 未找到Cython模块，将使用Python版本")
    process_palette_block = None


def worker_process_py(
        shm_input_name: str,
        shm_output_name: str,
        input_shape: Tuple[int, int],
        output_shape: Tuple[int, int, int],
        palette_lut: np.ndarray,
        start_row: int,
        end_row: int
) -> float:
    """
    Python版本工作进程（Cython未编译时使用）
    注意：这必须是模块级函数，不能是类的方法
    """
    # 连接到共享内存
    shm_input = shared_memory.SharedMemory(name=shm_input_name)
    shm_output = shared_memory.SharedMemory(name=shm_output_name)

    # 创建数组视图
    input_array = np.ndarray(input_shape, dtype=np.uint8, buffer=shm_input.buf)
    output_array = np.ndarray(output_shape, dtype=np.uint8, buffer=shm_output.buf)

    start_time = time.time()

    # 处理当前块
    for y in range(start_row, end_row):
        row_data = input_array[y, :]
        for x in range(input_shape[1]):
            idx = row_data[x]
            if idx < 256:
                output_array[0, y, x] = palette_lut[idx, 0]
                output_array[1, y, x] = palette_lut[idx, 1]
                output_array[2, y, x] = palette_lut[idx, 2]

    elapsed = time.time() - start_time

    # 清理
    shm_input.close()
    shm_output.close()

    return elapsed


def worker_process_cy(
        shm_input_name: str,
        shm_output_name: str,
        input_shape: Tuple[int, int],
        output_shape: Tuple[int, int, int],
        palette_lut: np.ndarray,
        start_row: int,
        end_row: int
) -> float:
    """
    Cython版本工作进程
    注意：这必须是模块级函数，不能是类的方法
    """
    # 连接到共享内存
    shm_input = shared_memory.SharedMemory(name=shm_input_name)
    shm_output = shared_memory.SharedMemory(name=shm_output_name)

    # 创建数组视图
    input_array = np.ndarray(input_shape, dtype=np.uint8, buffer=shm_input.buf)
    output_array = np.ndarray(output_shape, dtype=np.uint8, buffer=shm_output.buf)

    start_time = time.time()

    # 调用Cython处理函数
    if process_palette_block is not None:
        process_palette_block(
            input_array,
            output_array,
            palette_lut,
            start_row,
            end_row
        )
    else:
        # 回退到Python版本
        for y in range(start_row, end_row):
            row_data = input_array[y, :]
            for x in range(input_shape[1]):
                idx = row_data[x]
                if idx < 256:
                    output_array[0, y, x] = palette_lut[idx, 0]
                    output_array[1, y, x] = palette_lut[idx, 1]
                    output_array[2, y, x] = palette_lut[idx, 2]

    elapsed = time.time() - start_time

    # 清理
    shm_input.close()
    shm_output.close()

    return elapsed


# 工作线程类
class ConversionThread(QThread):
    """转换工作线程"""

    # 定义信号
    log_signal = Signal(str, str)  # 消息, 颜色
    progress_signal = Signal(int)  # 进度百分比
    finished_signal = Signal(bool, str)  # 是否成功, 消息

    def __init__(self, input_path, output_path, proc_num):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.proc_num = proc_num
        self.is_running = False

    def run(self):
        """运行转换任务"""
        self.is_running = True
        try:
            self.convert_palette_geotiff()
        except Exception as e:
            self.log_signal.emit(f"转换失败: {str(e)}", "red")
            self.log_signal.emit(f"错误详情: {traceback.format_exc()}", "red")
            self.finished_signal.emit(False, str(e))
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False
        self.terminate()

    def log(self, message, color="black"):
        self.log_signal.emit(message, color)

    def create_shared_memory_blocks(self, input_path: str):
        """创建输入输出共享内存块"""
        image = Image.open(input_path)

        # 检查是否为调色板图像
        if image.mode != 'P':
            raise ValueError("输入文件不是调色板图像 (P mode)")

        data = np.array(image)
        input_shape = data.shape
        input_dtype = data.dtype

        palette = image.getpalette()
        if palette is None:
            raise ValueError("输入文件没有调色板")

        palette_lut = np.zeros((256, 3), dtype=np.uint8)

        # PIL的调色板是长度为768的列表 [R0, G0, B0, R1, G1, B1, ...]
        for i in range(256):
            idx = i * 3
            if idx + 2 < len(palette):
                palette_lut[i] = [palette[idx], palette[idx + 1], palette[idx + 2]]

        # 计算输出形状
        output_shape = (3, input_shape[0], input_shape[1])

        shm_input = shared_memory.SharedMemory(
            create=True,
            size=data.nbytes
        )
        input_array = np.ndarray(input_shape, dtype=input_dtype, buffer=shm_input.buf)
        np.copyto(input_array, data)

        shm_output = shared_memory.SharedMemory(
            create=True,
            size=int(np.prod(output_shape) * np.dtype(np.uint8).itemsize)
        )

        output_array = np.ndarray(output_shape, dtype=np.uint8, buffer=shm_output.buf)
        output_array[:] = 0

        # 保存元数据
        metadata = {
            'input_shape': input_shape,
            'output_shape': output_shape
        }

        image.close()
        return shm_input, shm_output, palette_lut, output_shape, metadata

    def divide_rows(self, total_rows: int, n_blocks: int) -> List[Tuple[int, int]]:
        """将行数分成块"""
        rows_per_block = total_rows // n_blocks
        blocks = []
        for i in range(n_blocks):
            start = i * rows_per_block
            end = start + rows_per_block if i < n_blocks - 1 else total_rows
            blocks.append((start, end))
        return blocks

    def convert_palette_geotiff(self):
        """主函数：转换调色板TIFF为RGB"""
        self.log(f"输入文件: {self.input_path}", "blue")
        self.log(f"输出文件: {self.output_path}", "blue")
        self.log(f"工作进程数: {self.proc_num}", "blue")
        self.log(f"使用Cython: {process_palette_block is not None}", "blue")

        # 1. 创建共享内存
        self.log("创建共享内存...", "darkblue")
        try:
            shm_input, shm_output, palette_lut, output_shape, metadata = \
                self.create_shared_memory_blocks(self.input_path)
        except Exception as e:
            self.log(f"错误: 创建共享内存失败 - {str(e)}", "red")
            raise

        input_shape = metadata['input_shape']
        total_rows = input_shape[0]

        # 2. 分块
        blocks = self.divide_rows(total_rows, self.proc_num)
        self.log(f"图像尺寸: {input_shape}", "darkblue")
        self.log(f"分块数量: {len(blocks)}", "darkblue")

        # 3. 准备进程参数
        args_list = []
        for start_row, end_row in blocks:
            args = (
                shm_input.name,
                shm_output.name,
                input_shape,
                output_shape,
                palette_lut,
                start_row,
                end_row
            )
            args_list.append(args)

        # 4. 启动进程池
        self.log("启动进程池...", "darkblue")
        start_time = time.time()

        try:
            # 使用spawn方法，安全
            with mp.get_context('spawn').Pool(processes=self.proc_num) as pool:
                if process_palette_block is not None:
                    results = pool.starmap(worker_process_cy, args_list)
                else:
                    results = pool.starmap(worker_process_py, args_list)
        except Exception as e:
            self.log(f"进程池错误: {str(e)}", "red")
            # 清理共享内存
            shm_input.close()
            shm_input.unlink()
            shm_output.close()
            shm_output.unlink()
            raise

        total_time = time.time() - start_time
        self.log(f"处理完成，总时间: {total_time:.3f}秒", "green")

        # 5. 从共享内存读取结果
        output_array = np.ndarray(
            output_shape,
            dtype=np.uint8,
            buffer=shm_output.buf
        ).copy()

        # 6. 保存
        self.log("保存结果...", "darkblue")

        # (3, H, W)->(H, W, 3)
        rgb_array = np.transpose(output_array, (1, 2, 0))

        rgb_image = Image.fromarray(rgb_array, mode='RGB')
        rgb_image.save(self.output_path)

        # 7. 清理共享内存
        shm_input.close()
        shm_input.unlink()
        shm_output.close()
        shm_output.unlink()

        self.log(f"转换完成!", "green")
        self.finished_signal.emit(True, "转换完成！")


# 主窗口类
class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.conversion_thread = None
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("TIFF调色板转RGB工具")
        self.setGeometry(100, 100, 800, 600)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 添加标题
        # title_label = QLabel("TIFF调色板转RGB转换器")
        # title_font = QFont()
        # title_font.setPointSize(16)
        # title_font.setBold(True)
        # title_label.setFont(title_font)
        # title_label.setAlignment(Qt.AlignCenter)
        # main_layout.addWidget(title_label)

        # 输入文件选择区域
        input_group = QGroupBox("输入文件")
        input_layout = QHBoxLayout()

        self.input_label = QLabel("TIFF文件:")
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText("请选择输入文件...")
        self.input_browse_btn = QPushButton("浏览...")
        self.input_browse_btn.clicked.connect(self.browse_input_file)

        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_path_edit, 1)
        input_layout.addWidget(self.input_browse_btn)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # 输出文件选择区域
        output_group = QGroupBox("输出文件")
        output_layout = QHBoxLayout()

        self.output_label = QLabel("RGB文件:")
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("请选择输出文件...")
        self.output_browse_btn = QPushButton("浏览...")
        self.output_browse_btn.clicked.connect(self.browse_output_file)

        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path_edit, 1)
        output_layout.addWidget(self.output_browse_btn)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # 参数设置区域
        param_group = QGroupBox("参数设置")
        param_layout = QHBoxLayout()

        self.proc_label = QLabel("并发进程数:")
        self.proc_spinbox = QSpinBox()
        self.proc_spinbox.setMinimum(1)
        self.proc_spinbox.setMaximum(mp.cpu_count())
        self.proc_spinbox.setValue(max(1, mp.cpu_count() // 2))
        self.proc_spinbox.setToolTip(f"CPU核心数: {mp.cpu_count()}")

        param_layout.addWidget(self.proc_label)
        param_layout.addWidget(self.proc_spinbox)
        param_layout.addStretch()
        param_group.setLayout(param_layout)
        main_layout.addWidget(param_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setFixedHeight(40)
        self.convert_btn.clicked.connect(self.start_conversion)
        self.convert_btn.setEnabled(False)

        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.clicked.connect(self.clear_log)

        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.clear_btn)
        main_layout.addLayout(button_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 日志区域
        log_group = QGroupBox("转换日志")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))

        # 设置背景色
        palette = self.log_text.palette()
        palette.setColor(QPalette.Base, QColor(240, 240, 240))
        self.log_text.setPalette(palette)

        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)

        # 监听输入路径变化
        self.input_path_edit.textChanged.connect(self.validate_inputs)
        self.output_path_edit.textChanged.connect(self.validate_inputs)

        # 添加状态栏
        self.statusBar().showMessage("就绪")

    def browse_input_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择TIFF文件",
            "",
            "TIFF Files (*.tif *.tiff);;All Files (*.*)"
        )

        if file_path:
            self.input_path_edit.setText(file_path)

            # 如果输出路径为空，自动生成输出路径
            if not self.output_path_edit.text():
                base, ext = os.path.splitext(file_path)
                output_path = f"{base}_rgb{ext}"
                self.output_path_edit.setText(output_path)

    def browse_output_file(self):
        """浏览输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存RGB文件",
            self.output_path_edit.text() or "",
            "TIFF Files (*.tif *.tiff);;All Files (*.*)"
        )

        if file_path:
            self.output_path_edit.setText(file_path)

    def validate_inputs(self):
        """验证输入是否有效"""
        input_path = self.input_path_edit.text().strip()
        output_path = self.output_path_edit.text().strip()

        is_valid = (
                input_path != "" and
                output_path != "" and
                os.path.exists(input_path)
        )

        self.convert_btn.setEnabled(is_valid)
        return is_valid

    def start_conversion(self):
        """开始转换"""
        if not self.validate_inputs():
            QMessageBox.warning(self, "警告", "请先选择有效的输入输出文件路径！")
            return

        input_path = self.input_path_edit.text().strip()
        output_path = self.output_path_edit.text().strip()
        proc_num = self.proc_spinbox.value()

        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            QMessageBox.critical(self, "错误", f"输入文件不存在: {input_path}")
            return

        # 检查输出目录是否存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建输出目录: {str(e)}")
                return

        # 检查输出文件是否已存在
        if os.path.exists(output_path):
            reply = QMessageBox.question(
                self,
                "确认",
                f"输出文件已存在:\n{output_path}\n是否覆盖？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 禁用控件
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("转换中...")
        self.input_browse_btn.setEnabled(False)
        self.output_browse_btn.setEnabled(False)
        self.proc_spinbox.setEnabled(False)
        self.clear_btn.setEnabled(False)

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 清空日志
        self.log_text.clear()
        self.log_message("开始转换...", "blue")
        self.log_message(f"输入文件: {input_path}", "darkblue")
        self.log_message(f"输出文件: {output_path}", "darkblue")
        self.log_message(f"并发进程数: {proc_num}", "darkblue")

        # 创建并启动工作线程
        self.conversion_thread = ConversionThread(input_path, output_path, proc_num)
        self.conversion_thread.log_signal.connect(self.log_message)
        self.conversion_thread.progress_signal.connect(self.update_progress)
        self.conversion_thread.finished_signal.connect(self.conversion_finished)
        self.conversion_thread.start()

        # 更新状态栏
        self.statusBar().showMessage("转换进行中...")

    def conversion_finished(self, success, message):
        """转换完成回调"""
        # 启用控件
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("开始转换")
        self.input_browse_btn.setEnabled(True)
        self.output_browse_btn.setEnabled(True)
        self.proc_spinbox.setEnabled(True)
        self.clear_btn.setEnabled(True)

        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)

        if success:
            self.log_message(message, "green")
            self.statusBar().showMessage("转换完成")

            # 询问是否打开输出目录
            reply = QMessageBox.question(
                self,
                "转换完成",
                "转换已完成！\n是否打开输出文件所在目录？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                output_path = self.output_path_edit.text()
                output_dir = os.path.dirname(output_path)
                if os.path.exists(output_dir):
                    if sys.platform == "win32":
                        os.startfile(output_dir)
                    elif sys.platform == "darwin":
                        os.system(f'open "{output_dir}"')
                    else:
                        os.system(f'xdg-open "{output_dir}"')
        else:
            self.log_message(f"转换失败: {message}", "red")
            self.statusBar().showMessage("转换失败")

        # 重置线程
        self.conversion_thread = None

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def log_message(self, message, color="black"):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())

        # 使用HTML格式显示颜色
        html_message = f'<span style="color: {color}">[{timestamp}] {message}</span>'

        # 保存当前滚动位置
        scrollbar = self.log_text.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        # 添加消息
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertHtml(html_message + "<br>")

        # 如果之前已经在底部，保持滚动到底部
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.statusBar().showMessage("日志已清空")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.conversion_thread and self.conversion_thread.is_running:
            reply = QMessageBox.question(
                self,
                "确认",
                "转换正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                if self.conversion_thread:
                    self.conversion_thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# 主程序
def main():
    """主程序入口"""
    # 初始化多进程支持
    freeze_support()
    Image.MAX_IMAGE_PIXELS = None

    # 在Windows上，multiprocessing需要使用spawn方法
    if sys.platform == "win32":
        mp.set_start_method('spawn', force=True)

    # 创建应用
    app = QApplication(sys.argv)
    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setApplicationName("TIFF调色板转RGB工具")

    # 创建主窗口
    window = MainWindow()
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()