# 精确差异

审核范围是 Git 提交：

```text
baseline: 66302091e6e7403e094f8e1fe69b6bf6874abdf9
candidate: a9f8a83c2c0fa2c86cb5b53443579d8ddfd26f1d
command: git diff --check 66302091e6e7403e094f8e1fe69b6bf6874abdf9..a9f8a83c2c0fa2c86cb5b53443579d8ddfd26f1d
```

候选只修改 17 个轻量账本与说明文件，共 88 行新增、37 行删除；没有改模型、训练入口、评估、数据、配置或工作流代码，也没有把日志、缓存或模型文件提交到 Git。
