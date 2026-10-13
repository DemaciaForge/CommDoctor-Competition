"""
测试诊断模块

验证DC偏移估计和信号统计测量功能。
"""

import numpy as np
import pytest
from commdoctor.diagnosis import estimate_dc_offset, measure_signal_statistics
from commdoctor.modulation import bpsk_modulate


class TestDCOffsetEstimation:
    """测试DC偏移估计"""

    def test_estimate_dc_with_training_symbols(self):
        """测试使用训练符号估计DC偏移（两点法）"""
        # 已知发送符号
        tx_symbols = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])
        dc_offset = 0.5

        # 接收信号 = 发送符号 + DC偏移
        rx_symbols = tx_symbols + dc_offset

        result = estimate_dc_offset(rx_symbols, transmitted_symbols=tx_symbols)

        # 验证估计方法
        assert result["method"] == "two_point"

        # 验证DC估计值
        assert np.abs(result["dc_estimate"] - 0.5) < 1e-10

        # 验证均值
        assert np.abs(result["mean_for_minus1"] - (-0.5)) < 1e-10
        assert np.abs(result["mean_for_plus1"] - 1.5) < 1e-10

    def test_estimate_dc_with_training_bits(self):
        """测试使用训练比特估计DC偏移"""
        tx_bits = np.array([0, 1, 0, 1, 0, 1])
        tx_symbols = bpsk_modulate(tx_bits)  # [-1, 1, -1, 1, -1, 1]
        dc_offset = 0.3

        rx_symbols = tx_symbols + dc_offset

        result = estimate_dc_offset(rx_symbols, training_bits=tx_bits)

        # 应该使用两点法
        assert result["method"] == "two_point"
        assert np.abs(result["dc_estimate"] - 0.3) < 1e-10

    def test_estimate_dc_without_training(self):
        """测试不使用训练序列估计DC偏移（均值法）"""
        # 等概的信号
        rx_symbols = np.array([-0.5, 1.5, -0.5, 1.5, -0.5, 1.5])

        result = estimate_dc_offset(rx_symbols)

        # 验证估计方法
        assert result["method"] == "mean"

        # 验证DC估计值（均值）
        assert np.abs(result["dc_estimate"] - 0.5) < 1e-10

    def test_estimate_dc_with_noise(self):
        """测试在有噪声情况下估计DC偏移"""
        np.random.seed(42)

        tx_symbols = np.array([-1.0, 1.0] * 500)
        dc_offset = 0.4
        noise = np.random.normal(0, 0.2, size=len(tx_symbols))
        rx_symbols = tx_symbols + dc_offset + noise

        result = estimate_dc_offset(rx_symbols, transmitted_symbols=tx_symbols)

        # DC估计应该接近真实值
        assert np.abs(result["dc_estimate"] - 0.4) < 0.02

        # 标准误差应该很小
        assert result["std_error"] < 0.01

    def test_estimate_dc_negative_offset(self):
        """测试估计负DC偏移"""
        tx_symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        dc_offset = -0.6
        rx_symbols = tx_symbols + dc_offset

        result = estimate_dc_offset(rx_symbols, transmitted_symbols=tx_symbols)

        assert np.abs(result["dc_estimate"] - (-0.6)) < 1e-10

    def test_estimate_dc_large_offset(self):
        """测试估计较大的DC偏移"""
        tx_symbols = np.array([-1.0, 1.0] * 50)
        dc_offset = 2.0
        rx_symbols = tx_symbols + dc_offset

        result = estimate_dc_offset(rx_symbols, transmitted_symbols=tx_symbols)

        assert np.abs(result["dc_estimate"] - 2.0) < 1e-10

    def test_estimate_dc_unbalanced_data_mean_method(self):
        """测试不平衡数据的均值法（会有偏差）"""
        # 大量的+1，少量的-1
        tx_symbols = np.array([1.0] * 90 + [-1.0] * 10)
        dc_offset = 0.5
        rx_symbols = tx_symbols + dc_offset

        # 均值法会有偏差
        result_mean = estimate_dc_offset(rx_symbols)
        # 真实均值 = 0.8*1.5 + 0.1*(-0.5) + 0.1*(-0.5) = 1.2 - 0.1 = 1.3
        # 等等，让我重新计算：0.9 * (1+0.5) + 0.1 * (-1+0.5) = 1.35 - 0.05 = 1.3
        expected_mean = 0.9 * 1.5 + 0.1 * (-0.5)
        assert np.abs(result_mean["dc_estimate"] - expected_mean) < 1e-10

        # 两点法应该准确
        result_two_point = estimate_dc_offset(rx_symbols, transmitted_symbols=tx_symbols)
        assert np.abs(result_two_point["dc_estimate"] - 0.5) < 1e-10

    def test_estimate_dc_invalid_input(self):
        """测试无效输入"""
        # 空数组
        with pytest.raises(ValueError, match="不能为空"):
            estimate_dc_offset(np.array([]))

        # 训练序列不包含两种符号
        with pytest.raises(ValueError):
            estimate_dc_offset(
                np.array([1.0, 1.0, 1.0]),
                transmitted_symbols=np.array([1.0, 1.0, 1.0]),
            )

    def test_estimate_dc_returns_num_samples(self):
        """测试返回样本数量"""
        rx = np.array([-0.5, 1.5, -0.5, 1.5])
        result = estimate_dc_offset(rx)

        assert result["num_samples"] == 4


class TestSignalStatistics:
    """测试信号统计测量"""

    def test_measure_basic_statistics(self):
        """测试基本统计量测量"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])

        stats = measure_signal_statistics(symbols)

        # 验证均值
        assert np.abs(stats["mean"] - 0.0) < 1e-10

        # 验证方差（无偏估计）
        # 对于[-1, 1, -1, 1]: 均值=0, 方差=sum((x-0)^2)/(n-1) = (1+1+1+1)/3 = 4/3
        expected_var = 4.0 / 3.0
        assert np.abs(stats["variance"] - expected_var) < 1e-10

        # 验证标准差
        assert np.abs(stats["std"] - np.sqrt(expected_var)) < 1e-10

        # 验证样本数
        assert stats["num_samples"] == 4

    def test_measure_statistics_with_dc_offset(self):
        """测试带DC偏移的信号统计"""
        symbols = np.array([-0.5, 1.5, -0.5, 1.5])

        stats = measure_signal_statistics(symbols)

        # 均值应该是DC偏移
        assert np.abs(stats["mean"] - 0.5) < 1e-10

        # 方差不受DC偏移影响
        # 对于[-0.5, 1.5, -0.5, 1.5]: 均值=0.5
        # 方差 = sum((x-0.5)^2)/(n-1) = (1+1+1+1)/3 = 4/3
        expected_var = 4.0 / 3.0
        assert np.abs(stats["variance"] - expected_var) < 1e-10

    def test_measure_statistics_with_noise(self):
        """测试带噪声信号的统计"""
        np.random.seed(42)

        # BPSK符号 + DC + 噪声
        clean_symbols = np.array([-1.0, 1.0] * 500)
        dc_offset = 0.3
        noise_std = 0.2
        noise = np.random.normal(0, noise_std, size=len(clean_symbols))
        noisy_symbols = clean_symbols + dc_offset + noise

        stats = measure_signal_statistics(noisy_symbols)

        # 均值应该接近DC偏移
        assert np.abs(stats["mean"] - dc_offset) < 0.05

        # 方差应该接近 Var[s] + Var[w]
        # 对于[-1,1]交替: E[s]=0, E[s^2]=1, Var[s]=1
        # 总方差约为 1 + 0.04 = 1.04
        expected_var = 1.0 + noise_std**2
        assert np.abs(stats["variance"] - expected_var) < 0.1

        # 标准误差应该合理
        assert stats["mean_std_error"] < 0.05

    def test_measure_statistics_constant_signal(self):
        """测试常数信号的统计"""
        symbols = np.array([0.5, 0.5, 0.5, 0.5])

        stats = measure_signal_statistics(symbols)

        assert np.abs(stats["mean"] - 0.5) < 1e-10
        assert np.abs(stats["variance"]) < 1e-10
        assert np.abs(stats["std"]) < 1e-10

    def test_measure_statistics_returns_errors(self):
        """测试返回标准误差"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])

        stats = measure_signal_statistics(symbols)

        # 验证返回了误差项
        assert "mean_std_error" in stats
        assert "var_std_error" in stats
        assert stats["mean_std_error"] > 0
        assert stats["var_std_error"] > 0

    def test_measure_statistics_invalid_input(self):
        """测试无效输入"""
        with pytest.raises(ValueError, match="不能为空"):
            measure_signal_statistics(np.array([]))
