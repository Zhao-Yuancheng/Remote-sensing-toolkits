@echo off
CALL conda activate rstDev

REM ============================================================
REM TIFF 调色板转 RGB 工具 CLI 版本 - Windows 启动脚本
REM ============================================================
REM --file_path:   输入 TIFF 文件路径（必须是调色板模式 P 的图像）
REM --result_path: 输出 RGB 图像路径（支持 TIFF、PNG、JPEG 等）
REM --proc_num:    并发进程数（默认为 CPU 核心数的一半，建议 1-16）
REM ============================================================

python paletteTransCLI.py ^
--file_path "D:\Code\Project\Python\Remote-sensing-toolkits\test\ptest.tif" ^
--result_path "D:\Code\Project\Python\Remote-sensing-toolkits\ptest_RGB.jpg" ^
--proc_num 8

pause
