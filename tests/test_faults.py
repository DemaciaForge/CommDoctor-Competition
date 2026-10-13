"""
测试故障注入模块

验证DC偏移注入和移除功能的正确性。
"""

import numpy as np
import pytest
from commdoctor.faults import inject_dc_offset, remove_dc_offset


class TestDCOffsetInjection:
    """测试DC偏移注入"""

    def test_inject_positive_dc(self):
        """测试注入正DC偏移"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        dc_offset = 0.5

        faulty = inject_dc_offset(symbols, dc_offset)

        # 验证每个符号都增加了DC偏移
        expected = np.array([-0.5, 1.5, -0.5, 1.5])
        np.testing.assert_array_almost_equal(faulty, expected)

        # 验证均值等于DC偏移
        assert np.abs(np.mean(faulty) - dc_offset) < 1e-10

    def test_inject_negative_dc(self):
        """测试注入负DC偏移"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        dc_offset = -0.3

        faulty = inject_dc_offset(symbols, dc_offset)

        expected = np.array([-1.3, 0.7, -1.3, 0.7])
        np.testing.assert_array_almost_equal(faulty, expected)

    def test_inject_zero_dc(self):
        """测试注入零DC偏移（应该不改变信号）"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        dc_offset = 0.0

        faulty = inject_dc_offset(symbols, dc_offset)

        np.testing.assert_array_almost_equal(faulty, symbols)

    def test_inject_large_dc(self):
        """测试注入较大的DC偏移"""
        symbols = np.array([-1.0, 1.0])
        dc_offset = 2.0

        faulty = inject_dc_offset(symbols, dc_offset)

        expected = np.array([1.0, 3.0])
        np.testing.assert_array_almost_equal(faulty, expected)

    def test_inject_dc_does_not_modify_input(self):
        """测试注入操作不修改输入数组"""
        symbols = np.array([-1.0, 1.0, -1.0, 1.0])
        original = symbols.copy()

        inject_dc_offset(symbols, dc_offset=0.5)

        np.testing.assert_array_equal(symbols, original)

    def test_inject_dc_invalid_input(self):
        """测试无效输入"""
        symbols = np.array([-1.0, 1.0])

        # 测试非有限DC偏移
        with pytest.raises(ValueError, match="DC偏移必须是有限数值"):
            inject_dc_offset(symbols, dc_offset=np.nan)

        with pytest.raises(ValueError, match="DC偏移必须是有限数值"):
            inject_dc_offset(symbols, dc_offset=np.inf)

        # 测试非数组输入
        with pytest.raises(TypeError, match="symbols必须是numpy数组"):
            inject_dc_offset([1, 2, 3], dc_offset=0.5)


class TestDCOffsetRemoval:
    """测试DC偏移移除"""

    def test_remove_dc_automatic_estimation(self):
        """测试自动估计并移除DC偏移"""
        # 接收信号有DC偏移
        received = np.array([-0.5, 1.5, -0.5, 1.5])

        corrected, dc_est = remove_dc_offset(received)

        # 验证估计的DC偏移
        assert np.abs(dc_est - 0.5) < 1e-10

        # 验证移除后的信号
        expected = np.array([-1.0, 1.0, -1.0, 1.0])
        np.testing.assert_array_almost_equal(corrected, expected)

        # 验证移除后均值接近0
        assert np.abs(np.mean(corrected)) < 1e-10

    def test_remove_dc_with_provided_estimate(self):
        """测试使用提供的DC估计值移除DC偏移"""
        received = np.array([-0.3, 1.7, -0.2, 1.8])
        dc_estimate = 0.5

        corrected, dc_est = remove_dc_offset(received, dc_estimate=dc_estimate)

        # 验证使用的DC估计值
        assert dc_est == 0.5

        # 验证移除后的信号
        expected = received - 0.5
        np.testing.assert_array_almost_equal(corrected, expected)

    def test_remove_negative_dc(self):
        """测试移除负DC偏移"""
        received = np.array([-1.3, 0.7, -1.3, 0.7])

        corrected, dc_est = remove_dc_offset(received)

        # 验证估计的DC偏移
        assert np.abs(dc_est - (-0.3)) < 1e-10

        # 验证移除后的信号
        expected = np.array([-1.0, 1.0, -1.0, 1.0])
        np.testing.assert_array_almost_equal(corrected, expected)

    def test_remove_dc_no_offset(self):
        """测试移除不存在的DC偏移"""
        received = np.array([-1.0, 1.0, -1.0, 1.0])

        corrected, dc_est = remove_dc_offset(received)

        # DC估计应该接近0
        assert np.abs(dc_est) < 1e-10

        # 信号应该基本不变
        np.testing.assert_array_almost_equal(corrected, received)

    def test_remove_dc_with_noise(self):
        """测试在有噪声的信号上移除DC偏移"""
        np.random.seed(42)

        # 理想符号 + DC偏移 + 噪声
        symbols = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0] * 100)
        dc_offset = 0.4
        noise = np.random.normal(0, 0.1, size=len(symbols))
        received = symbols + dc_offset + noise

        corrected, dc_est = remove_dc_offset(received)

        # DC估计应该接近真实DC偏移
        assert np.abs(dc_est - dc_offset) < 0.02  # 允许小误差

        # 移除后的均值应该接近0
        assert np.abs(np.mean(corrected)) < 0.02

    def test_remove_dc_does_not_modify_input(self):
        """测试移除操作不修改输入数组"""
        received = np.array([-0.5, 1.5, -0.5, 1.5])
        original = received.copy()

        remove_dc_offset(received)

        np.testing.assert_array_equal(received, original)

    def test_remove_dc_invalid_input(self):
        """测试无效输入"""
        # 测试空数组
        with pytest.raises(ValueError, match="不能为空"):
            remove_dc_offset(np.array([]))

        # 测试非数组输入
        with pytest.raises(TypeError, match="必须是numpy数组"):
            remove_dc_offset([1, 2, 3])

        # 测试非有限DC估计值
        received = np.array([-1.0, 1.0])
        with pytest.raises(ValueError, match="dc_estimate必须是有限数值"):
            remove_dc_offset(received, dc_estimate=np.nan)


class TestDCOffsetRoundTrip:
    """测试DC偏移注入和移除的往返操作"""

    def test_inject_and_remove_dc(self):
        """测试注入后移除能恢复原始信号"""
        original = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])
        dc_offset = 0.7

        # 注入DC偏移
        faulty = inject_dc_offset(original, dc_offset)

        # 移除DC偏移
        recovered, dc_est = remove_dc_offset(faulty)

        # 验证能恢复原始信号
        np.testing.assert_array_almost_equal(recovered, original)

        # 验证DC估计准确
        assert np.abs(dc_est - dc_offset) < 1e-10

    def test_inject_and_remove_with_noise(self):
        """测试在有噪声情况下的往返操作"""
        np.random.seed(123)

        original = np.array([-1.0, 1.0] * 500)
        dc_offset = 0.3
        noise = np.random.normal(0, 0.2, size=len(original))

        # 注入DC偏移和噪声
        faulty = inject_dc_offset(original, dc_offset) + noise

        # 移除DC偏移
        recovered, dc_est = remove_dc_offset(faulty)

        # DC估计应该接近真实值
        assert np.abs(dc_est - dc_offset) < 0.02

        # 恢复的信号应该接近原始信号（除了噪声）
        # 验证均值接近原始信号均值（0）
        assert np.abs(np.mean(recovered)) < 0.02
