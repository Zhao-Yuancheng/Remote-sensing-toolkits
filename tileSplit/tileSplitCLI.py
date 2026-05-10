import argparse
from PIL import Image
import numpy as np
from multiprocessing import shared_memory
from multiprocessing import Pool
from multiprocessing import freeze_support
import os,sys


def split_tile(result_root, save_x, save_y, result_format, x1, y1, x2, y2, shm_name, h, w, channels):
    try:
        existing_shm = shared_memory.SharedMemory(name=shm_name, create=False)

        # 根据通道数创建不同形状的数组
        if channels == 1:
            tot_map = np.ndarray((h, w), dtype=np.uint8, buffer=existing_shm.buf)
        else:  # channels == 3
            tot_map = np.ndarray((h, w, 3), dtype=np.uint8,
                                 buffer=existing_shm.buf)

        os.makedirs(os.path.join(result_root, str(save_x)), exist_ok=True)
        save_path = os.path.join(result_root, str(save_x), str(save_y)+"."+result_format.replace(".",""))
        if channels == 1:
            array = tot_map[y1:y2, x1:x2]
        else:
            array = tot_map[y1:y2, x1:x2,:]
        Image.fromarray(array).save(save_path)
        existing_shm.close()
    except Exception as e:
        print(f"Error in integrate at (save_x={save_x}, save_y={save_y}): {e}", flush=True)
        raise


if __name__ == "__main__":
    Image.MAX_IMAGE_PIXELS = None
    freeze_support()

    parser = argparse.ArgumentParser()
    parser.add_argument('--file_path', type=str,required=True)
    parser.add_argument('--result_dir', type=str,required=True)
    parser.add_argument('--result_format', type=str,required=True)
    parser.add_argument('--x_begin', type=int,required=True)
    parser.add_argument('--x_step', type=int,required=True)
    parser.add_argument('--y_begin', type=int,required=True)
    parser.add_argument('--y_step', type=int,required=True)
    parser.add_argument('--tile_width', type=int,required=True)
    parser.add_argument('--tile_height', type=int,required=True)
    parser.add_argument('--tile_channels', type=int, choices=[1, 3],
                        help='Number of channels: 1 for grayscale, 3 for RGB',required=True)
    parser.add_argument('--proc_num', type=int,required=True)

    args = parser.parse_known_args()[0]

    input_img = np.array(Image.open(args.file_path), dtype=np.uint8)
    print(input_img.shape)
    h,w = input_img.shape[:2]
    c = args.tile_channels

    # 根据通道数计算共享内存大小
    try:
        shm = shared_memory.SharedMemory(
            create=True,
            size=h * w * c
        )
    except Exception as e:
        print("系统资源不足，任务中止！",e)
        sys.exit()
    shm_name = shm.name

    # 根据通道数创建不同形状的数组
    if c == 1:
        totMap = np.ndarray((h, w), dtype=np.uint8, buffer=shm.buf)
    else:  # channels == 3
        totMap = np.ndarray((h, w, 3), dtype=np.uint8, buffer=shm.buf)

    totMap[:]=input_img
    #释放内存
    del input_img

    params = []
    x_num = w//args.tile_width
    y_num = h//args.tile_width
    for x_idx in range(0,x_num):
        for y_idx in range(0,y_num):
            params.append((
                args.result_dir,
                x_idx*args.x_step+args.x_begin, # 保存的x
                y_idx*args.y_step+args.y_begin, # 保存的y
                args.result_format,
                x_idx*args.tile_width, # 图上x1
                y_idx*args.tile_width, # 图上y1
                (x_idx+1)*args.tile_width, # 图上x2
                (y_idx+1)*args.tile_width, # 图上y2
                shm_name,
                h,
                w,
                c
            ))

    with Pool(processes=args.proc_num) as pool:
        try:
            pool.starmap(split_tile, params)
        except Exception as e:
            print(f"Error in pool: {e}")
            shm.close()
            shm.unlink()
            raise

    shm.close()
    shm.unlink()