#!/usr/bin/env python3
"""Generate/inspect a tiny original synthetic MP4 entirely offline."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

for tool in ("ffmpeg", "ffprobe"):
    if shutil.which(tool) is None:
        raise SystemExit(f"SKIP (tool unavailable): {tool}; install FFmpeg to run this test")
with tempfile.TemporaryDirectory(prefix="fns_media_test_") as td:
    p=Path(td)/"synthetic.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","lavfi","-i","testsrc2=size=160x90:rate=10",
        "-f","lavfi","-i","sine=frequency=440:sample_rate=48000",
        "-t","1","-c:v","mpeg4","-c:a","aac","-shortest",str(p)],check=True,timeout=30)
    raw=subprocess.run(["ffprobe","-v","quiet","-of","json","-show_streams",str(p)],check=True,capture_output=True,text=True,timeout=15)
    kinds={stream["codec_type"] for stream in json.loads(raw.stdout)["streams"]}
    assert {"audio","video"}<=kinds
    print("PASS: generated and decoded tiny synthetic audio+video MP4; zero external media")
    print("This is not a real episode renderer or QA validation.")
