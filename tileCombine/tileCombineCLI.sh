#!/bin/bash  
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

python tileCombineCLI.py \
--root_dir "input_tiles_root_path" \
--result_path "output_file_path" \
--x_begin 1651817 \
--x_end 1652613 \
--x_step 4 \
--y_begin 822436 \
--y_end 823328 \
--y_step 4 \
--tile_width 1024 \
--tile_height 1024 \
--tile_format ".png" \
--proc_hum 8