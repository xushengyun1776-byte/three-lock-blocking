#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assemble_prompt.py - 三锁控场法 五维提示词组装器

把「角色资产 / 站位图 / 运镜预演 / 时间码节拍」组装成视频模型可用的五维提示词。
对应 SKILL.md 第三节：D1 运镜锚定 / D2 角色声明 / D3 摄影灯光 / D4 当前状态 / D5 时间码。

输入：一个 JSON（--in input.json），结构见 --sample。
输出：可直接粘贴到 即梦 / 可灵 / H3 / ComfyUI 图生视频 的提示词文本（--out 可选，否则 stdout）。

关键纪律（写进输出，提醒遵守）：
  - C1-C6 只在前部声明一次（锁一铁律）
  - 站位锁定后中后段不重描整房（锁二铁律）
  - 时间码越靠后越局部（锁三铁律）

用法：
  python assemble_prompt.py --sample            # 打印示例输入 JSON
  python assemble_prompt.py --in input.json     # 组装并打印
  python assemble_prompt.py --in input.json --out prompt.txt
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def sample_input() -> dict:
    return {
        "previz": "视频1是一个简单模型运镜视频，严格锚定视频中人物站位与空间关系，"
                  "严格逐秒复刻，不自行改轨迹、不增加镜头、不甩镜、不切镜；场景参考图片2。",
        "characters": [
            {"code": "C1", "name": "伊芙", "image": "图片4"},
            {"code": "C2", "name": "丹尼尔", "image": "图片5"},
            {"code": "C3", "name": "亚瑟", "image": "图片6"},
            {"code": "C4", "name": "薇拉", "image": "图片7"},
            {"code": "C5", "name": "朱利安", "image": "图片8"},
            {"code": "C6", "name": "管家", "image": "图片9"},
        ],
        "staging": "图片3作为场景中人物站位锚定",
        "cinematography": "写实风格，好莱坞 VFX，ARRI 35，变形镜头，高反差光效，非 3D 动画。"
                         "光效参考图片2。手持呼吸一镜到底拍摄，保持真实透视。"
                         "人物进入不同光区时曝光连续，暗部有层次，不变成通透明亮的棚拍。"
                         "真实电影质感的单镜到底群像戏。",
        "current_state": "当前镜头：c1 伊芙坐在红色长沙发上，身体面向房间中央。",
        "beats": [
            {"start": 0.00, "end": 4.00,
             "text": "第一帧镜头位于红色长沙发背后缓慢前推。前景右侧是 c1 伊芙（图片4）的肩膀、"
                     "侧脸与上半身，背景左侧是站在壁炉前的 c5 朱利安（图片8）。"
                     "c1 伊芙头与眼睛转向画面左侧，与没有出镜的 c3 亚瑟争吵。"},
        ],
    }


def assemble(d: dict) -> str:
    lines = []
    # D1 运镜锚定（最前，权重最高）
    lines.append(d.get("previz", "").strip())
    lines.append("")
    # D2 角色声明（仅前部一次）
    lines.append("【人物初始站位设定】" + d.get("staging", "").strip())
    char_block = "；".join(
        f"{c['code']} {c['name']} {c['image']}" for c in d.get("characters", [])
    )
    if char_block:
        lines.append(char_block + "；")
    lines.append("")
    # D3 摄影灯光
    lines.append("【摄影与灯光】")
    lines.append(d.get("cinematography", "").strip())
    lines.append("")
    # D4 当前状态
    cs = d.get("current_state", "").strip()
    if cs:
        lines.append("【当前状态】")
        lines.append(cs)
        lines.append("")
    # D5 时间码
    lines.append("【精确时间码、画面、表演与对白】")
    for b in d.get("beats", []):
        lines.append(f"{b['start']:05.2f}-{b['end']:05.2f}：{b['text'].strip()}")
    lines.append("")
    lines.append("要求最终镜头严格遵循这条预演。")
    # 纪律红线提醒（注释形式，不污染主提示词）
    lines.append("")
    lines.append("# —— 纪律红线（不要写进视频模型提示词，仅作自检）——")
    lines.append("# 1. C1-C6 只声明一次，后续镜头不重描全角色")
    lines.append("# 2. 站位锁定后中后段提示词不重描整房")
    lines.append("# 3. 时间码越靠后越局部、越具体，不重复整套空间设定")
    lines.append("# 4. 白模预演不追求质感，只验证空间/节奏/路径")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True,
        description="三锁控场法 五维提示词组装器")
    ap.add_argument("--in", dest="inp", default="",
        help="输入 JSON 路径（含 characters/staging/previz/cinematography/beats）")
    ap.add_argument("--out", default="", help="输出提示词文件路径")
    ap.add_argument("--sample", action="store_true",
        help="打印示例输入 JSON 后退出")
    args = ap.parse_args()

    if args.sample:
        print(json.dumps(sample_input(), ensure_ascii=False, indent=2))
        return 0

    if not args.inp:
        print("错误：需 --in input.json 或 --sample", file=sys.stderr)
        return 2

    try:
        d = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"读取/解析 JSON 失败：{e}", file=sys.stderr)
        return 1

    prompt = assemble(d)
    if args.out:
        Path(args.out).write_text(prompt, encoding="utf-8")
        print(f"已写入 {args.out}（{len(prompt)} 字符）")
    else:
        print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
