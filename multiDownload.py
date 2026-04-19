import urllib.request
import subprocess
import os
import random
import math
import sys
import concurrent.futures
import threading
import traceback
import time
from datetime import datetime
from typing import List, Tuple, Optional
from urllib.error import URLError, HTTPError
from PySide2.QtCore import QObject, Signal, Slot, QThread,Qt
from PySide2.QtWidgets import *


# 线程安全的计数器
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def get(self):
        with self.lock:
            return self.value


# User-Agent列表
agents = [
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1'
]


class GoogleMapDownloader(QObject):
    """Google地图下载器，带PySide2信号支持"""

    # 定义信号
    error_occurred = Signal(str, str)  # 错误信号: (错误标题, 错误详情)
    progress_updated = Signal(int, int, int)  # 进度信号: (当前进度, 总数, 成功数)
    download_complete = Signal(dict)  # 完成信号: 结果字典
    status_changed = Signal(str)  # 状态变化信号

    def __init__(self, level, LT_lat, LT_lon, RB_lat, RB_lon, root_dir, max_workers=50,
                 parent=None):
        super().__init__(parent)
        self.level = level
        self.LT_lat = LT_lat
        self.LT_lon = LT_lon
        self.RB_lat = RB_lat
        self.RB_lon = RB_lon
        self.root_dir = root_dir
        self.max_workers = max_workers

        # 线程安全计数器
        self.total_downloads = ThreadSafeCounter()
        self.total_errors = ThreadSafeCounter()
        self.total_tasks = 0
        self.success_tasks = 0

        # 下载控制标志
        self._stop_requested = False
        self._download_thread = None

    def stop_download(self):
        """停止下载"""
        self._stop_requested = True
        self.status_changed.emit("正在停止下载...")

    # 经纬度反算切片行列号 3857坐标系
    def deg2num(self, lat_deg, lon_deg, zoom):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int(
            (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    def download_single_image(self, Tpath: str, Spath: str, x: int, y: int,
                              max_retries: int = 3) -> bool:
        """
        下载单个图片，带重试机制
        返回: True表示成功，False表示失败
        """
        # 如果请求停止，立即返回
        if self._stop_requested:
            return False

        # 如果文件已存在，跳过下载
        if os.path.isfile(Spath):
            print(f"文件已存在，跳过: {x}_{y}")
            return True

        # 创建目录（如果不存在）
        try:
            os.makedirs(os.path.dirname(Spath), exist_ok=True)
        except Exception as e:
            error_msg = f"创建目录失败: {os.path.dirname(Spath)}"
            self.error_occurred.emit("目录创建错误", f"{error_msg}\n错误详情: {str(e)}")
            return False

        for retry in range(max_retries):
            try:
                req = urllib.request.Request(Tpath)
                req.add_header('User-Agent', random.choice(agents))

                # 设置超时
                response = urllib.request.urlopen(req, timeout=30)

                # 读取数据
                data = response.read()

                # 写入文件
                with open(Spath, 'wb') as f:
                    f.write(data)

                # 更新计数器
                downloaded = self.total_downloads.increment()
                self.success_tasks += 1

                # 每下载10个文件发送一次进度更新
                if downloaded % 10 == 0:
                    self.progress_updated.emit(downloaded, self.total_tasks, self.success_tasks)

                return True

            except (URLError, HTTPError, ConnectionError, TimeoutError) as e:
                error_type = type(e).__name__
                if retry < max_retries - 1:
                    wait_time = 2 ** retry
                    error_msg = f"下载失败 {x}_{y}, 第{retry + 1}次重试，等待{wait_time}秒"
                    self.error_occurred.emit(f"{error_type}-可恢复错误",
                                             f"{error_msg}\n错误详情: {str(e)}")
                    time.sleep(wait_time)
                else:
                    self.total_errors.increment()
                    error_msg = f"下载失败 {x}_{y}，重试{max_retries}次后放弃"
                    self.error_occurred.emit(f"{error_type}-最终失败",
                                             f"{error_msg}\n错误详情: {str(e)}")
                    return False
            except Exception as e:
                self.total_errors.increment()
                error_type = type(e).__name__
                error_msg = f"未知错误 {x}_{y}"
                error_trace = traceback.format_exc()
                self.error_occurred.emit(f"{error_type}-未知错误",
                                         f"{error_msg}\n错误详情: {str(e)}\n堆栈跟踪:\n{error_trace}")
                return False

        return False

    def download_task_wrapper(self, args: Tuple[str, str, int, int]) -> Tuple[int, int, bool]:
        """
        包装下载任务，方便线程池调用
        返回: (x, y, 是否成功)
        """
        Tpath, Spath, x, y = args
        success = self.download_single_image(Tpath, Spath, x, y)
        return x, y, success

    def parallel_download(self, tasks: List[Tuple[str, str, int, int]]) -> dict:
        """
        并行下载多个图片
        """
        self._stop_requested = False

        results = {
            'total': len(tasks),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        self.total_tasks = len(tasks)
        self.success_tasks = 0
        self.total_downloads = ThreadSafeCounter()
        self.total_errors = ThreadSafeCounter()

        self.status_changed.emit(f"开始下载 {len(tasks)} 个文件，使用 {self.max_workers} 个线程...")

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {
                    executor.submit(self.download_task_wrapper, task): task
                    for task in tasks
                }

                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_task):
                    # 检查是否请求停止
                    if self._stop_requested:
                        self.status_changed.emit("下载被用户中断")
                        results['interrupted'] = True
                        # 取消所有未完成的任务
                        for f in future_to_task:
                            f.cancel()
                        break

                    task = future_to_task[future]
                    Tpath, Spath, x, y = task

                    try:
                        x_result, y_result, success = future.result(timeout=5)
                        if success:
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append(f"下载失败: {x}_{y}")
                    except concurrent.futures.TimeoutError:
                        results['failed'] += 1
                        error_msg = f"任务超时: {x}_{y}"
                        results['errors'].append(error_msg)
                        self.error_occurred.emit("任务超时", error_msg)
                    except Exception as e:
                        results['failed'] += 1
                        error_msg = f"任务执行异常: {x}_{y}, 错误: {str(e)}"
                        results['errors'].append(error_msg)
                        self.error_occurred.emit("任务异常",
                                                 f"{error_msg}\n堆栈跟踪:\n{traceback.format_exc()}")

                # 发送最终进度
                self.progress_updated.emit(
                    self.total_downloads.get(),
                    self.total_tasks,
                    self.success_tasks
                )

        except Exception as e:
            error_msg = f"并行下载过程发生错误: {str(e)}"
            self.error_occurred.emit("并行下载错误",
                                     f"{error_msg}\n堆栈跟踪:\n{traceback.format_exc()}")
            results['failed'] = self.total_tasks
            results['errors'].append(error_msg)

        return results

    def start_download(self):
        """开始下载的主方法"""
        try:
            self._stop_requested = False

            zoom = self.level
            lefttop = self.deg2num(self.LT_lat, self.LT_lon, zoom)
            rightbottom = self.deg2num(self.RB_lat, self.RB_lon, zoom)

            info_msg = f"""
            缩放级别: {zoom}
            X范围: {lefttop[0]} 到 {rightbottom[0]}
            Y范围: {lefttop[1]} 到 {rightbottom[1]}
            X方向切片数: {rightbottom[0] - lefttop[0]}
            Y方向切片数: {rightbottom[1] - lefttop[1]}
            """
            self.status_changed.emit(info_msg)

            # 准备所有下载任务
            tasks = []
            for x in range(lefttop[0], rightbottom[0]):
                if self._stop_requested:
                    break

                path = os.path.join(self.root_dir, str(zoom), str(x))

                for y in range(lefttop[1], rightbottom[1]):
                    tilepath = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"
                    filepath = os.path.join(path, f"{y}.png")
                    tasks.append((tilepath, filepath, x, y))

            if self._stop_requested:
                self.status_changed.emit("下载被取消")
                return

            self.status_changed.emit(f"总共 {len(tasks)} 个切片需要下载")

            # 并行下载
            start_time = time.time()
            results = self.parallel_download(tasks)
            end_time = time.time()

            if self._stop_requested:
                self.status_changed.emit("下载被中断")
                return

            # 保存错误日志
            if results.get('errors'):
                error_file = os.path.join(self.root_dir, f"download_errors_zoom{zoom}.txt")
                try:
                    with open(error_file, 'w', encoding='utf-8') as f:
                        for error in results['errors']:
                            f.write(error + "\n")
                    self.status_changed.emit(f"详细错误日志已保存到: {error_file}")
                except Exception as e:
                    self.error_occurred.emit("保存错误日志失败", str(e))

            # 发送完成信号
            results['elapsed_time'] = end_time - start_time
            self.download_complete.emit(results)

        except Exception as e:
            error_msg = f"下载过程发生错误: {str(e)}"
            self.error_occurred.emit("下载错误",
                                     f"{error_msg}\n堆栈跟踪:\n{traceback.format_exc()}")



class DownloadManager:
    """下载管理器，用于在PySide2界面中管理下载"""

    def __init__(self, parent_widget=None):
        self.parent_widget = parent_widget
        self.downloader = None
        self.download_thread = None

    def start_download(self, level, LT_lat, LT_lon, RB_lat, RB_lon, root_dir, max_workers=50):
        """开始下载"""
        # 创建下载器
        self.downloader = GoogleMapDownloader(
            level, LT_lat, LT_lon, RB_lat, RB_lon, root_dir, max_workers
        )

        # 创建线程
        self.download_thread = QThread()
        self.downloader.moveToThread(self.download_thread)

        # 连接信号
        self.downloader.error_occurred.connect(self.on_download_error)
        self.downloader.progress_updated.connect(self.on_download_progress)
        self.downloader.download_complete.connect(self.on_download_complete)
        self.downloader.status_changed.connect(self.on_status_changed)

        # 连接线程信号
        self.download_thread.started.connect(self.downloader.start_download)
        self.download_thread.finished.connect(self.on_thread_finished)

        # 启动线程
        self.download_thread.start()

    def stop_download(self):
        """停止下载"""
        if self.downloader:
            self.downloader.stop_download()

    def on_download_error(self, error_title, error_detail):
        """处理下载错误"""
        if self.parent_widget:
            # 可以使用QMessageBox显示错误
            from PySide2.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.parent_widget,
                f"下载错误: {error_title}",
                error_detail
            )
        else:
            print(f"[ERROR] {error_title}: {error_detail}")

    def on_download_progress(self, current, total, success):
        """处理下载进度"""
        if self.parent_widget:
            # 更新界面进度条等
            pass
        print(f"进度: {current}/{total} (成功: {success})")

    def on_download_complete(self, results):
        """处理下载完成"""
        if self.parent_widget:
            # 显示完成信息
            from PySide2.QtWidgets import QMessageBox
            QMessageBox.information(
                self.parent_widget,
                "下载完成",
                f"下载完成!\n总耗时: {results.get('elapsed_time', 0):.2f}秒\n"
                f"成功: {results.get('success', 0)}\n"
                f"失败: {results.get('failed', 0)}"
            )

        print(f"下载完成! 成功: {results.get('success', 0)}, 失败: {results.get('failed', 0)}")

        # 停止线程
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.quit()
            self.download_thread.wait()

    def on_status_changed(self, status):
        """处理状态变化"""
        if self.parent_widget:
            # 更新状态栏等
            pass
        print(f"状态: {status}")

    def on_thread_finished(self):
        """线程完成"""
        if self.download_thread:
            self.download_thread.quit()
            self.download_thread.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google 卫星地图瓦片下载器")
        self.resize(950, 750)

        # 使用 parent_widget=None，避免 DownloadManager 重复弹窗，
        # 所有 UI 反馈统一由 MainWindow 处理
        self.download_manager = DownloadManager(parent_widget=None)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ==================== 参数设置区 ====================
        param_group = QGroupBox("下载参数")
        form_layout = QFormLayout(param_group)

        self.level_spin = QSpinBox()
        self.level_spin.setRange(1, 22)
        self.level_spin.setValue(16)
        form_layout.addRow("缩放级别 (1-22):", self.level_spin)

        self.lt_lat_spin = QDoubleSpinBox()
        self.lt_lat_spin.setRange(-90.0, 90.0)
        self.lt_lat_spin.setDecimals(6)
        self.lt_lat_spin.setValue(36.161000)
        form_layout.addRow("左上角纬度:", self.lt_lat_spin)

        self.lt_lon_spin = QDoubleSpinBox()
        self.lt_lon_spin.setRange(-180.0, 180.0)
        self.lt_lon_spin.setDecimals(6)
        self.lt_lon_spin.setValue(103.553300)
        form_layout.addRow("左上角经度:", self.lt_lon_spin)

        self.rb_lat_spin = QDoubleSpinBox()
        self.rb_lat_spin.setRange(-90.0, 90.0)
        self.rb_lat_spin.setDecimals(6)
        self.rb_lat_spin.setValue(36.020300)
        form_layout.addRow("右下角纬度:", self.rb_lat_spin)

        self.rb_lon_spin = QDoubleSpinBox()
        self.rb_lon_spin.setRange(-180.0, 180.0)
        self.rb_lon_spin.setDecimals(6)
        self.rb_lon_spin.setValue(103.955700)
        form_layout.addRow("右下角经度:", self.rb_lon_spin)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请选择瓦片保存目录...")
        self.path_edit.setText(os.path.join("D:\\", "satellite") + os.sep)
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setFixedWidth(120)
        self.browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        form_layout.addRow("保存路径:", path_layout)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 4096)
        self.workers_spin.setValue(512)
        form_layout.addRow("并发线程数:", self.workers_spin)

        main_layout.addWidget(param_group)

        # ==================== 进度显示区 ====================
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%  (%v / %m)")
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪 — 请设置参数后点击“开始下载”")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)

        main_layout.addWidget(progress_group)

        # ==================== 日志显示区 ====================
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group, 1)  # 日志区占据主要伸缩空间

        # ==================== 按钮区 ====================
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.start_btn = QPushButton("▶ 开始下载")
        self.start_btn.setFixedHeight(34)
        self.start_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ 停止下载")
        self.stop_btn.setFixedHeight(34)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        btn_layout.addWidget(self.stop_btn)

        self.open_dir_btn = QPushButton("📂 打开目录")
        self.open_dir_btn.setFixedHeight(34)
        self.open_dir_btn.clicked.connect(self.open_save_directory)
        btn_layout.addWidget(self.open_dir_btn)

        self.clear_log_btn = QPushButton("🗑 清空日志")
        self.clear_log_btn.setFixedHeight(34)
        self.clear_log_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_log_btn)

        main_layout.addLayout(btn_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                padding-bottom: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QPushButton {
                padding: 4px 16px;
                font-weight: 500;
            }
            QPushButton:disabled {
                color: #888888;
            }
            QTextEdit {
                font-family: "Microsoft YaHei Mono", Consolas, "Courier New", monospace;
                font-size: 12px;
                background-color: #fafafa;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QProgressBar {
                text-align: center;
                height: 22px;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QDoubleSpinBox, QSpinBox, QLineEdit {
                padding: 3px;
            }
        """)

    # ==================== 功能槽函数 ====================

    def browse_directory(self):
        current = self.path_edit.text().strip() or "."
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录", current)
        if dir_path:
            self.path_edit.setText(os.path.normpath(dir_path) + os.sep)

    def open_save_directory(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "提示", "请先设置保存路径")
            return
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建目录：{e}")
                return
        norm_path = os.path.normpath(path)
        if sys.platform == "win32":
            os.startfile(norm_path)
        else:
            subprocess.run(["xdg-open", norm_path])

    def clear_log(self):
        self.log_text.clear()

    def append_log(self, message, color="#333333"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        html = (f'<span style="color:#999999">[{timestamp}]</span> '
                f'<span style="color:{color}">{message}</span>')
        self.log_text.append(html)

    def validate_inputs(self):
        lt_lat = self.lt_lat_spin.value()
        lt_lon = self.lt_lon_spin.value()
        rb_lat = self.rb_lat_spin.value()
        rb_lon = self.rb_lon_spin.value()
        path = self.path_edit.text().strip()

        if not path:
            QMessageBox.warning(self, "输入错误", "请指定瓦片保存路径")
            return False
        if lt_lat <= rb_lat:
            QMessageBox.warning(self, "输入错误",
                                "左上角纬度必须大于右下角纬度（请确认地理范围是否正确）")
            return False
        if lt_lon >= rb_lon:
            QMessageBox.warning(self, "输入错误",
                                "左上角经度必须小于右下角经度（请确认地理范围是否正确）")
            return False

        # 尝试创建目录验证路径有效性
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存路径无效或无法创建：{e}")
            return False
        return True

    def start_download(self):
        if not self.validate_inputs():
            return

        level = self.level_spin.value()
        lt_lat = self.lt_lat_spin.value()
        lt_lon = self.lt_lon_spin.value()
        rb_lat = self.rb_lat_spin.value()
        rb_lon = self.rb_lon_spin.value()
        root_dir = self.path_edit.text().strip()
        max_workers = self.workers_spin.value()

        # 重置 UI 状态
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(False)
        self.status_label.setText("正在准备任务...")
        self.status_bar.showMessage("下载中...")

        self.append_log("=" * 45, "#666666")
        self.append_log("启动下载任务", "#0066cc")
        self.append_log(f"缩放级别: {level}  |  线程数: {max_workers}", "#555555")
        self.append_log(f"范围: ({lt_lat:.6f}, {lt_lon:.6f}) → ({rb_lat:.6f}, {rb_lon:.6f})",
                        "#555555")
        self.append_log(f"保存路径: {root_dir}", "#555555")
        self.append_log("=" * 45, "#666666")

        # 启动后台下载
        self.download_manager.start_download(
            level, lt_lat, lt_lon, rb_lat, rb_lon, root_dir, max_workers
        )

        # 将下载器信号连接到主界面（DownloadManager 内部已处理流程，这里补充 UI 反馈）
        d = self.download_manager.downloader
        if d:
            d.error_occurred.connect(self.on_downloader_error)
            d.progress_updated.connect(self.on_downloader_progress)
            d.download_complete.connect(self.on_downloader_complete)
            d.status_changed.connect(self.on_downloader_status)

    def stop_download(self):
        self.append_log("用户请求停止下载...", "#ff6600")
        self.download_manager.stop_download()
        # 由于手动中断不会触发 download_complete，需手动恢复按钮
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(True)
        self.status_label.setText("已停止")
        self.status_bar.showMessage("已停止")

    def on_downloader_error(self, error_title, error_detail):
        # 日志中只显示简要信息，防止堆栈跟踪刷屏
        self.append_log(f"[错误] {error_title}", "#cc0000")
        if len(error_detail) < 180:
            self.append_log(error_detail, "#cc0000")

    def on_downloader_progress(self, current, total, success):
        if total > 0:
            self.progress_bar.setValue(int(current / total * 100))
        self.status_label.setText(f"正在下载: {current} / {total}  (成功 {success})")
        self.status_bar.showMessage(f"进度: {current}/{total}")

    def on_downloader_complete(self, results):
        elapsed = results.get("elapsed_time", 0)
        success_cnt = results.get("success", 0)
        failed_cnt = results.get("failed", 0)

        self.progress_bar.setValue(100)
        self.append_log("=" * 45, "#666666")
        self.append_log("下载任务结束", "#009900")
        self.append_log(f"总耗时: {elapsed:.2f} 秒", "#555555")
        self.append_log(f"成功: {success_cnt}  |  失败: {failed_cnt}", "#555555")
        self.append_log("=" * 45, "#666666")

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(True)
        self.status_label.setText(
            f"完成 — 成功 {success_cnt}, 失败 {failed_cnt}, 耗时 {elapsed:.1f}s"
        )
        self.status_bar.showMessage("下载完成")

        if failed_cnt > 0:
            QMessageBox.warning(self, "下载完成",
                                f"任务已完成，但存在 {failed_cnt} 个文件下载失败。\n"
                                f"总耗时: {elapsed:.2f} 秒\n"
                                f"详细错误请查看日志文件及上方日志窗口。")
        else:
            QMessageBox.information(self, "下载完成",
                                    f"全部下载成功！\n总耗时: {elapsed:.2f} 秒")

    def on_downloader_status(self, status):
        # 处理内部状态消息，特别是“被中断/被取消”等需要恢复 UI 的场景
        clean = status.strip().replace("\n", " | ")
        if not clean:
            return

        if "被中断" in clean or "被取消" in clean:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.clear_log_btn.setEnabled(True)
            self.status_label.setText("下载已中断")
            self.status_bar.showMessage("已中断")

        self.append_log(clean, "#444444")

    def closeEvent(self, event):
        thread = self.download_manager.download_thread
        if thread and thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "当前有下载任务正在进行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.download_manager.stop_download()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    # 测试下载器
    # downloader = GoogleMapDownloader(
    #     level=10,
    #     LT_lat=36.1610,
    #     LT_lon=103.5533,
    #     RB_lat=36.0203,
    #     RB_lon=103.9557,
    #     root_dir="D:\\satellite\\",
    #     max_workers=20
    # )


    # 连接信号到控制台输出
    def on_error(title, detail):
        print(f"\n[错误] {title}: {detail}")


    def on_progress(current, total, success):
        print(f"\r进度: {current}/{total} (成功: {success})", end="")


    def on_complete(results):
        print(f"\n下载完成!")
        print(f"总耗时: {results.get('elapsed_time', 0):.2f}秒")
        print(f"成功: {results.get('success', 0)}")
        print(f"失败: {results.get('failed', 0)}")


    def on_status(status):
        print(f"[状态] {status}")


    # downloader.error_occurred.connect(on_error)
    # downloader.progress_updated.connect(on_progress)
    # downloader.download_complete.connect(on_complete)
    # downloader.status_changed.connect(on_status)
    #
    # # 启动下载
    # downloader.start_download()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

