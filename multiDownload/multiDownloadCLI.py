import urllib.request
import argparse
import os
import random
import math
import sys
import concurrent.futures
import threading
from typing import List, Tuple
from urllib.error import URLError, HTTPError
import time

source_dict={
    0:"Google Earth",
    1:"高德矢量底图",
    2:"高德卫星影像",
    3:"高德路网标记",
}


# 线程安全的计数器
class ThreadSafeCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value

    def get(self):
        with self.lock:
            return self.value


# 全局下载计数器
total_downloads = ThreadSafeCounter()
total_errors = ThreadSafeCounter()

# User-Agent列表
agents = [
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1'
]

# 创建线程本地存储
thread_local = threading.local()


# 经纬度反算切片行列号 3857坐标系
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


# 下载单个图片（优化后的版本，无递归）
def download_single_image(Tpath: str, Spath: str, x: int, y: int, max_retries: int = 3) -> bool:
    """
    下载单个图片，带重试机制
    返回: True表示成功，False表示失败
    """
    # 如果文件已存在，跳过下载
    if os.path.isfile(Spath):
        print(f"文件已存在，跳过: {x}_{y}")
        return True

    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(Spath), exist_ok=True)

    for retry in range(max_retries):
        try:
            req = urllib.request.Request(Tpath)
            req.add_header('User-Agent', random.choice(agents))

            # 设置超时
            response = urllib.request.urlopen(req, timeout=30)

            # 读取数据
            data = response.read()

            # 写入文件
            with open(Spath, 'wb') as f:
                f.write(data)

            # 更新计数器
            downloaded = total_downloads.increment()
            if downloaded % 100 == 0:
                print(f"已下载 {downloaded} 个文件")

            # print(f"下载成功: {x}_{y} (第{retry + 1}次尝试)")
            return True

        except (URLError, HTTPError, ConnectionError, TimeoutError) as e:
            if retry < max_retries - 1:
                wait_time = 2 ** retry  # 指数退避
                print(f"下载失败 {x}_{y}, 第{retry + 1}次重试，等待{wait_time}秒: {e}")
                time.sleep(wait_time)
            else:
                print(f"下载失败 {x}_{y}，重试{max_retries}次后放弃")
                total_errors.increment()
                return False
        except Exception as e:
            print(f"未知错误 {x}_{y}: {e}")
            total_errors.increment()
            return False

    return False


# 并行下载任务包装器
def download_task_wrapper(args: Tuple[str, str, int, int]) -> Tuple[int, int, bool]:
    """
    包装下载任务，方便线程池调用
    返回: (x, y, 是否成功)
    """
    Tpath, Spath, x, y = args
    success = download_single_image(Tpath, Spath, x, y)
    return x, y, success


# 并行下载函数
def parallel_download(tasks: List[Tuple[str, str, int, int]], max_workers: int = 100) -> dict:
    """
    并行下载多个图片
    """
    results = {
        'total': len(tasks),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    print(f"开始下载 {len(tasks)} 个文件，使用 {max_workers} 个线程...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_task = {
            executor.submit(download_task_wrapper, task): task
            for task in tasks
        }

        # 处理完成的任务
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            Tpath, Spath, x, y = task

            try:
                x_result, y_result, success = future.result()
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"下载失败: {x}_{y}")
            except Exception as e:
                results['failed'] += 1
                error_msg = f"任务执行异常: {x}_{y}, 错误: {str(e)}"
                results['errors'].append(error_msg)
                print(error_msg)

    return results


# 主下载函数（并行版本）
def download(k,rootDir,source, LTlat, LTlon, RBlat, RBlon, max_workers: int = 100):
    """
    并行下载指定区域和缩放级别的切片
    """
    zoom = k
    lefttop = deg2num(LTlat, LTlon, zoom)
    rightbottom = deg2num(RBlat, RBlon, zoom)

    print(f"缩放级别: {zoom}")
    print(f"X范围: {lefttop[0]} 到 {rightbottom[0]}")
    print(f"Y范围: {lefttop[1]} 到 {rightbottom[1]}")
    print(f"X方向切片数: {rightbottom[0] - lefttop[0]}")
    print(f"Y方向切片数: {rightbottom[1] - lefttop[1]}")

    # 准备所有下载任务
    tasks = []


    for x in range(lefttop[0], rightbottom[0]):
        path = os.path.join(rootDir, str(zoom), str(x))

        for y in range(lefttop[1], rightbottom[1]):
            if source == 0:
                tilepath = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"
            elif source == 1:
                tilepath = f"https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={zoom}"  # 高德矢量底图
            elif source == 2:
                tilepath = f"https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={zoom}"  # 高德卫星影像
            elif source == 3:
                tilepath = f"https://webst01.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={zoom}"  # 高德路网标记
            else:
                print("您输入的source代码有误！")
                return

            filepath = os.path.join(path, f"{y}.png")

            tasks.append((tilepath, filepath, x, y))

    print(f"总共 {len(tasks)} 个切片需要下载")

    # 并行下载
    start_time = time.time()
    results = parallel_download(tasks, max_workers)
    end_time = time.time()

    # 打印统计信息
    print("\n" + "=" * 50)
    print("下载完成!")
    print(f"总耗时: {end_time - start_time:.2f} 秒")
    print(f"总任务数: {results['total']}")
    print(f"成功: {results['success']}")
    print(f"失败: {results['failed']}")

    if results['errors']:
        print(f"\n前10个错误:")
        for error in results['errors'][:10]:
            print(f"  - {error}")

        # 保存错误日志
        error_file = f"download_errors_zoom{zoom}.txt"
        with open(error_file, 'w', encoding='utf-8') as f:
            for error in results['errors']:
                f.write(error + "\n")
        print(f"详细错误日志已保存到: {error_file}")

    return results


# 批量下载多个缩放级别
def batch_download(root_dir,source,level_start, level_end, LT_lat, LT_lon, RB_lat, RB_lon,
                   max_workers_per_level=50):
    """
    批量下载多个缩放级别
    每个级别使用不同的线程数，高级别使用较少线程
    """
    for zoom in range(level_start, level_end + 1):
        print(f"\n{'=' * 60}")
        print(f"开始下载缩放级别: {zoom}")
        print(f"{'=' * 60}")

        # 动态调整线程数，高级别使用较少线程
        if zoom <= 15:
            workers = max_workers_per_level
        elif zoom <= 18:
            workers = max_workers_per_level // 2
        else:
            workers = max_workers_per_level // 4

        print(f"使用 {workers} 个线程")

        # 计算当前级别的边界
        # if zoom > 15:
        #     delta_lat = LT_lat - RB_lat
        #     delta_lon = RB_lon - LT_lon
        #     LT_lat_current = LT_lat - delta_lat * 1 / 4
        #     LT_lon_current = LT_lon + delta_lon * 1 / 4
        #     RB_lat_current = RB_lat + delta_lat * 1 / 4
        #     RB_lon_current = RB_lon - delta_lon * 1 / 4
        # else:
        LT_lat_current, LT_lon_current, RB_lat_current, RB_lon_current = LT_lat, LT_lon, RB_lat, RB_lon

        print(f"下载区域:")
        print(f"  左上: ({LT_lat_current}, {LT_lon_current})")
        print(f"  右下: ({RB_lat_current}, {RB_lon_current})")

        # 执行下载
        results = download(
            zoom,
            root_dir,
            source,
            LT_lat_current, LT_lon_current,
            RB_lat_current, RB_lon_current,
            workers
        )

        # 如果错误太多，暂停一下
        if results['failed'] > results['total'] * 0.1:  # 失败率超过10%
            print("错误率较高，暂停30秒...")
            time.sleep(30)

        # 级别间暂停，避免请求过于频繁
        if zoom < level_end:
            print(f"等待5秒后开始下一级别...")
            time.sleep(5)


# 主程序入口
if __name__ == "__main__":
    # 参数设置
    parser = argparse.ArgumentParser()
    parser.add_argument('--root_dir',type=str)
    parser.add_argument('--source',type=int,help="请输入数字\n0: Google Earth\n1: 高德矢量底图\n2: 高德卫星影像\n3: 高德路网标记")
    parser.add_argument('--level_start', type=int)
    parser.add_argument('--level_end', type=int)
    parser.add_argument('--LT_lat', type=float)
    parser.add_argument('--LT_lon', type=float)
    parser.add_argument('--RB_lat', type=float)
    parser.add_argument('--RB_lon', type=float)
    parser.add_argument('--workers_num', type=int)
    args = parser.parse_known_args()[0]


    root_dir = args.root_dir
    source = args.source
    level_start = args.level_start
    level_end = args.level_end
    LT_lat = args.LT_lat
    LT_lon = args.LT_lon
    RB_lat = args.RB_lat
    RB_lon = args.RB_lon
    max_workers_per_level = args.workers_num


    print("多线程地图切片下载器")
    print(f"下载范围: 级别 {level_start} 到 {level_end}")
    print(f"区域: 左上({LT_lat}, {LT_lon}) 右下({RB_lat}, {RB_lon})")
    print(f"每个文件约70KB，总文件数取决于缩放级别和区域大小")

    if not os.path.exists(root_dir):
        os.makedirs(root_dir)
        print(f"创建主目录: {root_dir}")

    # 开始批量下载
    try:
        print(root_dir,source,level_start,level_end,LT_lat)
        batch_download(root_dir,source,level_start, level_end, LT_lat, LT_lon, RB_lat, RB_lon,
                       max_workers_per_level=1024)

        # 最终统计
        print("\n" + "=" * 60)
        print("所有级别下载完成!")
        print(f"总下载文件数: {total_downloads.get()}")
        print(f"总错误数: {total_errors.get()}")

    except KeyboardInterrupt:
        print("\n用户中断下载")
    except Exception as e:
        print(f"下载过程发生错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n程序结束")