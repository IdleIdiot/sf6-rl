#!/usr/bin/env python3
"""Audit all Mai moves for correctness."""
import json
from pathlib import Path

fd_path = Path("sf6_env/data/mai_frames.json")
fd = json.loads(fd_path.read_text(encoding="utf-8"))

# Expected action_id mapping from mai.py
ACTION_MAP = {
    0: "idle", 1: "walk_forward", 2: "walk_back", 3: "crouch", 4: "jump",
    5: "5LP", 6: "5MP", 7: "5HP", 8: "5LK", 9: "5MK", 10: "5HK",
    11: "2LP", 12: "2MP", 13: "2HP", 14: "2LK", 15: "2MK", 16: "2HK",
    17: "jLP", 18: "jMP", 19: "jHP", 20: "jLK", 21: "jMK", 22: "jHK",
    23: "kachousen_L", 24: "kachousen_M", 25: "kachousen_H",
    26: "idle", 27: "idle", 28: "idle",  # unused slots (midare_kachousen removed)
    29: "ryuuenbu_L", 30: "ryuuenbu_M", 31: "ryuuenbu_H",
    32: "shinobibachi_L", 33: "shinobibachi_M", 34: "shinobibachi_H",
    35: "hishou_ryuuenjin_L", 36: "hishou_ryuuenjin_M", 37: "hishou_ryuuenjin_H",
    38: "musasabi_L", 39: "musasabi_M", 40: "musasabi_H",
    41: "kachousen_OD", 42: "ryuuenbu_OD", 43: "hishou_ryuuenjin_OD",
    44: "SA1", 45: "SA2", 46: "SA3",
    47: "drive_impact", 48: "drive_reversal",
    49: "forward_throw", 50: "back_throw",
    51: "dash_forward", 52: "dash_back",
    53: "jump_forward", 54: "jump_back",
    55: "shinobibachi_OD", 56: "hien_ren_kyaku", 57: "hoshi_kujaku", 58: "senkotsu_uchi",
}

AIRBORNE_ONLY = {17, 18, 19, 20, 21, 22, 38, 39, 40}
GROUND_ONLY = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
               23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
               41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58}

issues = []

print("=== MOVE AUDIT ===\n")

# Check all mapped moves exist in JSON
for action_id, move_name in ACTION_MAP.items():
    if move_name not in fd:
        issues.append(f"MISSING: action {action_id} -> {move_name} not in JSON")

# Check critical fields for each move
for move_name, data in fd.items():
    # Find action_id
    action_id = None
    for aid, name in ACTION_MAP.items():
        if name == move_name:
            action_id = aid
            break

    # Check required fields
    if "startup" not in data:
        issues.append(f"{move_name}: missing 'startup'")
    if "active" not in data:
        issues.append(f"{move_name}: missing 'active'")
    if "recovery" not in data:
        issues.append(f"{move_name}: missing 'recovery'")

    # Check projectiles have active=0 or hitboxes=[]
    if "projectile" in data.get("properties", []):
        if data.get("active", 0) > 0 and len(data.get("hitboxes", [])) > 0:
            issues.append(f"{move_name}: projectile with active>0 AND hitboxes (should be one or other)")

    # Check knockdown moves have on_hit=60 or knockdown property
    if data.get("on_hit", 0) == 60 and "knockdown" not in data.get("properties", []):
        issues.append(f"{move_name}: on_hit=60 but missing 'knockdown' property")
    if "knockdown" in data.get("properties", []) and data.get("on_hit", 0) != 60:
        issues.append(f"{move_name}: has 'knockdown' but on_hit={data.get('on_hit')} (should be 60)")

    # Check air moves have "air" property
    if action_id in AIRBORNE_ONLY and "air" not in data.get("properties", []):
        issues.append(f"{move_name}: airborne-only but missing 'air' property")

    # Check specials have "special" property (exclude dashes 51-54 and throws 49-50)
    if action_id and action_id >= 23 and action_id <= 58 and action_id not in {49, 50, 51, 52, 53, 54}:
        if "special" not in data.get("properties", []):
            issues.append(f"{move_name}: special move but missing 'special' property")

    # Check OD moves have drive_cost=2.0
    if "OD" in move_name or "overdrive" in data.get("properties", []):
        if data.get("drive_cost", 0) != 2.0:
            issues.append(f"{move_name}: OD move but drive_cost={data.get('drive_cost')} (should be 2.0)")

    # Check supers have super_cost
    if "super" in data.get("properties", []):
        if data.get("super_cost", 0) == 0:
            issues.append(f"{move_name}: has 'super' property but super_cost=0")

    # Check musasabi_M and musasabi_H missing hit_count
    if move_name in ("musasabi_M", "musasabi_H") and "hit_count" not in data:
        issues.append(f"{move_name}: missing 'hit_count' field")

    # Check drive_impact and drive_reversal missing hit_count
    if move_name in ("drive_impact", "drive_reversal") and "hit_count" not in data:
        issues.append(f"{move_name}: missing 'hit_count' field")

print(f"Found {len(issues)} issues:\n")
for issue in issues:
    print(f"  - {issue}")

if not issues:
    print("  OK All moves pass audit")
