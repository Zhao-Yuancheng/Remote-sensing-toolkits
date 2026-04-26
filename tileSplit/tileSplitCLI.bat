CALL conda activate your_environment_name

python tileSplitCLI.py ^
--file_path "input_file_path" ^
--result_dir "output_tiles_root_path" ^
--result_format "saving format(eg: .jpg)" ^
--x_begin 0 ^
--x_step 1 ^
--y_begin 100 ^
--y_step 10 ^
--seg_width 1024 ^
--seg_height 1024 ^
--proc_num 8 ^
--channels 3