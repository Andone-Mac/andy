#!/bin/bash
# 压缩 siteV5 首屏轮播视频：CRF23 + 去音轨（静音播放）+ faststart
# 权威源在 /home/UOS/JAVIS/VideosPictures/video0910/*/final*.mp4，本目录副本可安全覆盖
set -u
cd /home/UOS/JAVIS/siteV5/assets/videos || exit 1
echo "=== 开始压缩 $(date +%T) ==="
total_before=0; total_after=0
for f in v1 v2 v3 v4 v5 v1_p v2_p v3_p v4_p v5_p; do
  src="$f.mp4"
  [ -f "$src" ] || { echo "SKIP $src (不存在)"; continue; }
  before=$(stat -c%s "$src")
  ffmpeg -y -v error -i "$src" -c:v libx264 -preset slow -crf 23 -an \
         -movflags +faststart -pix_fmt yuv420p "/tmp/_opt_$f.mp4" || { echo "FAIL $src"; continue; }
  after=$(stat -c%s "/tmp/_opt_$f.mp4")
  mv -f "/tmp/_opt_$f.mp4" "$src"
  total_before=$((total_before+before)); total_after=$((total_after+after))
  printf "%s: %dMB → %dMB (-%d%%)\n" "$src" $((before/1048576)) $((after/1048576)) $(( (before-after)*100/before ))
done
echo "=== 合计: $((total_before/1048576))MB → $((total_after/1048576))MB ==="
ls -la *.mp4 | awk '{s+=$5} END {print "目录实际总量:", int(s/1048576)"MB"}'
echo "=== 完成 $(date +%T) ==="
