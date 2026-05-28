# SF6 模拟器 - 开发文档

## 当前进度（IDE 重启前状态）

所有代码文件已创建完毕，等待 IDE 重启后运行测试。

## 已完成的文件

- sf6_env/engine/physics.py - 物理系统
- sf6_env/engine/collision.py - AABB 碰撞检测
- sf6_env/engine/drive.py - Drive Gauge 系统
- sf6_env/engine/character.py - 角色状态机
- sf6_env/engine/game.py - 游戏主循环
- sf6_env/characters/base.py - 帧数据加载基类
- sf6_env/characters/mai.py - 不知火舞配置（49个动作）
- sf6_env/data/mai_frames.json - 48个动作帧数据
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

## IDE 重启后需要执行的操作

1. 安装依赖：pip install -r requirements.txt
2. 运行测试：python -m pytest tests/ -v
3. 修复测试中发现的 bug
4. 运行人类可玩模式：python main.py
5. 对照游戏内帧数据核对 mai_frames.json
6. 启动训练：python train.py

## 已知需要检查的问题

1. character.py 中飞道具生成：_start_attack 需要对 projectile 属性的动作调用 spawn_projectile()
2. obs.py 中 action_to_move 反向查找效率低
3. pygame_renderer.py 中 super_gauge 属性名需确认
4. mai_frames.json 中 crouch/jump/hitstun 等基础状态缺少完整字段

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