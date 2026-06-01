# SF6 模拟器 - 开发文档

## 当前进度

帧数据已从 4rays/sf6-move-data (GitHub) + supercombo.gg 双源合并，覆盖全部 25 个角色。

## 已完成的文件

- sf6_env/engine/physics.py - 物理系统
- sf6_env/engine/collision.py - AABB 碰撞检测（支持 active_frames 多段判定、per_hit 分段伤害）
- sf6_env/engine/drive.py - Drive Gauge 系统
- sf6_env/engine/character.py - 角色状态机（invuln_str 解析、drive_gain_block 负值处理）
- sf6_env/engine/game.py - 游戏主循环
- sf6_env/characters/base.py - 帧数据加载基类（注入系统技 Drive Impact/Reversal/Dash）
- sf6_env/characters/mai.py - 不知火舞配置（59个动作，含 OD 技）
- sf6_env/data/characters/ - 25个角色帧数据（JSON，来自 scrape_all_characters.py）
- sf6_env/rl/obs.py - 22维 observation space
- sf6_env/rl/reward.py - reward function
- sf6_env/rl/env.py - gymnasium.Env 实现
- sf6_env/rl/train.py - SB3 PPO 训练函数
- sf6_env/render/pygame_renderer.py - pygame 渲染
- main.py - 人类可玩入口
- train.py - RL 训练入口
- tests/test_collision.py
- tests/test_drive.py
- tests/test_env.py

## 帧数据字段说明

每个 move JSON 包含：
- startup / active / recovery / active_frames（多段判定帧列表）
- damage / chip_damage / per_hit（每段伤害列表）/ hit_count
- on_hit / on_block
- drive_gain_hit（正值，攻击方命中得 Drive）/ drive_gain_block（负值，攻击方被防御失 Drive）
- invuln_str（如 "1-8 Full, 9-39 Air (Upper Body)"）
- properties（special / super / knockdown / throw / projectile / armor / invincible）
- cancel_into（由 mai.py CANCEL_RULES 注入）

## 已知需要检查的问题

1. obs.py 中 action_to_move 反向查找效率低
2. pygame_renderer.py 中 super_gauge 属性名需确认
3. 其余 24 个角色尚未实现 CharacterData 子类（目前只有 Mai）

## Drive 系统参数

- Drive Impact: 消耗 1.0 格，起手 26F，护甲 1-25F
- Drive Parry: 持续消耗 0.03 格/帧
- Drive Rush（直接）: 消耗 1.5 格，冲刺 18F
- Drive Rush（从 Parry）: 消耗 0 格
- Drive Reversal: 消耗 2.0 格，起手 20F 无敌
- Overdrive: 消耗 2.0 格
- Burnout: Drive=0 时触发，180F 后恢复
- Burnout 效果: 无法使用 Drive 技能，被 block +4F blockstun，受 chip damage

## Observation Space（22维）

己方 10 维: x, y, health, drive, super, action_id, frame_pct, airborne, burnout, blocking
对方 10 维: 同上
全局 2 维: distance, timer

## Action Space（49个离散动作）

0: idle
1: walk_forward, 2: walk_back, 3: crouch, 4: jump
5-10: 站立普通技 (5LP/5MP/5HP/5LK/5MK/5HK)
11-16: 蹲下普通技 (2LP/2MP/2HP/2LK/2MK/2HK)
17-22: 跳跃普通技 (jLP/jMP/jHP/jLK/jMK/jHK)
23-25: 花蝶扇 L/M/H (236P)
26-28: 乱れ花蝶扇 L/M/H (214P)
29-31: 龙炎舞 L/M/H (236K)
32-34: 忍蜂 L/M/H (214K)
35-37: 飞翔龙炎陣 L/M/H (623P)
38-40: 燕飞 L/M/H (j214K)
41: 花蝶扇 OD, 42: 龙炎舞 OD, 43: 飞翔龙炎陣 OD
44: SA1, 45: SA2, 46: SA3
47: Drive Impact, 48: Drive Reversal