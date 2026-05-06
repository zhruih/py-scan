# -*- coding: utf-8 -*-
import socket
import concurrent.futures
import time
import random

class Discovery:
    def __init__(self, timeout=0.3):
        self.timeout = timeout
        # 只保留最关键的一两个端口用于大网段极速探测
        # 445 (Windows), 80 (Web/Gateway) 是内网最密集的两个服务
        self.check_ports = [445, 80]

    def is_alive(self, ip):
        """
        极速探测：只要有一个端口通了就返回，不再继续尝试其他端口
        """
        for port in self.check_ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    return ip
            except:
                pass
        return None

    def run(self, ips, threads=1000):
        # 优化点：打乱扫描顺序，防止瞬时网络风暴压垮网关
        random.shuffle(ips)
        
        print("[*] Starting ultra-fast discovery for {} targets...".format(len(ips)))
        print("[*] Concurrency: {} threads | Timeout: {}s".format(threads, self.timeout))
        
        alive_ips = []
        # Python 线程在大规模 IO 场景下比 Process 更有优势，
        # 我们将线程数提升到 1000+
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            # 采用 submit 配合 as_completed 提高响应速度
            future_to_ip = {executor.submit(self.is_alive, ip): ip for ip in ips}
            for future in concurrent.futures.as_completed(future_to_ip):
                res = future.result()
                if res:
                    alive_ips.append(res)
                    # 使用 format 兼容旧版本输出
                    output = "[+] Found alive: {:<15}".format(res)
                    import sys
                    sys.stdout.write(output + '\r')
                    sys.stdout.flush()
        
        print("\n[+] Discovery finished. Total alive: {}".format(len(alive_ips)))
        return alive_ips
