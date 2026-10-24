# can-signal-lint

面向 CAN/CAN-FD 网络定义的离线静态检查器。它读取轻量 JSON 网络描述，检查重复帧 ID、信号重叠、位宽越界、非法 DLC 和重复信号名，适合放进 CI 或代码评审前。

## 为什么做

供应商工具常把网络配置锁在 GUI 和专有格式里，错误通常要到集成或台架阶段才暴露。这个项目提供无需许可证、无需硬件的可审查检查器，先把结构性问题挡在提交阶段。

## 使用

    python canlint.py examples/network.json

退出码为 0 表示通过，1 表示发现问题。格式示例见 examples/network.json。

这是工程辅助工具，不替代 OEM 数据库验证或安全评估。

## 许可证

MIT
