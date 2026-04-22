import math
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import skimage
from PIL import Image, ImageFile
from scipy import signal
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
from skimage.color import rgb2lab, rgba2rgb

matplotlib.use('TkAgg')

w = None
h = None
original_image = None
image = None

NUM_BLOCK_INIT_V = 5
NUM_BLOCK_INIT_H = 5

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
    # plt.plot(grad_profile_v)
    # plt.show(block=False)
    if len(p_v) == 0:
        return x

    return p_v[0].tolist() + x1


def detect_original_horizontal(y, dy):
    global original_image, h
    y1, y2 = max(0, y - dy), min(y + dy, h)
    img = original_image[y1:y2 + 1, :, :]
    p_h, grad_profile_h, grad_norm_h = detect_color_boundaries_horizontal(img, num_blocks=3)
    # plt.plot(grad_profile_h)
    # plt.show(block=False)
    if len(p_h) == 0:
        return y
    return p_h[0].tolist() + y1


def process_image():
    global h, w, original_image, image
    # 1. 打开输入文件
    filetypes = [
        ('Image files', '*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif'),
        ('All files', '*.*')
    ]

    INPUT_FILE_PATH = filedialog.askopenfilename(
        title="选择输入图片",
        filetypes=filetypes
    )

    if not INPUT_FILE_PATH:
        return

    try:
        original_image = skimage.io.imread(INPUT_FILE_PATH)
        if original_image.shape[2] == 4:
            original_image = rgba2rgb(original_image)
    except Exception as e:
        messagebox.showerror("错误", f"无法读取图片: {str(e)}")
        return

    h, w = original_image.shape[:2]

    scale_factor = 800 / max(w, h)  # 目标最大边长为800
    new_w, new_h = int(w * scale_factor), int(h * scale_factor)
    image = skimage.transform.resize(original_image, (new_h, new_w), anti_aliasing=True)

    # 创建GUI窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 显示原始缩略图
    plt.figure(figsize=(10, 6))
    plt.imshow(image)
    plt.title("原始缩略图")
    plt.axis('off')
    plt.show(block=False)

    # 等待用户确认
    if not messagebox.askyesno("确认", "是否继续处理？"):
        plt.close('all')
        return
    plt.close('all')

    peaks_v, grad_profile_v, grad_map_v = detect_color_boundaries_vertical(image,
                                                                           num_blocks=NUM_BLOCK_INIT_V)
    peaks_h, grad_profile_h, grad_map_h = detect_color_boundaries_horizontal(image,
                                                                             num_blocks=NUM_BLOCK_INIT_H)

    # 绘制边界线（第一步）很多分界线
    plt.figure(figsize=(15, 8))
    show_split_image = image.copy()
    for i, boundary_v in enumerate(peaks_v):
        cv2.line(show_split_image, (boundary_v, 0), (boundary_v, image.shape[0]),
                 (255, 0, 0), 3)
    for i, boundary_h in enumerate(peaks_h):
        cv2.line(show_split_image, (0, boundary_h), (image.shape[1], boundary_h),
                 (255, 0, 0), 3)

    plt.imshow(show_split_image)
    plt.title("检测到的分割线")
    plt.show(block=False)

    # 使用对话框获取用户选择的竖直分割线
    while True:
        input_text = simpledialog.askstring(
            "选择竖直分割线",
            f"共检测到 {len(peaks_v)} 条竖直分割线\n"
            f"请输入需要保留的分割线序号（从1开始），用空格隔开："
        )
        if input_text is None:
            plt.close('all')
            return
        try:
            choose_v_list = [int(i) - 1 for i in input_text.strip().split(" ") if i.isdigit()]
            if all(0 <= i < len(peaks_v) for i in choose_v_list):
                break
            else:
                messagebox.showwarning("警告", f"序号超出范围 (1-{len(peaks_v)})")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字")

    # 使用对话框获取用户选择的水平分割线
    while True:
        input_text = simpledialog.askstring(
            "选择水平分割线",
            f"共检测到 {len(peaks_h)} 条水平分割线\n"
            f"请输入需要保留的分割线序号（从1开始），用空格隔开："
        )
        if input_text is None:
            plt.close('all')
            return
        try:
            choose_h_list = [int(i) - 1 for i in input_text.strip().split(" ") if i.isdigit()]
            if all(0 <= i < len(peaks_h) for i in choose_h_list):
                break
            else:
                messagebox.showwarning("警告", f"序号超出范围 (1-{len(peaks_h)})")
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的数字")

    plt.close('all')

    choose_v_mask = np.zeros(NUM_BLOCK_INIT_V, dtype=bool)
    choose_h_mask = np.zeros(NUM_BLOCK_INIT_H, dtype=bool)

    for i in choose_v_list:
        try:
            choose_v_mask[i] = True
        except:
            messagebox.showwarning("警告", f"{i + 1} 是无效的竖直分割线序号")

    for i in choose_h_list:
        try:
            choose_h_mask[i] = True
        except:
            messagebox.showwarning("警告", f"{i + 1} 是无效的水平分割线序号")

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
    plt.title("选中的分割线（绿色）")
    plt.show(block=True)

    plt.close('all')

    # 显示分块
    plt_col_len = len(peaks_v_sorted) + 1
    plt_row_len = len(peaks_h_sorted) + 1
    plt_slice_v = [0] + list(peaks_v_sorted) + [image.shape[1]]
    plt_slice_h = [0] + list(peaks_h_sorted) + [image.shape[0]]

    fig, axes = plt.subplots(plt_row_len, plt_col_len, figsize=(15, 8))
    fig.suptitle("图像分块预览")

    for i in range(plt_row_len):
        for j in range(plt_col_len):
            ax = axes[i, j] if plt_row_len > 1 and plt_col_len > 1 else axes[i * plt_col_len + j]
            ax.imshow(image[plt_slice_h[i]:plt_slice_h[i + 1], plt_slice_v[j]:plt_slice_v[j + 1]])
            ax.axis("off")
            ax.set_title(f"({i + 1},{j + 1})")

    plt.tight_layout()
    plt.show(block=False)

    # 获取基准图块的行列号
    while True:
        input_text = simpledialog.askstring(
            "选择基准图块",
            f"请依次输入基准图块的行号、列号，用空格分开：\n"
            f"行号范围: 1-{plt_row_len}, 列号范围: 1-{plt_col_len}"
        )
        if input_text is None:
            plt.close('all')
            return
        try:
            parts = input_text.strip().split()
            if len(parts) != 2:
                raise ValueError("需要两个数字")
            basic_block_h_idx = int(parts[0]) - 1
            basic_block_v_idx = int(parts[1]) - 1
            if 0 <= basic_block_h_idx < plt_row_len and 0 <= basic_block_v_idx < plt_col_len:
                break
            else:
                messagebox.showwarning("警告",
                                       f"行号范围: 1-{plt_row_len}, 列号范围: 1-{plt_col_len}")
        except ValueError as e:
            messagebox.showwarning("警告", f"输入无效: {str(e)}")

    plt.close('all')

    slice_v = [0] + list(peaks_v_sorted) + [w]
    slice_h = [0] + list(peaks_h_sorted) + [h]

    # 应用直方图匹配
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
    plt.title("直方图匹配后的缩略图预览")
    plt.show(block=False)

    # 确认是否继续
    if not messagebox.askyesno("确认", "预览图已生成，是否继续处理原图？"):
        plt.close('all')
        messagebox.showinfo("提示", "操作已取消")
        return

    plt.close('all')

    # 选择输出文件
    OUTPUT_FILE_PATH = filedialog.asksaveasfilename(
        title="保存处理后的图片",
        defaultextension=".png",
        filetypes=filetypes
    )

    if not OUTPUT_FILE_PATH:
        plt.close('all')
        return

    print(0, original_image.shape)

    # 处理原图
    x_divisions = []
    y_divisions = []

    for x in peaks_v_sorted_original:
        x_divisions.append(detect_original_vertical(x, dx))
    for y in peaks_h_sorted_original:
        y_divisions.append(detect_original_horizontal(y, dx))
        time.sleep(5)

    original_slice_v = [0] + list(x_divisions) + [w]
    original_slice_h = [0] + list(y_divisions) + [h]
    print(1, original_image.shape)

    for i in range(plt_row_len):
        for j in range(plt_col_len):
            if (i, j) != (basic_block_h_idx, basic_block_v_idx):
                original_image[
                    original_slice_h[i]:original_slice_h[i + 1],
                    original_slice_v[j]:original_slice_v[j + 1]
                ] = skimage.exposure.match_histograms(
                    original_image[
                        original_slice_h[i]:original_slice_h[i + 1],
                        original_slice_v[j]:original_slice_v[j + 1]
                    ],
                    original_image[
                        original_slice_h[basic_block_h_idx]:original_slice_h[basic_block_h_idx + 1],
                        original_slice_v[basic_block_v_idx]:original_slice_v[basic_block_v_idx + 1]
                    ], channel_axis=-1)

    print(2, original_image.shape)
    # 保存图片
    # 添加数据类型转换
    if original_image.dtype == np.float64 or original_image.dtype == np.float32:
        # 检查值的范围
        if original_image.max() <= 1.0:
            # 如果值在0-1范围内，转换为0-255
            original_image = (original_image * 255).astype(np.uint8)
        else:
            # 如果值在0-255范围内，直接转换为uint8
            original_image = np.clip(original_image, 0, 255).astype(np.uint8)
    elif original_image.dtype != np.uint8:
        # 如果是其他类型，也转换为uint8
        original_image = original_image.astype(np.uint8)

    print(3, original_image.shape, original_image.dtype, original_image.min(), original_image.max())

    # 保存图片
    try:
        skimage.io.imsave(OUTPUT_FILE_PATH, original_image)
        messagebox.showinfo("成功", f"处理成功！图片已保存到：\n{OUTPUT_FILE_PATH}")
    except Exception as e:
        messagebox.showerror("错误", f"保存图片失败: {str(e)}")


if __name__ == "__main__":
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    Image.MAX_IMAGE_PIXELS = None
    # 创建主窗口
    root = tk.Tk()
    root.title("图片分割与直方图匹配工具")
    root.geometry("300x150")

    # 添加按钮
    btn_process = tk.Button(
        root,
        text="开始处理图片",
        command=process_image,
        font=("Arial", 12),
        height=2,
        width=20
    )
    btn_process.pack(expand=True, padx=20, pady=20)

    btn_exit = tk.Button(
        root,
        text="退出",
        command=root.quit,
        font=("Arial", 10)
    )
    btn_exit.pack(pady=10)

    root.mainloop()
