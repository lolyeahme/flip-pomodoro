# -*- coding: utf-8 -*-
"""生成 README 用的翻页动画 GIF：逐帧截图后合成。"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "file:///" + os.path.join(ROOT, "index.html").replace("\\", "/") + \
       "?autostart=1&task=Writing%20paper&mins=25&rounds=4"

W, H = 760, 560
FRAMES = 20
STEP_MS = 420          # 相邻帧的虚拟时间间隔（毫秒）
OUT = os.path.join(ROOT, "docs", "demo.gif")

tmp = tempfile.mkdtemp(prefix="flipgif-")
paths = []
try:
    for i in range(FRAMES):
        budget = 600 + i * STEP_MS
        shot = os.path.join(tmp, "f%02d.png" % i)
        cmd = [
            CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--window-size=%d,%d" % (W, H),
            "--virtual-time-budget=%d" % budget,
            "--screenshot=" + shot, PAGE,
        ]
        r = subprocess.run(cmd, capture_output=True)
        if not os.path.exists(shot):
            sys.exit("frame %d failed: %s" % (i, r.stderr.decode("utf-8", "ignore")[:300]))
        paths.append(shot)

    imgs = [Image.open(p).convert("RGB") for p in paths]
    size = imgs[0].size
    imgs = [im.resize(size, Image.LANCZOS) for im in imgs]
    # 首帧多停一会儿，末帧停留，读起来更像一次真实走秒
    durations = [900] + [STEP_MS] * (len(imgs) - 2) + [1400]
    imgs[0].save(OUT, save_all=True, append_images=imgs[1:],
                 duration=durations, loop=0, optimize=True)
    print("frames:", len(imgs), "size:", size)
    print("gif bytes:", os.path.getsize(OUT))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
