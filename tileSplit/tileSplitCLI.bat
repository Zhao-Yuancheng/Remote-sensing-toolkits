CALL conda activate rstDev

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
