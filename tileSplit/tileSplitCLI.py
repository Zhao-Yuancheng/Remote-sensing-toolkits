import argparse
from PIL import Image
import numpy as np
from multiprocessing import shared_memory
from multiprocessing import Pool
from multiprocessing import freeze_support
import os
import sys
from tqdm import tqdm


def split_tile_wrapper(args):
    """包装函数，用于多进程调用和进度跟踪"""
    result = split_tile(*args[:-1])  # 最后一个参数是进度计数器
    # 更新进度
    args[-1].value += 1
    return result


def split_tile(result_root, save_x, save_y, result_format, x1, y1, x2, y2, shm_name, h, w,
               channels):
    """
    从大图中分割单个瓦片
    参数:
        result_root: 结果保存根目录
        save_x, save_y: 保存的瓦片行列号
        result_format: 瓦片文件格式
        x1, y1, x2, y2: 瓦片在大图中的坐标范围
        shm_name: 共享内存名称
        h, w: 大图的高度和宽度
        channels: 通道数
    返回:
        成功返回1，失败返回0
    """
    try:
        # 打开共享内存
        existing_shm = shared_memory.SharedMemory(name=shm_name, create=False)

        # 根据通道数创建不同形状的数组
        if channels == 1:
            tot_map = np.ndarray((h, w), dtype=np.uint8, buffer=existing_shm.buf)
        else:  # channels == 3
            tot_map = np.ndarray((h, w, 3), dtype=np.uint8,
                                 buffer=existing_shm.buf)

        # 创建保存目录
        os.makedirs(os.path.join(result_root, str(save_x)), exist_ok=True)
        save_path = os.path.join(result_root, str(save_x),
                                 str(save_y) + "." + result_format.replace(".", ""))

        # 提取瓦片区域
        if channels == 1:
            array = tot_map[y1:y2, x1:x2]
        else:
            array = tot_map[y1:y2, x1:x2, :]

        # 保存瓦片
        Image.fromarray(array).save(save_path)
        existing_shm.close()
        return 1  # 成功

    except FileNotFoundError:
        print(f"错误: 无法访问共享内存 {shm_name}", flush=True)
        return 0
    except Exception as e:
        print(f"错误: 处理瓦片({save_x}, {save_y})时发生异常: {e}", flush=True)
        return 0


if __name__ == "__main__":
    # 设置PIL最大图像像素，防止大图报错
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    parser = argparse.ArgumentParser(
        description="多进程瓦片分割工具 - 将大幅遥感图像自动分割为标准尺寸的瓦片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python tileSplitCLI.py --file_path ./large_image.png --result_dir ./tiles --result_format png \\
    --x_begin 1000 --x_step 1 --y_begin 1000 --y_step 1 \\
    --tile_width 256 --tile_height 256 --tile_channels 3 --proc_num 8

参数说明:
  x_begin, y_begin: 瓦片起始编号，用于生成瓦片文件名
  x_step, y_step: 瓦片编号的步长（通常为1）
  tile_width, tile_height: 生成的瓦片尺寸
  tile_channels: 1-灰度图，3-RGB彩色图
        """
    )

    # 必需参数
    parser.add_argument('--file_path', type=str, required=True,
                        help='输入的大幅遥感图像路径，支持PNG、JPEG、TIFF等格式')
    parser.add_argument('--result_dir', type=str, required=True,
                        help='瓦片保存的根目录，目录结构为 result_dir/X/Y.format')
    parser.add_argument('--result_format', type=str, required=True,
                        help='瓦片文件格式，如 "png", "jpg", "tif"（无需加点）')
    parser.add_argument('--x_begin', type=int, required=True,
                        help='X方向瓦片起始编号，用于生成瓦片文件名')
    parser.add_argument('--x_step', type=int, required=True,
                        help='X方向瓦片编号步长（通常为1）')
    parser.add_argument('--y_begin', type=int, required=True,
                        help='Y方向瓦片起始编号，用于生成瓦片文件名')
    parser.add_argument('--y_step', type=int, required=True,
                        help='Y方向瓦片编号步长（通常为1）')
    parser.add_argument('--tile_width', type=int, required=True,
                        help='生成的瓦片宽度（像素）')
    parser.add_argument('--tile_height', type=int, required=True,
                        help='生成的瓦片高度（像素）')
    parser.add_argument('--tile_channels', type=int, choices=[1, 3], required=True,
                        help='瓦片通道数: 1表示灰度图，3表示RGB彩色图')
    parser.add_argument('--proc_num', type=int, required=True,
                        help='使用的进程数，建议设置为CPU核心数或略少于核心数')

    # 可选参数
    parser.add_argument('--skip_existing', action='store_true',
                        help='如果结果目录已存在则跳过分割')

    args = parser.parse_args()

    # 参数验证
    if not os.path.exists(args.file_path):
        print(f"错误: 输入文件不存在: {args.file_path}")
        sys.exit(1)

    if args.tile_width <= 0 or args.tile_height <= 0:
        print("错误: 瓦片尺寸必须大于0")
        sys.exit(1)

    if args.x_step <= 0 or args.y_step <= 0:
        print("错误: 步长必须大于0")
        sys.exit(1)

    if args.proc_num <= 0:
        print("错误: 进程数必须大于0")
        sys.exit(1)

    # 检查结果目录
    if args.skip_existing and os.path.exists(args.result_dir):
        print(f"结果目录已存在: {args.result_dir}")
        print("跳过分割过程")
        sys.exit(0)

    # 创建结果目录
    os.makedirs(args.result_dir, exist_ok=True)

    print("\n" + "=" * 60)
    print("瓦片分割工具启动")
    print(f"输入文件: {args.file_path}")
    print(f"输出目录: {args.result_dir}")
    print(f"瓦片格式: {args.result_format}")
    print(f"瓦片尺寸: {args.tile_width}×{args.tile_height} 像素")
    print(f"通道数: {args.tile_channels}")
    print(f"使用进程: {args.proc_num} 个")
    print("=" * 60)

    # 加载输入图像
    print(f"\n加载输入图像: {args.file_path}")
    try:
        input_img = np.array(Image.open(args.file_path), dtype=np.uint8)
    except Exception as e:
        print(f"错误: 无法加载输入图像 - {e}")
        sys.exit(1)

    h, w = input_img.shape[:2]
    c = args.tile_channels

    print(f"图像尺寸: {w}×{h} 像素")
    print(f"实际通道数: {input_img.shape[2] if len(input_img.shape) > 2 else 1}")

    # 验证通道数匹配
    actual_channels = input_img.shape[2] if len(input_img.shape) > 2 else 1
    if actual_channels != c:
        print(f"警告: 指定通道数({c})与实际通道数({actual_channels})不匹配")

    # 计算可生成的瓦片数量
    x_num = w // args.tile_width
    y_num = h // args.tile_height
    total_tiles = x_num * y_num

    if x_num == 0 or y_num == 0:
        print(f"错误: 输入图像尺寸({w}×{h})小于瓦片尺寸({args.tile_width}×{args.tile_height})")
        sys.exit(1)

    print(f"可生成瓦片: {x_num}×{y_num} = {total_tiles} 个")

    # 计算剩余像素（无法生成完整瓦片的部分）
    remaining_x = w % args.tile_width
    remaining_y = h % args.tile_height
    if remaining_x > 0 or remaining_y > 0:
        print(f"注意: 图像边缘有剩余像素 - X方向:{remaining_x}, Y方向:{remaining_y}")

    # 创建共享内存
    print(f"\n创建共享内存 ({w}×{h} 像素, {c}通道)...")
    try:
        memory_needed = h * w * c
        memory_needed_mb = memory_needed / (1024 * 1024)
        print(f"内存需求: {memory_needed_mb:.2f} MB")

        if memory_needed_mb > 1024:  # 超过1GB
            print(f"警告: 输入图像较大 ({memory_needed_mb / 1024:.1f} GB)，确保有足够内存")

        shm = shared_memory.SharedMemory(
            create=True,
            size=memory_needed
        )
    except Exception as e:
        print(f"错误: 无法分配共享内存 ({memory_needed_mb:.2f} MB)")
        print(f"原因: {e}")
        print("建议: 使用更小的图像或增加系统内存")
        sys.exit(1)

    shm_name = shm.name

    # 将图像数据复制到共享内存
    print("复制图像数据到共享内存...")
    if c == 1:
        totMap = np.ndarray((h, w), dtype=np.uint8, buffer=shm.buf)
        if len(input_img.shape) == 2:
            totMap[:] = input_img
        else:
            # 如果是3通道图像但要求1通道，转换为灰度
            from PIL import Image as PILImage

            gray_img = PILImage.fromarray(input_img).convert('L')
            totMap[:] = np.array(gray_img, dtype=np.uint8)
    else:  # channels == 3
        totMap = np.ndarray((h, w, 3), dtype=np.uint8, buffer=shm.buf)
        if len(input_img.shape) == 2:
            # 如果是1通道图像但要求3通道，转换为RGB
            rgb_img = np.stack([input_img] * 3, axis=2)
            totMap[:] = rgb_img
        else:
            totMap[:] = input_img

    # 释放原始图像内存
    del input_img

    # 准备任务参数
    print("准备分割任务...")
    from multiprocessing import Manager

    with Manager() as manager:
        progress_counter = manager.Value('i', 0)

        params = []
        for x_idx in range(x_num):
            for y_idx in range(y_num):
                params.append((
                    args.result_dir,
                    x_idx * args.x_step + args.x_begin,  # 保存的x
                    y_idx * args.y_step + args.y_begin,  # 保存的y
                    args.result_format,
                    x_idx * args.tile_width,  # 图上x1
                    y_idx * args.tile_height,  # 图上y1
                    (x_idx + 1) * args.tile_width,  # 图上x2
                    (y_idx + 1) * args.tile_height,  # 图上y2
                    shm_name,
                    h,
                    w,
                    c,
                    progress_counter
                ))

        print(f"\n开始分割 {len(params)} 个瓦片...")

        # 使用多进程池处理任务
        with Pool(processes=args.proc_num) as pool:
            try:
                # 创建进度条
                with tqdm(total=len(params), desc="分割进度", ncols=100,
                          bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

                    # 使用imap_unordered获取结果
                    results = []
                    for i, result in enumerate(pool.imap_unordered(split_tile_wrapper, params)):
                        results.append(result)

                        # 更新进度条
                        pbar.update(1)

                        # 每处理100个瓦片更新一次进度条描述
                        if i % 100 == 0:
                            success_count = sum(results)
                            pbar.set_postfix_str(f"成功: {success_count}")

                # 统计结果
                success_count = sum(results)
                failed_count = len(results) - success_count

                print(f"\n分割完成!")
                print(f"成功: {success_count} 个瓦片")
                print(f"失败: {failed_count} 个瓦片")

                if failed_count > 0:
                    print(f"失败率: {failed_count / len(results) * 100:.1f}%")

            except KeyboardInterrupt:
                print("\n分割被用户中断")
                shm.close()
                shm.unlink()
                sys.exit(1)
            except Exception as e:
                print(f"\n错误: 多进程处理异常 - {e}")
                shm.close()
                shm.unlink()
                raise

        # 清理共享内存
        shm.close()
        shm.unlink()

        print("\n" + "=" * 60)
        print("分割任务完成!")
        print(f"输出目录: {args.result_dir}")
        print(f"瓦片格式: {args.result_format}")
        print(f"瓦片数量: {x_num}×{y_num} = {total_tiles} 个")
        print(f"瓦片尺寸: {args.tile_width}×{args.tile_height} 像素")
        print("=" * 60)