# 不知火舞连招系统与确反数据

## 确反（Punish）系统

### 确反原理
- **帧优势（Frame Advantage）**：攻击方动作结束时，与防守方解除硬直的帧数差
  - `on_block > 0`：攻击方先动（+帧）
  - `on_block < 0`：防守方先动（-帧，可被确反）
  - `on_block = 0`：双方同时恢复

### 确反分级（基于 -帧数）
| 帧数 | 确反等级 | 可用技能 |
|------|---------|---------|
| -1 ~ -3 | 微劣势 | 无法确反，但失去主动权 |
| -4 ~ -6 | 轻确反 | 5LP(4F), 5LK(4F), 2LP(4F), 2LK(5F) |
| -7 ~ -10 | 中确反 | 5MP(8F), 2MP(6F), 5MK(9F), 2MK(7F) |
| -11 ~ -15 | 重确反 | 5HP(9F), 5HK(14F), 2HP(10F), 2HK(9F) |
| -16+ | 超重确反 | 特殊技、超必杀 |

### 不知火舞技能确反表
| 技能 | on_block | 被确反等级 | 推荐确反技 |
|------|----------|-----------|-----------|
| 5LP | -2 | 微劣势 | 无 |
| 5MP | -3 | 微劣势 | 无 |
| 5HP | -3 | 微劣势 | 无 |
| 5LK | -1 | 微劣势 | 无 |
| 5MK | -4 | 轻确反 | 5LP, 5LK |
| 5HK | -3 | 微劣势 | 无 |
| 2LP | -1 | 微劣势 | 无 |
| 2MP | -3 | 微劣势 | 无 |
| 2HP | -3 | 微劣势 | 无 |
| 2LK | -2 | 微劣势 | 无 |
| 2MK | -6 | 轻确反 | 5LP, 5LK, 2LP, 2LK |
| 2HK | -11 | 重确反 | 5HP, 2HP, 2HK |
| ryuuenbu_L | -4 | 轻确反 | 5LP, 5LK |
| ryuuenbu_M | -6 | 轻确反 | 5LP, 5LK, 2LP, 2LK |
| ryuuenbu_H | -6 | 轻确反 | 5LP, 5LK, 2LP, 2LK |
| shinobibachi_L | -10 | 中确反 | 5MP, 2MP, 5MK, 2MK |
| shinobibachi_M | -12 | 重确反 | 5HP, 2HP, 2HK |
| shinobibachi_H | -13 | 重确反 | 5HP, 2HP, 2HK |
| hishou_ryuuenjin_L | -29 | 超重确反 | SA1, SA2, SA3 |
| hishou_ryuuenjin_M | -28 | 超重确反 | SA1, SA2, SA3 |
| hishou_ryuuenjin_H | -31 | 超重确反 | SA1, SA2, SA3 |
| drive_impact | -6 | 轻确反 | 5LP, 5LK, 2LP, 2LK |
| drive_reversal | -10 | 中确反 | 5MP, 2MP, 5MK, 2MK |

---

## 连招系统（Target Combos）

### 连招取消规则
1. **普通技 → 特殊技**：轻/中攻击可取消进特殊技
2. **普通技 → 超必杀**：所有普通技可取消进超必杀
3. **特殊技 → 超必杀**：所有特殊技可取消进超必杀
4. **取消窗口**：在 active 帧期间或 recovery 前 3 帧内输入

### 不知火舞基础连招

#### 地面连招
```
# 轻确认连招
5LP > 5LP > 5LK > 236LP (kachousen_L)
2LP > 2LP > 2LK > 236LP

# 中距离连招
5MP > 5MK > 236MK (ryuuenbu_M)
2MP > 5MK > 236MK

# 重攻击连招
5HP > 236HP (kachousen_H)
2HP > 623HP (hishou_ryuuenjin_H)

# 角落连招
5MP > 5MK > 236MK > SA1 (超必杀取消)
```

#### 跳跃连招
```
jHP > 5HP > 236HP
jMK > 2MK > 236MK
jHK > 5HK > SA3
```

#### Drive Rush 连招
```
5LP > 5LP > DR > 5MP > 5MK > 236MK > SA1
2MP > DR > 5HP > 623HP
```

#### 最大伤害连招
```
# 角落满资源
jHP > 5HP > 236HP > SA3 (约 6000 伤害)

# 中场 Drive Rush
5MP > DR > 5HP > 236HP > SA2 (约 5500 伤害)

# Burnout 惩罚
Drive Impact (crumple) > 5HP > 623HP > SA1 (约 4500 伤害)
```

---

## 实现需求

### 1. 连招取消系统
- 在 `Character._process_action()` 中检测 `cancel_into` 字段
- 允许在 active 帧或 recovery 前 3 帧取消
- 取消后立即切换到新动作，重置 `action_frame`

### 2. 确反 AI 逻辑
- 在 `rl/reward.py` 中添加确反奖励
- 检测对手技能 on_block < 0 时，使用对应帧数的确反技能
- 奖励公式：`punish_reward = abs(on_block) * 0.1 * (damage_dealt / 1000)`

### 3. 连招训练奖励
- 连续命中奖励：`combo_bonus = hit_count * 0.5`
- 取消成功奖励：`cancel_bonus = 1.0`
- 最大伤害奖励：`max_damage_bonus = total_damage / 100`

---

## 待验证数据
⚠️ 以下数据需要在游戏中实测确认：
- [ ] 所有技能的 cancel_into 列表是否完整
- [ ] 取消窗口是否为 active 帧 + recovery 前 3 帧
- [ ] Drive Rush 后的帧优势加成（+4F）
- [ ] Burnout 状态下的 blockstun 加成（+4F）
- [ ] 投技的确反窗口（5F startup）
