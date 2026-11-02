#!/bin/bash
# ============================================================
# 多线程瓦片下载工具 CLI 版本 - Linux 启动脚本
# ============================================================
# 使用前请修改以下两行为你的 conda 环境路径和环境名称：
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

# ---- 参数说明（请根据实际情况修改以下参数） ----
# --root_dir:     瓦片保存根目录
# --source:       数据源类型
#                  0: Google Earth 卫星影像
#                  1: 高德矢量底图
#                  2: 高德卫星影像
#                  3: 高德路网标记
# --level_start:  起始缩放级别（1-22）
# --level_end:    结束缩放级别（需大于等于起始级别）
# --LT_lat:       左上角纬度（WGS84 坐标系）
# --LT_lon:       左上角经度（WGS84 坐标系）
# --RB_lat:       右下角纬度（WGS84 坐标系）
# --RB_lon:       右下角经度（WGS84 坐标系）
# --workers_num:  每个级别的最大工作线程数（默认 50）
# --------------------------------------------------

python multiDownloadCLI.py \
--root_dir "./satellite" \
--source 2 \
--level_start 13 \
--level_end 16 \
--LT_lat 36.161000 \
--LT_lon 103.553300 \
--RB_lat 36.020300 \
--RB_lon 103.955700 \
--workers_num 64
