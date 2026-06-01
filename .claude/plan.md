# SF6 Env Bug 修复计划

## 修复范围（按优先级）

### P0 — 核心逻辑错误（必须修复，影响训练正确性）

1. **Drive Gain 双重计算** (`character.py`)
   - `game.py` 调用 `mark_hit_connected()` 后又自己调用 `drive.gain()`
   - 修复：`game.py` 中删除多余的 `drive.gain()` 调用，只保留 `mark_hit_connected()` 内部的

2. **蹲挡逻辑错误** (`character.py` `_handle_movement`)
   - `crouch` 时 `is_blocking = False`，导致蹲挡完全失效
   - 修复：蹲下时保持 `is_blocking` 不变（由方向键决定），或引入 `crouch_blocking` 状态
   - 实际方案：`walk_back` 设 `is_blocking=True`，`crouch` 时如果已经在 `is_blocking` 状态则保持；更简单的方案是：蹲下时 `is_blocking` 由上一帧状态决定，即蹲下不改变 `is_blocking`

3. **Pushbox 不处理角色交叉** (`physics.py`)
   - `overlap` 计算假设 p1 在左，p2 在右；角色交叉后 overlap 为负直接 return
   - 修复：用 `abs(p1.x - p2.x)` 判断是否重叠，并根据实际位置关系决定推力方向

4. **Drive Parry 成功后给错误方硬直** (`character.py` `receive_hit`)
   - 精防成功后给防守方自己 6F 硬直，应该给攻击方
   - 修复：精防成功时不给自己硬直，而是通过返回值或标记让 `game.py` 给攻击方施加硬直
   - 实现方案：`receive_hit` 返回一个 `parry_success: bool`，`game.py` 检测后给攻击方 `stun_frames = DP_SUCCESS_ADVANTAGE`

5. **连击计数器重置时机错误** (`game.py`)
   - 攻击方进入 idle 就重置 combo，应该在对手从 hitstun 恢复时重置
   - 修复：删除 `game.py` 中基于攻击方状态的 combo reset；改为在 `character.py` 的 `_finish_action` 中，当从 hitstun/knockdown 恢复时通知对手重置 combo（或在 game.py 检测对手状态变化）

### P1 — 功能性错误（影响游戏机制正确性）

6. **空中投技永远无法命中** (`collision.py`)
   - `_check_throw` 直接拒绝空中 defender，但空中投技需要空中 defender
   - 修复：检查 move 的 properties 是否含 `"air_throw"`，若是则要求 defender 在空中

7. **DI 护甲无次数限制** (`character.py`)
   - 护甲可以无限吸收攻击
   - 修复：添加 `di_armor_used: bool` 标志，吸收一次后设为 True，后续不再吸收

8. **取消窗口包含 startup 帧** (`character.py`)
   - `in_cancel_window` 从 `startup` 开始，应从第一个 active 帧开始
   - 修复：`in_cancel_window = (_last_active_frame_start <= frame < startup + active + 3)`
   - 简化：用 `_in_active_window(frame, move) or (frame >= startup + active and frame < startup + active + 3)`

9. **落地无硬直** (`character.py` `_finish_action` / `physics.py`)
   - 落地后直接回 idle，应有 4F 落地硬直
   - 修复：在 `PhysicsBody.integrate()` 检测落地时设置标志，`character.py` 检测到落地时进入 4F 的 `landing` 状态

### P1 — 数值错误

10. **Drive Impact 帧数据修正** (`base.py`)
    - active: 2→4，active_frames: [26,29]，on_block: -5→-6

11. **Drive Reversal 帧数据修正** (`base.py`)
    - on_block: -5→-10

### P2 — 奖励函数修复

12. **drive_spent 奖励方向错误** (`reward.py`)
    - 被打导致 drive 减少也会触发奖励
    - 修复：只在主动花费 drive（OD/DI/DR）时奖励，通过检查是否造成伤害且 drive 减少

## 文件修改清单

| 文件 | 修改内容 |
|------|---------|
| `sf6_env/engine/game.py` | 删除多余 drive.gain()；修复 combo reset 时机 |
| `sf6_env/engine/character.py` | 蹲挡逻辑；DI护甲次数；取消窗口；落地硬直；Parry返回值；drive gain |
| `sf6_env/engine/physics.py` | Pushbox 交叉处理；落地检测标志 |
| `sf6_env/engine/collision.py` | 空中投技条件 |
| `sf6_env/engine/base.py` (实为 characters/base.py) | DI/DR 帧数据 |
| `sf6_env/rl/reward.py` | drive_spent 奖励修复 |

## 不在本次修复范围

- Hitstun/Blockstun 基础值重构（需要验证帧数据格式，风险高）
- Target Combo 系统（新功能）
- 空中格挡（新功能）
- 投技位置传送（新功能）
- Drive Gauge 受击后冻结（新功能）
