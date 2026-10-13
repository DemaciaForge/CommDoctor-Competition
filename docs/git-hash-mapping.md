# Git提交哈希映射表

本文档记录了2026-10-13历史清理操作的提交哈希变更。

## 清理说明

- **操作日期**: 2026-10-13
- **清理目的**: 移除Git提交信息中的Claude Co-Authored-By标记
- **清理工具**: git filter-branch
- **影响范围**: 全部13个提交的哈希值改变
- **代码内容**: 完全未改变
- **提交结构**: 分支和合并关系完整保留

## 哈希映射

| 原始哈希 (93ee04a之前) | 清理后哈希 (c78b976之后) | 提交标题 |
|------------------------|---------------------------|----------|
| 93ee04a423a11604f267563c209ebb2e8e1b1d58 | c78b976b8c45a4bb72beb763c7fe86b3838c497d | chore: 添加MIT开源许可证 |
| 6753aac221c322cdb1c0ab1dcbdcd3365d371e8d | eb565a4d3489a7ef3328f0212daa05c8f526a49f | docs: 标准化作者字段为GitHub用户名DemaciaForge |
| d0182b9867fb83208defd2d1e3446e02a9d21802 | 8deec258cd449278c6685458e4e498838056fa6d | docs(stage02b): 添加Git分支合并与整合完整报告 |
| f268738e9bbe30521e0d7d22c14e3475eaecbee7 | 6208dc512001dfb4c7777c45b1b3d144538a5788 | docs(stage02a): 标注教学示例BER数值,避免与实验参数混淆 |
| 8d2ac3cd1122afee45febcde530a1af5e11114a1 | 4dbfc2e8dc468cbf299811154bda90ce590c7612 | merge: 集成阶段01-02B开发成果 |
| ed58ad202664c902c97354339d3bf350679b54ca | ce903e79202684c2ac4a6f738af9629d2b5586d1 | docs(stage02b): 添加阶段02-B Git分支与交付完整性审计报告 |
| e2a591471256cd6bee165a09bd7845076a7093d3 | c0f389fa86bc17624f123da7a7b27a0628f284b1 | feat(stage02b): 实现DC偏移故障完整闭环验证 |
| 56f9baf4b57d556c1ef31ede4802b75180cbb7ec | f0349ed23ffb085914f2d39dba3fa24274bc739a | docs(stage02a): 添加阶段02-A总结报告 |
| 5b5efd3278d9fd36d552129434ea028dd1c739df | 2c97769a0976387f4107ef0e5f44891373bab492 | docs(stage02a): 完成故障诊断系统技术设计 |
| 1b0e5058ee6f949fa36b889eda9496cd44837858 | 5198778f8c7bb3076b6b589de300c136fa6e9755 | docs(stage01): 添加阶段01最终验收报告 |
| 36e6cce4e55c6019a52f5ef3dd80badf6aac7982 | 93b4598587908bf18595174cce185a1c1b8382da | feat(stage01): 迁移BPSK通信仿真内核并完成验证 |
| 53e109d990159237188b97ae93a7d705da60c45a | e56afc27d31a8a915ad92e179314e5997866120e | docs: 完成阶段00总结和记录更新 |
| d6bdbfd9b69c2c2d34bd5806f95bbde6d4fae351 | 428e6d68bbb332e82926115c2f2895f7b2022d2c | chore: 初始化项目结构和开发规范 |

## 验证信息

- **清理前Co-Authored-By数量**: 13个
- **清理后Co-Authored-By数量**: 0个
- **pytest测试结果**: 60/60通过
- **DC偏移演示**: 全部验收标准通过
- **备份位置**: `D:\CommDoctor-Competition-backup-20261013-190056`

## 注意事项

1. 原始Prompt归档中引用的旧哈希仍然有效（在备份中）
2. 本映射表用于追溯开发历史，不代表伪造
3. 后续开发应基于清理后的仓库进行
