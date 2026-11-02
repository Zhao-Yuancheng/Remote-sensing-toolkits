@echo off
CALL conda activate rstDev

REM ============================================================
REM 多线程瓦片下载工具 CLI 版本 - Windows 启动脚本
REM ============================================================
REM --source 参数说明:
REM   0: Google Earth 卫星影像
REM   1: 高德矢量底图
REM   2: 高德卫星影像
REM   3: 高德路网标记
REM --level_start / --level_end: 缩放级别范围（1-22）
REM --LT_lat / --LT_lon: 左上角纬度/经度（WGS84）
REM --RB_lat / --RB_lon: 右下角纬度/经度（WGS84）
REM --workers_num: 并发线程数（默认 50）
REM ============================================================

python multiDownloadCLI.py ^
--root_dir ".\satellite" ^
--source 2 ^
--level_start 14 ^
--level_end 15 ^
--LT_lat 36.161000 ^
--LT_lon 103.553300 ^
--RB_lat 36.020300 ^
--RB_lon 103.955700 ^
--workers_num 64

pause
