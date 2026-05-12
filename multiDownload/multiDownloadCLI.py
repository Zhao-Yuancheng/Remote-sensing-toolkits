import argparse
import concurrent.futures
import math
import os
import random
import threading
import time
import urllib.request
from typing import List, Tuple
from urllib.error import URLError, HTTPError

from tqdm import tqdm

# 数据源定义
source_dict = {
    0: "Google Earth 卫星影像",
    1: "高德地图 矢量底图",
    2: "高德地图 卫星影像",
    3: "高德地图 路网标记",
}


# 线程安全的计数器
class ThreadSafeCounter:
    """线程安全的计数器，用于统计下载进度"""

    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self, amount: int = 1) -> int:
        """增加计数值，返回增加后的值"""
        with self.lock:
            self.value += amount
            return self.value

    def get(self) -> int:
        """获取当前计数值"""
        with self.lock:
            return self.value

    def set(self, value: int) -> None:
        """设置计数值"""
        with self.lock:
            self.value = value


# 全局统计器
class DownloadStats:
    """下载统计信息"""

    def __init__(self):
        self.total_tasks = ThreadSafeCounter()  # 总任务数
        self.completed_tasks = ThreadSafeCounter()  # 已完成任务数
        self.successful_tasks = ThreadSafeCounter()  # 成功任务数
        self.failed_tasks = ThreadSafeCounter()  # 失败任务数

    def reset(self, total: int = 0) -> None:
        """重置统计器"""
        self.total_tasks.set(total)
        self.completed_tasks.set(0)
        self.successful_tasks.set(0)
        self.failed_tasks.set(0)

    def get_progress(self) -> Tuple[int, int, int, int]:
        """获取进度信息：已完成数，成功数，失败数，总数"""
        return (
            self.completed_tasks.get(),
            self.successful_tasks.get(),
            self.failed_tasks.get(),
            self.total_tasks.get()
        )


# 全局下载统计
download_stats = DownloadStats()

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


# 经纬度反算切片行列号 3857坐标系
def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    """
    将经纬度转换为瓦片行列号
    参数:
        lat_deg: 纬度
        lon_deg: 经度
        zoom: 缩放级别
    返回:
        (x, y) 瓦片行列号
    """
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (xtile, ytile)


# 下载单个图片
def download_single_image(Tpath: str, Spath: str, x: int, y: int, max_retries: int = 3) -> bool:
    """
    下载单个图片，带重试机制
    参数:
        Tpath: 瓦片URL
        Spath: 保存路径
        x, y: 瓦片坐标
        max_retries: 最大重试次数
    返回:
        True表示成功，False表示失败
    """
    # 如果文件已存在，跳过下载
    if os.path.isfile(Spath):
        return True

    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(Spath), exist_ok=True)

    for retry in range(max_retries):
        try:
            req = urllib.request.Request(Tpath)
            req.add_header('User-Agent', random.choice(agents))

            # 设置超时
            response = urllib.request.urlopen(req, timeout=30)
            data = response.read()

            # 写入文件
            with open(Spath, 'wb') as f:
                f.write(data)

            return True

        except (URLError, HTTPError, ConnectionError, TimeoutError) as e:
            if retry < max_retries - 1:
                wait_time = 2 ** retry  # 指数退避
                time.sleep(wait_time)
            else:
                return False
        except Exception as e:
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

    # 更新统计信息
    download_stats.completed_tasks.increment(1)
    if success:
        download_stats.successful_tasks.increment(1)
    else:
        download_stats.failed_tasks.increment(1)

    return x, y, success


# 并行下载函数
def parallel_download(tasks: List[Tuple[str, str, int, int]], max_workers: int = 100) -> dict:
    """
    并行下载多个图片
    参数:
        tasks: 下载任务列表
        max_workers: 最大工作线程数
    返回:
        下载结果字典
    """
    # 重置统计器
    download_stats.reset(len(tasks))

    results = {
        'total': len(tasks),
        'success': 0,
        'failed': 0,
        'errors': []
    }

    print(f"\n开始并行下载 {len(tasks)} 个瓦片，使用 {max_workers} 个工作线程...")

    # 创建进度条
    with tqdm(total=len(tasks), desc="下载进度", ncols=100,
              bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:

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
                    x_result, y_result, success = future.result(timeout=60)
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"瓦片({x},{y})下载失败")
                except concurrent.futures.TimeoutError:
                    results['failed'] += 1
                    error_msg = f"瓦片({x},{y})任务超时"
                    results['errors'].append(error_msg)
                except Exception as e:
                    results['failed'] += 1
                    error_msg = f"瓦片({x},{y})任务异常: {str(e)}"
                    results['errors'].append(error_msg)

                # 更新进度条
                pbar.update(1)
                completed, success_cnt, failed_cnt, total = download_stats.get_progress()
                pbar.set_postfix_str(f"成功: {success_cnt}, 失败: {failed_cnt}")

    return results


# 主下载函数
def download(zoom: int, root_dir: str, source: int,
             LT_lat: float, LT_lon: float, RB_lat: float, RB_lon: float,
             max_workers: int = 100) -> dict:
    """
    下载指定区域和缩放级别的切片
    参数:
        zoom: 缩放级别
        root_dir: 保存根目录
        source: 数据源类型
        LT_lat, LT_lon: 左上角经纬度
        RB_lat, RB_lon: 右下角经纬度
        max_workers: 最大工作线程数
    返回:
        下载结果字典
    """
    # 计算瓦片范围
    lefttop = deg2num(LT_lat, LT_lon, zoom)
    rightbottom = deg2num(RB_lat, RB_lon, zoom)

    print(f"\n{'=' * 60}")
    print(f"缩放级别: {zoom}")
    print(f"数据源: {source_dict.get(source, '未知')}")
    print(f"瓦片范围: X[{lefttop[0]} → {rightbottom[0]}] Y[{lefttop[1]} → {rightbottom[1]}]")
    print(f"瓦片数量: {(rightbottom[0] - lefttop[0]) * (rightbottom[1] - lefttop[1])}")
    print(f"{'=' * 60}")

    # 准备所有下载任务
    tasks = []
    for x in range(lefttop[0], rightbottom[0]):
        path = os.path.join(root_dir, str(zoom), str(x))

        for y in range(lefttop[1], rightbottom[1]):
            # 根据数据源生成URL
            if source == 0:
                tilepath = f"https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={zoom}"
            elif source == 1:
                tilepath = f"https://webrd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={zoom}"
            elif source == 2:
                tilepath = f"https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={zoom}"
            elif source == 3:
                tilepath = f"https://webst01.is.autonavi.com/appmaptile?style=8&x={x}&y={y}&z={zoom}"
            else:
                print(f"错误: 不支持的数据源代码 {source}")
                return {'total': 0, 'success': 0, 'failed': 0, 'errors': []}

            filepath = os.path.join(path, f"{y}.png")
            tasks.append((tilepath, filepath, x, y))

    # 并行下载
    start_time = time.time()
    results = parallel_download(tasks, max_workers)
    end_time = time.time()

    # 打印统计信息
    elapsed_time = end_time - start_time
    print(f"\n下载完成! 耗时: {elapsed_time:.2f}秒")
    print(f"平均速度: {results['success'] / elapsed_time:.2f} 瓦片/秒")

    if results['errors']:
        print(f"\n错误统计: 共 {len(results['errors'])} 个失败任务")
        if len(results['errors']) <= 10:
            for error in results['errors']:
                print(f"  - {error}")
        else:
            print(f"  (显示前10个错误)")
            for error in results['errors'][:10]:
                print(f"  - {error}")

        # 保存错误日志
        error_file = os.path.join(root_dir, f"errors_zoom{zoom}.log")
        with open(error_file, 'w', encoding='utf-8') as f:
            for error in results['errors']:
                f.write(error + "\n")
        print(f"详细错误日志已保存到: {error_file}")

    return results


# 批量下载多个缩放级别
def batch_download(root_dir: str, source: int, level_start: int, level_end: int,
                   LT_lat: float, LT_lon: float, RB_lat: float, RB_lon: float,
                   max_workers_per_level: int = 50) -> None:
    """
    批量下载多个缩放级别
    """
    print(f"\n{'#' * 60}")
    print("批量下载任务开始")
    print(f"数据源: {source_dict.get(source, '未知')}")
    print(f"级别范围: {level_start} → {level_end}")
    print(f"区域: 左上({LT_lat}, {LT_lon}) 右下({RB_lat}, {RB_lon})")
    print(f"保存目录: {root_dir}")
    print(f"{'#' * 60}\n")

    total_success = 0
    total_failed = 0

    for zoom in range(level_start, level_end + 1):
        print(f"\n▶ 正在处理级别 {zoom}...")

        # 动态调整线程数
        if zoom <= 15:
            workers = max_workers_per_level
        elif zoom <= 18:
            workers = max_workers_per_level // 2
        else:
            workers = max_workers_per_level // 4

        # 执行下载
        results = download(
            zoom, root_dir, source,
            LT_lat, LT_lon, RB_lat, RB_lon,
            workers
        )

        total_success += results['success']
        total_failed += results['failed']

        # 如果错误率过高，暂停一下
        if results.get('failed', 0) > results.get('total', 1) * 0.2:  # 失败率超过20%
            print("⚠ 错误率较高，暂停10秒...")
            time.sleep(10)

        # 级别间暂停
        if zoom < level_end:
            print("等待3秒后开始下一级别...")
            time.sleep(3)

    # 最终统计
    print(f"\n{'#' * 60}")
    print("批量下载任务完成!")
    print(f"总成功: {total_success}")
    print(f"总失败: {total_failed}")
    print(f"成功率: {total_success / (total_success + total_failed) * 100:.1f}%")
    print(f"{'#' * 60}")


# 主程序入口
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="多线程地图瓦片下载器 - 支持Google Earth、高德地图等多个数据源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python multiDownloadCLI.py --root_dir ./tiles --source 0 --level_start 10 --level_end 12 \\
    --LT_lat 36.1610 --LT_lon 103.5533 --RB_lat 36.0203 --RB_lon 103.9557 --workers_num 50

数据源说明:
  0: Google Earth 卫星影像
  1: 高德地图 矢量底图
  2: 高德地图 卫星影像
  3: 高德地图 路网标记
        """
    )

    parser.add_argument('--root_dir', type=str, required=True,
                        help='瓦片保存的根目录路径')
    parser.add_argument('--source', type=int, required=True, choices=[0, 1, 2, 3],
                        help='数据源类型: 0-Google Earth, 1-高德矢量, 2-高德卫星, 3-高德路网')
    parser.add_argument('--level_start', type=int, required=True,
                        help='起始缩放级别 (通常1-20)')
    parser.add_argument('--level_end', type=int, required=True,
                        help='结束缩放级别 (需大于等于起始级别)')
    parser.add_argument('--LT_lat', type=float, required=True,
                        help='左上角纬度 (WGS84坐标系)')
    parser.add_argument('--LT_lon', type=float, required=True,
                        help='左上角经度 (WGS84坐标系)')
    parser.add_argument('--RB_lat', type=float, required=True,
                        help='右下角纬度 (WGS84坐标系)')
    parser.add_argument('--RB_lon', type=float, required=True,
                        help='右下角经度 (WGS84坐标系)')
    parser.add_argument('--workers_num', type=int, default=50,
                        help='每个级别的最大工作线程数 (默认: 50)')

    args = parser.parse_args()

    # 参数验证
    if args.level_start > args.level_end:
        print("错误: 起始级别不能大于结束级别")
        exit(1)

    if not os.path.exists(args.root_dir):
        os.makedirs(args.root_dir)
        print(f"创建目录: {args.root_dir}")

    # 打印配置信息
    print("\n" + "=" * 60)
    print("地图瓦片下载器启动")
    print(f"数据源: {source_dict.get(args.source, '未知')}")
    print(f"级别范围: {args.level_start} → {args.level_end}")
    print(f"下载区域: ({args.LT_lat}, {args.LT_lon}) → ({args.RB_lat}, {args.RB_lon})")
    print(f"保存位置: {args.root_dir}")
    print("=" * 60)

    try:
        # 开始批量下载
        batch_download(
            args.root_dir, args.source,
            args.level_start, args.level_end,
            args.LT_lat, args.LT_lon,
            args.RB_lat, args.RB_lon,
            args.workers_num
        )

    except KeyboardInterrupt:
        print("\n\n下载被用户中断")
    except Exception as e:
        print(f"\n下载过程发生错误: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("\n程序结束")
