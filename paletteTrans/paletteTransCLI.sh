#!/bin/bash
# ============================================================
# TIFF 调色板转 RGB 工具 CLI 版本 - Linux 启动脚本
# ============================================================
# 使用前请修改以下两行为你的 conda 环境路径和环境名称：
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

# ---- 参数说明（请根据实际情况修改以下参数） ----
# --file_path:   输入 TIFF 文件路径（必须是调色板模式 P 的图像）
# --result_path: 输出 RGB 图像路径（支持 TIFF、PNG、JPEG 等）
# --proc_num:    并发进程数（默认为 CPU 核心数的一半，建议 1-16）
# --------------------------------------------------

python paletteTransCLI.py \
--file_path "./input_palette.tif" \
--result_path "./output_rgb.tif" \
--proc_num 8
