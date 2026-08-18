# Framework Diagram

```text
CLS x -> cosine(x, Mean8 prototype) ---------------------------+
patches v[p] + role text t[c,r]                                |
  -> cosine(v[p], t[c,r])                                      |
  -> mean(top-8 patches) - mean(all 576 patches)               |
  -> lambda/8 * eight role terms ------------------------------+-> final logits
```

每个角色项是真实 raw score 加数；删除该项后的分数变化必须与记录贡献一致。patch 相似度只能解释模型内部匹配，不能宣称真实部位定位或人类因果。
