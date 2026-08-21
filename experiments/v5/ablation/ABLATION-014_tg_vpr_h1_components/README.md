# V5-ABLATION-014：H1成分消融

四个条件使用相同seed 7、数据、50轮训练、损失、scheduler和评估口径：

1. `SINGLE-GROUP-VALUE`：8句先平均成一个原型，再走单一Value路径。
2. `THREE-GROUP-NO-VALUE`：三组固定等权，不使用Value重参数化。
3. `THREE-GROUP-FIXED-EQUAL-VALUE`：三组固定`1/3`并使用Value路径。
4. `FULL-H1-LEARNED-WEIGHTS`：完整H1，三组权重可学习。

单变量判断：

- `A vs C`：两者都使用Value且固定融合，差异只在单组还是三组，用于隔离三组结构。
- `B vs C`：两者都是三组固定`1/3`，差异只在是否使用Value，用于隔离Value路径。
- `C vs D`：两者都是三组加Value，差异只在权重固定还是学习，用于隔离可学习组权重。

若C≈D则删除可学习权重；若B≈C则Value贡献不足；若A≈C则三组结构贡献不足。D与A/B/C的总体差异只能描述完整组合效果，不能替代上述配对因果判断。
