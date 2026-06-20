# 数据准备

数据集和特征缓存不纳入 Git 管理。

预期本地路径：

```text
data/xlsa17/data/CUB/
data/xlsa17/data/AWA2/
data/xlsa17/data/SUN/
data/CUB/images/
data/gpt4_data/
data/cache/
```

不要提交：

- 原始数据集
- CLIP 特征缓存
- checkpoint
- 大型训练日志

对于一次运行记录，Git 中只保存轻量摘要，并记录大型产物的本地路径或云端路径。
