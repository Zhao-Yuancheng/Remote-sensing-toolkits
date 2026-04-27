# 新增必要的导入

import io
import sys
from PIL import Image
from term_image.image import AutoImage
from multiprocessing import freeze_support

# ... (前面的所有库导入保持不变，包括matplotlib, tkinter等) ...
import math
import time
# 注意：tkinter 仅用于 filedialog 等模块，主窗口逻辑将被移除

from multiprocessing import Pool
from multiprocessing import cpu_count
from multiprocessing import shared_memory
# 删除主窗口相关的导入，如：from tkinter import Tk, Button, Label, Entry, StringVar

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import skimage
from PIL import Image, ImageFile
from scipy import signal
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
import skimage.io
import skimage.transform
from skimage.color import rgb2lab, rgba2rgb

matplotlib.use('Agg')  # 改为非交互式后端，因为不再需要GUI窗口
# ... (w, h, original_image, image等全局变量定义保持不变) ...
w = None
h = None
original_image = None
image = None

INPUT_FILE_PATH = None
OUTPUT_FILE_PATH = None

plt.rcParams['font.family'] = 'SimHei'
matplotlib.set_loglevel("error")


def detect_color_boundaries_vertical(image, num_blocks=2, require_grad_norm=True):
    image_lab = rgb2lab(image)
    L_channel = image_lab[:, :, 0]  # 亮度通道
    grad_x = np.abs(signal.convolve2d(L_channel, np.array([[-1, 0, 1]]), mode='same'))
    grad_smooth = gaussian_filter(grad_x, sigma=2)
    grad_norm = (grad_smooth - grad_smooth.min()) / (grad_smooth.max() - grad_smooth.min() + 1e-8)

    # 寻找梯度峰值（潜在边界位置）
    grad_profile = np.mean(grad_norm, axis=0)
    peaks, properties = find_peaks(grad_profile, height=0.1, distance=10)

    if len(peaks) < num_blocks - 1:
        peaks, properties = find_peaks(grad_profile, height=0.08, distance=8)

    if len(peaks) > 0:
        peak_heights = properties['peak_heights']
        sorted_indices = np.argsort(peak_heights)[::-1]  # 从高到低
        peaks = peaks[sorted_indices]

        # 只保留前几个最强的峰值
        peaks = peaks[:min(len(peaks), num_blocks)]
        # peaks = np.sort(peaks)  # 按位置排序
    if not require_grad_norm:
        return peaks
    return peaks, grad_profile, grad_norm


def detect_color_boundaries_horizontal(image, num_blocks=2, require_grad_norm=True):
    img_lab = rgb2lab(image)
    L_channel = img_lab[:, :, 0]  # 亮度通道
    grad_x = np.abs(signal.convolve2d(L_channel, np.array([[-1], [0], [1]]), mode='same'))
    grad_smooth = gaussian_filter(grad_x, sigma=2)
    grad_norm = (grad_smooth - grad_smooth.min()) / (grad_smooth.max() - grad_smooth.min() + 1e-8)

    # 寻找梯度峰值（潜在边界位置）
    grad_profile = np.mean(grad_norm, axis=1)
    peaks, properties = find_peaks(grad_profile, height=0.1, distance=10)

    if len(peaks) < num_blocks - 1:
        peaks, properties = find_peaks(grad_profile, height=0.08, distance=8)

    if len(peaks) > 0:
        peak_heights = properties['peak_heights']
        sorted_indices = np.argsort(peak_heights)[::-1]  # 从高到低
        peaks = peaks[sorted_indices]

        # 只保留前几个最强的峰值
        peaks = peaks[:min(len(peaks), num_blocks)]
        # peaks = np.sort(peaks)  # 按位置排序
    if not require_grad_norm:
        return peaks
    return peaks, grad_profile, grad_norm


def detect_original_vertical(x, dx):
    global original_image, w
    x1 = max(0, x - dx)
    x2 = min(x + dx, w)
    img = original_image[:, x1:x2 + 1, :]
    p_v, grad_profile_v, grad_norm_v = detect_color_boundaries_vertical(img, num_blocks=3)
    if len(p_v) == 0:
        return x

    return p_v[0].tolist() + x1


def detect_original_horizontal(y, dy):
    global original_image, h
    y1, y2 = max(0, y - dy), min(y + dy, h)
    img = original_image[y1:y2 + 1, :, :]
    p_h, grad_profile_h, grad_norm_h = detect_color_boundaries_horizontal(img, num_blocks=3)
    if len(p_h) == 0:
        return y
    return p_h[0].tolist() + y1


def single_original_process_image(x1, y1, x2, y2, bx1, by1, bx2, by2, h, w, shm_name):
    # 一个进程处理原图
    try:
        shm = shared_memory.SharedMemory(name=shm_name, create=False)
        original_image = np.ndarray((h, w, 3), dtype=np.uint8, buffer=shm.buf)

        original_image[
            y1:y2,
            x1:x2
        ] = skimage.exposure.match_histograms(
            original_image[
                y1:y2,
                x1:x2
            ],
            original_image[
                by1:by2,
                bx1:bx2
            ], channel_axis=-1)
    except Exception as e:
        raise
    finally:
        shm.close()


# 1. 移除所有GUI主窗口相关代码，包括 root, label, entry, btn_process, on_closing, validate_range
# 2. 将文件对话框替换为命令行输入
# 3. 将消息框(askyesno, showinfo, showerror, showwarning)替换为 print 和 input
# 4. 将 plt.show(block=False) 的显示逻辑替换为终端图像输出

# ========== 新增函数：切除白色边缘 ==========
def cutWhiteEdge(plt_image):
    """
    切除PIL Image图像周围的白色（或接近白色）边缘。
    参数:
        plt_image: PIL.Image 对象
    返回:
        cropped_img: 切除白色边缘后的 PIL.Image 对象
    """
    # 将图像转换为numpy数组
    img_array = np.array(plt_image)

    # 定义白色的阈值（RGB接近255,255,255），可以根据需要调整
    # 使用较高的阈值以容忍接近白色的边缘
    white_threshold = 250
    # 创建一个掩码，标记非白色的像素
    # 任何通道的值低于阈值，则认为该像素不是白色
    non_white_mask = np.any(img_array < white_threshold, axis=-1)

    # 如果没有非白色像素（整个图像都是白色），则返回原图
    if not np.any(non_white_mask):
        return plt_image

    # 找到非白色像素的边界
    rows = np.any(non_white_mask, axis=1)
    cols = np.any(non_white_mask, axis=0)

    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]

    # 添加一个小的边距（可选，可根据需要调整或移除）
    margin = 1
    height, width = img_array.shape[:2]
    y_min = max(0, y_min - margin)
    y_max = min(height - 1, y_max + margin)
    x_min = max(0, x_min - margin)
    x_max = min(width - 1, x_max + margin)

    # 裁剪图像
    cropped_img = plt_image.crop((x_min, y_min, x_max + 1, y_max + 1))
    return cropped_img


# ========== cutWhiteEdge 函数结束 ==========

# ========== 新增函数：在终端显示matplotlib图形 ==========
def show_plot_in_terminal(block=False):
    """
    替代 plt.show(block=False)，将当前图形显示在终端中。
    参数 block 在此CLI版本中忽略，仅用于兼容原函数签名。
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    plt_img = Image.open(buf).convert('RGB')
    plt_img = cutWhiteEdge(plt_img)
    term_plt_img = AutoImage(plt_img)
    # 打印图像到终端
    print(str(term_plt_img))
    plt.close()  # 关闭图形以释放内存


# ========== 终端显示函数结束 ==========

# ========== 修改现有的 process_image 函数 ==========
def process_image():
    # ... (函数开头部分保持不变，直到文件选择) ...
    global h, w, original_image, image
    # 删除对 text_var 的引用，改为从命令行参数或输入获取
    # 原代码: if not len(text_var.get()): text_var.set("5")

    # 1. 获取分割灵敏度（替换原Tkinter输入框）
    sensitivity = 5
    sensitivity_input = input("请输入分割灵敏度 (默认 5, 范围 1-20): ").strip()
    if sensitivity_input:
        try:
            sensitivity = int(sensitivity_input)
            if not (1 <= sensitivity <= 20):
                print("警告：输入值超出范围，将使用默认值5。")
                sensitivity = 5
        except ValueError:
            print("警告：输入无效，将使用默认值5。")
            sensitivity = 5
    print(f"使用分割灵敏度: {sensitivity}")

    # 2. 打开输入文件（替换filedialog）
    print("\n请提供输入图片的完整路径:")
    INPUT_FILE_PATH = input("> ").strip()
    if not INPUT_FILE_PATH:
        print("未提供路径，操作取消。")
        return

    # ... (图片读取、shared_memory 等处理逻辑完全不变) ...
    try:
        input_image = skimage.io.imread(INPUT_FILE_PATH)
        if input_image.shape[2] == 4:
            input_image = rgba2rgb(input_image) * 255
    except Exception as e:
        print(f"错误: 无法读取图片: {str(e)}")
        return

    h, w = input_image.shape[:2]
    shm = shared_memory.SharedMemory(create=True, size=h * w * 3)
    shm_name = shm.name
    original_image = np.ndarray((h, w, 3), dtype=np.uint8, buffer=shm.buf)
    original_image[:] = input_image
    del input_image

    scale_factor = 800 / max(w, h)
    new_w, new_h = int(w * scale_factor), int(h * scale_factor)
    image = skimage.transform.resize(original_image, (new_h, new_w), anti_aliasing=True)
    num_block_scale_factor = sensitivity / min(w, h)  # 使用从命令行输入的 sensitivity
    NUM_BLOCK_INIT_V, NUM_BLOCK_INIT_H = math.ceil(w * num_block_scale_factor), math.ceil(
        h * num_block_scale_factor)

    # 3. 显示原始缩略图（替换 plt.show）
    plt.figure(figsize=(10, 6))
    plt.imshow(image)
    plt.axis('off')
    plt.tight_layout()
    print("\n=== 原始缩略图 ===")
    show_plot_in_terminal()

    # 等待用户确认（替换 messagebox.askyesno）
    print("\n是否继续处理？(Y/n):")
    response = input("> ").strip().lower()
    if response not in ['y', 'yes','Y', 'Yes','是', '1','']:
        print("操作已取消。")
        return

    # ... (检测边界线等逻辑保持不变) ...
    peaks_v, grad_profile_v, grad_map_v = detect_color_boundaries_vertical(image,
                                                                           num_blocks=NUM_BLOCK_INIT_V)
    peaks_h, grad_profile_h, grad_map_h = detect_color_boundaries_horizontal(image,
                                                                             num_blocks=NUM_BLOCK_INIT_H)

    # 绘制边界线（第一步）很多分界线
    plt.figure(figsize=(15, 8))
    show_split_image = image.copy()
    for i, boundary_v in enumerate(peaks_v):
        cv2.line(show_split_image, (boundary_v, 0), (boundary_v, image.shape[0]),
                 (255, 0, 0), 1)
    for i, boundary_h in enumerate(peaks_h):
        cv2.line(show_split_image, (0, boundary_h), (image.shape[1], boundary_h),
                 (255, 0, 0), 1)

    plt.imshow(show_split_image)
    plt.axis('off')
    plt.tight_layout()
    print("\n=== 检测到的分割线 (红色) ===")
    show_plot_in_terminal()

    # 4. 使用命令行输入获取用户选择的竖直分割线（替换 simpledialog.askstring）
    print(f"\n共检测到 {len(peaks_v)} 条竖直分割线")
    print("请输入需要保留的分割线序号（从1开始），用空格隔开（直接回车跳过不选）：")
    while True:
        input_text = input("> ").strip()
        if input_text == "":
            choose_v_list = []
            break
        try:
            choose_v_list = [int(i) - 1 for i in input_text.split() if i.isdigit()]
            if not choose_v_list:
                print("警告：你未输入任何有效数字，请重新输入（或直接回车跳过）。")
                continue
            if all(0 <= i < len(peaks_v) for i in choose_v_list):
                break
            else:
                print(f"警告：序号超出范围 (1-{len(peaks_v)})，请重新输入。")
        except ValueError:
            print("警告：请输入有效的数字，用空格分隔。")

    # 5. 使用命令行输入获取用户选择的水平分割线
    print(f"\n共检测到 {len(peaks_h)} 条水平分割线")
    print("请输入需要保留的分割线序号（从1开始），用空格隔开（直接回车跳过不选）：")
    while True:
        input_text = input("> ").strip()
        if input_text == "":
            choose_h_list = []
            break
        try:
            choose_h_list = [int(i) - 1 for i in input_text.split() if i.isdigit()]
            if not choose_h_list:
                print("警告：你未输入任何有效数字，请重新输入（或直接回车跳过）。")
                continue
            if all(0 <= i < len(peaks_h) for i in choose_h_list):
                break
            else:
                print(f"警告：序号超出范围 (1-{len(peaks_h)})，请重新输入。")
        except ValueError:
            print("警告：请输入有效的数字，用空格分隔。")

    # ... (后续处理逻辑保持不变，包括 choose_v_mask, peaks_v_sorted 等计算) ...
    choose_v_mask = np.zeros(NUM_BLOCK_INIT_V, dtype=bool)
    choose_h_mask = np.zeros(NUM_BLOCK_INIT_H, dtype=bool)

    for i in choose_v_list:
        try:
            choose_v_mask[i] = True
        except:
            print(f"警告：{i + 1} 是无效的竖直分割线序号，已忽略。")

    for i in choose_h_list:
        try:
            choose_h_mask[i] = True
        except:
            print(f"警告：{i + 1} 是无效的水平分割线序号，已忽略。")

    peaks_v_sorted = np.sort(peaks_v)[choose_v_mask]
    peaks_h_sorted = np.sort(peaks_h)[choose_h_mask]

    peaks_v_sorted_original = ((peaks_v_sorted / scale_factor).astype(np.int32)).tolist()
    peaks_h_sorted_original = ((peaks_h_sorted / scale_factor).astype(np.int32)).tolist()

    dx = math.ceil(w * 0.008)
    dy = math.ceil(h * 0.008)

    # 可视化选中的分割线
    plt.figure(figsize=(15, 8))
    show_split_image = image.copy()
    for i, boundary_v in enumerate(peaks_v_sorted):
        cv2.line(show_split_image, (boundary_v, 0), (boundary_v, image.shape[0]),
                 (0, 255, 0), 3)
    for i, boundary_h in enumerate(peaks_h_sorted):
        cv2.line(show_split_image, (0, boundary_h), (image.shape[1], boundary_h),
                 (0, 255, 0), 3)

    plt.imshow(show_split_image)
    plt.axis('off')
    plt.tight_layout()
    print("\n=== 选中的分割线（绿色）===")
    show_plot_in_terminal()

    # 6. 确认是否继续（替换 messagebox.askyesno）
    print("\n是否继续处理？(Y/n):")
    response = input("> ").strip().lower()
    if response not in ['y', 'yes','Y', 'Yes','是', '1','']:
        print("操作已取消。")
        return

    # 显示分块
    plt_col_len = len(peaks_v_sorted) + 1
    plt_row_len = len(peaks_h_sorted) + 1
    plt_slice_v = [0] + list(peaks_v_sorted) + [image.shape[1]]
    plt_slice_h = [0] + list(peaks_h_sorted) + [image.shape[0]]

    fig, axes = plt.subplots(plt_row_len, plt_col_len, figsize=(15, 8))

    for i in range(plt_row_len):
        for j in range(plt_col_len):
            ax = axes[i, j] if plt_row_len > 1 and plt_col_len > 1 else axes[i * plt_col_len + j]
            ax.imshow(image[plt_slice_h[i]:plt_slice_h[i + 1], plt_slice_v[j]:plt_slice_v[j + 1]])
            ax.axis("off")
            # ax.set_title(f"({i + 1},{j + 1})")

    plt.tight_layout()
    plt.axis('off')
    plt.tight_layout()
    print("\n=== 图像分块预览 ===")
    show_plot_in_terminal()

    # 7. 获取基准图块的行列号（替换 simpledialog.askstring）
    print(f"\n请选择基准图块（将以此图块的颜色为基准进行色彩匹配）。")
    while True:
        print(f"行号范围: 1-{plt_row_len}, 列号范围: 1-{plt_col_len}")
        print("请依次输入基准图块的行号、列号，用空格分开：")
        input_text = input("> ").strip()
        if input_text is None or input_text.lower() == 'cancel':
            print("操作已取消。")
            return
        try:
            parts = input_text.split()
            if len(parts) != 2:
                print("错误：需要两个数字，用空格分隔。")
                continue
            basic_block_h_idx = int(parts[0]) - 1
            basic_block_v_idx = int(parts[1]) - 1
            if 0 <= basic_block_h_idx < plt_row_len and 0 <= basic_block_v_idx < plt_col_len:
                break
            else:
                print(f"错误：行号范围: 1-{plt_row_len}, 列号范围: 1-{plt_col_len}")
        except ValueError as e:
            print(f"输入无效: {str(e)}，请重新输入。")

    # ... (直方图匹配处理逻辑保持不变) ...
    slice_v = [0] + list(peaks_v_sorted) + [w]
    slice_h = [0] + list(peaks_h_sorted) + [h]

    for i in range(plt_row_len):
        for j in range(plt_col_len):
            if (i, j) != (basic_block_h_idx, basic_block_v_idx):
                image[
                    slice_h[i]:slice_h[i + 1],
                    slice_v[j]:slice_v[j + 1]
                ] = skimage.exposure.match_histograms(
                    image[
                        slice_h[i]:slice_h[i + 1],
                        slice_v[j]:slice_v[j + 1]
                    ],
                    image[
                        slice_h[basic_block_h_idx]:slice_h[basic_block_h_idx + 1],
                        slice_v[basic_block_v_idx]:slice_v[basic_block_v_idx + 1]
                    ], channel_axis=-1)

    # 显示缩略图预览
    plt.figure(figsize=(10, 6))
    plt.imshow(image)
    plt.axis('off')
    plt.tight_layout()
    print("\n=== 直方图匹配后的缩略图预览 ===")
    show_plot_in_terminal()

    # 8. 确认是否继续处理原图（替换 messagebox.askyesno）
    print("\n预览图已生成，是否继续处理原图？(Y/n):")
    response = input("> ").strip().lower()
    if response not in ['y', 'yes','Y','Yes', '是', '1','']:
        print("操作已取消。")
        return

    # 9. 选择输出文件（替换 filedialog.asksaveasfilename）
    print("\n请提供输出图片的完整保存路径（包括文件名和扩展名，如：/path/to/output.png）:")
    OUTPUT_FILE_PATH = input("> ").strip()
    if not OUTPUT_FILE_PATH:
        print("未提供保存路径，操作取消。")
        return

    x_divisions = []
    y_divisions = []

    for x in peaks_v_sorted_original:
        x_divisions.append(detect_original_vertical(x, dx))
    for y in peaks_h_sorted_original:
        y_divisions.append(detect_original_horizontal(y, dx))
        time.sleep(5)

    original_slice_v = [0] + list(x_divisions) + [w]
    original_slice_h = [0] + list(y_divisions) + [h]

    params_list = []
    for i in range(plt_row_len):
        for j in range(plt_col_len):
            if (i, j) != (basic_block_h_idx, basic_block_v_idx):
                params_list.append((
                    original_slice_v[j],
                    original_slice_h[i],
                    original_slice_v[j + 1],
                    original_slice_h[i + 1],
                    original_slice_v[basic_block_v_idx],
                    original_slice_h[basic_block_h_idx],
                    original_slice_v[basic_block_v_idx + 1],
                    original_slice_h[basic_block_h_idx + 1],
                    h,
                    w,
                    shm_name
                ))

    with Pool(cpu_count() // 2) as pool:
        pool.starmap(single_original_process_image, params_list)

    # 保存图片
    if original_image.dtype == np.float64 or original_image.dtype == np.float32:
        if original_image.max() <= 1.0:
            original_image = (original_image * 255).astype(np.uint8)
        else:
            original_image = np.clip(original_image, 0, 255).astype(np.uint8)
    elif original_image.dtype != np.uint8:
        original_image = original_image.astype(np.uint8)

    try:
        skimage.io.imsave(OUTPUT_FILE_PATH, original_image)
        print(f"成功！处理后的图片已保存到：{OUTPUT_FILE_PATH}")
    except Exception as e:
        print(f"错误: 保存图片失败: {str(e)}")
    finally:
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    print("=== 色彩平衡工具 (CLI 版本) ===\n")
    process_image()