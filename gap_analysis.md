# SF6 模拟器查漏补缺分析

## 一、空中攻击系统问题

### 1.1 空中攻击判定时机不准确
**问题**：
- 空中攻击的 `active` 帧数过长（jLP=9F, jLK=7F），但没有考虑下落过程
- 跳跃总时长：startup(4) + active(35) + recovery(4) = 43F
- 空中攻击在下落过程中判定框应该随高度变化

**当前状态**：
- 空中攻击可以释放 ✓
- 但判定框位置固定，不随角色 Y 坐标变化 ✗

**修复方案**：
1. 空中攻击的 hitbox 应该使用角色当前 Y 坐标（已实现）
2. 需要验证下落过程中判定框是否正确跟随

### 1.2 空中特殊技缺失
**问题**：
- musasabi (燕飛) 系列：空中 214K，当前有 L/M/H 三个版本
- musasabi_L 缺少 `hit_count` 字段 ✗
- musasabi 的 `on_hit=0` 和 `recovery=0` 不合理（空中技落地应该有硬直）

**修复方案**：
1. 给 musasabi_L 添加 `hit_count: 1`
2. 修正 musasabi 系列的 on_hit 和 recovery 数据

### 1.3 空中超必杀缺失
**问题**：
- SA2_air 存在但未映射到 action_id ✗
- 空中 SA2 应该可以在跳跃中释放

**修复方案**：
1. 在 mai.py 中添加 SA2_air 的 action_id 映射
2. 在 main.py 的 MOTION_TABLE 中添加空中 SA2 指令

---

## 二、Drive 系统缺失功能

### 2.1 Drive Parry（精防）未实现
**当前状态**：
- `drive.py` 中有 `start_drive_parry()` 和 `stop_drive_parry()` 方法 ✓
- 但 `character.py` 中没有调用 ✗
- `main.py` 中没有精防输入映射 ✗

**SF6 精防机制**：
- 按住 MP+MK 进入精防状态
- 持续消耗 Drive（0.03/帧）
- 成功精防后获得 +6F 优势
- 可以从精防取消进 Drive Rush（消耗 0 格）

**修复方案**：
1. 在 `character.py` 中添加 `parrying` 状态
2. 在 `receive_hit()` 中检测精防状态，成功则不受伤
3. 在 `main.py` 中添加 MP+MK 输入映射

### 2.2 Drive Rush（迸发）未实现
**当前状态**：
- `drive.py` 中有 `start_drive_rush()` 方法 ✓
- `drive.rushing` 状态已追踪 ✓
- `collision.py` 中 `attacker_drive_rush` 已传递 ✓
- `character.py` 中 DR 的 +4F hitstun/blockstun 已实现 ✓
- 但没有 DR 的启动逻辑 ✗

**SF6 DR 机制**：
- 方式1：从精防取消（消耗 0 格）
- 方式2：直接冲刺（消耗 1.5 格）
- 效果：+4F hitstun/blockstun

**修复方案**：
1. 在 `character.py` 中添加 DR 启动逻辑
2. 在 `main.py` 中添加 DR 输入映射（PP+前 或 KK+前）

### 2.3 Burnout（斗气耗尽）chip damage 未完全实现
**当前状态**：
- `_apply_blockstun()` 中有 burnout chip damage ✓
- 但只在 block 时生效
- `_apply_hitstun()` 中 burnout 时特殊技伤害减少 25% ✓

**SF6 Burnout 机制**：
- Drive = 0 时进入 Burnout
- 所有被 block 的攻击造成 chip damage
- 特殊技/超必杀的 chip damage = 正常伤害的 25%
- 可被 chip damage KO
- 额外 +4F blockstun
- 约 180F 后自动恢复满 Drive

**当前实现正确** ✓

---

## 三、招式数据问题

### 3.1 musasabi_L 缺少 hit_count
```json
"musasabi_L": {
  "hit_count": 1  // 缺失
}
```

### 3.2 特殊技 hien_ren_kyaku / hoshi_kujaku / senkotsu_uchi 未映射
**问题**：
- 这些招式在 JSON 中存在
- 但在 mai.py 的 ACTION_MAP 中已映射（56, 57, 58）✓
- 在 main.py 的 MOTION_TABLE 中缺失输入指令 ✗

**修复方案**：
1. 在 main.py 中添加这些招式的输入指令

### 3.3 hoshi_kujaku_followup 未映射
**问题**：
- hoshi_kujaku 应该有后续派生技
- 但没有 action_id 映射 ✗

---

## 四、投技系统问题

### 4.1 投技输入未实现
**当前状态**：
- forward_throw / back_throw 在 JSON 中存在 ✓
- 在 mai.py 中已映射（49, 50）✓
- 在 main.py 中没有输入映射 ✗

**SF6 投技输入**：
- LP+LK = forward_throw
- 后+LP+LK = back_throw

**修复方案**：
1. 在 main.py 中添加投技输入检测

### 4.2 投技距离判定
**当前状态**：
- `collision.py` 中 `THROW_RANGE = 80.0` ✓
- `_check_throw()` 中有距离和方向判定 ✓

**当前实现正确** ✓

---

## 五、取消系统问题

### 5.1 普通技取消普通技未实现
**当前状态**：
- `_try_cancel()` 中只允许 special/super 取消 ✓
- 但 SF6 中部分普通技可以取消进其他普通技（target combo）

**SF6 Target Combo**：
- 5LP → 5MP
- 2LP → 2MP
- 等等

**修复方案**：
1. 在帧数据中添加 `cancel_into: ["normals"]`
2. 在 `_try_cancel()` 中实现普通技取消逻辑

### 5.2 空中取消未实现
**当前状态**：
- 空中攻击的 `cancel_into: []` 为空 ✓
- SF6 中空中攻击通常不能取消

**当前实现正确** ✓

---

## 六、其他缺失功能

### 6.1 Counter Hit / Punish Counter 判定
**当前状态**：
- `collision.py` 中 `_get_hit_type()` 已实现 ✓
- Counter Hit: 在 startup 期间被击中 ✓
- Punish Counter: 在 recovery 期间被击中 ✓
- `_apply_hitstun()` 中 CH +2F, PC +4F 已实现 ✓

**当前实现正确** ✓

### 6.2 Combo Scaling
**当前状态**：
- `_apply_hitstun()` 中伤害缩放已实现 ✓
- 100% → 90% → 80% → ... → 20% 最低 ✓

**当前实现正确** ✓

### 6.3 Punish Window 追踪
**当前状态**：
- `character.py` 中 `punish_window` 已追踪 ✓
- `_apply_blockstun()` 中设置 punish_window ✓

**当前实现正确** ✓

---

## 修复优先级

### P0（核心功能缺失）
1. ✅ 空中攻击输入映射（已修复）
2. ❌ Drive Parry 实现
3. ❌ Drive Rush 实现
4. ❌ 投技输入映射

### P1（数据完整性）
5. ❌ musasabi_L 添加 hit_count
6. ❌ 特殊技输入指令补全（hien_ren_kyaku, hoshi_kujaku, senkotsu_uchi）
7. ❌ SA2_air 映射

### P2（进阶功能）
8. ❌ Target Combo 系统
9. ❌ hoshi_kujaku_followup 实现
10. ❌ musasabi 帧数据修正（on_hit, recovery）

---

## 下一步操作

1. 修复 musasabi_L 的 hit_count
2. 实现 Drive Parry 系统
3. 实现 Drive Rush 系统
4. 添加投技输入映射
5. 补全特殊技输入指令
