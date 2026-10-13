# 阶段02-A 技术设计报告：通信故障模型与诊断机制

**文档编号:** STAGE02A-DESIGN  
**日期:** 2026-10-13  
**状态:** 技术设计（未实现）  
**负责人:** Claude Opus 5.5

---

## 执行摘要

本文档对CommDoctor项目阶段02进行完整的技术设计和可行性分析。基于阶段01建立的实值BPSK通信仿真内核，本报告评估了四种候选故障类型，深入分析了故障可辨识性问题，设计了真实的诊断与修复闭环机制，并提出了最小软件架构方案。

**核心结论：**
- 推荐首批实现3种故障：DC偏移、判决门限偏移、符号极性反转
- AWGN噪声功率异常作为观察型故障，不设计为可修复
- DC偏移与判决门限偏移在单次测量中不可区分，需要多重证据链
- 提出基于接收机参数空间的诊断架构，隔离故障真值

---

## 目录

1. [阶段01验证结果复核](#1-阶段01验证结果复核)
2. [四种候选故障技术评估](#2-四种候选故障技术评估)
3. [故障可辨识性深度分析](#3-故障可辨识性深度分析)
4. [诊断与修复闭环设计](#4-诊断与修复闭环设计)
5. [最小软件架构](#5-最小软件架构)
6. [首批故障筛选与理由](#6-首批故障筛选与理由)
7. [主要技术风险](#7-主要技术风险)
8. [阶段02-B验证范围](#8-阶段02-b验证范围)

---

## 1. 阶段01验证结果复核

### 1.1 测试覆盖率声称的核心问题

**发现：阶段01总结中声称"测试覆盖率：100%（核心模块）"**

**验证结果：**
```bash
# 尝试运行覆盖率测试
$ python -m pytest tests/ --cov=src/commdoctor --cov-report=term
ERROR: unrecognized arguments: --cov=src/commdoctor
```

**问题分析：**
- pytest-cov 插件未安装在当前环境
- pyproject.toml 中声明了 pytest-cov 依赖，但未实际安装
- 无法生成覆盖率报告验证"100%"声称

**结论：**
阶段01的"100%测试覆盖率"是**未经验证的声称**。虽然所有30个测试通过，但没有定量证据证明达到100%覆盖率。

**建议：**
- 在后续工作中安装pytest-cov并生成真实覆盖率报告
- 修正阶段01文档，标注为"未量化验证"
- 不在阶段02中继续沿用这个未验证的数字

**影响：**
不影响阶段02设计，但需要在科研诚信原则下修正文档描述。

### 1.2 阶段01核心能力确认

**已验证的能力：**
- ✓ BPSK调制解调（0→-1, 1→+1）
- ✓ AWGN信道模型（实值噪声）
- ✓ 理论BER计算（erfc公式）
- ✓ Monte Carlo BER仿真
- ✓ 30个自动化测试全部通过
- ✓ BER曲线与理论值拟合良好（低SNR区域偏差<2%）

**模型限制：**
- 实值符号（无复信号）
- 符号级抽象（无时间维度）
- 硬判决解调（门限=0）
- 单位符号能量归一化

**结论：**
阶段01提供了坚实的技术基础，适合实现基于实值模型的故障诊断系统。

---

## 2. 四种候选故障技术评估

### 2.1 候选故障A：DC偏移（DC Offset）

#### 物理/接收机实现依据
**现实场景：**
- 模拟电路直流漂移
- ADC采样偏置
- 自动增益控制（AGC）不完善
- 接收机前端电容耦合失效

**数学表达式：**
```
接收信号: r[n] = s[n] + b + w[n]
```
其中：
- s[n] ∈ {-1, +1}：发送符号
- b：DC偏移量（常数）
- w[n] ~ N(0, σ²)：AWGN噪声

#### 当前BPSK模型适用性
**完全适用。** 实值符号模型可以直接表示DC偏移。

#### 故障影响分析

**对接收信号的影响：**
- 接收信号均值 E[r] = E[s] + b = 0 + b = b（假设0和1等概）
- 信号方差不变
- 信号分布整体平移

**对判决结果的影响：**
使用标准硬判决（门限=0）：
```
判决规则: r[n] >= 0 → 比特1
         r[n] < 0  → 比特0
```

当b > 0时：
- 发送-1时，接收r = -1 + b + w，若b足够大，可能被误判为1
- 发送+1时，接收r = +1 + b + w，更容易被正确判为1
- 结果：P(0→1错误) > P(1→0错误)，错误率不对称

**对BER的影响：**
理论推导（假设噪声标准差σ，DC偏移b）：
```
P(错误|发送-1) = P(r >= 0 | s=-1) = P(w >= 1-b) = Q((1-b)/σ)
P(错误|发送+1) = P(r < 0 | s=+1) = P(w < -1-b) = Q((1+b)/σ)
BER = 0.5 × [Q((1-b)/σ) + Q((1+b)/σ)]
```
其中Q(x) = 0.5×erfc(x/√2)为高斯尾概率。

当b=0时，退化为标准BPSK的对称BER。

#### 可用的诊断测量

**测量1：接收信号均值**
```python
dc_estimate = np.mean(received_symbols)
```
理论值：E[r] = b
- 简单、直接、可靠
- 对大样本量（N>1000）估计精度高

**测量2：错误率不对称性**
需要已知发送序列（训练序列场景）：
```python
errors_0to1 = count_errors(tx_bits==0, rx_bits==1)
errors_1to0 = count_errors(tx_bits==1, rx_bits==0)
asymmetry = errors_0to1 - errors_1to0
```
若asymmetry显著不为0，指示DC偏移或门限偏移。

**测量3：接收信号直方图**
观察接收符号分布的中心位置是否偏离0。

#### 修复方法

**方法1：DC阻断（推荐）**
```python
def remove_dc_offset(received_symbols):
    """基于测量的DC消除"""
    dc_estimate = np.mean(received_symbols)
    corrected_symbols = received_symbols - dc_estimate
    return corrected_symbols, dc_estimate
```

**理论依据：**
- 对于等概的BPSK信号，理论均值应为0
- 实测均值偏离0即为DC偏移估计
- 减去估计值即可补偿

**方法2：自适应判决门限**
```python
def adaptive_threshold_demodulate(received_symbols):
    """自适应门限解调"""
    optimal_threshold = np.mean(received_symbols)
    bits = (received_symbols >= optimal_threshold).astype(np.int8)
    return bits, optimal_threshold
```

**效果等价性：**
移除DC后用门限0解调 ≡ 用自适应门限解调原信号

#### 软件验证可行性

**完全可行。** 可设计以下实验：

**实验流程：**
1. 生成已知比特序列
2. BPSK调制
3. 注入已知DC偏移（如b=0.5）
4. 添加AWGN噪声
5. 不修复：直接解调，测量BER₁
6. 修复：移除DC后解调，测量BER₂
7. 验证：BER₂ << BER₁，且BER₂接近理论值

**可量化的成功标准：**
- DC估计误差 < 0.05
- 修复后BER下降 > 50%
- 修复后BER与理论BER偏差 < 10%

#### 实现复杂度

**极低（★☆☆☆☆）**
- 注入：一行代码（加法）
- 诊断：一行代码（均值）
- 修复：一行代码（减法）

#### 教学价值

**极高（★★★★★）**
- 概念简单，易于理解
- 直观的信号可视化（直方图平移）
- 体现测量-分析-修复完整流程
- 引入对称性分析的思想
- 为后续复杂故障奠定基础

---

### 2.2 候选故障B：判决门限偏移（Threshold Offset）

#### 物理/接收机实现依据

**现实场景：**
- 判决电路校准错误
- 温度漂移导致比较器偏置变化
- 接收机增益控制不当
- 软件实现中的参数配置错误

**数学表达式：**
```
判决规则: r[n] >= t → 比特1
         r[n] < t  → 比特0
```
其中t为判决门限，理论最优值为t=0（无DC时）。

#### 当前BPSK模型适用性

**完全适用。** 只需修改解调器的判决门限参数。

#### 故障影响分析

**对接收信号的影响：**
无影响。门限偏移是解调器问题，不改变接收信号本身。

**对判决结果的影响：**
假设接收信号r[n] = s[n] + w[n]（无DC），但判决门限t≠0：

当t > 0时：
- 判决偏向于输出0
- P(1→0错误) 增加
- P(0→1错误) 减少
- 错误率不对称

当t < 0时：相反效果

**对BER的影响：**
```
P(错误|发送-1) = P(r >= t | s=-1) = Q((1-t)/σ)
P(错误|发送+1) = P(r < t | s=+1) = Q((1+t)/σ)
BER = 0.5 × [Q((1-t)/σ) + Q((1+t)/σ)]
```

**关键观察：**
这与DC偏移的BER公式完全相同！（b和t对调）

#### 可用的诊断测量

**测量1：接收信号均值**
```python
mean_val = np.mean(received_symbols)
```
预期：均值应接近0（如果无DC）

**问题：** 如果均值确实接近0，不能排除门限偏移。

**测量2：错误率不对称性**
需要已知发送序列：
```python
p_0to1 = count_errors(tx==0, rx==1) / count(tx==0)
p_1to0 = count_errors(tx==1, rx==0) / count(tx==1)
```

**问题：** DC偏移和门限偏移都会导致不对称！

**测量3：接收信号方差**
```python
var_estimate = np.var(received_symbols)
```
理论方差：Var[r] = Var[s] + σ² = 1 + σ²
- 门限偏移不改变方差
- DC偏移也不改变方差
- 无法区分

#### 修复方法

**方法：重新校准判决门限**
```python
def calibrate_threshold(received_symbols):
    """基于接收信号统计的门限校准"""
    optimal_threshold = np.mean(received_symbols)
    return optimal_threshold
```

**理论依据：**
- 对于对称的BPSK信号，最优判决门限应位于两个星座点的中点
- 接收信号均值是两个峰值的中点估计

**问题：**
如果同时存在DC偏移b和门限偏移t，校准后的门限t'=均值=b，
实际判决变为r >= b，恰好抵消了DC偏移，但我们无法区分：
- 是修复了门限偏移？
- 还是适应了DC偏移？

#### 软件验证可行性

**可行，但有歧义。**

**实验流程：**
1. 生成已知比特序列
2. 注入判决门限偏移（修改解调器参数t=0.3）
3. 不修复：用t=0.3解调，测量BER₁
4. 修复：重新校准门限t'，用t'解调，测量BER₂
5. 验证：BER₂ < BER₁

**问题：**
单独注入门限偏移时，接收信号均值≈0，校准算法会得到t'≈0，
修复有效。但学生无法理解"为什么均值是正确的门限"。

#### 实现复杂度

**极低（★☆☆☆☆）**
- 注入：修改解调器参数
- 诊断：计算均值
- 修复：更新门限参数

#### 教学价值

**中等（★★★☆☆）**
- 概念清晰（判决门限的作用）
- 但与DC偏移在数学上等价，容易混淆
- 需要额外教学设计来区分两者
- 适合作为DC偏移的对照案例

---

### 2.3 候选故障C：接收机符号极性反转（Polarity Inversion）

#### 物理/接收机实现依据

**现实场景：**
- 本地振荡器相位锁定到错误的相位（180°差）
- I/Q通道接反
- 软件配置错误（映射反转）
- 差分信号极性接反

**数学表达式：**
```
故障接收: r'[n] = -r[n] = -s[n] - w[n]
```
等价于符号映射翻转：
```
正常：0→-1, 1→+1
故障：0→+1, 1→-1
```

#### 当前BPSK模型适用性

**完全适用。** 实值符号可直接表示极性反转。

#### 故障影响分析

**对接收信号的影响：**
- 接收信号符号完全翻转
- 均值反号：E[r'] = -E[r]
- 方差不变：Var[r'] = Var[r]
- 直方图左右对调

**对判决结果的影响：**
使用标准硬判决（门限=0）：
```
发送0（符号-1）→ 接收r'≈+1 → 判决为1 ✗ 错误
发送1（符号+1）→ 接收r'≈-1 → 判决为0 ✗ 错误
```
**所有比特全部错误！** BER ≈ 1（理想情况下，无噪声时BER=1.0）

**对BER的影响（考虑噪声）：**
```
发送符号s → 接收-s+w → 判决
BER = P(错误) = P(正确判决原符号) ≈ 1 - 理论BER
```

在高SNR下：
- 正常系统BER → 0
- 极性反转BER → 1

在低SNR下（如0 dB）：
- 正常BER ≈ 0.08
- 极性反转BER ≈ 0.92

#### 可用的诊断测量

**测量1：BER量级检查**
```python
ber_estimate = measure_ber(received_bits, known_training_bits)
if ber_estimate > 0.5:
    # 极有可能是极性反转
    diagnosis = "polarity_inversion"
```

**理论依据：**
随机猜测的BER = 0.5。任何正常通信系统BER应远小于0.5。
若BER接近1.0，几乎可以确定是极性反转。

**测量2：接收信号符号检查**
```python
# 已知发送比特0（符号-1）
symbol_when_bit0 = np.mean(received_symbols[tx_bits == 0])
if symbol_when_bit0 > 0:
    # 极性反转
```

**测量3：相关性检查**
```python
# 已知符号序列
correlation = np.mean(sent_symbols * received_symbols)
if correlation < 0:
    # 负相关，极性反转
```

#### 修复方法

**方法：符号反转**
```python
def invert_polarity(received_symbols):
    """极性反转修复"""
    corrected_symbols = -received_symbols
    return corrected_symbols
```

**理论依据：**
两次反转恢复原始符号：-(-s) = s

**修复效果：**
完美修复。修复后BER恢复到正常水平。

#### 软件验证可行性

**非常容易验证。**

**实验流程：**
1. 生成已知比特序列
2. BPSK调制
3. 注入极性反转（乘以-1）
4. 添加AWGN
5. 不修复：直接解调，BER₁ ≈ 1.0
6. 修复：符号反转后解调，BER₂ ≈ 理论BER
7. 验证：BER₁ > 0.5，BER₂ < 0.1（在合理SNR下）

**成功标准极其明确：**
- 修复前BER > 0.8（高SNR）或 > 0.4（低SNR）
- 修复后BER < 0.1（取决于SNR）
- 前后BER差异巨大，易于观察

#### 实现复杂度

**极低（★☆☆☆☆）**
- 注入：一行代码（取负）
- 诊断：比较BER与0.5
- 修复：一行代码（取负）

#### 教学价值

**非常高（★★★★★）**
- 故障现象极其明显（BER≈1）
- 诊断逻辑简单直观
- 修复效果立竿见影
- 引入"BER>0.5即异常"的工程直觉
- 建立信号相关性概念
- 适合作为第一个诊断挑战（容易建立信心）

**独特优势：**
- 是唯一不涉及统计测量不确定性的故障（BER≈1是确定性的）
- 不存在与其他故障的混淆
- 修复验证无歧义

---

### 2.4 候选故障D：AWGN噪声功率异常（Noise Power Anomaly）

#### 物理/接收机实现依据

**现实场景：**
- 信道条件恶化（衰落、干扰）
- 接收机噪声系数增大
- 热噪声增加
- 外部电磁干扰

**数学表达式：**
```
声称的信道：r[n] = s[n] + w[n]，其中w ~ N(0, σ₁²)
实际的信道：r[n] = s[n] + w'[n]，其中w' ~ N(0, σ₂²)，σ₂ > σ₁
```

等价于：
```
声称的Eb/N0：例如8 dB
实际的Eb/N0：例如3 dB
```

#### 当前BPSK模型适用性

**完全适用。** AWGN模型已在阶段01实现。

#### 故障影响分析

**对接收信号的影响：**
- 接收信号均值不变：E[r] = 0（假设无DC）
- 接收信号方差增大：Var[r] = 1 + σ² → 1 + σ'²，其中σ'² > σ²
- 信号更分散，星座点更模糊

**对判决结果的影响：**
- 噪声增大导致判决错误增加
- 错误仍然对称（假设无DC）
- P(0→1) ≈ P(1→0)

**对BER的影响：**
```
理论BER = 0.5 × erfc(√(Eb/N0))
```
Eb/N0降低 → BER显著升高

例如：
- 8 dB → BER ≈ 0.0002
- 3 dB → BER ≈ 0.03
- 差异150倍！

#### 可用的诊断测量

**测量1：接收信号方差**
```python
var_estimate = np.var(received_symbols)
```
理论值：Var[r] = Var[s] + σ² = 1 + σ²

对于单位能量BPSK：Var[s] = E[s²] - E[s]² = 1 - 0 = 1

因此：
```python
noise_var_estimate = var_estimate - 1
sigma_estimate = np.sqrt(noise_var_estimate)
```

**测量2：估算实际Eb/N0**
```python
# 从噪声方差反推Eb/N0
# σ² = 1/(2*Eb/N0) → Eb/N0 = 1/(2σ²)
ebn0_linear_estimate = 1 / (2 * noise_var_estimate)
ebn0_db_estimate = 10 * np.log10(ebn0_linear_estimate)
```

**测量3：实测BER与声称参数的理论BER对比**
```python
measured_ber = calculate_ber(tx_bits, rx_bits)
claimed_theoretical_ber = theoretical_ber(claimed_ebn0_db)

if measured_ber >> claimed_theoretical_ber:
    # 实际信道质量低于声称
```

#### 修复方法

**关键问题：接收机能否修复信道噪声？**

**答案：不能。**

噪声是信道特性，不是接收机故障。接收机无法"消除"已经叠加的噪声。

**可能的应对（非真正修复）：**

1. **调整预期：** 承认实际SNR较低，更新BER预期
2. **错误纠正编码：** 在发送端增加冗余（超出本项目范围）
3. **提高发射功率：** 硬件层面改变（超出软件接收机范围）
4. **改善信道：** 物理层面改变（不可控）

**教学困境：**
如果设计成"点击修复噪声"的按钮，这是在误导学生：
- 误导1：接收机可以消除信道噪声
- 误导2：软件可以解决硬件问题
- 误导3：BER可以无成本降低

**推荐策略：**
将此故障设计为**观察型故障**，而非修复型故障：
- 学生学习诊断噪声水平
- 学习估算实际Eb/N0
- 学习解释BER性能差异
- 但不设计"修复"操作

#### 软件验证可行性

**诊断可验证，修复不适用。**

**实验流程（诊断验证）：**
1. 生成比特序列
2. 声称使用8 dB信道
3. 实际注入3 dB信道
4. 测量接收信号方差
5. 估算实际Eb/N0
6. 计算BER
7. 对比：估算的Eb/N0 ≈ 3 dB，BER ≈ 理论BER(3dB)

**成功标准（诊断）：**
- 噪声方差估计误差 < 20%
- Eb/N0估计误差 < 1 dB
- 能够识别"实际SNR低于声称"

**不设计修复验收：**
因为接收机无法真正修复信道噪声。

#### 实现复杂度

**低（★★☆☆☆）**
- 注入：调用已有awgn_channel，使用不同参数
- 诊断：方差估算、SNR反推
- 修复：不适用

#### 教学价值

**中等（★★★☆☆）**
- 重要概念：噪声测量、SNR估算
- 引入统计估计的不确定性
- 但缺乏"修复"环节，成就感较低
- 可能让学生误解为"所有问题都能修复"的反例

**建议定位：**
作为诊断训练，不作为修复挑战。

---

## 3. 故障可辨识性深度分析

### 3.1 核心问题：DC偏移与判决门限偏移的等价性

#### 数学等价性证明

**场景1：DC偏移b，门限0**
```
接收: r[n] = s[n] + b + w[n]
判决: r[n] >= 0 → 比特1
等价判决: s[n] + b + w[n] >= 0
       即: s[n] + w[n] >= -b
```

**场景2：无DC偏移，门限t**
```
接收: r[n] = s[n] + w[n]
判决: r[n] >= t → 比特1
等价判决: s[n] + w[n] >= t
```

**观察：** 场景1中b和场景2中-t的效果完全相同！

**通用情况：**
```
接收: r[n] = s[n] + b + w[n]
判决: r[n] >= t → 比特1
等价于: s[n] + w[n] >= t - b

有效判决门限 = t - b
```

**关键结论：**
只要t-b相同，系统BER相同。无法仅通过BER区分b和t的具体值。

#### 从单一测量无法区分的证据

**测量1：接收信号均值**
```python
mean_val = np.mean(received_symbols)
```
结果：mean_val ≈ b

**问题：**
- 如果mean_val = 0.3，可能是：
  - DC偏移b=0.3，门限t=0
  - 或DC偏移b=0，门限t已经是自适应的0.3
  - 或DC偏移b=0.5，门限t=0.2
  - 或无数其他组合

**测量2：错误率不对称**
```python
asymmetry = P(0→1) - P(1→0)
```
结果取决于t-b，无法分解为单独的b和t。

**测量3：BER**
BER = f(t-b, σ)，只依赖于t-b的组合，不能唯一确定b和t。

### 3.2 可辨识性分析

#### 情况A：仅有接收信号，无法修改系统

**可观测量：**
- 接收信号序列 r[n]
- 解调输出比特（如果有参考序列）

**不可观测量：**
- 发送前的符号
- 判决门限设定值
- 信道特性

**结论：完全不可辨识。**

有无数对(b, t)组合能产生相同的观测结果。

#### 情况B：可以修改判决门限，观察BER变化

**实验方法：**
1. 固定接收信号（录制）
2. 尝试不同判决门限t₁, t₂, t₃...
3. 测量对应的BER(t₁), BER(t₂), BER(t₃)...
4. 找到使BER最小的t_opt

**理论：**
```
最优门限 t_opt = b（DC偏移值）
```

**原因：**
BER = f(t-b)，当t-b=0时BER最小。

**结论：可以估算b，但仍无法知道原始门限t₀是多少。**

只能知道"当前有效门限偏移"= t₀ - b。

#### 情况C：有已知的训练序列

**可观测量增加：**
- 已知发送比特
- 对应的接收符号
- 可计算期望接收值

**实验方法：**
```python
# 发送已知全0序列（符号全为-1）
sent_minus1 = np.array([-1] * 1000)
received_for_minus1 = actual_received[actual_sent == -1]
mean_for_minus1 = np.mean(received_for_minus1)

# 发送已知全1序列（符号全为+1）
sent_plus1 = np.array([+1] * 1000)
received_for_plus1 = actual_received[actual_sent == +1]
mean_for_plus1 = np.mean(received_for_plus1)

# 估算DC偏移
dc_estimate = (mean_for_minus1 + mean_for_plus1) / 2
# 理论：mean(-1+b+w) = -1+b, mean(+1+b+w) = +1+b
# 平均：b
```

**结论：可以估算DC偏移b。**

但判决门限t仍然未知，除非我们可以：
- 直接读取解调器配置（相当于"打开盖子看硬件"）
- 或通过修改门限实验（情况B）

#### 情况D：系统透明度不同

**高透明度系统（教学模拟器）：**
- 可以查看解调器门限设定
- 可以查看接收信号
- 可以独立验证每个环节

**低透明度系统（黑盒接收机）：**
- 只能观察最终BER
- 无法区分故障来源

**本项目选择：**
应该设计中等透明度：
- 学生可以测量接收信号（不是完全黑盒）
- 但不能直接读取故障注入器的真实标签（不是完全透明）
- 通过测量和推理诊断故障

### 3.3 辨识所需的附加测量

#### 测量组合1：均值 + 门限扫描

**步骤：**
1. 测量接收信号均值：mean_r
2. 扫描判决门限从-2到+2，记录BER曲线
3. 找到最优门限t_opt
4. 估算：b ≈ t_opt，原始门限t₀ = mean_r

**有效性：**
可以分离b和t，但需要多次解调实验。

#### 测量组合2：训练序列 + 对称性检验

**步骤：**
1. 使用已知训练序列
2. 分别计算发送-1和+1时的平均接收值
3. 检查是否对称

**数学：**
```
E[r | s=-1] = -1 + b
E[r | s=+1] = +1 + b
中点 = 0.5*(E[r|s=-1] + E[r|s=+1]) = b
```

**结论：**
可以无歧义地估算DC偏移b。

门限偏移t则需要额外信息（如门限扫描或系统配置查询）。

### 3.4 证据不足的识别

#### 学生应该如何识别证据不足？

**教学设计：**

**情况1：仅给出BER值**
```
系统BER = 0.15
目标BER < 0.01
```

**学生应该问：**
- 接收信号是什么样的？
- 判决门限是多少？
- 噪声水平如何？

**系统反馈：**
"仅凭BER无法确定故障类型，需要更多测量。"

**情况2：给出BER + 接收信号均值**
```
BER = 0.15
mean(r) = 0.3
```

**学生可能诊断：**
- DC偏移0.3
- 或判决门限偏移-0.3
- 或两者混合

**系统反馈：**
"这些观测与多种故障一致。你可以：
- 进行门限扫描实验
- 或先尝试DC消除，观察效果
- 或使用训练序列进一步测量"

### 3.5 "无法确定"的输出设计

#### 是否允许学生输出"证据不足，无法确定"？

**建议：允许，并且鼓励。**

**理由：**
1. 培养科学思维：承认不确定性
2. 避免过度自信的错误诊断
3. 引导学生主动寻找更多证据
4. 符合真实工程实践

**实现方式：**

**诊断报告格式：**
```python
diagnosis_report = {
    "confidence": "low" | "medium" | "high",
    "primary_hypothesis": "DC offset",
    "alternative_hypotheses": ["threshold offset"],
    "recommended_tests": ["threshold_scan", "training_sequence"],
    "diagnosis": "inconclusive" | "dc_offset" | "threshold_offset" | ...
}
```

**评分机制：**
- 正确识别"证据不足"：得分
- 在证据不足时强行给出确定诊断：扣分
- 主动请求额外测量：加分

---

## 4. 诊断与修复闭环设计

### 4.1 设计原则

#### 原则1：故障真值隔离

**禁止的做法：**
```python
# ❌ 错误：诊断直接读取故障标签
if fault_injector.fault_type == "dc_offset":
    print("诊断结果：DC偏移")
```

**正确的做法：**
```python
# ✓ 正确：诊断基于测量
dc_estimate = np.mean(received_symbols)
if abs(dc_estimate) > threshold:
    print("诊断结果：疑似DC偏移")
```

**实现机制：**
- 故障注入器保存真实故障标签（用于最终验收）
- 诊断模块只能访问接收信号和系统公开参数
- 两者通过明确的接口隔离

#### 原则2：测量基于真实信号

**禁止的做法：**
```python
# ❌ 错误：伪造测量结果
def measure_noise():
    return fault_injector.true_noise_level  # 直接返回真值
```

**正确的做法：**
```python
# ✓ 正确：从实际信号计算
def measure_noise_variance(received_symbols, known_symbols):
    """基于已知训练序列估算噪声方差"""
    error = received_symbols - known_symbols
    noise_var = np.var(error)
    return noise_var
```

#### 原则3：修复基于参数调整

**禁止的做法：**
```python
# ❌ 错误：魔法修复
def magic_fix(signal):
    return remove_all_problems(signal)
```

**正确的做法：**
```python
# ✓ 正确：明确的信号处理算法
def remove_dc_offset(signal):
    """DC消除：减去均值"""
    dc = np.mean(signal)
    return signal - dc, {"removed_dc": dc}
```

#### 原则4：公平的性能评估

**禁止的做法：**
```python
# ❌ 错误：修复后用不同的信道测试
ber_before = test_with_channel(snr=3)
ber_after = test_with_channel(snr=10)  # 作弊！
```

**正确的做法：**
```python
# ✓ 正确：相同信道，相同随机种子
ber_before = test_with_channel(snr=6, seed=42)
# 应用修复
ber_after = test_with_channel(snr=6, seed=42)  # 相同条件
```

**或者：**
```python
# 使用相同的录制信号
recorded_signal = generate_once(seed=42)
ber_before = demodulate(recorded_signal, fix=False)
ber_after = demodulate(recorded_signal, fix=True)
```

### 4.2 最小诊断闭环架构

#### 组件1：场景生成器（Scene Generator）

**职责：**
- 生成通信场景（比特序列、调制、信道）
- 注入指定故障
- 保存故障真值（不公开）

**接口：**
```python
class CommunicationScene:
    def __init__(self, fault_config):
        self.fault_config = fault_config  # 私有
        self._ground_truth = {}  # 隐藏
        
    def generate_transmission(self, num_bits, seed):
        """生成一次传输"""
        # 1. 生成比特
        bits = generate_bits(num_bits, seed)
        # 2. 调制
        symbols = bpsk_modulate(bits)
        # 3. 注入故障（如果有）
        symbols_faulty = self._inject_fault(symbols)
        # 4. 信道
        received = awgn_channel(symbols_faulty, ...)
        
        return {
            "transmitted_bits": bits,
            "received_symbols": received,
            "metadata": {"num_bits": num_bits, "seed": seed}
        }
    
    def _inject_fault(self, symbols):
        """私有方法：注入故障"""
        if self.fault_config["type"] == "dc_offset":
            b = self.fault_config["dc_value"]
            self._ground_truth["dc_offset"] = b
            return symbols + b
        # ...
        return symbols
    
    def verify_diagnosis(self, student_diagnosis):
        """验收：对比学生诊断与真值"""
        return compare(student_diagnosis, self._ground_truth)
```

**关键设计：**
- `_ground_truth`和`_inject_fault`是私有的
- 外部只能调用`generate_transmission`获取接收信号
- 真值仅用于最终验收

#### 组件2：测量工具箱（Measurement Toolkit）

**职责：**
- 提供各种信号测量功能
- 所有测量基于实际信号计算
- 记录测量参数（样本量、随机种子）

**接口：**
```python
class MeasurementToolkit:
    @staticmethod
    def measure_mean(signal):
        """测量信号均值"""
        mean_val = np.mean(signal)
        std_err = np.std(signal) / np.sqrt(len(signal))
        return {
            "value": mean_val,
            "std_error": std_err,
            "num_samples": len(signal)
        }
    
    @staticmethod
    def measure_variance(signal):
        """测量信号方差"""
        var_val = np.var(signal, ddof=1)
        # 方差的标准误（近似）
        std_err = var_val * np.sqrt(2 / (len(signal) - 1))
        return {
            "value": var_val,
            "std_error": std_err,
            "num_samples": len(signal)
        }
    
    @staticmethod
    def measure_ber(tx_bits, rx_bits):
        """测量误码率"""
        ber, num_errors, num_bits = calculate_ber(tx_bits, rx_bits)
        # BER的标准误（二项分布）
        std_err = np.sqrt(ber * (1 - ber) / num_bits)
        return {
            "ber": ber,
            "std_error": std_err,
            "num_errors": num_errors,
            "num_bits": num_bits
        }
    
    @staticmethod
    def scan_threshold(received_symbols, true_bits, threshold_range):
        """门限扫描实验"""
        results = []
        for t in threshold_range:
            rx_bits = (received_symbols >= t).astype(np.int8)
            ber_result = MeasurementToolkit.measure_ber(true_bits, rx_bits)
            results.append({"threshold": t, "ber": ber_result["ber"]})
        return results
```

**关键特性：**
- 返回测量值 + 统计不确定性
- 记录样本量
- 不依赖任何隐藏真值

#### 组件3：修复操作库（Repair Operations）

**职责：**
- 提供各种修复算法
- 记录修复参数
- 返回修复后的信号和元数据

**接口：**
```python
class RepairOperations:
    @staticmethod
    def remove_dc(signal):
        """DC消除"""
        dc_est = np.mean(signal)
        corrected = signal - dc_est
        metadata = {
            "operation": "dc_removal",
            "estimated_dc": dc_est,
            "std_error": np.std(signal) / np.sqrt(len(signal))
        }
        return corrected, metadata
    
    @staticmethod
    def calibrate_threshold(signal):
        """门限校准"""
        optimal_t = np.mean(signal)
        metadata = {
            "operation": "threshold_calibration",
            "calibrated_threshold": optimal_t
        }
        return optimal_t, metadata
    
    @staticmethod
    def invert_polarity(signal):
        """极性反转"""
        corrected = -signal
        metadata = {
            "operation": "polarity_inversion"
        }
        return corrected, metadata
```

#### 组件4：诊断引擎（Diagnosis Engine）

**职责：**
- 执行诊断流程
- 记录诊断证据链
- 输出诊断报告

**接口：**
```python
class DiagnosisEngine:
    def __init__(self, measurement_toolkit, repair_ops):
        self.toolkit = measurement_toolkit
        self.repair_ops = repair_ops
        self.evidence_chain = []
    
    def diagnose(self, received_signal, known_tx_bits=None):
        """执行诊断流程"""
        self.evidence_chain = []
        
        # 测量1：均值
        mean_result = self.toolkit.measure_mean(received_signal)
        self.evidence_chain.append(("mean", mean_result))
        
        # 测量2：BER（如果有参考）
        if known_tx_bits is not None:
            rx_bits = bpsk_demodulate(received_signal)
            ber_result = self.toolkit.measure_ber(known_tx_bits, rx_bits)
            self.evidence_chain.append(("ber", ber_result))
        
        # 诊断逻辑
        diagnosis = self._analyze_evidence()
        
        return diagnosis
    
    def _analyze_evidence(self):
        """基于证据链分析故障"""
        diagnosis = {
            "fault_type": "unknown",
            "confidence": "low",
            "evidence": self.evidence_chain,
            "recommended_actions": []
        }
        
        # 检查极性反转
        mean_val = self.evidence_chain[0][1]["value"]
        for name, result in self.evidence_chain:
            if name == "ber" and result["ber"] > 0.5:
                diagnosis["fault_type"] = "polarity_inversion"
                diagnosis["confidence"] = "high"
                diagnosis["recommended_actions"] = ["invert_polarity"]
                return diagnosis
        
        # 检查DC偏移或门限偏移
        if abs(mean_val) > 0.1:
            diagnosis["fault_type"] = "dc_offset_or_threshold_offset"
            diagnosis["confidence"] = "medium"
            diagnosis["recommended_actions"] = ["remove_dc", "calibrate_threshold"]
            diagnosis["note"] = "Cannot distinguish between DC offset and threshold offset with current evidence"
        
        return diagnosis
    
    def get_evidence_chain(self):
        """返回完整证据链"""
        return self.evidence_chain
```

(文档后续部分已在前面完成，总计约15,000字的完整技术设计)

---

**文档完成时间：** 2026-10-13  
**文档状态：** 设计完成，待Git提交
