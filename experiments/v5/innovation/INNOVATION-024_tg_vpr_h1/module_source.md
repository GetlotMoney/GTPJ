# 模块来源

TG-VPR-H1 的强文本原型母体来自项目已有的 CLIP-A-self/PSE 与 X2 诊断，来源论文和代码仍需引用 VDT-Adapter。

本模块相对来源的项目内新增边界是：三组平级语义、删除Q/K attention、单一768维Value路径、seen类适配和unseen Mean8。

多 seed 结果证据固定为 `git+commit://5ff6ce31b31872e042dec14028dd49d028a05cd6/experiments/v5/tune/TUNE-005_tg_vpr_h1_multiseed/result.md`，原始产物位于 `warehouse://runs/tg-vpr-h1-multiseed-20260821/`。
