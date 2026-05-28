#!/usr/bin/env python3
import json, re, requests
from bs4 import BeautifulSoup
from pathlib import Path

HEADERS = {"User-Agent": "Mozilla/5.0"}
URL = "https://ultimateframedata.com/sf6/mai"

MOVE_NAME_MAP = {
    "Standing Light Punch": "5LP", "Standing Medium Punch": "5MP", "Standing Heavy Punch": "5HP",
    "Standing Light Kick": "5LK", "Standing Medium Kick": "5MK", "Standing Heavy Kick": "5HK",
    "Crouching Light Punch": "2LP", "Crouching Medium Punch": "2MP", "Crouching Heavy Punch": "2HP",
    "Crouching Light Kick": "2LK", "Crouching Medium Kick": "2MK", "Crouching Heavy Kick": "2HK",
    "Jump Light Punch": "jLP", "Jump Medium Punch": "jMP", "Jump Heavy Punch": "jHP",
    "Jump Light Kick": "jLK", "Jump Medium Kick": "jMK", "Jump Heavy Kick": "jHK",
    "Kachousen (Light Punch)": "kachousen_L", "Kachousen (Medium Punch)": "kachousen_M", "Kachousen (Heavy Punch)": "kachousen_H",
    "Kachousen (Overdrive)": "kachousen_OD",
    "Hishou Ryuuenjin (Light Kick)": "hishou_ryuuenjin_L", "Hishou Ryuuenjin (Medium Kick)": "hishou_ryuuenjin_M", "Hishou Ryuuenjin (Heavy Kick)": "hishou_ryuuenjin_H",
    "Hishou Ryuuenjin (Overdrive)": "hishou_ryuuenjin_OD",
    "Ryuuenbu (Light Punch)": "ryuuenbu_L", "Ryuuenbu (Medium Punch)": "ryuuenbu_M", "Ryuuenbu (Heavy Punch)": "ryuuenbu_H",
    "Ryuuenbu (Overdrive)": "ryuuenbu_OD",
    "Hissatsu Shinobi Bachi (Light Kick)": "shinobibachi_L", "Hissatsu Shinobi Bachi (Medium Kick)": "shinobibachi_M", "Hissatsu Shinobi Bachi (Heavy Kick)": "shinobibachi_H",
    "Hissatsu Shinobi Bachi (Overdrive)": "shinobibachi_OD",
    "Musasabi no Mai (During Forward Jump Only)": "musasabi_L",
    "Forward + Medium Punch (Senkotsu Uchi)": "senkotsu_uchi",
    "Back + Heavy Kick (Hoshi Kujaku)": "hoshi_kujaku",
    "Light Kick, Light Kick, Light Kick (Hien Ren Kyaku)": "hien_ren_kyaku",
    "Kagerou no Mai (Level 1)": "SA1",
    "Chou Hissatsu Shinobi Bachi (Level 2)": "SA2",
    "Air Chou Hissatsu Shinobi Bachi (Level 2)": "SA2_air",
    "Shiranui Ryuu: Enbu Ada Zakura (Level 3)": "SA3",
    "Forward Throw": "forward_throw", "Back Throw": "back_throw",
}

def parse_int(s):
    m = re.search(r'\d+', s)
    return int(m.group()) if m else 0

def parse_frames(s):
    if not s or s == "N/A": return 0
    if "~" in s: return parse_int(s.split("~")[0])
    return parse_int(s)

def parse_advantage(s):
    if not s or s == "N/A": return 0
    if "KD" in s or "Knockdown" in s: return 60
    if "Crumple" in s: return 80
    m = re.search(r'[+-]?\d+', s)
    return int(m.group()) if m else 0

def parse_damage(s):
    if not s or s == "N/A": return 0
    # strip parenthetical and bracketed variants (flame stock, OD), take base values only
    s = re.sub(r'[\(\[].*?[\)\]]', '', s)
    parts = re.findall(r'\d+', s)
    return sum(int(p) for p in parts) if parts else 0

def count_hits(s):
    if not s or s == "N/A": return 1
    s = re.sub(r'[\(\[].*?[\)\]]', '', s)
    parts = re.findall(r'\d+', s)
    return max(1, len(parts))

SUPER_COSTS = {"SA1": 1, "SA2": 2, "SA2_air": 2, "SA3": 3}
DRIVE_COSTS = {"kachousen_OD": 2.0, "hishou_ryuuenjin_OD": 2.0, "ryuuenbu_OD": 2.0, "shinobibachi_OD": 2.0,
               "drive_impact": 1.0, "drive_reversal": 2.0}

def get_text(container, cls):
    el = container.find(class_=cls)
    return el.get_text(strip=True) if el else ""

def scrape():
    resp = requests.get(URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.find_all("div", class_="movecontainer")
    print(f"Found {len(containers)} move containers")

    raw = []
    for c in containers:
        name_raw = get_text(c, "movename")
        startup_raw = get_text(c, "startup")
        active_raw = get_text(c, "activeframes")
        recovery_raw = get_text(c, "recovery")
        total_raw = get_text(c, "totalframes")
        on_hit_raw = get_text(c, "onhit")
        on_block_raw = get_text(c, "onblock")
        damage_raw = get_text(c, "basedamage")
        cancel_raw = get_text(c, "cancellable")
        notes_raw = get_text(c, "notes")
        attack_type = get_text(c, "attacktype")
        raw.append({
            "name": name_raw, "startup": startup_raw, "active": active_raw,
            "recovery": recovery_raw, "total": total_raw,
            "on_hit": on_hit_raw, "on_block": on_block_raw,
            "damage": damage_raw, "cancel": cancel_raw,
            "notes": notes_raw, "attack_type": attack_type,
        })
    return raw

def convert_to_framedata(raw):
    fd = {}
    for m in raw:
        key = MOVE_NAME_MAP.get(m["name"])
        if not key: continue
        startup = parse_frames(m["startup"])
        active = parse_frames(m["active"])
        recovery = parse_frames(m["recovery"])
        total = parse_frames(m["total"])
        if total == 0: total = startup + active + recovery
        on_hit = parse_advantage(m["on_hit"])
        on_block = parse_advantage(m["on_block"])
        damage = parse_damage(m["damage"])
        hit_count = count_hits(m["damage"])
        props = []
        notes_lower = m["notes"].lower()
        if "projectile" in notes_lower: props.append("projectile")
        if "low" in m["attack_type"].lower(): props.append("low")
        if "overhead" in m["attack_type"].lower(): props.append("overhead")
        if "throw" in m["attack_type"].lower(): props.append("throw")
        if "knockdown" in m["on_hit"].lower(): props.append("knockdown")
        if "crumple" in m["on_hit"].lower(): props.append("crumple")
        if key in ("SA1", "SA2", "SA2_air", "SA3"): props.append("special")
        if key in ("kachousen_L", "kachousen_M", "kachousen_H", "kachousen_OD"): props.append("projectile")
        cancel_into = []
        cancel_lower = m["cancel"].lower()
        if "special" in cancel_lower: cancel_into.append("specials")
        if "super" in cancel_lower: cancel_into.append("super")
        if "chain" in cancel_lower: cancel_into.append("normals")
        fd[key] = {
            "startup": startup, "active": active, "recovery": recovery,
            "on_hit": on_hit, "on_block": on_block, "damage": damage,
            "chip_damage": damage // 4, "drive_gain_hit": 0.5, "drive_gain_block": 0.25,
            "drive_cost": DRIVE_COSTS.get(key, 0.0),
            "super_cost": SUPER_COSTS.get(key, 0),
            "cancel_into": cancel_into, "properties": props, "hit_count": hit_count,
            "hitboxes": [{"x_offset": 50, "y_offset": 80, "w": 60, "h": 40}],
            "hurtboxes": [{"x_offset": 0, "y_offset": 0, "w": 40, "h": 120}],
        }
    return fd

if __name__ == "__main__":
    out_dir = Path("sf6_env/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = scrape()
    raw_path = out_dir / "mai_scraped_raw.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Raw data saved to {raw_path} ({len(raw)} entries)")
    fd = convert_to_framedata(raw)
    fd_path = out_dir / "mai_scraped_framedata.json"
    fd_path.write_text(json.dumps(fd, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Frame data saved to {fd_path} ({len(fd)} moves mapped)")
