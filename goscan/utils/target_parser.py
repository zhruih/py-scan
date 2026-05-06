import ipaddress

def parse_targets(target_str):
    """
    解析目标 IP, 格式支持: 192.168.1.1, 192.168.1.1/24, 192.168.1.1-100
    """
    targets = []
    try:
        if '/' in target_str:
            # 处理 CIDR
            network = ipaddress.ip_network(target_str, strict=False)
            targets = [str(ip) for ip in network.hosts()]
        elif '-' in target_str:
            # 处理 192.168.1.1-100
            prefix = target_str.rsplit('.', 1)[0]
            start_end = target_str.rsplit('.', 1)[1].split('-')
            start = int(start_end[0])
            end = int(start_end[1])
            for i in range(start, end + 1):
                targets.append(f"{prefix}.{i}")
        else:
            targets = [target_str]
    except Exception as e:
        print(f"Error parsing targets: {e}")
    return targets
