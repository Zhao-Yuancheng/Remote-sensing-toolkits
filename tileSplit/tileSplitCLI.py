import argparse
from PIL import Image
import numpy as np
from multiprocessing import shared_memory
from multiprocessing import Pool
from multiprocessing import freeze_support
import os


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
    Image.MAX_IMAGE_PIXELS = 1e15
    freeze_support()

    parser = argparse.ArgumentParser()
    # parser.add_argument('--root_dir', type=str)
    # parser.add_argument('--result_path', type=str)
    parser.add_argument('--file_path', type=str)
    parser.add_argument('--result_dir', type=str)
    parser.add_argument('--result_format', type=str)
    parser.add_argument('--x_begin', type=int)
    # parser.add_argument('--x_end', type=int)
    parser.add_argument('--x_step', type=int)
    parser.add_argument('--y_begin', type=int)
    # parser.add_argument('--y_end', type=int)
    parser.add_argument('--y_step', type=int)
    parser.add_argument('--seg_width', type=int)
    parser.add_argument('--seg_height', type=int)
    parser.add_argument('--proc_num', type=int)
    parser.add_argument('--channels', type=int, choices=[1, 3],
                        help='Number of channels: 1 for grayscale, 3 for RGB')
    args = parser.parse_known_args()[0]

    input_img = np.array(Image.open(args.file_path), dtype=np.uint8)
    print(input_img.shape)
    h,w = input_img.shape[:2]
    c = args.channels

    # 根据通道数计算共享内存大小
    shm = shared_memory.SharedMemory(
        create=True,
        size=h * w * c
    )
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
    x_num = w//args.seg_width
    y_num = h//args.seg_height
    for x_idx in range(0,x_num):
        for y_idx in range(0,y_num):
            params.append((
                args.result_dir,
                x_idx*args.x_step+args.x_begin, # 保存的x
                y_idx*args.y_step+args.y_begin, # 保存的y
                args.result_format,
                x_idx*args.seg_width, # 图上x1
                y_idx*args.seg_height, # 图上y1
                (x_idx+1)*args.seg_width, # 图上x2
                (y_idx+1)*args.seg_height, # 图上y2
                # os.path.join(args.result_dir, str(args.x_begin + x_idx * args.x_step),
                #              str(args.y_begin + y_idx * args.y_step)) + ".png",
                # args.seg_width,
                # args.seg_height,
                # tot_width,
                # tot_height,
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

    # # 根据通道数保存图片
    # if channels == 1:
    #     result = Image.fromarray(totMap, mode='L')
    # else:  # channels == 3
    #     result = Image.fromarray(totMap, mode='RGB')
    #
    # result.save(args.result_path)
    shm.close()
    shm.unlink()