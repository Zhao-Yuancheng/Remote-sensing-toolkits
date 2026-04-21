import math
import sys
import time
import  matplotlib

import cv2
import matplotlib.pyplot as plt
import numpy as np
import skimage
from scipy import signal
from scipy.ndimage import gaussian_filter
from scipy.signal import find_peaks
from skimage.color import rgb2lab, rgba2rgb


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



if __name__ == "__main__":
    INPUT_FILE_PATH = #TODO
    original_image = skimage.io.imread(INPUT_FILE_PATH)
    if original_image.shape[2] == 4:
        original_image = rgba2rgb(original_image)

    h, w = original_image.shape[:2]

    scale_factor = 800 / max(w, h)  # 目标最大边长为800
    new_w, new_h = int(w * scale_factor), int(h * scale_factor)
    image = skimage.transform.resize(original_image, (new_h, new_w), anti_aliasing=True)

    

    plt.figure(figsize=(10, 6))
    plt.imshow(image)
    plt.title("原始缩略图")
    plt.axis('off')
    plt.show(block=False)

    

    peaks_v, grad_profile_v, grad_map_v = detect_color_boundaries_vertical(image,
                                                                           num_blocks=NUM_BLOCK_INIT_V)
    peaks_h, grad_profile_h, grad_map_h = detect_color_boundaries_horizontal(image,
                                                                             num_blocks=NUM_BLOCK_INIT_H)
    

    plt.figure(figsize=(15, 8))

    # 绘制边界线（第一步）很多分界线
    show_split_image = image.copy()
    for i, boundary_v in enumerate(peaks_v):
        cv2.line(show_split_image, (boundary_v, 0), (boundary_v, image.shape[0]),
                 (255, 0, 0), 3)
    for i, boundary_h in enumerate(peaks_h):
        cv2.line(show_split_image, (0, boundary_h), (image.shape[1], boundary_h),
                 (255, 0, 0), 3)

    plt.imshow(show_split_image)
    plt.show(block=False)

    
    print("请选择需要保留的分割线序号（从1开始），若有多个数据，请用空格隔开")
    choose_v_list = [int(i) - 1 for i in input("竖直分割线：").strip().split(" ") if i.isdigit()]
    choose_h_list = [int(i) - 1 for i in input("水平分割线：").strip().split(" ") if i.isdigit()]
    choose_v_mask = np.zeros(NUM_BLOCK_INIT_V, dtype=bool)
    choose_h_mask = np.zeros(NUM_BLOCK_INIT_H, dtype=bool)
    for i in choose_v_list:
        try:
            choose_v_mask[i] = True
        except:
            print(f"{i} is an error index for vertical list: {choose_v_list}")
    for i in choose_h_list:
        try:
            choose_h_mask[i] = True
        except:
            print(f"{i} is an error index for horizontal list: {choose_h_list}")

    
    peaks_v_sorted = np.sort(peaks_v)[choose_v_mask]
    peaks_h_sorted = np.sort(peaks_h)[choose_h_mask]

    peaks_v_sorted_original = ((peaks_v_sorted / scale_factor).astype(np.int32)).tolist()
    peaks_h_sorted_original = ((peaks_h_sorted / scale_factor).astype(np.int32)).tolist()

    dx = math.ceil(w * 0.008)
    dy = math.ceil(h * 0.008)

    
    # 可视化分割结果（第二次）选中的分割线
    plt.figure(figsize=(15, 8))

    # 绘制边界线
    show_split_image = image.copy()
    for i, boundary_v in enumerate(peaks_v_sorted):
        cv2.line(show_split_image, (boundary_v, 0), (boundary_v, image.shape[0]),
                 (255, 0, 0), 3)
    for i, boundary_h in enumerate(peaks_h_sorted):
        cv2.line(show_split_image, (0, boundary_h), (image.shape[1], boundary_h),
                 (255, 0, 0), 3)

    plt.imshow(show_split_image)
    plt.show(block=False)

    
    plt_col_len = len(peaks_v_sorted) + 1
    plt_row_len = len(peaks_h_sorted) + 1
    plt_slice_v = [0] + list(peaks_v_sorted) + [image.shape[1]]
    plt_slice_h = [0] + list(peaks_h_sorted) + [image.shape[0]]

    for i in range(plt_row_len):
        for j in range(plt_col_len):
            plt.subplot(plt_row_len, plt_col_len, i * plt_col_len + j + 1)
            plt.imshow(image[plt_slice_h[i]:plt_slice_h[i + 1], plt_slice_v[j]:plt_slice_v[j + 1]])
            plt.axis("off")
    plt.tight_layout()
    plt.show(block=False)

    
    [basic_block_h_idx, basic_block_v_idx] = [int(i) - 1 for i in input(
        "请依次输入基准图块的行号、列号，用空格分开：").strip().split(" ")]

    
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

    plt.title("缩略图预览")
    plt.imshow(image)
    plt.show(block=False)

    if input("预览图已生成，是否继续操作？(Y/n) ") in ["N", "n", "No", "no"]:
        print("欢迎使用")
        sys.exit()

    OUTPUT_FILE_PATH = #TODO

    x_divisions = []
    y_divisions = []

    for x in peaks_v_sorted_original:
        x_divisions.append(detect_original_vertical(x, dx))
    for y in peaks_h_sorted_original:
        y_divisions.append(detect_original_horizontal(y, dx))
        time.sleep(5)

    original_slice_v = [0] + list(x_divisions) + [w]
    original_slice_h = [0] + list(y_divisions) + [h]

    
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

    skimage.io.imsave(OUTPUT_FILE_PATH, original_image)
    print("处理成功！")