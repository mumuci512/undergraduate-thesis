#!/usr/bin/env python3
"""Reflect user-supplied official MD5 in periodically regenerated status."""
import os,time
from pathlib import Path
run=Path('/home/ysheng4/research/GSMF-RS-DIL/experiments/road_fog_severity/eval-final-seed0-20261109-182100')
status=run/'STATUS.md'; done=run/'acquisition-20261110/driver.exit'
old='官方独立 MD5 尚未提供，归档本地哈希见 `acquisition-20261110/archive-hashes.txt`。'
new='官方页面 MD5（用户提供）与本地 ZIP MD5 一致，见 `acquisition-20261110/official-md5-check.log`。'
while not done.exists():
 try:
  text=status.read_text()
  if old in text:
   temp=status.with_name('STATUS.md.md5-update-tmp')
   temp.write_text(text.replace(old,new))
   if status.read_text()==text:os.replace(str(temp),str(status))
   else:temp.unlink()
 except (OSError,UnicodeError):pass
 time.sleep(2)
