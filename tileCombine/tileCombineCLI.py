import argparse
import os
import sys
from multiprocessing import Pool, freeze_support, Manager
from PIL import Image
import numpy as np
from multiprocessing.shared_memory import SharedMemory
from tqdm import tqdm


def integrate(idx, x_idx, y_idx, file_path, tile_width, tile_height, tot_width, tot_height,
              shm_name,
              channels, progress_counter):
    """
    合并单个瓦片到总图中
    参数:
        idx: 任务索引
        x_idx, y_idx: 瓦片在总图中的行列索引
        file_path: 瓦片文件路径
        tile_width, tile_height: 瓦片宽高
        tot_width, tot_height: 总图宽高
        shm_name: 共享内存名称
        channels: 通道数
        progress_counter: 进度计数器
    返回:
        成功返回True，失败返回False
    """
    try:
        # 打开共享内存
        existing_shm = SharedMemory(name=shm_name, create=False)

        # 根据通道数创建不同形状的数组
        if channels == 1:
            tot_map = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=existing_shm.buf)
        else:  # channels == 3
            tot_map = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8,
                                 buffer=existing_shm.buf)

        # 读取瓦片图片
        array = np.array(Image.open(file_path), dtype=np.uint8)

        # 放置到正确位置
        y_start = y_idx * tile_height
        y_end = (y_idx + 1) * tile_height
        x_start = x_idx * tile_width
        x_end = (x_idx + 1) * tile_width

        if channels == 1:
            tot_map[y_start:y_end, x_start:x_end] = array
        else:  # channels == 3
            tot_map[y_start:y_end, x_start:x_end, :] = array

        existing_shm.close()

        # 更新进度
        progress_counter.value += 1

        return True, (x_idx, y_idx)

    except FileNotFoundError:
        print(f"警告: 瓦片文件不存在 {file_path}", flush=True)
        return False, (x_idx, y_idx)
    except Exception as e:
        print(f"错误: 处理瓦片({x_idx},{y_idx})时发生异常: {e}", flush=True)
        return False, (x_idx, y_idx)


def integrate_wrapper(args):
    """包装函数，用于多进程调用"""
    return integrate(*args)


if __name__ == "__main__":
    # 设置PIL最大图像像素，防止大图报错
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    parser = argparse.ArgumentParser(
        description="多进程瓦片合并工具 - 将分散的瓦片图片合并成完整的大图",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python tileCombineCLI.py --root_dir ./tiles --result_path ./result.png \\
    --x_begin 100 --x_end 200 --x_step 1 --y_begin 50 --y_end 150 --y_step 1 \\
    --tile_width 256 --tile_height 256 --tile_format .png --tile_channels 3 --proc_num 8

参数说明:
  x_begin, x_end: X方向瓦片的起始和结束编号
  y_begin, y_end: Y方向瓦片的起始和结束编号
  x_step, y_step: 瓦片编号的步长（通常为1）
  tile_width, tile_height: 单个瓦片的像素尺寸
  tile_channels: 1-灰度图，3-RGB彩色图
        """
    )

    # 必需参数
    parser.add_argument('--root_dir', type=str, required=True,
                        help='瓦片图片存储的根目录，目录结构应为 root_dir/X/Y.png')
    parser.add_argument('--result_path', type=str, required=True,
                        help='合并结果的保存路径，支持.png, .jpg, .tif等格式')
    parser.add_argument('--x_begin', type=int, required=True,
                        help='X方向瓦片起始编号（最小X值）')
    parser.add_argument('--x_end', type=int, required=True,
                        help='X方向瓦片结束编号（最大X值）')
    parser.add_argument('--x_step', type=int, required=True,
                        help='X方向瓦片编号步长（通常为1）')
    parser.add_argument('--y_begin', type=int, required=True,
                        help='Y方向瓦片起始编号（最小Y值）')
    parser.add_argument('--y_end', type=int, required=True,
                        help='Y方向瓦片结束编号（最大Y值）')
    parser.add_argument('--y_step', type=int, required=True,
                        help='Y方向瓦片编号步长（通常为1）')
    parser.add_argument('--tile_width', type=int, required=True,
                        help='单个瓦片的宽度（像素）')
    parser.add_argument('--tile_height', type=int, required=True,
                        help='单个瓦片的高度（像素）')
    parser.add_argument('--tile_format', type=str, required=True,
                        help='瓦片文件的后缀名，如 ".png"')
    parser.add_argument('--tile_channels', type=int, choices=[1, 3], required=True,
                        help='瓦片图片的通道数: 1表示灰度图，3表示RGB彩色图')
    parser.add_argument('--proc_num', type=int, required=True,
                        help='使用的进程数，建议设置为CPU核心数或略少于核心数')

    # 可选参数
    parser.add_argument('--show_progress', action='store_true', default=True,
                        help='显示进度条（默认开启）')
    parser.add_argument('--skip_existing', action='store_true', default=False,
                        help='如果结果文件已存在则跳过合并（默认关闭）')

    args = parser.parse_args()

    # 检查结果文件是否已存在
    if args.skip_existing and os.path.exists(args.result_path):
        print(f"结果文件已存在: {args.result_path}")
        print("跳过合并过程")
        sys.exit(0)

    # 参数验证
    if args.x_begin > args.x_end:
        print("错误: x_begin 不能大于 x_end")
        sys.exit(1)
    if args.y_begin > args.y_end:
        print("错误: y_begin 不能大于 y_end")
        sys.exit(1)
    if args.x_step <= 0 or args.y_step <= 0:
        print("错误: x_step 和 y_step 必须大于0")
        sys.exit(1)
    if args.tile_width <= 0 or args.tile_height <= 0:
        print("错误: 瓦片尺寸必须大于0")
        sys.exit(1)
    if args.proc_num <= 0:
        print("错误: 进程数必须大于0")
        sys.exit(1)

    # 计算总瓦片数和输出图像尺寸
    x_num = int((args.x_end - args.x_begin) / args.x_step) + 1
    y_num = int((args.y_end - args.y_begin) / args.y_step) + 1
    channels = args.tile_channels

    tot_width = x_num * args.tile_width
    tot_height = y_num * args.tile_height

    print("\n" + "=" * 60)
    print("瓦片合并工具启动")
    print(f"输入目录: {args.root_dir}")
    print(f"输出文件: {args.result_path}")
    print(f"瓦片范围: X[{args.x_begin}→{args.x_end}] Y[{args.y_begin}→{args.y_end}]")
    print(f"瓦片数量: {x_num}×{y_num} = {x_num * y_num} 个")
    print(f"单个瓦片: {args.tile_width}×{args.tile_height} 像素, {channels}通道")
    print(
        f"输出图像: {tot_width}×{tot_height} 像素 ({tot_width / 1000:.1f}k×{tot_height / 1000:.1f}k)")
    print(f"使用进程: {args.proc_num} 个")
    print("=" * 60)

    # 检查输出目录是否存在
    result_dir = os.path.dirname(args.result_path)
    if result_dir and not os.path.exists(result_dir):
        os.makedirs(result_dir)
        print(f"创建输出目录: {result_dir}")

    # 计算所需共享内存大小
    total_pixels = tot_width * tot_height * channels
    memory_needed_mb = total_pixels / (1024 * 1024)  # 转换为MB

    print(f"\n内存需求: {memory_needed_mb:.2f} MB")
    if memory_needed_mb > 1024:  # 超过1GB
        print(f"警告: 输出图像较大 ({memory_needed_mb / 1024:.1f} GB)，确保有足够内存")

    # 创建共享内存
    try:
        shm = SharedMemory(
            create=True,
            size=total_pixels
        )
    except Exception as e:
        print(f"\n错误: 无法分配共享内存 ({memory_needed_mb:.2f} MB)")
        print(f"原因: {e}")
        print("建议: 减少合并范围或增加系统内存")
        sys.exit(1)

    shm_name = shm.name

    # 根据通道数创建不同形状的数组
    if channels == 1:
        totMap = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=shm.buf)
    else:  # channels == 3
        totMap = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8, buffer=shm.buf)

    # 初始化共享内存
    print("初始化共享内存...")

    totMap.fill(0)

    # 准备任务参数
    params = []
    for x_idx in range(x_num):
        for y_idx in range(y_num):
            tile_x = args.x_begin + x_idx * args.x_step
            tile_y = args.y_begin + y_idx * args.y_step
            tile_path = os.path.join(args.root_dir, str(tile_x), str(tile_y) + args.tile_format)

            params.append((
                x_idx * y_num + y_idx,  # 任务索引
                x_idx,  # X索引
                y_idx,  # Y索引
                tile_path,  # 瓦片路径
                args.tile_width,  # 瓦片宽度
                args.tile_height,  # 瓦片高度
                tot_width,  # 总图宽度
                tot_height,  # 总图高度
                shm_name,  # 共享内存名称
                channels,  # 通道数
                0  # 进度计数器占位，将在进程池中替换
            ))

    # 创建进度计数器
    with Manager() as manager:
        progress_counter = manager.Value('i', 0)

        # 更新参数中的进度计数器
        params_with_counter = []
        for param in params:
            param_list = list(param)
            param_list[-1] = progress_counter  # 替换最后一个参数为进度计数器
            params_with_counter.append(tuple(param_list))

        print(f"\n开始合并 {len(params_with_counter)} 个瓦片...")

        # 使用多进程池处理任务
        with Pool(processes=args.proc_num) as pool:
            try:
                # 创建进度条
                with tqdm(total=len(params_with_counter), desc="合并进度", ncols=100,
                          bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

                    # 使用imap_unordered获取结果
                    results = []
                    for i, result in enumerate(
                            pool.imap_unordered(integrate_wrapper, params_with_counter)):
                        success, (x_idx, y_idx) = result
                        results.append((success, x_idx, y_idx))

                        # 更新进度条
                        pbar.update(1)

                        # 每处理100个瓦片更新一次进度条描述
                        if i % 100 == 0:
                            completed = progress_counter.value
                            pbar.set_postfix_str(f"成功: {sum(1 for r in results if r[0])}")

                # 统计结果
                success_count = sum(1 for success, _, _ in results if success)
                failed_count = len(results) - success_count

                print(f"\n合并完成!")
                print(f"成功: {success_count} 个瓦片")
                print(f"失败: {failed_count} 个瓦片")

                if failed_count > 0:
                    failed_tiles = [(x, y) for success, x, y in results if not success]
                    print(f"失败的瓦片位置: {failed_tiles[:10]}")  # 只显示前10个
                    if len(failed_tiles) > 10:
                        print(f"  ... 共 {len(failed_tiles)} 个失败瓦片")

            except KeyboardInterrupt:
                print("\n合并被用户中断")
                shm.close()
                shm.unlink()
                sys.exit(1)
            except Exception as e:
                print(f"\n错误: 多进程处理异常 - {e}")
                shm.close()
                shm.unlink()
                raise

    # 保存结果图片
    print(f"\n保存结果到: {args.result_path}")
    try:
        if channels == 1:
            result_img = Image.fromarray(totMap, mode='L')
        else:  # channels == 3
            result_img = Image.fromarray(totMap, mode='RGB')

        # 根据文件扩展名选择保存格式
        result_img.save(args.result_path)
        file_size_mb = os.path.getsize(args.result_path) / (1024 * 1024)
        print(f"文件大小: {file_size_mb:.2f} MB")

    except Exception as e:
        print(f"错误: 保存结果图片失败 - {e}")
        shm.close()
        shm.unlink()
        sys.exit(1)

    # 清理共享内存
    shm.close()
    shm.unlink()

    print("\n" + "=" * 60)
    print("合并任务完成!")
    print(f"输出文件: {args.result_path}")
    print(f"图像尺寸: {tot_width}×{tot_height} 像素")
    print("=" * 60)