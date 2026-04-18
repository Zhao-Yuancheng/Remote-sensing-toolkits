import urllib.request
import os
import random
import math
import sys
import concurrent.futures
import threading
import traceback
import time
from typing import List, Tuple, Optional
from urllib.error import URLError, HTTPError
from PySide2.QtCore import QObject, Signal, Slot, QThread


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

    def batch_download(self, level_start, level_end, max_workers_per_level=50):
        """批量下载多个缩放级别"""
        try:
            for zoom in range(level_start, level_end + 1):
                if self._stop_requested:
                    break

                self.level = zoom
                self.status_changed.emit(f"开始下载缩放级别: {zoom}")

                # 动态调整线程数
                if zoom <= 15:
                    workers = max_workers_per_level
                elif zoom <= 18:
                    workers = max_workers_per_level // 2
                else:
                    workers = max_workers_per_level // 4

                self.max_workers = workers
                self.status_changed.emit(f"使用 {workers} 个线程")

                # 执行下载
                self.start_download()

                if self._stop_requested:
                    break

                # 级别间暂停
                if zoom < level_end:
                    self.status_changed.emit(f"等待5秒后开始下一级别...")
                    time.sleep(5)

            if not self._stop_requested:
                self.status_changed.emit("所有级别下载完成!")

        except Exception as e:
            error_msg = f"批量下载过程发生错误: {str(e)}"
            self.error_occurred.emit("批量下载错误",
                                     f"{error_msg}\n堆栈跟踪:\n{traceback.format_exc()}")


# 使用示例（在PySide2界面中）
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


# 在PySide2界面中的使用示例
"""
# 在您的PySide2主窗口类中
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_manager = DownloadManager(parent_widget=self)
        self.setup_ui()

    def setup_ui(self):
        # 创建界面元素...
        # 添加开始下载按钮
        self.download_btn = QPushButton("开始下载", self)
        self.download_btn.clicked.connect(self.start_download)

        # 添加停止按钮
        self.stop_btn = QPushButton("停止下载", self)
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)

        # 添加进度条
        self.progress_bar = QProgressBar(self)

        # 添加日志文本框
        self.log_text = QTextEdit(self)
        self.log_text.setReadOnly(True)

    def start_download(self):
        # 获取参数
        level = 21
        LT_lat = 36.1610
        LT_lon = 103.5533
        RB_lat = 36.0203
        RB_lon = 103.9557
        root_dir = "D:\\satellite\\"

        # 开始下载
        self.download_manager.start_download(
            level, LT_lat, LT_lon, RB_lat, RB_lon, root_dir, max_workers=50
        )

        # 更新按钮状态
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_download(self):
        self.download_manager.stop_download()
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    # 可以添加其他方法连接到DownloadManager的信号
"""

# 命令行测试
if __name__ == "__main__":
    # 测试下载器
    downloader = GoogleMapDownloader(
        level=21,
        LT_lat=36.1610,
        LT_lon=103.5533,
        RB_lat=36.0203,
        RB_lon=103.9557,
        root_dir="D:\\satellite\\",
        max_workers=20
    )


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


    downloader.error_occurred.connect(on_error)
    downloader.progress_updated.connect(on_progress)
    downloader.download_complete.connect(on_complete)
    downloader.status_changed.connect(on_status)

    # 启动下载
    downloader.start_download()