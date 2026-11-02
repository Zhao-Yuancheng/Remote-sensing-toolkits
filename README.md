# 智图匀影 · ZhiTu YunYing

**遥感 GIS 瓦片图全流程智能处理工具集** · *A tile-centric toolkit for remote-sensing AI data preparation*

[中文](#中文) | [English](#english)

---

## 中文

智图匀影是一套面向遥感 AI 训练数据制备的瓦片图处理工具集，覆盖「下载 → 切分 → 合并 → 色彩统一 → 调色板转换」的完整流程。每个工具都提供图形界面（PySide6）与命令行（适用于 Linux 超算集群）两个版本，二者共享同一套核心算法。

本工具集用于构建 *Lanzhou Rooftop Material Dataset*（LRMD）：按经纬度范围下载 21 级瓦片，4×4 合并为 1024×1024 图块，再切分为训练/验证/测试集。

### 功能模块

| 模块 | 作用 | 关键能力 |
|---|---|---|
| [multiDownload](multiDownload) | 按经纬度范围批量下载 XYZ 瓦片 | 四种数据源（Google 卫星、高德矢量/卫星/路网）、多线程、指数退避重试、断点续传、自定义层级 |
| [tileSplit](tileSplit) | 大图切分为标准瓦片 | 多进程 + 共享内存零拷贝、灰度/RGB 通道自适应、二维网格进度可视化 |
| [tileCombine](tileCombine) | 瓦片合并为大图 | 自动探测编号范围/步长/尺寸、多进程并行、亿像素级图像 |
| [colorBalance](colorBalance) | 多幅影像色彩统一 | LAB 空间梯度分割 + 直方图匹配、交互式分割线、双阶段边界定位 |
| [paletteTrans](paletteTrans) | 调色板 TIFF → RGB | 256×3 LUT、共享内存分块、Cython `prange` 加速（含纯 Python 回退） |

### 安装

```bash
# GDAL 建议用 conda 安装（pip 源码编译较慢）
conda create -n ztyy python=3.10 -y
conda activate ztyy
conda install -c conda-forge gdal pyside6 -y
pip install -r requirements.txt
```

图形界面在 Windows 10/11 与 Linux 桌面环境可用；命令行版本已在 CentOS 7 / Ubuntu 20.04 的 Slurm 集群上运行。

### 快速开始（命令行）

```bash
# 1) 下载 21 级瓦片：左上/右下角经纬度定义范围
python multiDownload/multiDownloadCLI.py \
  --root_dir ./satellite --source 0 \
  --level_start 21 --level_end 21 \
  --LT_lat 36.1577 --LT_lon 103.5659 \
  --RB_lat 36.0202 --RB_lon 103.9539 \
  --workers_num 50

# 2) 把大图切成 256×256 瓦片
python tileSplit/tileSplitCLI.py \
  --file_path ./mosaic.tif --result_dir ./tiles --result_format png \
  --x_begin 0 --x_step 256 --y_begin 0 --y_step 256 \
  --tile_width 256 --tile_height 256 --tile_channels 3 --proc_num 8

# 3) 把 4×4 相邻瓦片合并为 1024×1024（编号步长为 4）
python tileCombine/tileCombineCLI.py \
  --root_dir ./tiles --result_path ./blocks \
  --x_begin 1651821 --x_end 1653961 --x_step 4 \
  --y_begin 822362 --y_end 823130 --y_step 4 \
  --tile_width 256 --tile_height 256 --tile_format png --tile_channels 3 \
  --proc_num 8

# 4) 调色板影像批量转 RGB
python paletteTrans/paletteTransCLI.py \
  --file_path ./labels_tif --result_path ./labels_png --proc_num 8
```

图形界面直接运行各模块的 `*.py`（不带 `CLI` 后缀）即可，例如 `python multiDownload/multiDownload.py`。

> `colorBalanceCLI.py` 通过文件顶部的 `INPUT_FILE_PATH` / `OUTPUT_FILE_PATH` 配置输入输出，直接运行脚本即可。

### 目录结构

```
multiDownload/     瓦片下载（GUI + CLI）
tileSplit/         大图切瓦片（GUI + CLI）
tileCombine/       瓦片合并（GUI + CLI）
colorBalance/      色彩平衡（GUI + CLI + GDAL 版本）
paletteTrans/      调色板转换（GUI + CLI + GDAL 版本）
icon/              图标资源
uiDesignFIles/     Qt Designer 界面源文件
docs/              用户手册（manual.md）与配图
*.spec             PyInstaller 打包配置
```

### 打包为可执行程序

```bash
pyinstaller multiDownload.spec
```

十个 `.spec` 文件覆盖五个工具的 GUI/CLI 两种形态；打包产物（`build/`、`dist/`）已在 `.gitignore` 中排除。

### 文档

- 完整用户手册：[docs/manual.md](docs/manual.md)（含界面截图、参数说明与典型场景）
- 软件著作权：智图匀影——遥感GIS瓦片图全流程智能处理工具集（V1.0），已在中国版权保护中心登记

### 许可

[Apache-2.0](LICENSE)。可自由用于科研与商业项目，请保留版权与许可声明。

---

## English

ZhiTu YunYing is a tile-centric toolkit for preparing remote-sensing training data. Five modules cover the whole chain — download, split, merge, colour balancing, and palette conversion — and each ships as both a PySide6 desktop application and an `argparse` command-line tool that runs on Linux clusters.

The toolkit was used to build the *Lanzhou Rooftop Material Dataset* (LRMD): tiles at zoom level 21 are downloaded over a bounding box, merged in 4×4 blocks into 1024×1024 images, and then split into train/validation/test sets.

### Modules

| Module | Purpose | Highlights |
|---|---|---|
| [multiDownload](multiDownload) | Batch-download XYZ tiles over a bounding box | four sources (Google satellite, Amap vector/satellite/road), thread pool, exponential-backoff retries, resume support, any zoom level |
| [tileSplit](tileSplit) | Cut a large raster into tiles | multiprocessing with shared-memory zero-copy, grayscale/RGB aware, 2-D grid progress display |
| [tileCombine](tileCombine) | Merge tiles back into a mosaic | automatic detection of index range/step/tile size, parallel writes, images up to 10^8 pixels |
| [colorBalance](colorBalance) | Colour-consistent mosaics | LAB gradient segmentation plus histogram matching, interactive cut-line selection, two-stage boundary refinement |
| [paletteTrans](paletteTrans) | Palette TIFF to RGB | 256×3 lookup table, shared-memory blocks, optional Cython `prange` acceleration with a pure-Python fallback |

### Install

```bash
conda create -n ztyy python=3.10 -y
conda activate ztyy
conda install -c conda-forge gdal pyside6 -y
pip install -r requirements.txt
```

GDAL is installed through conda because the PyPI build is slow to compile.

### Quick start

```bash
python multiDownload/multiDownloadCLI.py --root_dir ./satellite --source 0 \
  --level_start 21 --level_end 21 \
  --LT_lat 36.1577 --LT_lon 103.5659 --RB_lat 36.0202 --RB_lon 103.9539 \
  --workers_num 50

python tileSplit/tileSplitCLI.py --file_path ./mosaic.tif \
  --result_dir ./tiles --result_format png \
  --x_begin 0 --x_step 256 --y_begin 0 --y_step 256 \
  --tile_width 256 --tile_height 256 --tile_channels 3 --proc_num 8

python tileCombine/tileCombineCLI.py --root_dir ./tiles --result_path ./blocks \
  --x_begin 1651821 --x_end 1653961 --x_step 4 \
  --y_begin 822362 --y_end 823130 --y_step 4 \
  --tile_width 256 --tile_height 256 --tile_format png --tile_channels 3 \
  --proc_num 8

python paletteTrans/paletteTransCLI.py --file_path ./labels_tif \
  --result_path ./labels_png --proc_num 8
```

Launch the graphical versions by running the modules without the `CLI` suffix.

### Documentation and packaging

Full user manual (Chinese, with screenshots): [docs/manual.md](docs/manual.md).
Build standalone executables with `pyinstaller <tool>.spec`; `build/` and
`dist/` are ignored by git.

### License

[Apache-2.0](LICENSE). Scientific and commercial use are both permitted;
please keep the copyright and licence notices.

---

## 引用 / Citation

If this toolkit contributed to a publication, please cite the dataset paper it
was built for:

```bibtex
@article{zhao2026fdsunext,
  title   = {Boundary-Aware Adaptation of Frozen Foundation Models for
             Fine-Grained Rooftop Segmentation},
  author  = {Zhao, Yuancheng and Wang, Jie and Li, Faguo and Liu, Erte and
             Meng, Xiangying and Chen, Yueyue},
  journal = {Remote Sensing},
  year    = {2026},
  note    = {Under review}
}
```

Contact: Yuancheng Zhao, Lanzhou University.
