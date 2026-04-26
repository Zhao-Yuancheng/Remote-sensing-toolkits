CALL conda activate your_environment_name

python multiDownloadCLI.py ^
--root_dir ".\satellite" ^
--source 2 ^
--level_start 13 ^
--level_end 16 ^
--LT_lat 36.161000 ^
--LT_lon 103.553300 ^
--RB_lat 36.020300 ^
--RB_lon 103.955700 ^
--workers_num 64

:: source 
:: 0: Google Earth
:: 1: 高德矢量底图
:: 2: 高德卫星影像
:: 3: 高德路网标记