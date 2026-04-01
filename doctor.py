#!/usr/bin/env python3
"""
Home Device Control Doctor - 诊断工具
检查各渠道状态，输出健康报告
"""

import sys
from channels import list_channels


def check():
    """检查所有渠道状态"""
    print("🩺 Home Device Control 健康检查")
    print("=" * 40)
    print()
    
    channels = list_channels()
    
    print("渠道状态:")
    print("-" * 40)
    
    all_ready = True
    
    for name, status in channels.items():
        if status.available and status.configured:
            icon = "✅"
        elif status.available and not status.configured:
            icon = "⚠️"
            all_ready = False
        else:
            icon = "❌"
            all_ready = False
        
        print(f"  {icon} {name:10} - {status.message}")
        
        if status.suggestion:
            print(f"     建议: {status.suggestion}")
    
    print()
    print("=" * 40)
    
    if all_ready:
        print("✅ 所有渠道就绪")
        return 0
    else:
        print("⚠️  部分渠道需要配置")
        return 1


if __name__ == "__main__":
    sys.exit(check())
