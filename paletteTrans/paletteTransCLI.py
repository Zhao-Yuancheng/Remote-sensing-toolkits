#!/usr/bin/env python3
"""
TIFF调色板转RGB - 多进程优化版（使用PIL）
支持将单通道调色板TIFF转换为标准RGB图像，适合AI训练使用
"""

import multiprocessing as mp
import os
import sys
import time
import argparse
from multiprocessing import shared_memory, freeze_support
from typing import Tuple, List
from tqdm import tqdm

import numpy as np
from PIL import Image


def create_shared_memory_blocks(
        input_path: str
) -> Tuple[shared_memory.SharedMemory, shared_memory.SharedMemory,
np.ndarray, Tuple[int, int, int], dict]:
    """
    创建输入输出共享内存块

    返回:
        shm_input: 输入共享内存
        shm_output: 输出共享内存
        palette_lut: 调色板查找表
        output_shape: 输出形状 (3, H, W)
        metadata: 元数据
    """
    image = Image.open(input_path)

    # 检查是否为调色板图像
    if image.mode != 'P':
        raise ValueError("输入文件不是调色板图像 (P mode)")

    data = np.array(image)
    input_shape = data.shape
    input_dtype = data.dtype

    # 获取调色板
    palette = image.getpalette()
    if palette is None:
        raise ValueError("输入文件没有调色板")

    palette_lut = np.zeros((256, 3), dtype=np.uint8)

    # PIL的调色板是长度为768的列表 [R0, G0, B0, R1, G1, B1, ...]
    for i in range(256):
        idx = i * 3
        if idx + 2 < len(palette):
            palette_lut[i] = [palette[idx], palette[idx + 1], palette[idx + 2]]

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


def divide_rows(total_rows: int, n_blocks: int) -> List[Tuple[int, int]]:
    """将行数分成块"""
    rows_per_block = total_rows // n_blocks
    blocks = []
    for i in range(n_blocks):
        start = i * rows_per_block
        end = start + rows_per_block if i < n_blocks - 1 else total_rows
        blocks.append((start, end))
    return blocks


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
    """
    # 连接到共享内存
    shm_input = shared_memory.SharedMemory(name=shm_input_name)
    shm_output = shared_memory.SharedMemory(name=shm_output_name)

    # 创建数组视图
    input_array = np.ndarray(input_shape, dtype=np.uint8, buffer=shm_input.buf)
    output_array = np.ndarray(output_shape, dtype=np.uint8, buffer=shm_output.buf)

    start_time = time.time()

    # 调用Cython处理函数
    from palette_processor_cy import process_palette_block
    process_palette_block(
        input_array,
        output_array,
        palette_lut,
        start_row,
        end_row
    )

    elapsed = time.time() - start_time

    # 清理
    shm_input.close()
    shm_output.close()

    return elapsed


def convert_palette_geotiff(
        input_path: str,
        output_path: str,
        nproc: int
) -> None:
    """
    主函数：转换调色板TIFF为RGB
    """
    print("\n" + "=" * 60)
    print("TIFF调色板转换工具")
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"工作进程数: {nproc}")
    print("=" * 60)

    # 尝试导入Cython模块
    try:
        from palette_processor_cy import process_palette_block
        use_cython = True
    except ImportError:
        print("注意: 未找到Cython优化模块，将使用Python版本（速度较慢）")
        use_cython = False
        process_palette_block = None

    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在: {input_path}")
        sys.exit(1)

    # 检查输出目录是否存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    # 1. 创建共享内存
    print("\n1. 加载图像并创建共享内存...")
    try:
        shm_input, shm_output, palette_lut, output_shape, metadata = \
            create_shared_memory_blocks(input_path)
    except ValueError as e:
        print(f"错误: 输入文件格式错误 - {e}")
        print("提示: 请确保输入文件是单通道调色板TIFF图像（模式为'P'）")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 无法加载输入文件 - {e}")
        sys.exit(1)

    input_shape = metadata['input_shape']
    total_rows = input_shape[0]

    print(f"   输入尺寸: {input_shape[1]}×{input_shape[0]} 像素")
    print(f"   输出尺寸: {output_shape[2]}×{output_shape[1]}×{output_shape[0]} (C×H×W)")
    print(f"   内存需求: 输入 {input_shape[0] * input_shape[1] / 1024 / 1024:.2f} MB, "
          f"输出 {output_shape[0] * output_shape[1] * output_shape[2] / 1024 / 1024:.2f} MB")

    # 2. 分块
    nproc = min(nproc, total_rows)  # 进程数不能超过行数
    blocks = divide_rows(total_rows, nproc)

    print(f"\n2. 任务划分:")
    print(f"   总行数: {total_rows}")
    print(f"   使用进程: {nproc}")
    print(f"   块划分: {[f'({start},{end})' for start, end in blocks]}")

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
    print(f"\n3. 启动进程池处理...")
    start_time = time.time()

    try:
        with mp.Pool(processes=nproc) as pool:
            if use_cython:
                print(f"   使用Cython加速版本")
                results = list(tqdm(
                    pool.starmap(worker_process_cy, args_list),
                    total=len(args_list),
                    desc="处理进度",
                    ncols=100,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
                ))
            else:
                print(f"   使用Python标准版本")
                results = list(tqdm(
                    pool.starmap(worker_process_py, args_list),
                    total=len(args_list),
                    desc="处理进度",
                    ncols=100,
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
                ))
    except KeyboardInterrupt:
        print("\n处理被用户中断")
        shm_input.close()
        shm_input.unlink()
        shm_output.close()
        shm_output.unlink()
        sys.exit(1)

    total_time = time.time() - start_time

    # 显示处理时间统计
    if len(results) > 0:
        avg_time = sum(results) / len(results)
        print(f"   平均块处理时间: {avg_time:.3f}秒")

    print(f"   总处理时间: {total_time:.3f}秒")
    if total_rows > 0:
        print(f"   处理速度: {total_rows / total_time:.1f} 行/秒")

    # 5. 从共享内存读取结果
    print(f"\n4. 读取处理结果...")
    output_array = np.ndarray(
        output_shape,
        dtype=np.uint8,
        buffer=shm_output.buf
    ).copy()

    # 6. 保存结果
    print(f"5. 保存结果到: {output_path}")
    try:
        # (3, H, W)->(H, W, 3)
        rgb_array = np.transpose(output_array, (1, 2, 0))

        # 保存为RGB图像
        rgb_image = Image.fromarray(rgb_array, mode='RGB')
        rgb_image.save(output_path)

        # 获取文件大小
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   输出文件大小: {file_size:.2f} MB")
    except Exception as e:
        print(f"错误: 保存输出文件失败 - {e}")
        shm_input.close()
        shm_input.unlink()
        shm_output.close()
        shm_output.unlink()
        sys.exit(1)

    # 7. 清理共享内存
    shm_input.close()
    shm_input.unlink()
    shm_output.close()
    shm_output.unlink()

    print(f"\n" + "=" * 60)
    print("转换完成!")
    print(f"输出文件: {output_path}")
    print(f"图像尺寸: {rgb_array.shape[1]}×{rgb_array.shape[0]} 像素")
    print(f"通道数: 3 (RGB)")
    print("=" * 60)


if __name__ == "__main__":
    # 设置PIL支持大图像
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    parser = argparse.ArgumentParser(
        description='调色板TIFF转RGB工具 - 将单通道调色板TIFF转换为标准RGB图像',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python paletteTransCLI.py --file_path ./input_palette.tif --result_path ./output_rgb.tif --proc_num 8

注意事项:
  1. 输入文件必须是单通道调色板TIFF（图像模式为'P'）
  2. 输出文件将保存为标准RGB图像
  3. 程序会自动尝试使用Cython加速模块（如存在），否则使用Python版本
  4. proc_num建议设置为CPU核心数或略少于核心数
        """
    )

    parser.add_argument('--file_path', type=str, required=True,
                        help='输入TIFF文件路径（必须是调色板图像）')
    parser.add_argument('--result_path', type=str, required=True,
                        help='输出RGB图像路径，支持TIFF、PNG、JPEG等格式')
    parser.add_argument('--proc_num', type=int, default=None,
                        help='并发进程数（默认: CPU核心数的一半，建议1-16之间）')

    args = parser.parse_args()

    # 设置默认进程数
    if args.proc_num is None:
        args.proc_num = max(1, mp.cpu_count() // 2)

    # 验证进程数
    if args.proc_num <= 0:
        print("错误: 进程数必须大于0")
        sys.exit(1)
    if args.proc_num > 32:
        print(f"警告: 进程数({args.proc_num})较大，可能影响系统性能")

    # 执行转换
    convert_palette_geotiff(args.file_path, args.result_path, args.proc_num)