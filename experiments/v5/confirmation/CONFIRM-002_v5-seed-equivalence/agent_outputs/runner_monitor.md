# runner_monitor

decision: pass

检查了五个 RUN 的 `0/1、0/1、0` 三波计划、两张 GPU 锁、STOP、失败后不发下一波、服务器固定 Python 和真实 bwrap CUDA 可见性。服务器沙箱实测能看到两张 RTX 4090。
