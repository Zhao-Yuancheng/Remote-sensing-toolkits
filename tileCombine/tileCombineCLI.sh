#!/bin/bash
# ============================================================
# 瓦片合并工具 CLI 版本 - Linux 启动脚本
# ============================================================
# 使用前请修改以下两行为你的 conda 环境路径和环境名称：
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

# ---- 参数说明（请根据实际情况修改以下参数） ----
# --root_dir:       瓦片图片存储根目录，结构应为 root_dir/X/Y.png
# --result_path:    合并结果保存路径（支持 .png、.jpg、.tif 等）
# --x_begin:        X 方向瓦片起始编号（最小 X 值）
# --x_end:          X 方向瓦片结束编号（最大 X 值）
# --x_step:         X 方向编号步长（通常为 1）
# --y_begin:        Y 方向瓦片起始编号（最小 Y 值）
# --y_end:          Y 方向瓦片结束编号（最大 Y 值）
# --y_step:         Y 方向编号步长（通常为 1）
# --tile_width:     单个瓦片宽度（像素）
# --tile_height:    单个瓦片高度（像素）
# --tile_format:    瓦片文件后缀名（如 .png）
# --tile_channels:  通道数，1=灰度图，3=RGB 彩色图
# --proc_num:       进程数，建议设为 CPU 核心数或略少
# --------------------------------------------------

python tileCombineCLI.py \
--root_dir "./tiles" \
--result_path "./result.png" \
--x_begin 1651817 \
--x_end 1652613 \
--x_step 4 \
--y_begin 822436 \
--y_end 823328 \
--y_step 4 \
--tile_width 1024 \
--tile_height 1024 \
--tile_format ".png" \
--tile_channels 3 \
--proc_num 8
