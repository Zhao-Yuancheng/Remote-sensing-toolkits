#!/bin/bash
# ============================================================
# 瓦片分割工具 CLI 版本 - Linux 启动脚本
# ============================================================
# 使用前请修改以下两行为你的 conda 环境路径和环境名称：
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

# ---- 参数说明（请根据实际情况修改以下参数） ----
# --file_path:     输入的大幅遥感图像路径（支持 PNG、JPEG、TIFF）
# --result_dir:    瓦片保存根目录，结构为 result_dir/X/Y.format
# --result_format: 瓦片文件格式（如 png、jpg、tif，无需加点）
# --x_begin:       X 方向瓦片起始编号（用于文件命名）
# --x_step:        X 方向编号步长（通常为 1）
# --y_begin:       Y 方向瓦片起始编号（用于文件命名）
# --y_step:        Y 方向编号步长（通常为 1）
# --tile_width:    瓦片宽度（像素）
# --tile_height:   瓦片高度（像素）
# --tile_channels: 通道数，1=灰度图，3=RGB 彩色图
# --proc_num:      进程数，建议设为 CPU 核心数或略少
# --------------------------------------------------

python tileSplitCLI.py \
--file_path "./large_image.png" \
--result_dir "./tiles" \
--result_format "png" \
--x_begin 0 \
--x_step 1 \
--y_begin 0 \
--y_step 1 \
--tile_width 256 \
--tile_height 256 \
--tile_channels 3 \
--proc_num 8
