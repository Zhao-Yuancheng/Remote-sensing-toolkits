@echo off
CALL conda activate rstDev

REM ============================================================
REM 瓦片分割工具 CLI 版本 - Windows 启动脚本
REM ============================================================
REM --file_path:     输入的大幅遥感图像路径（支持 PNG、JPEG、TIFF）
REM --result_dir:    瓦片保存根目录，结构为 result_dir/X/Y.format
REM --result_format: 瓦片文件格式（如 .jpg、.png）
REM --x_begin:       X 方向瓦片起始编号（用于文件命名）
REM --x_step:        X 方向编号步长（通常为 1）
REM --y_begin:       Y 方向瓦片起始编号（用于文件命名）
REM --y_step:        Y 方向编号步长（通常为 1）
REM --tile_width:    瓦片宽度（像素）
REM --tile_height:   瓦片高度（像素）
REM --tile_channels: 通道数，1=灰度图，3=RGB 彩色图
REM --proc_num:      进程数，建议设为 CPU 核心数或略少
REM ============================================================

python tileSplitCLI.py ^
--file_path "D:\satellite\高德卫星影像\integrate.png" ^
--result_dir "D:\satellite\高德卫星影像\split" ^
--result_format ".jpg" ^
--x_begin 0 ^
--x_step 1 ^
--y_begin 0 ^
--y_step 1 ^
--tile_width 1024 ^
--tile_height 1024 ^
--tile_channels 3 ^
--proc_num 8

pause
