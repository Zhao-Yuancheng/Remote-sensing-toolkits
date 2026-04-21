import sys
from ui_tileCombine import Ui_MainWindow
from PySide2 import QtCore, QtWidgets, QtGui
from multiprocessing import Pool, shared_memory
import os
from PIL import Image
import numpy as np


# 瓦片合并函数（从代码二移植过来）
def integrate(idx, x_idx, y_idx, file_path, seg_width, seg_height, tot_width, tot_height, shm_name,
              channels,x_num,y_num,progress_shm_name):
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
        progress_map = np.ndarray((y_num,x_num), dtype=np.uint8, buffer=existing_progress_shm.buf)
        progress_map[y_idx,x_idx] = 0

        existing_progress_shm.close()

        # if not idx % 250:
        #     print(f"{idx}:\tx_idx={x_idx}, y_idx={y_idx}, file_path={file_path}", flush=True)
    except Exception as e:
        print(f"Error in integrate at (x_idx={x_idx}, y_idx={y_idx}): {e}", flush=True)
        raise


def run_tile_combine(params):
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

        # PROGRESS 二维进度表示
        progress_shm = shared_memory.SharedMemory(
            create=True,
            size =y_num * x_num
        )
        progress_shm_name = progress_shm.name


        # 根据通道数创建不同形状的数组
        if channels == 1:
            totMap = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=shm.buf)
        else:  # channels == 3
            totMap = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8, buffer=shm.buf)

        # PROGRESS
        progressMap = np.ndarray((y_num,x_num),dtype=np.uint8,buffer=progress_shm.buf)
        progressMap.fill(255)

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

        tmp = Image.fromarray(progressMap, mode='L')
        tmp.save("tmp.png")
        progress_shm.close()
        progress_shm.unlink()

        return True, "合并完成！"

    except Exception as e:
        return False, f"合并失败: {str(e)}"


class WorkerThread(QtCore.QThread):
    """工作线程，用于执行耗时的瓦片合并操作"""
    finished = QtCore.Signal(bool, str)  # 信号：是否成功，消息

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        success, message = run_tile_combine(self.params)
        self.finished.emit(success, message)


class MyApp(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setup()
        self.show()

    def setup(self):
        # 连接按钮点击事件
        self.processBtn.clicked.connect(self.on_process_clicked)
        self.browseTileDirBtn.clicked.connect(self.browse_tile_dir)
        self.browseSaveFileBtn.clicked.connect(self.browse_save_file)

    def browse_tile_dir(self):
        """浏览瓦片图目录"""
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择瓦片图根目录")
        if dir_path:
            self.tileDirEdit.setText(dir_path)

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
            seg_width = int(self.tileWidthLineEdit.text())  # 注意：UI中宽度对应瓦片宽度
            seg_height = int(self.tileLengthLineEdit.text())  # 注意：UI中长度对应瓦片高度
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
            self.worker = WorkerThread(params)
            self.worker.finished.connect(self.on_process_finished)
            self.worker.start()

        except ValueError as e:
            QtWidgets.QMessageBox.warning(self, "警告", f"参数格式错误: {str(e)}")
            self.processBtn.setEnabled(True)
            self.processBtn.setText("开始处理")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"发生错误: {str(e)}")
            self.processBtn.setEnabled(True)
            self.processBtn.setText("开始处理")

    def on_process_finished(self, success, message):
        """处理完成回调"""
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