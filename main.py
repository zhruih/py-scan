import argparse
import time
from goscan.utils.target_parser import parse_targets
from goscan.core.discovery import Discovery

def banner():
    print("""
    #######################################
    #           Py-Internal-Scan          #
    #   专注于内网大网段优化扫描 (Python版) #
    #######################################
    """)

def main():
    banner()
    parser = argparse.ArgumentParser(description="Python Internal Network Scanner")
    parser.add_argument("-i", "--ip", help="Target IP range (e.g. 192.168.1.0/24)", required=True)
    parser.add_argument("-t", "--threads", type=int, default=1000, help="Number of threads (default: 1000)")
    parser.add_argument("--timeout", type=float, default=0.3, help="Socket timeout (default: 0.3)")

    args = parser.parse_args()

    # 1. 解析目标
    all_ips = parse_targets(args.ip)
    if not all_ips:
        print("[!] No valid targets found.")
        return

    start_time = time.time()
    
    # 2. 存活探测 (大网段算法优化的核心：先找活的)
    discovery = Discovery(timeout=args.timeout)
    alive_hosts = discovery.run(all_ips, threads=args.threads)

    print(f"\n[+] Discovery finished. Found {len(alive_hosts)} alive hosts.")
    for host in alive_hosts:
        print(f"  -> {host}")

    # 3. 接下来可以在这里针对 alive_hosts 进行端口扫描或漏洞检测
    
    end_time = time.time()
    print(f"\n[*] Total time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
