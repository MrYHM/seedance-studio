#!/usr/bin/env python3
"""seedance-studio 提示词自检器。

用法: python3 check_prompt.py <提示词文件> --duration <总秒数> [--version 2.0|2.5] [--long]

检查: 单条时长上限(2.0≤15s/2.5≤30s/--long≤180s)、时间码(从0开始/递增/无断档/
      无重叠/总时长)、镜头密度与时长变奏、台词语速、必需区块、声音行常量、
      素材声明(2.5)、字数预算、slop 词。error 退出码 1。
一条提示词 = 一次生成的完整时间轴；--duration 传本条时长（多段时逐段各跑一次）。
只做结构校验，不评判创意质量。
"""
import argparse
import re
import sys

# 匹配 "0-2s镜头1" / "0-3秒" / "镜头1 ｜ 0.0–6.0s" / "【0—3秒】" 等
SEG_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:s|S|秒)?\s*[—–\-~至]\s*(\d+(?:\.\d+)?)\s*(?:s|S|秒)"
)
QUOTE_RE = re.compile(r"「([^」]*)」")
CJK_RE = re.compile(r"[一-鿿]")

REQUIRED_BLOCKS = ["【风格与画质】", "【声音】", "【限制】"]
SOUND_CONSTANTS = ["不要生成任何背景音乐", "不要生成任何字幕"]
SLOP_WORDS = ["8K", "8k", "超清", "高清画质", "4K", "4k", "大师级",
              "电影感", "高级感", "饱和度高", "震撼", "精美绝伦"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--duration", type=float, required=True, help="本条提示词的总秒数")
    ap.add_argument("--version", default="2.0", choices=["2.0", "2.5"])
    ap.add_argument("--long", action="store_true",
                    help="2.5 超长模式（30-180s，须分幕，仅用户明确选择时）")
    args = ap.parse_args()
    if args.long and args.version != "2.5":
        ap.error("--long 仅适用于 --version 2.5")

    text = open(args.file, encoding="utf-8").read()
    errors, warnings = [], []

    # --- 单条时长上限（交付单位硬约束）---
    if args.version == "2.0" and args.duration > 15:
        errors.append(f"duration.cap: {args.duration:g}s 超过 2.0 单条上限 15s——"
                      "禁止逐镜生成，按 references/11-segmentation.md 拆条")
    elif args.version == "2.5" and not args.long and args.duration > 30:
        errors.append(f"duration.cap: {args.duration:g}s 超过 2.5 标准模式上限 30s——"
                      "拆条，或经用户确认后用超长模式（--long）")
    elif args.long and args.duration > 180:
        errors.append(f"duration.cap: {args.duration:g}s 超过 2.5 超长模式上限 180s")

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

        # --- 镜头密度与时长变奏 ---
        durs = [round(e - s, 2) for s, e in segs]
        if len(durs) >= 2:
            avg = sum(durs) / len(durs)
            if avg < 2.5:
                warnings.append(f"pacing.avg: 平均镜长 {avg:.1f}s < 2.5s，切分过碎——"
                                "按合镜规则把单动作镜合并成递进动作链")
            run = 1
            for i in range(1, len(durs)):
                run = run + 1 if abs(durs[i] - durs[i - 1]) < 0.05 else 1
                if run == 4:
                    warnings.append("pacing.monotony: 连续 4 镜时长相同，违反时长变奏强制"
                                    "（快剪组最多 2-3 镜，之后用中景/全景收住）")
                    break

        # --- 台词语速（按镜分配）---
        matches = list(SEG_RE.finditer(text))
        for i, m in enumerate(matches):
            span_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            span = text[m.end():span_end]
            total = 0
            for q in QUOTE_RE.findall(span):
                n_cjk = len(CJK_RE.findall(q))
                total += n_cjk
                if n_cjk > 15:
                    errors.append(f"dialogue.line: 第{i+1}镜台词「{q[:12]}…」"
                                  f"{n_cjk} 字超过单句上限 15 字")
            dur = segs[i][1] - segs[i][0]
            if total > dur * 6:
                errors.append(f"dialogue.speed: 第{i+1}镜台词共 {total} 字 > "
                              f"时长 {dur:g}s × 6 = {dur*6:g} 字，拆镜或删词")

    # --- 必需区块 ---
    for blk in REQUIRED_BLOCKS:
        if blk not in text:
            errors.append(f"block.missing: 缺少区块 {blk}")
    for c in SOUND_CONSTANTS:
        if c not in text:
            errors.append(f"sound.constant: 声音行缺少字面常量「{c}」")
    if "【参考】" not in text and "【素材声明】" not in text and "@图" not in text:
        warnings.append("reference.missing: 无任何参考素材引用（单条纯文生视频可忽略）")
    if args.version == "2.5" and ("@图" in text or "@视频" in text) \
            and "【素材声明】" not in text:
        warnings.append("assets.decl: 2.5 引用了素材但缺少【素材声明】区块"
                        "（职责/生效时段/禁止迁移项，防身份错位，见 06-prompt-v25.md）")

    # --- 超长模式结构 ---
    if args.long and not re.search(r"场景切换|第[一二三四五六七八九十0-9]+幕|幕旨", text):
        warnings.append("long.acts: 超长模式未见分幕/「场景切换」标记——"
                        "幕间必须显式重建立（见 06-prompt-v25.md 超长模式附加要求）")

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
