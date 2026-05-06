# Py-Internal-Scan

这是一个使用 Python 编写的内网快速扫描工具，旨在替代或补充 fscan/kscan 的功能，专注于大网段扫描的优化。

## 优化逻辑 (Python 实现)

1. **分阶段异步探测**:
   - **探测阶段 (Discovery)**: 使用 `ThreadPoolExecutor` 配合 `socket.connect_ex` 对大网段进行快速存活探测。通过对常见的内网存活端口（80, 445, 135）进行轻量级 TCP 握手，规避 ICMP 被禁用的情况，比顺序 Ping 更快。
   - **资源管理**: 采用生成器/惰性加载方式处理 IP 列表，避免在扫描 /8 段（1600万 IP）时一次性加载到内存导致 OOM。

2. **自适应并发**:
   - 默认支持 200-500 并发，这在 Python 的 IO 密集型操作中能显著提高扫描 B 段（65535 个 IP）的速度。

## 使用方法

```bash
python main.py -i 192.168.1.0/24 -t 300
```

## 目录结构
- `main.py`: 程序调度中心
- `goscan/core/`: 核心扫描与探测逻辑
- `goscan/utils/`: IP 解析等工具类
- `goscan/modules/`: 待开发的漏洞利用/弱口令插件
