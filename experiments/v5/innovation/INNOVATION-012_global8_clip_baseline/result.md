# V5-INNOVATION-012 结果

状态：`completed`；证据等级为 `valid_single_run`。这是无训练参数的确定性零号基线，不是新模块结果。

| Run | U | S | H | ZS | 可训练参数 | 决定 |
|---|---:|---:|---:|---:|---:|---|
| `RUN-001` | 63.037896 | 65.331149 | 64.164039 | 80.301231 | 0 | `baseline_established` |

- 运行提交：`2f9600a9c0db83bae5ede91c3a0c7834af3b3cef`
- 8 句缓存 SHA-256：`8c1a8e27a70681759b22e87412c424b6c9c3a7991ed391b3acc244bbc3a6bca3`
- 200 类顺序 SHA-256：`7b6ffe26103bfeb73324f328fac499d6ea7cfadfb2b56448b0df295aca22df38`
- 结果 JSON SHA-256：`5530ac947d5521441fd76e853627940829148bebd72c36e6c7fe5e9740a1a279`
- 运行日志 SHA-256：`4d6c82deb948322b2343060b6ba1f48276dd9da8cf9c91c4533c9e58d9ccecd6`

距离 `H=75` 目标还差 `10.835961` 个百分点。下一项实验从同一冻结 CLIP 和 8 句输入独立分叉，只加入共享 PSE；不加入 patch、局部分支或其他旧模块。
