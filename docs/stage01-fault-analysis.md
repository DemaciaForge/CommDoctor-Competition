# 阶段01：故障模拟技术分析

**文档编号:** STAGE01-FAULT-ANALYSIS  
**日期:** 2026-10-13  
**状态:** 技术建议（未实现）

---

## 一、当前模型能力与限制

### 1.1 当前BPSK模型特征

**已实现的信号模型：**
- 实值BPSK符号：+1 和 -1
- 单位符号能量归一化
- 实值AWGN噪声
- 硬判决解调
- 无时间维度（符号级抽象）
- 无载波表示（基带等效模型）

**数学表述：**
```
发送符号: s[n] ∈ {-1, +1}
接收信号: r[n] = s[n] + w[n]
其中 w[n] ~ N(0, σ²)
```

### 1.2 模型适用的故障类型

基于当前实值符号模型，以下故障类型可以**真实模拟**：

#### ✓ 可真实模拟的故障

1. **AWGN噪声过大**
   - 实现方式：增加噪声方差 σ²
   - 可观察现象：BER升高，接收符号分散
   - 修复方法：无法直接修复（需要提高发射功率或改善信道）
   - 诊断依据：测量接收信号方差，对比预期噪声水平

2. **符号能量不匹配**
   - 实现方式：发送符号幅度 ≠ 1（例如 0.5 或 1.5）
   - 可观察现象：等效SNR变化，BER偏离理论值
   - 修复方法：归一化接收信号或调整判决门限
   - 诊断依据：测量接收信号平均功率

3. **判决门限偏移**
   - 实现方式：解调器使用 threshold ≠ 0
   - 可观察现象：+1 和 -1 错误率不对称
   - 修复方法：重新校准判决门限
   - 诊断依据：统计 0→1 和 1→0 错误率

4. **DC偏移（直流偏置）**
   - 实现方式：接收信号 r[n] = s[n] + dc_offset + w[n]
   - 可观察现象：接收信号均值 ≠ 0，误码率升高
   - 修复方法：减去DC偏移或自适应门限
   - 诊断依据：计算接收信号均值

#### ✗ 不可真实模拟的故障（需要扩展模型）

以下故障无法在当前实值符号模型中真实实现：

1. **载波频率偏移（CFO）**
   - 需要：复基带信号 + 时间连续模型
   - 原因：实值符号无相位信息
   - 不能简单用"符号乘以随机相位"冒充，因为BPSK符号只有±1

2. **载波相位偏移**
   - 需要：复基带信号表示
   - 原因：相位是复信号的属性

3. **符号定时偏移**
   - 需要：过采样信号 + 时间轴
   - 原因：当前模型是符号级抽象，无时间维度

4. **多径衰落**
   - 需要：时间延迟 + 复信道增益
   - 原因：需要表示延迟副本的叠加

5. **IQ不平衡**
   - 需要：复信号I/Q两路
   - 原因：实值信号无I/Q概念

---

## 二、首期推荐故障类型（3种）

基于技术可行性和教学价值，推荐以下3种故障作为首期实现目标：

### 故障1：AWGN噪声功率异常

**故障现象：**
- 信道噪声水平超出设计范围
- BER显著高于预期

**注入方式：**
```python
# 正常: eb_n0_db = 8
# 故障: 实际噪声对应 eb_n0_db = 3
故障信道 = awgn_channel(symbols, eb_n0_db=3, seed=seed)
```

**诊断方法：**
- 测量接收信号的噪声方差
- 对比理论BER与实测BER
- 估算实际Eb/N0

**修复方法：**
- 提示：信道质量下降，需增加发射功率（教学场景）
- 实际：无法修复硬件信道，但可以识别问题

**教学价值：** ★★★★★  
学生学习如何测量噪声、估算SNR、理解BER曲线

---

### 故障2：判决门限偏移

**故障现象：**
- 0→1 和 1→0 错误率不对称
- BER高于最优门限下的理论值

**注入方式：**
```python
def faulty_demodulate(received_symbols, threshold=0.3):
    """故障解调器：判决门限偏移"""
    bits = (received_symbols >= threshold).astype(np.int8)
    return bits
```

**诊断方法：**
- 统计 P(0→1) 和 P(1→0)
- 如果不对称，说明门限偏移
- 估算最优门限位置

**修复方法：**
```python
# 自适应门限校准
optimal_threshold = np.mean(received_symbols)
corrected_bits = (received_symbols >= optimal_threshold).astype(np.int8)
```

**教学价值：** ★★★★☆  
学生学习最优判决理论、门限对性能的影响

---

### 故障3：DC偏移

**故障现象：**
- 接收信号整体上移或下移
- 即使无噪声也可能出现误码

**注入方式：**
```python
def add_dc_offset(symbols, dc_value=0.5):
    """添加直流偏移故障"""
    return symbols + dc_value
```

**诊断方法：**
- 计算接收信号均值
- 理论上应该接近0，偏移说明有DC分量

**修复方法：**
```python
# DC消除
mean_val = np.mean(received_symbols)
corrected_symbols = received_symbols - mean_val
```

**教学价值：** ★★★★☆  
学生学习DC偏移概念、均值计算、自适应补偿

---

## 三、未来扩展方向

如果要模拟更复杂的故障（如载波频率偏移），需要：

### 3.1 复基带信号模型

```python
# 当前: s[n] = ±1 (实数)
# 扩展: s[n] = exp(j*φ[n]) * A (复数)

def bpsk_modulate_complex(bits):
    """复基带BPSK调制"""
    # 0 → exp(jπ) = -1
    # 1 → exp(j0) = +1
    phases = bits * 0 + (1 - bits) * np.pi
    symbols = np.exp(1j * phases)
    return symbols
```

### 3.2 时间连续或过采样模型

```python
# 当前: 符号级抽象
# 扩展: 每符号N个采样点

samples_per_symbol = 8
time_signal = upsample_and_filter(symbols, samples_per_symbol)
```

### 3.3 故障注入接口设计

**推荐接口结构：**

```python
class FaultInjector:
    """故障注入器基类"""
    
    def inject(self, signal):
        """在信号中注入故障"""
        raise NotImplementedError
    
    def get_parameters(self):
        """返回故障参数（不暴露真值）"""
        return {}

class NoiseInjector(FaultInjector):
    """噪声故障注入"""
    def __init__(self, actual_ebn0_db, claimed_ebn0_db):
        self.actual = actual_ebn0_db
        self.claimed = claimed_ebn0_db
    
    def inject(self, symbols):
        return awgn_channel(symbols, self.actual)
    
    def get_parameters(self):
        # 只返回声称的参数，不暴露真实故障
        return {"claimed_ebn0_db": self.claimed}
```

**诊断模块隔离：**
- 诊断模块只能访问接收信号和声称的系统参数
- 不能直接读取故障注入器的真实参数
- 通过测量和计算推断故障

---

## 四、关键设计原则

### 4.1 真实性原则

❌ **错误做法：**
```python
# 伪造频率偏移（在实值模型中）
faulty_symbols = symbols * np.random.choice([-1, 1], size=len(symbols))
# 这不是真实的频率偏移，只是随机翻转符号
```

✅ **正确做法：**
```python
# 如果要模拟频率偏移，必须使用复信号
symbols_complex = np.exp(1j * phases)  # 复基带
freq_offset = 0.1  # 归一化频偏
time_axis = np.arange(len(symbols_complex))
faulty_symbols = symbols_complex * np.exp(2j * np.pi * freq_offset * time_axis)
```

### 4.2 可诊断性原则

故障必须通过可观测量诊断，不能依赖隐藏真值：

```python
# ✓ 可接受：测量噪声方差
noise_estimate = np.var(received_symbols[known_training_pattern])

# ✗ 不可接受：直接读取故障注入器的参数
true_noise = fault_injector._internal_noise_level  # 作弊！
```

### 4.3 可修复性原则

故障修复应该有明确的算法依据：

```python
# ✓ 可接受：基于测量的DC补偿
dc_estimate = np.mean(received_symbols)
corrected = received_symbols - dc_estimate

# ✗ 不可接受：魔法修复
corrected = apply_magic_fix(received_symbols)  # 无理论依据
```

---

## 五、阶段02建议

1. **先实现3种基础故障**（噪声/门限/DC），验证框架
2. **建立故障注入-诊断-修复闭环**
3. **设计交互式诊断挑战流程**
4. **阶段03再考虑**是否扩展到复基带模型以支持更多故障

---

**文档状态：** 技术分析完成，待阶段02实施  
**负责人：** Claude Opus 5.5  
**审核状态：** 待用户确认
