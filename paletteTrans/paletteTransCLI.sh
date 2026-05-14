#!/bin/bash
source /path/to/anaconda3/bin/activate your_environment_name
conda activate your_environment_name

python paletteTransCLI.py \
--file_path "D:\Code\Project\Python\Remote-sensing-toolkits\test\ptest.tif" \
--result_path "D:\Code\Project\Python\Remote-sensing-toolkits\ptest_RGB.jpg" \
--proc_num 8

pause