# -*- coding: utf-8 -*-
"""
网段探测配置示例
"""

# 场景 1: 快速探测 Class A 网段
CONFIG_FAST_SCAN = {
    "network": "10.0.0.0/8",
    "mode": "network",
    "threads": 1000,
    "timeout": 0.3,
    "description": "快速探测 10.0.0.0/8，预计 30-60 秒"
}

# 场景 2: 精确探测单个 C 段
CONFIG_PRECISE_SCAN = {
    "network": "192.168.1.0/24",
    "mode": "host",
    "threads": 2000,
    "timeout": 0.5,
    "description": "逐 IP 精确扫描 C 段，预计 5-10 秒"
}

# 场景 3: 隐蔽探测（超低发包）
CONFIG_STEALTH_SCAN = {
    "network": "10.0.0.0/16",
    "mode": "network",
    "threads": 100,
    "timeout": 1.0,
    "description": "低并发隐蔽探测，减少网络活跃度"
}

# 场景 4: 多步骤探测流程
CONFIG_WORKFLOW = [
    {
        "step": 1,
        "network": "10.0.0.0/8",
        "mode": "network",
        "threads": 1000,
        "timeout": 0.5,
        "description": "第一步：快速定位活跃 /16"
    },
    {
        "step": 2,
        "network": "10.1.0.0/16",  # 假设第一步发现了这个 /16
        "mode": "network",
        "threads": 500,
        "timeout": 0.3,
        "description": "第二步：细化活跃 /24 网段"
    },
    {
        "step": 3,
        "network": "10.1.1.0/24",   # 假设第二步发现了这个 /24
        "mode": "host",
        "threads": 2000,
        "timeout": 0.2,
        "description": "第三步：发现所有活跃主机"
    }
]

if __name__ == "__main__":
    print("=== 网段探测配置示例 ===\n")
    
    configs = [
        CONFIG_FAST_SCAN,
        CONFIG_PRECISE_SCAN,
        CONFIG_STEALTH_SCAN
    ]
    
    for idx, config in enumerate(configs, 1):
        print(f"[场景 {idx}] {config['description']}")
        print(f"  命令: python main.py -i {config['network']} --mode {config['mode']} " +
              f"--threads {config['threads']} --timeout {config['timeout']}\n")
