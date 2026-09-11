#!/usr/bin/env python3
"""check_prompt.py 回归测试：黄金范例正向 + 构造坏样本负向。

用法: python3 tests/run_regression.py
全部通过退出 0，任一失败退出 1 并打印差异。
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_prompt.py"
EX20 = ROOT / "examples" / "冷宫美食工坊.md"
EX25 = ROOT / "examples" / "武松打虎.md"


def extract(md_path):
    """取出 markdown 里第一个代码块，即最终提示词。"""
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"```\n(.*?)```", text, re.S)
    if not m:
        sys.exit(f"FATAL 无法从 {md_path.name} 提取提示词代码块")
    return m.group(1)


def run(prompt, *args):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8",
                                    delete=False) as fh:
        fh.write(prompt)
        path = fh.name
    proc = subprocess.run([sys.executable, str(CHECKER), path, *args],
                          capture_output=True, text=True)
    Path(path).unlink(missing_ok=True)
    return proc.returncode, proc.stdout + proc.stderr


def main():
    g20, g25 = extract(EX20), extract(EX25)

    # (用例名, 提示词, 参数, 期望出现的码, 期望退出码)
    cases = [
        ("正向 2.0 黄金范例", g20, ["--duration", "15", "--version", "2.0"], "PASS", 0),
        ("正向 2.5 黄金范例", g25, ["--duration", "30", "--version", "2.5"], "PASS", 0),
        ("2.0 超单条上限须拦",
         g20, ["--duration", "99", "--version", "2.0"], "duration.cap", 1),
        ("2.5 标准模式超 30s 须拦",
         g25, ["--duration", "35", "--version", "2.5"], "duration.cap", 1),
        ("时间码断档",
         g20.replace("2-5s镜头2", "3-5s镜头2"),
         ["--duration", "15"], "timeline.gap", 1),
        ("声音行常量被改写",
         g20.replace("不要生成任何背景音乐", "不要背景音乐"),
         ["--duration", "15"], "sound.constant", 1),
        ("台词超语速预算",
         g20.replace("「冷宫食铺！开业啦！」",
                     "「冷宫食铺今天正式开业啦大家快来买好吃的糕点甜汤炸鸡腿全场八折先到先得」"),
         ["--duration", "15"], "dialogue.speed", 1),
        ("镜头时长单调",
         g20.replace("0-2s镜头1", "0-3s镜头1")
            .replace("2-5s镜头2", "3-6s镜头2")
            .replace("5-8s镜头3", "6-9s镜头3")
            .replace("8-12s镜头4", "9-12s镜头4"),
         ["--duration", "15"], "pacing.monotony", 0),
        ("连续同景别超 2 镜",
         g20.replace("【中景+舒缓跟拍】", "【近景+舒缓跟拍】"),
         ["--duration", "15"], "pacing.scale", 0),
        ("slop 画质词",
         g20.replace("写实电影质感", "8K超清大师级电影感"),
         ["--duration", "15"], "slop.word", 0),
        ("2.5 引用素材却缺素材声明",
         g25.replace("【素材声明】\n", ""),
         ["--duration", "30", "--version", "2.5"], "assets.decl", 0),
    ]

    failed = []
    for name, prompt, args, expect, expect_rc in cases:
        rc, out = run(prompt, *args)
        ok_code = expect in out
        ok_rc = rc == expect_rc
        status = "PASS" if (ok_code and ok_rc) else "FAIL"
        print(f"[{status}] {name}")
        if status == "FAIL":
            detail = []
            if not ok_code:
                detail.append(f"输出未含「{expect}」")
            if not ok_rc:
                detail.append(f"退出码 {rc} ≠ 期望 {expect_rc}")
            print("        " + "；".join(detail))
            print("        实际输出：" + out.strip().replace("\n", " | ")[:300])
            failed.append(name)

    print(f"\n共 {len(cases)} 项，失败 {len(failed)} 项")
    # --long 参数互斥性单独验证（argparse 报错走 stderr、退出码 2）
    rc, out = run(g20, "--duration", "15", "--version", "2.0", "--long")
    if "--long 仅适用于 --version 2.5" not in out:
        print("[FAIL] --long 与 2.0 的互斥校验未生效")
        failed.append("--long 互斥")
    else:
        print("[PASS] --long 与 2.0 互斥校验")

    if failed:
        sys.exit(1)
    print("全部回归通过")


if __name__ == "__main__":
    main()
