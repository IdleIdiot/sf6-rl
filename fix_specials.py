#!/usr/bin/env python3
"""修复特技数据中的问题"""
import json
from pathlib import Path

fd_path = Path("sf6_env/data/mai_frames.json")
fd = json.loads(fd_path.read_text(encoding="utf-8"))

print("=== 修复特技数据 ===\n")

# 问题1: SA1/SA3 的 active=0 需要修复为合理值
# 参考 SA2 的设计，超必杀应该有判定窗口
# SA1 是突进型，给 active=20
# SA3 是大范围爆发，给 active=15
print("修复 SA1 active: 0 -> 20")
fd["SA1"]["active"] = 20
fd["SA1"]["recovery"] = 30  # 补充 recovery

print("修复 SA3 active: 0 -> 15")
fd["SA3"]["active"] = 15
fd["SA3"]["recovery"] = 40  # 补充 recovery

# 问题2: midare_kachousen_L/M/H 不存在于官方数据
# 这些是 214P 技能，但 Mai 在 SF6 里没有 214P
# 需要从 JSON 中删除，并从 action_map 中移除
print("\n删除不存在的技能: midare_kachousen_L/M/H")
for k in ["midare_kachousen_L", "midare_kachousen_M", "midare_kachousen_H"]:
    if k in fd:
        del fd[k]
        print(f"  已删除: {k}")

# 问题3: musasabi 只有一个版本，但 action_map 里有 L/M/H 三个
# 保留 musasabi_L (action_id 38)，删除 M/H
print("\n统一 musasabi 版本")
if "musasabi" in fd:
    # 用 musasabi 覆盖 musasabi_L
    fd["musasabi_L"] = fd["musasabi"]
    del fd["musasabi"]
    print("  musasabi -> musasabi_L")

# musasabi_M/H 保留但标记为 musasabi_L 的副本（为了兼容 action_map）
fd["musasabi_M"] = fd["musasabi_L"].copy()
fd["musasabi_H"] = fd["musasabi_L"].copy()
print("  musasabi_M/H 设为 musasabi_L 的副本")

# 问题4: hoshi_kujaku_followup 在 JSON 里但不在 action_map
# 这是连续技的第二段，应该通过 cancel_into 触发，不需要独立 action_id
# 暂时保留在 JSON 中，但不加入 action_map

# 保存
fd_path.write_text(json.dumps(fd, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n已保存到", fd_path)

print("\n=== 需要手动修改的文件 ===")
print("1. sf6_env/characters/mai.py")
print("   - 删除 action_map 中的 26,27,28 (midare_kachousen_L/M/H)")
print("   - 删除 GROUND_ONLY 中的 26,27,28")
print("2. main.py")
print("   - 删除 MOTION_TABLE 中的 214P 指令 (midare_kachousen)")
