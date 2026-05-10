import argparse
from PIL import Image
import numpy as np
from multiprocessing import shared_memory
from multiprocessing import Pool
from multiprocessing import freeze_support
import os,sys


def integrate(idx, x_idx, y_idx, file_path, tile_width, tile_height, tot_width, tot_height, shm_name,
              channels):
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
            tot_map[y_idx * tile_height:(y_idx + 1) * tile_height,
            x_idx * tile_width:(x_idx + 1) * tile_width] = array
        else:  # channels == 3
            tot_map[y_idx * tile_height:(y_idx + 1) * tile_height,
            x_idx * tile_width:(x_idx + 1) * tile_width, :] = array

        existing_shm.close()

        if not idx % 250:
            print(f"{idx}:\tx_idx={x_idx}, y_idx={y_idx}, file_path={file_path}", flush=True)
    except Exception as e:
        print(f"Error in integrate at (x_idx={x_idx}, y_idx={y_idx}): {e}", flush=True)
        raise


if __name__ == "__main__":
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument('--root_dir', type=str,required=True)
    parser.add_argument('--result_path', type=str,required=True)
    parser.add_argument('--x_begin', type=int,required=True)
    parser.add_argument('--x_end', type=int,required=True)
    parser.add_argument('--x_step', type=int,required=True)
    parser.add_argument('--y_begin', type=int,required=True)
    parser.add_argument('--y_end', type=int,required=True)
    parser.add_argument('--y_step', type=int,required=True)
    parser.add_argument('--tile_width', type=int,required=True)
    parser.add_argument('--tile_height', type=int,required=True)
    parser.add_argument('--tile_format', type=str,required=True)
    parser.add_argument('--tile_channels', type=int, choices=[1, 3],
                        help='Number of channels: 1 for grayscale, 3 for RGB', required=True)
    parser.add_argument('--proc_num', type=int,required=True)


    args = parser.parse_known_args()[0]

    x_num = int((args.x_end - args.x_begin) / args.x_step) + 1
    y_num = int((args.y_end - args.y_begin) / args.y_step) + 1
    channels = args.tile_channels

    # 根据通道数计算共享内存大小
    try:
        shm = shared_memory.SharedMemory(
            create=True,
            size=x_num * y_num * args.tile_width * args.tile_height * channels
        )
    except Exception as e:
        print("系统资源不足，任务中止！",e)
        sys.exit()
    shm_name = shm.name
    tot_width, tot_height = x_num * args.tile_width, y_num * args.tile_height

    # 根据通道数创建不同形状的数组
    if channels == 1:
        totMap = np.ndarray((tot_height, tot_width), dtype=np.uint8, buffer=shm.buf)
    else:  # channels == 3
        totMap = np.ndarray((tot_height, tot_width, 3), dtype=np.uint8, buffer=shm.buf)

    params = []
    for x_idx in range(x_num):
        for y_idx in range(y_num):
            params.append((
                x_idx * y_num + y_idx,
                x_idx,
                y_idx,
                os.path.join(args.root_dir, str(args.x_begin + x_idx * args.x_step),
                             str(args.y_begin + y_idx * args.y_step)) + args.tile_format,
                args.tile_width,
                args.tile_height,
                tot_width,
                tot_height,
                shm_name,
                channels
            ))

    with Pool(processes=args.proc_num) as pool:
        try:
            pool.starmap(integrate, params)
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

    result.save(args.result_path)
    shm.close()
    shm.unlink()