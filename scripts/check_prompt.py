#!/usr/bin/env python3
"""seedance-studio 提示词自检器。

用法: python3 check_prompt.py <提示词文件> --duration <总秒数> [--version 2.0|2.5]

检查: 时间码(从0开始/递增/无断档/无重叠/总时长)、必需区块、声音行常量、
      字数预算、slop 词。error 退出码 1。
只做结构校验，不评判创意质量。
"""
import argparse
import re
import sys

# 匹配 "0-2s镜头1" / "0-3秒" / "镜头1 ｜ 0.0–6.0s" / "【0—3秒】" 等
SEG_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:s|S|秒)?\s*[—–\-~至]\s*(\d+(?:\.\d+)?)\s*(?:s|S|秒)"
)

REQUIRED_BLOCKS = ["【风格与画质】", "【声音】", "【限制】"]
SOUND_CONSTANTS = ["不要生成任何背景音乐", "不要生成任何字幕"]
SLOP_WORDS = ["8K", "8k", "超清", "高清画质", "4K", "4k", "大师级",
              "电影感", "高级感", "饱和度高", "震撼", "精美绝伦"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--duration", type=float, required=True, help="目标总秒数")
    ap.add_argument("--version", default="2.0", choices=["2.0", "2.5"])
    args = ap.parse_args()

    text = open(args.file, encoding="utf-8").read()
    errors, warnings = [], []

    # --- 时间轴 ---
    segs = [(float(m.group(1)), float(m.group(2))) for m in SEG_RE.finditer(text)]
    if not segs:
        errors.append("timeline.missing: 未识别到任何时间段")
    else:
        if segs[0][0] != 0:
            errors.append(f"timeline.start: 时间轴应从 0 开始（实际 {segs[0][0]}）")
        for i, (s, e) in enumerate(segs, 1):
            if e <= s:
                errors.append(f"timeline.invalid: 第{i}段 {s}-{e} 结束≤开始")
        for i in range(1, len(segs)):
            prev_end, cur_start = segs[i - 1][1], segs[i][0]
            if cur_start > prev_end + 0.05:
                errors.append(
                    f"timeline.gap: 第{i}段结束 {prev_end}s 与第{i+1}段开始 {cur_start}s 之间有断档")
            elif cur_start < prev_end - 0.05:
                errors.append(
                    f"timeline.overlap: 第{i+1}段开始 {cur_start}s 早于第{i}段结束 {prev_end}s")
        if abs(segs[-1][1] - args.duration) > 0.05:
            errors.append(
                f"timeline.duration: 末段结束 {segs[-1][1]}s ≠ 目标总时长 {args.duration}s")
        print(f"[info] 识别到 {len(segs)} 个时间段，末段结束于 {segs[-1][1]}s")

    # --- 必需区块 ---
    for blk in REQUIRED_BLOCKS:
        if blk not in text:
            errors.append(f"block.missing: 缺少区块 {blk}")
    for c in SOUND_CONSTANTS:
        if c not in text:
            errors.append(f"sound.constant: 声音行缺少字面常量「{c}」")
    if "【参考】" not in text and "【素材声明】" not in text and "@图" not in text:
        warnings.append("reference.missing: 无任何参考素材引用（单条纯文生视频可忽略）")

    # --- slop 词 ---
    for w in SLOP_WORDS:
        if w in text:
            warnings.append(f"slop.word: 出现空泛画质词「{w}」，改用具体物理表达（见 08-vocab.md）")

    # --- 字数预算 ---
    n = len(re.sub(r"\s", "", text))
    limit_err, limit_warn = (4000, 3500) if args.version == "2.5" else (99999, 1000)
    print(f"[info] 去空白字符数：{n}")
    if n > limit_err:
        errors.append(f"length: {n} 字超过 {args.version} 上限 {limit_err}")
    elif n > limit_warn:
        warnings.append(f"length: {n} 字超过 {args.version} 建议值 {limit_warn}，考虑按压缩优先级删减")

    # --- 输出 ---
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    if not errors and not warnings:
        print("PASS 全部检查通过")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
