import pygame
from collections import deque
from sf6_env.engine.game import Game
from sf6_env.characters.mai import MaiData
from sf6_env.render.pygame_renderer import PygameRenderer

# P1: WASD 方向 + UIOJKL 攻击
# P2: 方向键 + 小键盘攻击

P1_DIR = {
    pygame.K_w: "up",
    pygame.K_s: "down",
    pygame.K_a: "back",
    pygame.K_d: "forward",
}
P2_DIR = {
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "back",
    pygame.K_RIGHT: "forward",
}

# 攻击键 -> button 名
P1_ATK_BTN = {
    pygame.K_u: "LP",
    pygame.K_i: "MP",
    pygame.K_o: "HP",
    pygame.K_j: "LK",
    pygame.K_k: "MK",
    pygame.K_l: "HK",
}
P2_ATK_BTN = {
    pygame.K_KP4: "LP",
    pygame.K_KP5: "MP",
    pygame.K_KP6: "HP",
    pygame.K_KP1: "LK",
    pygame.K_KP2: "MK",
    pygame.K_KP3: "HK",
}

# button -> (地面, 蹲下, 跳跃) action_id
BTN_ACTION = {
    "LP": (5,  11, 17),
    "MP": (6,  12, 18),
    "HP": (7,  13, 19),
    "LK": (8,  14, 20),
    "MK": (9,  15, 21),
    "HK": (10, 16, 22),
}

# 指令序列 -> action_id
# 格式：方向序列用 "down"=下, "down-forward"=下前, "forward"=前, "back"=后, "down-back"=下后
# 最后一个元素是按钮
MOTION_TABLE = [
    # 波动拳系 236
    (["down", "down-forward", "forward"], "LP", 23),  # kachousen_L
    (["down", "down-forward", "forward"], "MP", 24),  # kachousen_M
    (["down", "down-forward", "forward"], "HP", 25),  # kachousen_H
    (["down", "down-forward", "forward"], "LK", 29),  # ryuuenbu_L
    (["down", "down-forward", "forward"], "MK", 30),  # ryuuenbu_M
    (["down", "down-forward", "forward"], "HK", 31),  # ryuuenbu_H
    # 竜巻系 214
    (["down", "down-back", "back"], "LK", 32),  # shinobibachi_L
    (["down", "down-back", "back"], "MK", 33),  # shinobibachi_M
    (["down", "down-back", "back"], "HK", 34),  # shinobibachi_H
    # 昇龍系 623
    (["forward", "down", "down-forward"], "LP", 35),  # hishou_ryuuenjin_L
    (["forward", "down", "down-forward"], "MP", 36),  # hishou_ryuuenjin_M
    (["forward", "down", "down-forward"], "HP", 37),  # hishou_ryuuenjin_H
    # 飛燕連脚 (hien_ren_kyaku): 2MK — 蹲下MK
    # 星屑脚 (hoshi_kujaku): 6HK — 前+HK
    (["forward"], "HK", 57),  # hoshi_kujaku
    # 閃骨打 (senkotsu_uchi): 6HP — 前+HP
    (["forward"], "HP", 58),  # senkotsu_uchi
    # OD versions (LP+MP or MK+HK)
    (["down", "down-forward", "forward"], "PP", 41),  # kachousen_OD
    (["down", "down-forward", "forward"], "KK", 42),  # ryuuenbu_OD
    (["forward", "down", "down-forward"], "PP", 43),  # hishou_ryuuenjin_OD
    (["down", "down-back", "back"], "KK", 55),  # shinobibachi_OD
    # Drive Impact / Reversal (PP/KK with no motion)
    ([], "PP", 47),  # drive_impact
    ([], "KK", 48),  # drive_reversal
    # Super Arts (236236)
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "LP", 44),  # SA1
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "MP", 44),
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "HP", 44),
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "LK", 45),  # SA2
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "MK", 45),
    (["down", "down-forward", "forward", "down", "down-forward", "forward"], "HK", 46),  # SA3
]

# 指令缓冲帧数（SF6 约 15 帧宽容）
BUFFER_FRAMES = 15


def get_dir_state(keys, dir_map) -> str:
    """返回当前方向状态字符串。"""
    has_up = any(keys[k] for k, d in dir_map.items() if d == "up")
    has_down = any(keys[k] for k, d in dir_map.items() if d == "down")
    has_fwd = any(keys[k] for k, d in dir_map.items() if d == "forward")
    has_back = any(keys[k] for k, d in dir_map.items() if d == "back")

    if has_down and has_fwd:
        return "down-forward"
    if has_down and has_back:
        return "down-back"
    if has_up and has_fwd:
        return "up-forward"
    if has_up and has_back:
        return "up-back"
    if has_down:
        return "down"
    if has_up:
        return "up"
    if has_fwd:
        return "forward"
    if has_back:
        return "back"
    return "neutral"


def check_motion(dir_buf: deque, btn: str) -> int:
    """检查方向缓冲区是否匹配某个指令，返回 action_id 或 0。"""
    buf_list = list(dir_buf)

    for motion_dirs, motion_btn, action_id in MOTION_TABLE:
        if motion_btn != btn:
            continue
        if not motion_dirs:
            return action_id
        idx = 0
        for required in motion_dirs:
            while idx < len(buf_list) and buf_list[idx] != required:
                idx += 1
            if idx >= len(buf_list):
                break
            idx += 1
        else:
            return action_id
    return 0


class InputReader:
    def __init__(self, dir_map, atk_btn_map):
        self.dir_map = dir_map
        self.atk_btn_map = atk_btn_map
        self.dir_buf: deque = deque(maxlen=BUFFER_FRAMES)
        self.prev_btns: set = set()
        self.prev_dir: str = "neutral"
        self.dash_cooldown: int = 0

    def read(self, keys, airborne: bool = False) -> tuple:
        """返回 (action_id, parry_held, drive_rush_pressed)。"""
        dir_state = get_dir_state(keys, self.dir_map)
        self.dir_buf.append(dir_state)

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        cur_btns = {btn for k, btn in self.atk_btn_map.items() if keys[k]}
        punches = {"LP", "MP", "HP"}
        kicks = {"LK", "MK", "HK"}
        if len(cur_btns & punches) >= 2:
            cur_btns.add("PP")
        if len(cur_btns & kicks) >= 2:
            cur_btns.add("KK")

        just_pressed = cur_btns - self.prev_btns
        self.prev_btns = cur_btns

        # Drive Parry: 按住 MP+MK
        parry_held = "MP" in cur_btns and "MK" in cur_btns

        # Drive Rush: 前+PP 或 前+KK（地面，非精防状态下）
        drive_rush = False
        if not airborne and not parry_held:
            if dir_state == "forward" and ("PP" in just_pressed or "KK" in just_pressed):
                drive_rush = True

        # 投技检测：LP+LK 同时按下（地面）
        if not airborne and "LP" in just_pressed and "LK" in cur_btns:
            if dir_state == "back":
                return 50, parry_held, drive_rush  # back_throw
            return 49, parry_held, drive_rush  # forward_throw
        if not airborne and "LK" in just_pressed and "LP" in cur_btns:
            if dir_state == "back":
                return 50, parry_held, drive_rush
            return 49, parry_held, drive_rush

        # hien_ren_kyaku: 蹲下 MK（2MK）
        if not airborne and "MK" in just_pressed and dir_state == "down":
            return 56, parry_held, drive_rush

        # dash detection: neutral → forward → forward (within 10 frames)
        if self.dash_cooldown == 0 and len(self.dir_buf) >= 3:
            recent = list(self.dir_buf)[-10:]
            if dir_state == "forward" and self.prev_dir == "neutral":
                for i in range(len(recent) - 2, -1, -1):
                    if recent[i] == "forward":
                        self.dash_cooldown = 20
                        self.prev_dir = dir_state
                        return 51, parry_held, drive_rush
                    if recent[i] == "neutral":
                        break
            if dir_state == "back" and self.prev_dir == "neutral":
                for i in range(len(recent) - 2, -1, -1):
                    if recent[i] == "back":
                        self.dash_cooldown = 20
                        self.prev_dir = dir_state
                        return 52, parry_held, drive_rush
                    if recent[i] == "neutral":
                        break

        self.prev_dir = dir_state

        # 精防状态下不处理任何攻击输入
        if not parry_held:
            for btn in just_pressed:
                action = check_motion(self.dir_buf, btn)
                if action:
                    return action, parry_held, drive_rush

            for btn in just_pressed:
                if btn in ("PP", "KK"):
                    continue
                ground, crouch, jump = BTN_ACTION[btn]
                if airborne:
                    return jump, parry_held, drive_rush
                if dir_state == "down":
                    return crouch, parry_held, drive_rush
                if dir_state == "up":
                    return 4, parry_held, drive_rush
                if dir_state == "up-forward":
                    return 53, parry_held, drive_rush
                if dir_state == "up-back":
                    return 54, parry_held, drive_rush
                return ground, parry_held, drive_rush

        # Movement without button press
        if dir_state == "up":
            return 4, parry_held, drive_rush
        if dir_state == "up-forward":
            return 53, parry_held, drive_rush
        if dir_state == "up-back":
            return 54, parry_held, drive_rush
        if dir_state in ("down", "down-forward", "down-back"):
            return 3, parry_held, drive_rush
        if dir_state == "forward":
            return 1, parry_held, drive_rush
        if dir_state == "back":
            return 2, parry_held, drive_rush
        return 0, parry_held, drive_rush


def apply_drive_input(character, parry_held: bool, drive_rush: bool) -> None:
    """根据输入状态更新角色的精防/迸发状态。"""
    if parry_held:
        if not character.parrying:
            character.start_drive_parry()
    else:
        if character.parrying:
            character.stop_drive_parry()

    if drive_rush and not character.drive_rushing:
        # 从精防取消迸发（免费），或直接迸发（消耗 1.5 格）
        from_parry = character.parrying
        character.start_drive_rush(from_parry=from_parry)


def main():
    pygame.init()
    mai_p1 = MaiData()
    mai_p2 = MaiData()
    game = Game(mai_p1, mai_p2)
    renderer = PygameRenderer()

    p1_reader = InputReader(P1_DIR, P1_ATK_BTN)
    p2_reader = InputReader(P2_DIR, P2_ATK_BTN)

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        p1_action, p1_parry, p1_rush = p1_reader.read(keys, game.p1.body.airborne)
        p2_action, p2_parry, p2_rush = p2_reader.read(keys, game.p2.body.airborne)

        apply_drive_input(game.p1, p1_parry, p1_rush)
        apply_drive_input(game.p2, p2_parry, p2_rush)

        round_over, winner = game.step(p1_action, p2_action)
        renderer.render(game)

        if round_over:
            label = f"P{winner + 1}" if winner is not None else "Draw"
            print(f"Round over! Winner: {label}")
            pygame.time.wait(2000)
            game.reset()

        clock.tick(60)

    renderer.close()


if __name__ == "__main__":
    main()
