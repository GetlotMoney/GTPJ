# Framework Diagram

```text
CLS x ------------------------------> cosine(x, Mean8 prototype) ----+
  |                                                                  |
8-role text -> full-200 same-role rivals -> target-rival evidence ---+-> final logits
                                                                      -> U/S/H/ZS
```

## 变量

- `x`：冻结 CLIP CLS。
- `t[c,r]`：类别 `c` 的角色 `r` 文本向量。
- `n(c,r)`：完整 200 类语义全集中同角色最近文本类。
- `contribution[c,r] = lambda/8 * (cos(x,t[c,r]) - cos(x,t[n(c,r),r]))`。

删除任一角色项时，raw score 的变化应严格等于该项贡献。
