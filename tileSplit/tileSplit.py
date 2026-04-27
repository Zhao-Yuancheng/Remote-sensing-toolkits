import sys
from ui_tileSplit import Ui_MainWindow
from PySide6 import QtCore, QtWidgets, QtGui
from multiprocessing import Pool, shared_memory,freeze_support
import os
from PIL import Image
import numpy as np


# 瓦片分割函数
def split_tile(result_root, save_x, save_y, result_format, x1, y1, x2, y2, shm_name, h, w, channels,
               progress_shm_name, x_num, y_num, x_idx, y_idx):
    try:
        existing_shm = shared_memory.SharedMemory(name=shm_name, create=False)

        # 根据通道数创建不同形状的数组
        if channels == 1:
            tot_map = np.ndarray((h, w), dtype=np.uint8, buffer=existing_shm.buf)
        else:  # channels == 3
            tot_map = np.ndarray((h, w, 3), dtype=np.uint8, buffer=existing_shm.buf)

        # 创建保存目录
        os.makedirs(os.path.join(result_root, str(save_x)), exist_ok=True)
        save_path = os.path.join(result_root, str(save_x),
                                 str(save_y) + "." + result_format.replace(".", ""))

        # 提取瓦片
        if channels == 1:
            array = tot_map[y1:y2, x1:x2]
        else:
            array = tot_map[y1:y2, x1:x2, :]

        # 保存瓦片
        Image.fromarray(array).save(save_path)
        existing_shm.close()

        # 更新进度
        if progress_shm_name:
            try:
                existing_progress_shm = shared_memory.SharedMemory(name=progress_shm_name,
                                                                   create=False)
                progress_map = np.ndarray((y_num, x_num), dtype=np.uint8,
                                          buffer=existing_progress_shm.buf)
                progress_map[y_idx, x_idx] = 255
                existing_progress_shm.close()
            except Exception as e:
                print(f"更新进度失败: {e}")

    except Exception as e:
        print(f"Error in integrate at (save_x={save_x}, save_y={save_y}): {e}", flush=True)
        raise


def run_tile_split(params, shm_name, progress_shm_name, x_num, y_num, progress_callback=None):
    """执行瓦片生成的主要函数"""
    try:
        # 从参数中获取值
        result_root = params['result_root']
        open_path = params['open_path']
        x_begin = params['x_begin']
        x_step = params['x_step']
        y_begin = params['y_begin']
        y_step = params['y_step']
        seg_width = params['seg_width']
        seg_height = params['seg_height']
        proc_num = params['proc_num']
        h = params['h']
        w = params['w']
        channels = params['channels']
        result_format = params['result_format']

        # 准备参数
        params_list = []
        for x_idx in range(0, x_num):
            for y_idx in range(0, y_num):
                params_list.append((
                    result_root,
                    x_idx * x_step + x_begin,  # 保存的x
                    y_idx * y_step + y_begin,  # 保存的y
                    result_format,
                    x_idx * seg_width,  # 图上x1
                    y_idx * seg_height,  # 图上y1
                    (x_idx + 1) * seg_width,  # 图上x2
                    (y_idx + 1) * seg_height,  # 图上y2
                    shm_name,
                    h,
                    w,
                    channels,
                    progress_shm_name,
                    x_num,
                    y_num,
                    x_idx,  # 添加x_idx用于进度更新
                    y_idx  # 添加y_idx用于进度更新
                ))

        print(f"params_list长度: {len(params_list)}", flush=True)

        # 使用多进程池处理
        with Pool(processes=proc_num) as pool:
            try:
                pool.starmap(split_tile, params_list)
            except Exception as e:
                print(f"Error in pool: {e}")
                raise

        return True, "生成完成！"

    except Exception as e:
        return False, f"生成失败: {str(e)}"


class WorkerThread(QtCore.QThread):
    """工作线程，用于执行耗时的瓦片分割操作"""
    finished = QtCore.Signal(bool, str)  # 信号：是否成功，消息
    progress_updated = QtCore.Signal(np.ndarray)  # 信号：进度图更新

    def __init__(self, params, shm_name, progress_shm_name, x_num, y_num):
        super().__init__()
        self.params = params
        self.shm_name = shm_name
        self.progress_shm_name = progress_shm_name
        self.x_num = x_num
        self.y_num = y_num
        self.running = True

    def run(self):
        try:
            # 运行分割函数
            success, message = run_tile_split(
                self.params,
                self.shm_name,
                self.progress_shm_name,
                self.x_num,
                self.y_num
            )

            # 发送最终进度
            if self.progress_shm_name:
                try:
                    progress_shm = shared_memory.SharedMemory(name=self.progress_shm_name,
                                                              create=False)
                    progress_map = np.ndarray((self.y_num, self.x_num), dtype=np.uint8,
                                              buffer=progress_shm.buf)
                    self.progress_updated.emit(progress_map.copy())
                    progress_shm.close()
                except Exception as e:
                    print(f"读取最终进度失败: {e}")

            self.finished.emit(success, message)

        except Exception as e:
            self.finished.emit(False, f"处理失败: {str(e)}")

    def stop(self):
        self.running = False


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setup()
        self.show()
        self.timer = None
        self.progress_shm = None
        self.shm = None
        self.progress_map = None
        self.x_num = 0
        self.y_num = 0

    def setup(self):
        # 连接按钮点击/更改事件
        self.processBtn.clicked.connect(self.on_process_clicked)
        self.browseTileDirBtn.clicked.connect(self.browse_tile_dir)
        self.browseOpenFileBtn.clicked.connect(self.browse_open_file)

    def update_progress_image(self):
        """更新进度图像显示"""
        if self.progress_shm and self.progress_map is not None:
            try:
                # 计算已完成瓦片数量
                completed = np.sum(self.progress_map == 255)
                total = self.x_num * self.y_num
                progress_percent = int((completed / total) * 100) if total > 0 else 0

                # 创建颜色映射：白色(255)表示已处理，黑色(0)表示未处理
                display_array = self.progress_map

                # 将numpy数组转换为QImage
                height, width = display_array.shape
                bytes_per_line = width
                qimage = QtGui.QImage(display_array.data.tobytes(), width, height,
                                      bytes_per_line, QtGui.QImage.Format_Grayscale8)

                # 将QImage转换为QPixmap并显示
                pixmap = QtGui.QPixmap.fromImage(qimage)

                # 缩放以适合label，但保持宽高比
                scaled_pixmap = pixmap.scaled(
                    self.imageLabel.size(),
                    QtCore.Qt.KeepAspectRatio,
                    # QtCore.Qt.SmoothTransformation
                )

                self.imageLabel.setPixmap(scaled_pixmap)
                self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)

                # 在状态栏显示进度
                if progress_percent == 100:
                    self.statusbar.showMessage(
                        f"处理进度: {completed}/{total} ({progress_percent}%)，正在保存……")
                else:
                    self.statusbar.showMessage(
                        f"处理进度: {completed}/{total} ({progress_percent}%)")

            except Exception as e:
                print(f"更新进度图像时出错: {e}")

    def browse_tile_dir(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择保存瓦片图的根目录")
        if dir_path:
            self.tileDirEdit.setText(dir_path)

    def browse_open_file(self):
        """浏览打开文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择打开文件", "",
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;TIFF Files (*.tif *.tiff);;All Files (*)"
        )
        if file_path:
            self.openFileEdit.setText(file_path)

    def on_process_clicked(self):
        """开始处理按钮点击事件"""
        # 禁用按钮，防止重复点击
        self.processBtn.setEnabled(False)
        self.processBtn.setText("处理中...")

        # 清空之前的进度显示
        self.imageLabel.clear()
        self.imageLabel.setText("处理中...")

        # 获取所有参数
        try:
            # 保存文件路径
            open_path = self.openFileEdit.text().strip()
            if not open_path:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入打开遥感文件路径！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 瓦片图保存根目录
            root_dir = self.tileDirEdit.text().strip()
            if not root_dir:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入有效的瓦片图保存根目录！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 创建根目录
            os.makedirs(root_dir, exist_ok=True)

            # x轴参数
            x_begin = int(self.xStartEdit.text())
            x_step = int(self.xStepEdit.text())

            # y轴参数
            y_begin = int(self.yStartEdit.text())
            y_step = int(self.yStepEdit.text())

            # 瓦片属性
            seg_width = int(self.tileWidthLineEdit.text())
            seg_height = int(self.tileHeightLineEdit.text())

            # 进程数
            proc_num_text = self.nProcEdit.text().strip()
            proc_num = int(proc_num_text) if proc_num_text else 1

            # 打开图像获取实际参数
            try:
                input_img = np.array(Image.open(open_path), dtype=np.uint8)
                h, w = input_img.shape[:2]

                # 根据实际图像确定通道数
                if len(input_img.shape) == 2:
                    channels = 1
                elif len(input_img.shape) == 3 and input_img.shape[2] == 3:
                    channels = 3
                else:
                    QtWidgets.QMessageBox.warning(self, "警告",
                                                  f"不支持的图像格式: 形状={input_img.shape}")
                    self.processBtn.setEnabled(True)
                    self.processBtn.setText("开始处理")
                    return

                    # 可以继续处理，但使用实际通道数
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "错误", f"无法打开图像: {str(e)}")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 计算瓦片数量
            x_num = w // seg_width
            y_num = h // seg_height

            if x_num == 0 or y_num == 0:
                QtWidgets.QMessageBox.warning(self, "警告", "瓦片尺寸大于图像尺寸，无法分割！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 参数验证
            if channels not in [1, 3]:
                QtWidgets.QMessageBox.warning(self, "警告", "通道数必须为1或3！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            if x_step <= 0 or y_step <= 0:
                QtWidgets.QMessageBox.warning(self, "警告", "步长必须大于0！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            if seg_width <= 0 or seg_height <= 0:
                QtWidgets.QMessageBox.warning(self, "警告", "瓦片尺寸必须大于0！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            if proc_num <= 0:
                QtWidgets.QMessageBox.warning(self, "警告", "进程数必须大于0！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 根据通道数计算共享内存大小
            shm = shared_memory.SharedMemory(
                create=True,
                size=h * w * channels
            )
            self.shm = shm
            self.shm_name = shm.name

            # 根据通道数创建不同形状的数组
            if channels == 1:
                totMap = np.ndarray((h, w), dtype=np.uint8, buffer=shm.buf)
            else:  # channels == 3
                totMap = np.ndarray((h, w, 3), dtype=np.uint8, buffer=shm.buf)

            # 复制图像数据到共享内存
            totMap[:] = input_img
            del input_img

            # 创建进度共享内存
            progress_shm = shared_memory.SharedMemory(
                create=True,
                size=y_num * x_num
            )
            self.progress_shm = progress_shm
            self.progress_shm_name = progress_shm.name

            # 初始化进度图
            self.progress_map = np.ndarray((y_num, x_num), dtype=np.uint8, buffer=progress_shm.buf)
            self.progress_map.fill(0)

            self.x_num = x_num
            self.y_num = y_num

            # 准备参数
            params = {
                'result_root': root_dir,
                'open_path': open_path,
                'x_begin': x_begin,
                'x_step': x_step,
                'y_begin': y_begin,
                'y_step': y_step,
                'seg_width': seg_width,
                'seg_height': seg_height,
                'proc_num': proc_num,
                'h': h,
                'w': w,
                'channels': channels,
                'result_format': self.resultFormatComboBox.currentText(),
            }

            # 在状态栏显示处理状态
            self.statusbar.showMessage("开始处理瓦片图生成...")

            # 创建工作线程并启动
            self.worker = WorkerThread(params, self.shm_name, self.progress_shm_name, x_num, y_num)
            self.worker.finished.connect(self.on_process_finished)
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.start()

            # 启动定时器定期更新进度
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.update_progress_image)
            self.timer.start(200)  # 每200毫秒更新一次

        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"参数格式错误: {str(e)}")
            self.cleanup()
            self.processBtn.setEnabled(True)
            self.processBtn.setText("开始处理")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")
            self.cleanup()
            self.processBtn.setEnabled(True)
            self.processBtn.setText("开始处理")

    def on_progress_updated(self, progress_map):
        """接收进度更新信号"""
        self.progress_map = progress_map.copy()
        self.update_progress_image()

    def cleanup(self):
        """清理资源"""
        if self.timer:
            self.timer.stop()
            self.timer = None

        if self.progress_shm:
            try:
                self.progress_shm.close()
                self.progress_shm.unlink()
            except:
                pass
            self.progress_shm = None

        if self.shm:
            try:
                self.shm.close()
                self.shm.unlink()
            except:
                pass
            self.shm = None

    def on_process_finished(self, success, message):
        """处理完成回调"""
        # 停止定时器
        if self.timer:
            self.timer.stop()
            self.timer = None

        # 清理共享内存
        self.cleanup()

        self.processBtn.setEnabled(True)
        self.processBtn.setText("开始处理")

        if success:
            QtWidgets.QMessageBox.information(self, "成功", message)
            self.statusbar.showMessage("处理完成！", 5000)
        else:
            QtWidgets.QMessageBox.critical(self, "错误", message)
            self.statusbar.showMessage("处理失败！", 5000)


if __name__ == '__main__':
    Image.MAX_IMAGE_PIXELS = 1e15  # 设置PIL最大像素限制
    freeze_support()

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec())