from __future__ import annotations

MAX_HEALTH = 10000.0


def compute_reward(prev_state: dict, curr_state: dict, perspective: int) -> float:
    if perspective == 0:
        self_key, opp_key = "p1", "p2"
    else:
        self_key, opp_key = "p2", "p1"

    prev_self = prev_state[self_key]
    curr_self = curr_state[self_key]
    prev_opp = prev_state[opp_key]
    curr_opp = curr_state[opp_key]

    damage_dealt = prev_opp["health"] - curr_opp["health"]
    damage_received = prev_self["health"] - curr_self["health"]

    # base reward: normalized damage delta
    reward = (damage_dealt - damage_received) / MAX_HEALTH * 10.0

    # combo bonus: reward scales with combo count
    combo = curr_self.get("combo_count", 0)
    if combo > 1 and damage_dealt > 0:
        reward += min(combo * 0.2, 2.0)

    # punish reward: reward for attacking during opponent's punish window
    opp_punish_window = prev_opp.get("punish_window", 0)
    if opp_punish_window > 0 and damage_dealt > 0:
        reward += 1.0 + damage_dealt / MAX_HEALTH * 5.0

    # drive efficiency: reward for spending drive on hits (only when actively spending,
    # not when drive decreases due to being hit or blocking)
    # We approximate "active spend" by checking if damage was dealt (attacker context)
    # and drive decreased — this filters out passive drain from being attacked
    prev_self_drive = prev_self.get("drive", 6.0)
    curr_self_drive = curr_self.get("drive", 6.0)
    drive_spent = prev_self_drive - curr_self_drive
    # Only reward drive spending when we dealt damage (i.e., we were the attacker)
    if drive_spent > 0 and damage_dealt > 0 and damage_received == 0:
        reward += drive_spent * 0.1

    # penalize burnout
    if curr_self.get("burnout", False) and not prev_self.get("burnout", False):
        reward -= 2.0

    # round end
    if curr_state["round_over"]:
        if curr_state["winner"] == perspective:
            reward += 10.0
        elif curr_state["winner"] is not None:
            reward -= 10.0

    return reward
