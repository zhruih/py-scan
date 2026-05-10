# -*- coding: utf-8 -*-
import socket
import concurrent.futures
import time
import random
import sys

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

    def detect_networks(self, network_cidr, threads=1000):
        """
        探测网段内存活的网段 (最小发包原则：每个C段抽样)
        采用递归二分法 + 抽样的方式处理大网段 (如 /8)
        """
        import ipaddress
        main_net = ipaddress.ip_network(network_cidr, strict=False)
        
        # 对于 /8, /7 等大网段，先进行 /16 级别的抽样探测
        if main_net.prefixlen <= 16:
            return self._detect_large_networks(main_net, threads)
        else:
            return self._detect_networks_direct(main_net, threads)
    
    def _detect_large_networks(self, main_net, threads=1000):
        """处理 /16 以上的大网段：先抽样 /16，再细化"""
        import ipaddress
        import queue
        import threading
        
        # 将大网段拆分为 /16 子网进行抽样
        subnets_16 = list(main_net.subnets(new_prefix=16))
        print("[*] Large network detected. Sampling {} /16 subnets from {}.".format(len(subnets_16), main_net))
        
        alive_subnets = []
        task_queue = queue.Queue()
        results_queue = queue.Queue()
        
        # 放入所有 /16 任务
        for subnet in subnets_16:
            task_queue.put(subnet)
        
        def check_subnet_16_worker():
            """处理 /16 采样的工作线程"""
            while True:
                try:
                    subnet = task_queue.get_nowait()
                except queue.Empty:
                    break
                
                # /16 子网采样：48 个采样点 - 更激进的覆盖
                # 每65536/48 ≈ 1365个地址采样一个点，确保高覆盖率
                samples = [
                    1, 2, 5, 8, 10, 15, 20, 25, 30, 35, 40, 50, 
                    60, 70, 75, 85, 90, 100, 110, 120, 128, 140, 150, 165,
                    180, 200, 210, 220, 230, 240, 245, 250, 254, 255,
                    256//8, 256//6, 256//5, 256//4, 256//3, 256*2//5,
                    256*2//3, 256*3//4, 256*5//8, 256*3//5
                ]
                for i in samples:
                    try:
                        ip = str(subnet[i])
                        if self.is_alive(ip):
                            results_queue.put(str(subnet))
                            break
                    except:
                        pass
        
        # 启动固定数量的工作线程处理 /16
        num_workers = min(threads, 50)  # /16 级别也用队列模式，50个线程足够
        workers = []
        for _ in range(num_workers):
            t = threading.Thread(target=check_subnet_16_worker, daemon=True)
            t.start()
            workers.append(t)
        
        # 等待所有工作线程完成
        for t in workers:
            t.join(timeout=600)
        
        # 收集所有 /16 发现结果
        while not results_queue.empty():
            try:
                res = results_queue.get_nowait()
                alive_subnets.append(res)
                sys.stdout.write("[+] Active /16 Found: {:<18}\r".format(res))
                sys.stdout.flush()
            except queue.Empty:
                break
        
        print("\n[+] Found {} active /16 subnets. Refining to /24...".format(len(alive_subnets)))
        
        # 对每个活跃的 /16 进一步细化到 /24
        # 关键改进：按顺序处理每个 /16，而不是一次性提交所有 /24 任务
        final_alive = []
        for subnet_16 in alive_subnets:
            refined = self._detect_networks_direct(ipaddress.ip_network(subnet_16, strict=False), threads)
            final_alive.extend(refined)
        
        print("[+] Network discovery finished. Found {} active /24 subnets.".format(len(final_alive)))
        return final_alive
    
    def _detect_networks_direct(self, main_net, threads=1000):
        """直接探测 /24 网段 - 使用简单队列而非 concurrent.futures"""
        import ipaddress
        import queue
        import threading
        
        subnets = list(main_net.subnets(new_prefix=24))
        
        if main_net.prefixlen < 24:
            print("[*] Split {} into {} /24 subnets.".format(main_net, len(subnets)))
        
        alive_subnets = []
        task_queue = queue.Queue()
        results_queue = queue.Queue()
        lock = threading.Lock()
        
        # 放入所有任务
        for subnet in subnets:
            task_queue.put(subnet)
        
        def worker():
            """工作线程函数"""
            while True:
                try:
                    subnet = task_queue.get_nowait()
                except queue.Empty:
                    break
                
                # 检查子网
                samples = [1, 2, 254, 255]
                max_host = subnet.num_addresses - 1
                for i in samples:
                    if i <= max_host:
                        try:
                            ip = str(subnet[i])
                            if self.is_alive(ip):
                                results_queue.put(str(subnet))
                                break
                        except:
                            pass
        
        # 启动固定数量的工作线程
        num_workers = min(threads, 30)
        workers = []
        for _ in range(num_workers):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            workers.append(t)
        
        # 等待所有工作线程完成
        for t in workers:
            t.join(timeout=600)  # 10分钟超时
        
        # 收集所有结果
        while not results_queue.empty():
            try:
                res = results_queue.get_nowait()
                alive_subnets.append(res)
                sys.stdout.write("[+] Active Subnet: {:<18}\r".format(res))
                sys.stdout.flush()
            except queue.Empty:
                break
        
        return alive_subnets

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
