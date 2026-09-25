#!/usr/bin/env python3
"""⚠️ 旧版去背：flood-fill 只处理外部背景，「保留图形内部白色区域」这句正是 bug 所在——
   被笔画围住的封闭白区（汉字里的空白、字母 A 的内三角）会残留成不透明白，贴深色底露白块。
   请改用 ../tools/fix_logo_alpha.py（按白色程度逐像素定 alpha，内部白区一并透明）。
   本脚本保留仅供理解历史做法。
"""
from PIL import Image
from collections import deque
import shutil, os

def make_transparent(path, out=None):
    out = out or path
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    TH = 225  # min(r,g,b) > TH 视为白底像素
    vis = bytearray(w * h)
    q = deque()
    def is_white(x, y):
        r, g, b, _ = px[x, y]
        return min(r, g, b) > TH
    # 边界种子
    for x in range(w):
        for y in (0, h - 1):
            if is_white(x, y) and not vis[y * w + x]:
                vis[y * w + x] = 1; q.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_white(x, y) and not vis[y * w + x]:
                vis[y * w + x] = 1; q.append((x, y))
    # BFS 洪泛：只连通到边界的白色区域变透明
    while q:
        x, y = q.popleft()
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not vis[ny * w + nx] and is_white(nx, ny):
                vis[ny * w + nx] = 1
                q.append((nx, ny))
    # 柔化：透明区边缘 1px 内的近白像素按"离白色距离"给半透明 alpha，消除锯齿白边
    alpha = im.split()[3].load()
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if vis[i]:
                px[x, y] = (0, 0, 0, 0)
    for y in range(h):
        for x in range(w):
            i = y * w + x
            if vis[i]:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            j = ny * w + nx
                            if not vis[j]:
                                r, g, b, a = px[nx, ny]
                                mn = min(r, g, b)
                                if mn > 195:  # 近白但被图形边缘挡住 → 半透明过渡
                                    t = (255 - mn) / (255 - 195)
                                    px[nx, ny] = (r, g, b, int(max(a * t, 255 * t)))
    im.save(out)
    n_bg = sum(vis)
    print(f"{path}: {w}x{h} 背景透明化 {n_bg}px ({100*n_bg//(w*h)}%) corners:", px[0,0], px[w-1,0])

for f in ["logo.png", "logo_mark.png"]:
    if not os.path.exists(f + ".bak"):
        shutil.copy2(f, f + ".bak")
    make_transparent(f)
print("完成。备份为 *.bak")
