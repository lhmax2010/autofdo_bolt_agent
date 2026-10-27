# RPi4 H.264 测试视频

来源：Blender Foundation — Big Buck Bunny（Sunflower 1080p/30fps 版本）。
官方目录：https://download.blender.org/demo/movies/BBB/
下载 URL：https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip
授权：Creative Commons Attribution 3.0，https://creativecommons.org/licenses/by/3.0/ 。
官方授权说明：https://peach.blender.org/about/ 。署名：© Blender Foundation / Big Buck Bunny，https://www.bigbuckbunny.org/ 。
本项目修改：截取 300–360 秒中段，去音轨，缩放/重编码；不暗示原作者背书。

官方下载提供 ZIP，内部是 H.264 High 1920×1080、30fps MP4（片长 634.6 秒）；未使用合成备用画面。
片源和下载归档留在 temp/media_src/；下述视频不进 Git，media/*.mp4 和 temp/ 均已忽略。

## 来源校验

- ZIP SHA-256：`e320fef389ec749117d0c1583945039266a40f25483881c2ff0d33207e62b362`
- 原始 MP4 SHA-256：`ae51005850b0ff757fe60c3dd7a12d754d3cd2397d87d939b55235e457f97658`

## 下载与提取

所有命令在 WORKDIR 执行，先 `export TMPDIR="$PWD/temp/tmp"`。没有安装主机工具。

```sh
nice -n 19 ionice -c3 curl -fSL --retry 1 --connect-timeout 30 --max-time 600 https://download.blender.org/demo/movies/BBB/bbb_sunflower_1080p_30fps_normal.mp4.zip -o temp/media_src/bbb_sunflower_1080p_30fps_normal.mp4.zip
nice -n 19 ionice -c3 python3 - <<'PY_EXTRACT'
import zipfile
from pathlib import Path
p = Path('temp/media_src/bbb_sunflower_1080p_30fps_normal.mp4.zip')
with zipfile.ZipFile(p) as z:
    for item in z.infolist():
        if item.filename.endswith('.mp4'):
            with z.open(item) as src, (p.parent / Path(item.filename).name).open('wb') as dst:
                while block := src.read(1024 * 1024):
                    dst.write(block)
PY_EXTRACT
```

## 完整编码命令

依次执行；libx264 只用 2 线程，滤镜 1 线程。`-y` 会覆盖同名目标文件。

```sh
nice -n 19 ionice -c3 ffmpeg -nostdin -hide_banner -loglevel warning -y -ss 300 -i temp/media_src/bbb_sunflower_1080p_30fps_normal.mp4 -t 60 -an -vf scale=1920:1080,setsar=1,fps=30 -c:v libx264 -preset veryfast -profile:v high -pix_fmt yuv420p -b:v 8M -maxrate 8M -bufsize 16M -threads 2 -filter_threads 1 -movflags +faststart media/bbb_1080p_h264_60s.mp4
```

```sh
nice -n 19 ionice -c3 ffmpeg -nostdin -hide_banner -loglevel warning -y -ss 300 -i temp/media_src/bbb_sunflower_1080p_30fps_normal.mp4 -t 60 -an -vf scale=1280:720,setsar=1,fps=30 -c:v libx264 -preset veryfast -profile:v high -pix_fmt yuv420p -b:v 4M -maxrate 4M -bufsize 8M -threads 2 -filter_threads 1 -movflags +faststart media/bbb_720p_h264_60s.mp4
```

## 产物与 ffprobe

| 文件 | SHA-256 | 分辨率 | 编码/Profile/像素 | 帧率 | 时长/帧数 | 视频码率 |
|---|---|---|---|---|---|---|
| bbb_1080p_h264_60s.mp4 | `31f72f11eb0566e0265358a14294e5dbddf13fce4ce1507d8872b04c2596a6da` | 1920×1080 | h264 / High / yuv420p | 30/1 | 60.000000s / 1800 | 8047973 bit/s |
| bbb_720p_h264_60s.mp4 | `b5e116b9d01cec8e7f697041c53575d36bd96a5928e40faa69e731f9ae2d00a4` | 1280×720 | h264 / High / yuv420p | 30/1 | 60.000000s / 1800 | 4000178 bit/s |

验证命令（两个文件分别执行）：

```sh
nice -n 19 ionice -c3 ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_frames,bit_rate:format=duration,bit_rate -of json media/bbb_1080p_h264_60s.mp4
nice -n 19 ionice -c3 ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,duration,nb_frames,bit_rate:format=duration,bit_rate -of json media/bbb_720p_h264_60s.mp4
```

未使用 -count_frames 做完整解码计数；nb_frames 为 MP4 流元数据，帧率与 60 秒时长一致。完整工具输出和编码退出码在 temp/rpi4_pmu/，精简证据随探测报告提交。
