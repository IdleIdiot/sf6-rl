"""
SF6 全角色帧数据爬虫
数据源 1: 4rays/sf6-move-data (GitHub TOML) - 精确帧数、Drive Gauge 数据
数据源 2: supercombo.gg Cargo API (MediaWiki) - 多段伤害、无敌帧、详细 notes

输出: sf6_env/data/characters/<char>_frames.json
"""
import urllib.request
import urllib.parse
import json
import toml
import time
from pathlib import Path

# ── 数据源配置 ──────────────────────────────────────────────────────────────
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/4rays/sf6-move-data/main/moves"
SUPERCOMBO_API  = "https://wiki.supercombo.gg/api.php"
OUTPUT_DIR      = Path("sf6_env/data/characters")

# 4rays repo 中的角色文件名 → supercombo.gg 中的 chara 字段值
CHARACTERS = {
    "aki":      "A.K.I.",
    "akuma":    "Akuma",
    "blanka":   "Blanka",
    "cammy":    "Cammy",
    "chunli":   "Chun-Li",
    "deejay":   "Dee Jay",
    "dhalsim":  "Dhalsim",
    "ed":       "Ed",
    "ehonda":   "E. Honda",
    "guile":    "Guile",
    "jamie":    "Jamie",
    "jp":       "JP",
    "juri":     "Juri",
    "ken":      "Ken",
    "kimberly": "Kimberly",
    "lily":     "Lily",
    "luke":     "Luke",
    "mai":      "Mai",
    "manon":    "Manon",
    "marisa":   "Marisa",
    "mbison":   "M. Bison",
    "rashid":   "Rashid",
    "ryu":      "Ryu",
    "terry":    "Terry",
    "zangief":  "Zangief",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; sf6-framedata-scraper/1.0)"}


# ── 数据源 1: 4rays GitHub TOML ─────────────────────────────────────────────

def fetch_github_toml(char_slug: str) -> dict:
    url = f"{GITHUB_RAW_BASE}/{char_slug}.toml"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return toml.loads(r.read().decode("utf-8"))


def parse_invuln_frames(notes: list[str]) -> dict:
    """从 notes 中解析无敌帧信息"""
    invuln = {}
    for note in notes:
        note_lower = note.lower()
        if "invincible" in note_lower or "invuln" in note_lower:
            if "strike" in note_lower and "throw" in note_lower:
                invuln["strike_throw"] = note
            elif "strike" in note_lower:
                invuln["strike"] = note
            elif "throw" in note_lower:
                invuln["throw"] = note
            elif "projectile" in note_lower:
                invuln["projectile"] = note
            elif "fully" in note_lower or "complete" in note_lower:
                invuln["full"] = note
    return invuln


def convert_github_move(move: dict) -> dict:
    """将 4rays TOML move 转换为内部格式"""
    startup = move.get("startup", 1)
    active = move.get("active", [1])
    if isinstance(active, int):
        active = [active]
    active_frames_array = active if active else [1]
    recovery = move.get("recovery", 1)

    frame_adv = move.get("frameAdvantage", {})
    on_hit   = frame_adv.get("hit", 0)
    on_block = frame_adv.get("block", 0)

    damage = move.get("damage", 0)

    drive_gauge = move.get("driveGauge", {})
    drive_gain_hit   = drive_gauge.get("onHit", 0) / 10000.0
    drive_gain_block = drive_gauge.get("onBlock", 0) / 10000.0

    properties = list(move.get("properties", []))
    move_type  = move.get("type", "normal")
    if "super" in move_type and "super" not in properties:
        properties.append("super")
    if "special" in move_type and "special" not in properties:
        properties.append("special")

    notes = move.get("notes", [])

    result = {
        "name":          move.get("name", ""),
        "name_ja":       move.get("name_ja", ""),
        "input":         move.get("input", ""),
        "type":          move_type,
        "block_type":    move.get("blockType", "high"),
        "startup":       startup,
        "active":        len(active_frames_array),
        "active_frames": active_frames_array,
        "recovery":      recovery,
        "on_hit":        on_hit,
        "on_block":      on_block,
        "damage":        damage,
        "chip_damage":   int(damage * 0.25),
        "drive_gain_hit":   drive_gain_hit,
        "drive_gain_block": drive_gain_block,
        "drive_cost":    0.0,
        "properties":    properties,
        "hitboxes":      [],
        "hurtboxes":     [{"x_offset": 0, "y_offset": 60, "w": 40, "h": 120}],
        "hit_count":     move.get("hitCount", 1),
        "notes":         notes,
        "invuln":        parse_invuln_frames(notes),
        "cancel":        move.get("cancel", ""),
        "scaling":       move.get("scaling", []),
    }

    if "super1" in move_type:
        result["super_cost"] = 1
    elif "super2" in move_type:
        result["super_cost"] = 2
    elif "super3" in move_type:
        result["super_cost"] = 3

    return result


# ── 数据源 2: supercombo.gg Cargo API ───────────────────────────────────────

CARGO_FIELDS = ",".join([
    "chara", "name", "input", "moveType",
    "damage", "chip", "dmgScaling",
    "startup", "active", "recovery", "total",
    "hitAdv", "blockAdv", "punishAdv",
    "invuln", "armor", "airborne",
    "driveDmgBlk", "driveDmgHit", "driveGain",
    "superGainHit", "superGainBlk",
    "jugStart", "jugIncrease", "jugLimit",
    "notes",
])


def fetch_supercombo_char(chara_name: str) -> list[dict]:
    """从 supercombo.gg Cargo API 获取单个角色的所有 move 数据"""
    all_moves = []
    offset = 0
    limit  = 100

    while True:
        params = urllib.parse.urlencode({
            "action":  "cargoquery",
            "tables":  "SF6_FrameData",
            "fields":  CARGO_FIELDS,
            "where":   f'chara="{chara_name}"',
            "limit":   limit,
            "offset":  offset,
            "format":  "json",
        })
        url = f"{SUPERCOMBO_API}?{params}"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"    supercombo fetch error (offset={offset}): {e}")
            break

        if "error" in data:
            print(f"    supercombo API error: {data['error'].get('info','')[:80]}")
            break

        batch = [item["title"] for item in data.get("cargoquery", [])]
        all_moves.extend(batch)

        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.3)  # 礼貌性延迟

    return all_moves


def parse_damage_string(dmg_str: str) -> tuple[int, int, list[int]]:
    """
    解析伤害字符串，例如:
      "500x4,800 (2800)"  -> total=2800, hits=5, per_hit=[500,500,500,500,800]
      "200x11,800 (3000)" -> total=3000, hits=12
      "800"               -> total=800, hits=1
    返回 (total_damage, hit_count, per_hit_list)
    """
    import re
    if not dmg_str:
        return 0, 1, []

    # 去掉 HTML 标签
    dmg_str = re.sub(r"<[^>]+>", "", dmg_str).strip()

    # 提取括号内的总伤害
    total_match = re.search(r"\((\d+)\)", dmg_str)
    total = int(total_match.group(1)) if total_match else None

    # 去掉括号部分
    base = re.sub(r"\([^)]*\)", "", dmg_str).strip().rstrip(",")

    per_hit = []
    for part in base.split(","):
        part = part.strip()
        if not part:
            continue
        xmatch = re.match(r"(\d+)x(\d+)", part)
        if xmatch:
            val, count = int(xmatch.group(1)), int(xmatch.group(2))
            per_hit.extend([val] * count)
        else:
            try:
                per_hit.append(int(re.sub(r"[^\d]", "", part)))
            except ValueError:
                pass

    hit_count = len(per_hit) if per_hit else 1
    if total is None:
        total = sum(per_hit) if per_hit else 0

    return total, hit_count, per_hit


def clean_frame_value(val: str) -> int | None:
    """将帧数字符串转换为整数，无法解析时返回 None"""
    import re
    if not val or val.strip() in ("", "-", "—", "N/A", "{{{invuln}}}"):
        return None
    # 去掉 HTML 和 wiki 标记
    val = re.sub(r"<[^>]+>", "", val)
    val = re.sub(r"'{2,}", "", val)
    val = val.strip()
    # 取第一个数字
    m = re.search(r"-?\d+", val)
    return int(m.group()) if m else None


def build_supercombo_index(moves: list[dict]) -> dict[str, dict]:
    """以 name 为 key 建立索引，同时解析多段伤害"""
    index = {}
    for m in moves:
        name = m.get("name", "").strip()
        if not name:
            continue

        dmg_str = m.get("damage", "")
        total_dmg, hit_count, per_hit = parse_damage_string(dmg_str)

        entry = {
            "sc_name":      name,
            "sc_input":     m.get("input", ""),
            "sc_move_type": m.get("moveType", ""),
            "damage_str":   dmg_str,
            "damage_total": total_dmg,
            "hit_count_sc": hit_count,
            "per_hit":      per_hit,
            "chip_str":     m.get("chip", ""),
            "startup_sc":   clean_frame_value(m.get("startup", "")),
            "active_sc":    m.get("active", ""),
            "recovery_sc":  clean_frame_value(m.get("recovery", "")),
            "on_hit_sc":    clean_frame_value(m.get("hitAdv", "")),
            "on_block_sc":  clean_frame_value(m.get("blockAdv", "")),
            "invuln_sc":    m.get("invuln", ""),
            "notes_sc":     m.get("notes", ""),
            "drive_dmg_blk": m.get("driveDmgBlk", ""),
            "drive_dmg_hit": m.get("driveDmgHit", ""),
            "jug_start":    m.get("jugStart", ""),
            "jug_limit":    m.get("jugLimit", ""),
        }
        index[name] = entry
    return index


# ── 合并两个数据源 ────────────────────────────────────────────────────────────

def merge_move(github_move: dict, sc_index: dict) -> dict:
    """
    以 4rays 数据为基础，用 supercombo.gg 数据补充/修正：
    - 多段伤害 (per_hit, hit_count)
    - 无敌帧字符串
    - supercombo 的详细 notes
    """
    result = dict(github_move)

    # 尝试用 name 匹配 supercombo 数据
    sc = sc_index.get(github_move.get("name", ""))
    if sc is None:
        # 尝试去掉 [Boosted] 前缀匹配
        name_clean = github_move.get("name", "").replace("[Boosted] ", "")
        sc = sc_index.get(name_clean)

    if sc:
        # 多段伤害
        if sc["per_hit"]:
            result["per_hit"]   = sc["per_hit"]
            result["hit_count"] = sc["hit_count_sc"]
            result["damage"]    = sc["damage_total"]
            result["chip_damage"] = int(sc["damage_total"] * 0.25)

        # 无敌帧（supercombo 的更详细）
        if sc["invuln_sc"] and sc["invuln_sc"] not in ("{{{invuln}}}", ""):
            result["invuln_str"] = sc["invuln_sc"]

        # 补充 supercombo notes
        if sc["notes_sc"]:
            result["notes_sc"] = sc["notes_sc"]

        # Drive Gauge 伤害（被打时）
        if sc["drive_dmg_blk"]:
            result["drive_dmg_on_block"] = sc["drive_dmg_blk"]
        if sc["drive_dmg_hit"]:
            result["drive_dmg_on_hit"] = sc["drive_dmg_hit"]

        # Juggle 数据
        if sc["jug_start"]:
            result["juggle_start"] = sc["jug_start"]
        if sc["jug_limit"]:
            result["juggle_limit"] = sc["jug_limit"]

    return result


# ── 主流程 ────────────────────────────────────────────────────────────────────

def process_character(char_slug: str, chara_name: str) -> dict:
    """下载并合并单个角色的数据"""
    # 1. 从 GitHub 获取基础数据
    toml_data = fetch_github_toml(char_slug)
    moves_dict = {}
    for move in toml_data.get("moves", []):
        slug = move.get("slug", move.get("name", "unknown"))
        moves_dict[slug] = convert_github_move(move)

    # 2. 从 supercombo.gg 获取补充数据
    sc_moves = fetch_supercombo_char(chara_name)
    sc_index = build_supercombo_index(sc_moves)

    # 3. 合并
    merged = {}
    for slug, move in moves_dict.items():
        merged[slug] = merge_move(move, sc_index)

    return merged, len(sc_moves)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading frame data for {len(CHARACTERS)} characters...")
    print(f"Sources: 4rays/sf6-move-data (GitHub) + supercombo.gg (Cargo API)")
    print()

    summary = []
    for i, (char_slug, chara_name) in enumerate(CHARACTERS.items(), 1):
        print(f"[{i:2}/{len(CHARACTERS)}] {char_slug:12}", end=" ", flush=True)
        try:
            merged, sc_count = process_character(char_slug, chara_name)

            output_file = OUTPUT_DIR / f"{char_slug}_frames.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)

            print(f"OK  {len(merged):3} moves  (supercombo: {sc_count})")
            summary.append((char_slug, len(merged), sc_count, None))
        except Exception as e:
            print(f"ERROR: {e}")
            summary.append((char_slug, 0, 0, str(e)))

        time.sleep(0.5)  # 礼貌性延迟

    # 输出汇总
    print()
    print("=" * 60)
    total_moves = sum(s[1] for s in summary)
    errors = [s for s in summary if s[3]]
    print(f"Done! {len(CHARACTERS) - len(errors)}/{len(CHARACTERS)} characters OK")
    print(f"Total moves: {total_moves}")
    print(f"Output: {OUTPUT_DIR.resolve()}")
    if errors:
        print(f"\nFailed ({len(errors)}):")
        for char, _, _, err in errors:
            print(f"  {char}: {err}")


if __name__ == "__main__":
    main()
