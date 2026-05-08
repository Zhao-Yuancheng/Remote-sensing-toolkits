#!/usr/bin/env python3
"""
GeoTIFF调色板转RGB - 多进程Cython优化版
"""

import numpy as np
import multiprocessing as mp
from multiprocessing import shared_memory,freeze_support
from osgeo import gdal
import time
import os
from typing import Tuple, List
import sys

# 添加Cython模块路径
sys.path.append('.')
try:
    from palette_processor_cy import process_palette_block
except ImportError:
    print("警告: 未找到Cython模块，将使用Python版本")
    process_palette_block = None

# process_palette_block = None

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
    dataset = gdal.Open(input_path)
    if dataset is None:
        raise ValueError(f"无法打开文件: {input_path}")

    band = dataset.GetRasterBand(1)
    color_table = band.GetColorTable()
    if color_table is None:
        raise ValueError("输入文件没有调色板")

    # 读取数据
    data = band.ReadAsArray()
    input_shape = data.shape
    input_dtype = data.dtype

    # 创建调色板查找表
    palette_lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        color = color_table.GetColorEntry(i)
        if color:
            palette_lut[i] = [color[0], color[1], color[2]]

    # 计算输出形状
    output_shape = (3, input_shape[0], input_shape[1])

    # 创建输入共享内存
    shm_input = shared_memory.SharedMemory(
        create=True,
        size=data.nbytes
    )
    input_array = np.ndarray(input_shape, dtype=input_dtype, buffer=shm_input.buf)
    np.copyto(input_array, data)

    # 创建输出共享内存
    shm_output = shared_memory.SharedMemory(
        create=True,
        size=int(np.prod(output_shape) * np.dtype(np.uint8).itemsize)
    )

    # 初始化输出为0
    output_array = np.ndarray(output_shape, dtype=np.uint8, buffer=shm_output.buf)
    output_array[:] = 0

    # 保存元数据
    metadata = {
        'transform': dataset.GetGeoTransform(),
        'projection': dataset.GetProjection(),
        'input_shape': input_shape,
        'output_shape': output_shape
    }

    dataset = None
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
        output_path: str = None
) -> None:
    """
    主函数：转换调色板GeoTIFF为RGB
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_rgb{ext}"

    # 确定工作进程数
    n_workers = max(1, mp.cpu_count() // 2)

    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"工作进程数: {n_workers}")
    print(f"使用Cython: {process_palette_block is not None}")

    # 1. 创建共享内存
    print("创建共享内存...")
    shm_input, shm_output, palette_lut, output_shape, metadata = \
        create_shared_memory_blocks(input_path)

    input_shape = metadata['input_shape']
    total_rows = input_shape[0]

    # 2. 分块
    blocks = divide_rows(total_rows, n_workers)
    print(f"图像尺寸: {input_shape}")
    print(f"分块: {blocks}")

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
    print("启动进程池...")
    start_time = time.time()

    with mp.Pool(processes=n_workers) as pool:
        if process_palette_block is not None:
            results = pool.starmap(worker_process_cy, args_list)
        else:
            results = pool.starmap(worker_process_py, args_list)

    total_time = time.time() - start_time
    print(f"处理完成，总时间: {total_time:.3f}秒")

    # 5. 从共享内存读取结果
    output_array = np.ndarray(
        output_shape,
        dtype=np.uint8,
        buffer=shm_output.buf
    ).copy()

    # 6. 保存结果
    print("保存结果...")
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(
        output_path,
        input_shape[1],  # 宽度
        input_shape[0],  # 高度
        3,  # 波段数
        gdal.GDT_Byte
    )

    dataset.SetGeoTransform(metadata['transform']) # TODO 此处是否有元数据需要重新写入，如果不存在是否报错
    dataset.SetProjection(metadata['projection'])

    for i in range(3):
        band = dataset.GetRasterBand(i + 1)
        band.WriteArray(output_array[i])
        band.FlushCache()

    dataset = None

    # 7. 清理共享内存
    shm_input.close()
    shm_input.unlink()
    shm_output.close()
    shm_output.unlink()

    print(f"转换完成!")


if __name__ == "__main__":
    import argparse

    # parser = argparse.ArgumentParser(description='转换调色板GeoTIFF为RGB')
    # parser.add_argument('input', help='输入GeoTIFF文件')
    # parser.add_argument('-o', '--output', help='输出GeoTIFF文件')
    #
    # args = parser.parse_args()

    # convert_palette_geotiff(args.input, args.output)
    freeze_support()
    convert_palette_geotiff("ptest.tif", "new.tif")