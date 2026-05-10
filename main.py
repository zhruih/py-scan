# -*- coding: utf-8 -*-
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
    parser.add_argument("--mode", choices=["host", "network"], default="host", help="Scan mode: host (ping all IPs) or network (sampling /24 subnets)")

    args = parser.parse_args()

    start_time = time.time()
    discovery = Discovery(timeout=args.timeout)

    if args.mode == "network":
        # 针对大网段的优化：抽样探测存活的C段
        alive_subnets = discovery.detect_networks(args.ip, threads=args.threads)
        print("\n[+] Found {} active C-class networks:".format(len(alive_subnets)))
        for net in alive_subnets:
            print("  -> {}".format(net))
    else:
        # 1. 解析目标
        all_ips = parse_targets(args.ip)
        if not all_ips:
            print("[!] No valid targets found.")
            return

        # 2. 存活探测
        alive_hosts = discovery.run(all_ips, threads=args.threads)

        print("\n[+] Discovery finished. Found {} alive hosts.".format(len(alive_hosts)))
        for host in alive_hosts:
            print("  -> {}".format(host))
    
    end_time = time.time()
    print("\n[*] Total time: {:.2f} seconds.".format(end_time - start_time))

if __name__ == "__main__":
    main()
