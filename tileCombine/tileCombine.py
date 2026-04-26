import sys
from ui_tileCombine import Ui_MainWindow
from PySide2 import QtCore, QtWidgets, QtGui
from multiprocessing import Pool, shared_memory
import os
from PIL import Image
import numpy as np


# 瓦片合并函数
def integrate(idx, x_idx, y_idx, file_path, seg_width, seg_height, tot_width, tot_height, shm_name,
              channels, x_num, y_num, progress_shm_name):
    try:
        existing_shm = shared_memory.SharedMemory(name=shm_name, create=False)

        # 根据通道数创建不同形状的数组
        if channels == 1:
            tot_map = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=existing_shm.buf)
        else:  # channels == 3
            tot_map = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8,
                                 buffer=existing_shm.buf)

        # 读取图片
        array = np.array(Image.open(file_path), dtype=np.uint8)

        # 放置到正确位置
        if channels == 1:
            tot_map[y_idx * seg_height:(y_idx + 1) * seg_height,
            x_idx * seg_width:(x_idx + 1) * seg_width] = array
        else:  # channels == 3
            tot_map[y_idx * seg_height:(y_idx + 1) * seg_height,
            x_idx * seg_width:(x_idx + 1) * seg_width, :] = array

        existing_shm.close()

        # PROGRESS
        existing_progress_shm = shared_memory.SharedMemory(name=progress_shm_name, create=False)
        progress_map = np.ndarray((y_num, x_num), dtype=np.uint8, buffer=existing_progress_shm.buf)
        progress_map[y_idx, x_idx] = 255
        existing_progress_shm.close()

    except Exception as e:
        print(f"Error in integrate at (x_idx={x_idx}, y_idx={y_idx}): {e}", flush=True)
        raise


def run_tile_combine(params,progress_shm_name, progress_callback=None):
    """执行瓦片合并的主要函数"""
    try:
        # 从参数中获取值
        root_dir = params['root_dir']
        result_path = params['result_path']
        x_begin = params['x_begin']
        x_end = params['x_end']
        x_step = params['x_step']
        y_begin = params['y_begin']
        y_end = params['y_end']
        y_step = params['y_step']
        seg_width = params['seg_width']
        seg_height = params['seg_height']
        proc_num = params['proc_num']
        channels = params['channels']

        x_num = int((x_end - x_begin) / x_step) + 1
        y_num = int((y_end - y_begin) / y_step) + 1

        # 根据通道数计算共享内存大小
        shm = shared_memory.SharedMemory(
            create=True,
            size=x_num * y_num * seg_width * seg_height * channels
        )
        shm_name = shm.name
        tot_width, tot_height = x_num * seg_width, y_num * seg_height

        # # PROGRESS 二维进度表示
        # progress_shm = shared_memory.SharedMemory(
        #     create=True,
        #     size=y_num * x_num
        # )
        # progress_shm_name = progress_shm.name

        # 根据通道数创建不同形状的数组
        if channels == 1:
            totMap = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=shm.buf)
        else:  # channels == 3
            totMap = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8, buffer=shm.buf)

        # PROGRESS
        # progressMap = np.ndarray((y_num, x_num), dtype=np.uint8, buffer=progress_shm.buf)
        # progressMap.fill(125)

        # 准备参数
        params_list = []
        for x_idx in range(x_num):
            for y_idx in range(y_num):
                params_list.append((
                    x_idx * y_num + y_idx,
                    x_idx,
                    y_idx,
                    os.path.join(root_dir, str(x_begin + x_idx * x_step),
                                 str(y_begin + y_idx * y_step)) + ".png",
                    seg_width,
                    seg_height,
                    tot_width,
                    tot_height,
                    shm_name,
                    channels,
                    x_num,
                    y_num,
                    progress_shm_name
                ))

        # 使用多进程池处理
        with Pool(processes=proc_num) as pool:
            try:
                pool.starmap(integrate, params_list)
            except Exception as e:
                print(f"Error in pool: {e}")
                shm.close()
                shm.unlink()
                raise


        # 根据通道数保存图片
        if channels == 1:
            result = Image.fromarray(totMap, mode='L')
        else:  # channels == 3
            result = Image.fromarray(totMap, mode='RGB')

        result.save(result_path)
        shm.close()
        shm.unlink()


        return True, "合并完成！"  # 返回进度图

    except Exception as e:
        return False, f"合并失败: {str(e)}", None


class WorkerThread(QtCore.QThread):
    """工作线程，用于执行耗时的瓦片合并操作"""
    finished = QtCore.Signal(bool, str)  # 信号：是否成功，消息
    progress_updated = QtCore.Signal(np.ndarray)  # 信号：进度图更新

    def __init__(self, params, progress_shm_name, x_num, y_num):
        super().__init__()
        self.params = params
        self.progress_shm_name = progress_shm_name
        self.x_num = x_num
        self.y_num = y_num
        self.running = True

    def run(self):
        try:
            # 打开进度共享内存
            progress_shm = shared_memory.SharedMemory(name=self.progress_shm_name, create=False)
            progress_map = np.ndarray((self.y_num, self.x_num), dtype=np.uint8,
                                      buffer=progress_shm.buf)

            # 运行合并函数
            success, message = run_tile_combine(self.params,self.progress_shm_name)

            # 发送最终进度
            self.progress_updated.emit(progress_map.copy())

            progress_shm.close()

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
        self.progress_map = None
        self.x_num = 0
        self.y_num = 0

    def setup(self):
        # 连接按钮点击/更改事件
        self.processBtn.clicked.connect(self.on_process_clicked)
        self.browseTileDirBtn.clicked.connect(self.browse_tile_dir)
        self.browseSaveFileBtn.clicked.connect(self.browse_save_file)
        self.tileDirEdit.textChanged.connect(self.set_other_params)

    def update_progress_image(self):
        """更新进度图像显示"""
        if self.progress_shm and self.progress_map is not None:
            try:
                # 计算已完成瓦片数量
                completed = np.sum(self.progress_map == 255)
                total = self.x_num * self.y_num
                progress_percent = int((completed / total) * 100) if total > 0 else 0

                # 创建颜色映射：白色(255)表示未处理，黑色(0)表示已处理
                # 我们可以将其反转以便更好看：黑色表示未处理，白色表示已处理
                # display_array = 255 - self.progress_map
                display_array = self.progress_map

                # 将numpy数组转换为QImage
                height, width = display_array.shape
                # print(height, width)
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
                    self.statusbar.showMessage(f"处理进度: {completed}/{total} ({progress_percent}%)，正在保存……")
                else:
                    self.statusbar.showMessage(
                        f"处理进度: {completed}/{total} ({progress_percent}%)")

            except Exception as e:
                print(f"更新进度图像时出错: {e}")

    def browse_tile_dir(self):
        """浏览瓦片图目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择瓦片图根目录")
        if dir_path:
            self.tileDirEdit.setText(dir_path)
            # self.set_other_params(dir_path)

    def set_other_params(self):
        dir_path = self.tileDirEdit.text()
        try:
            x_dir_list = [i for i in os.listdir(dir_path) if i.isdigit() and os.path.isdir(os.path.join(dir_path,i))]
        except:
            return
        if len(x_dir_list):
            y0_file_list = [i for i in os.listdir(os.path.join(dir_path,x_dir_list[0]))
                           if i.endswith((".jpg", ".png", ".gif",".jpeg", ".tif",".tiff",".bmp",".webp"))
                           and os.path.isfile(os.path.join(dir_path,x_dir_list[0],i))
                           and os.path.splitext(i)[0].isdigit()]
            num_x_dir_list = [int(i) for i in x_dir_list]
            self.xStartEdit.setText(str(min(num_x_dir_list)))
            self.xEndEdit.setText(str(max(num_x_dir_list)))
            self.xStepEdit.setText(str(((max(num_x_dir_list) - min(num_x_dir_list))//len(num_x_dir_list)+1)))
            if len(y0_file_list):
                num_y0_file_list = [int(os.path.splitext(i)[0]) for i in y0_file_list]
                self.yStartEdit.setText(str(min(num_y0_file_list)))
                self.yEndEdit.setText(str(max(num_y0_file_list)))
                self.yStepEdit.setText(str(((max(num_y0_file_list)-min(num_y0_file_list))//len(num_y0_file_list)+1)))
                try:
                    tmp_img = Image.open(os.path.join(dir_path,x_dir_list[0],y0_file_list[0]))
                    self.tileChannelsLineEdit.setText(str(len(tmp_img.split())))
                    self.tileWidthLineEdit.setText(str(tmp_img.width))
                    self.tileLengthLineEdit.setText(str(tmp_img.height))
                except:
                    return


    def browse_save_file(self):
        """浏览保存文件"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "选择保存文件", "", "PNG Files (*.png);;All Files (*)"
        )
        if file_path:
            self.saveFileEdit.setText(file_path)

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
            # 瓦片图根目录
            root_dir = self.tileDirEdit.text().strip()
            if not root_dir or not os.path.exists(root_dir):
                QtWidgets.QMessageBox.warning(self, "警告", "请输入有效的瓦片图根目录！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # 保存文件路径
            result_path = self.saveFileEdit.text().strip()
            if not result_path:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入保存文件路径！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            # x轴参数
            x_begin = int(self.xStartEdit.text())
            x_end = int(self.xEndEdit.text())
            x_step = int(self.xStepEdit.text())

            # y轴参数
            y_begin = int(self.yStartEdit.text())
            y_end = int(self.yEndEdit.text())
            y_step = int(self.yStepEdit.text())

            # 瓦片属性
            seg_width = int(self.tileWidthLineEdit.text())
            seg_height = int(self.tileLengthLineEdit.text())
            channels = int(self.tileChannelsLineEdit.text())

            # 进程数
            proc_num_text = self.nProcEdit.text().strip()
            proc_num = int(proc_num_text) if proc_num_text else 1

            # 参数验证
            if channels not in [1, 3]:
                QtWidgets.QMessageBox.warning(self, "警告", "通道数必须为1或3！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            if x_begin > x_end:
                QtWidgets.QMessageBox.warning(self, "警告", "x轴起始值不能大于终止值！")
                self.processBtn.setEnabled(True)
                self.processBtn.setText("开始处理")
                return

            if y_begin > y_end:
                QtWidgets.QMessageBox.warning(self, "警告", "y轴起始值不能大于终止值！")
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

            # 计算瓦片数量
            x_num = int((x_end - x_begin) / x_step) + 1
            y_num = int((y_end - y_begin) / y_step) + 1

            # 创建进度共享内存
            progress_shm = shared_memory.SharedMemory(
                create=True,
                size=y_num * x_num
            )
            self.progress_shm = progress_shm
            self.progress_shm_name = progress_shm.name
            self.x_num = x_num
            self.y_num = y_num

            # 初始化进度图
            self.progress_map = np.ndarray((y_num, x_num), dtype=np.uint8, buffer=progress_shm.buf)
            self.progress_map.fill(0)

            # 准备参数
            params = {
                'root_dir': root_dir,
                'result_path': result_path,
                'x_begin': x_begin,
                'x_end': x_end,
                'x_step': x_step,
                'y_begin': y_begin,
                'y_end': y_end,
                'y_step': y_step,
                'seg_width': seg_width,
                'seg_height': seg_height,
                'proc_num': proc_num,
                'channels': channels
            }

            # 在状态栏显示处理状态
            self.statusbar.showMessage("开始处理瓦片图合并...")

            # 创建工作线程并启动
            self.worker = WorkerThread(params, self.progress_shm_name, x_num, y_num)
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

    app = QtWidgets.QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec_())