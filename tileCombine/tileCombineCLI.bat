CALL conda activate rstDev

python tileCombineCLI.py ^
--root_dir "D:\satellite\高德卫星影像\16" ^
--result_path "D:\satellite\高德卫星影像\integrate.png" ^
--x_begin 51619 ^
--x_end 51691 ^
--x_step 1 ^
--y_begin 25698 ^
--y_end 25729 ^
--y_step 1 ^
--tile_width 256 ^
--tile_height 256 ^
--tile_format ".png" ^
--tile_channels 3 ^
--proc_num 8 ^