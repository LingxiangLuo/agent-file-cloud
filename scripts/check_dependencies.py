#!/usr/bin/env python3
"""
检查依赖是否完整
"""

import sys
import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
REQUIREMENTS_FILE = SKILL_DIR / "requirements.txt"


def check_dependencies():
    """检查依赖"""
    print("📦 依赖检查:\n")
    
    required = {
        'numpy': '向量计算',
        'qiniu': '七牛云上传'
    }
    
    optional = {
        'networkx': '图谱分析',
        'faiss': '向量索引加速',
        'dashscope': '阿里云 SDK',
        'openai': 'OpenAI API'
    }
    
    missing_required = []
    missing_optional = []
    installed = []
    
    for pkg, desc in required.items():
        try:
            __import__(pkg)
            installed.append(f"{pkg} ({desc})")
        except ImportError:
            missing_required.append(f"{pkg} ({desc})")
    
    for pkg, desc in optional.items():
        try:
            __import__(pkg)
            installed.append(f"{pkg} ({desc}) [可选]")
        except ImportError:
            missing_optional.append(f"{pkg} ({desc})")
    
    # 显示结果
    if installed:
        print("✅ 已安装:")
        for pkg in installed:
            print(f"   - {pkg}")
        print()
    
    if missing_required:
        print("❌ 缺少必需依赖:")
        for pkg in missing_required:
            print(f"   - {pkg}")
        print()
        print("安装命令:")
        print(f"   pip3 install {' '.join([m.split()[0] for m in missing_required])}")
        print()
        return False
    
    if missing_optional:
        print("⚠️  缺少可选依赖:")
        for pkg in missing_optional:
            print(f"   - {pkg}")
        print()
        print("安装命令（可选）:")
        print(f"   pip3 install {' '.join([m.split()[0] for m in missing_optional])}")
        print()
    
    print("✅ 所有必需依赖已安装")
    return True


def check_config():
    """检查配置"""
    print("\n⚙️  配置检查:\n")
    
    config_file = SKILL_DIR / "config" / "config.json"
    if not config_file.exists():
        print("❌ config.json 不存在")
        return False
    
    with open(config_file) as f:
        config = json.load(f)
    
    # 检查 API Key
    api_key = config.get('api', {}).get('dashscope_api_key')
    if api_key:
        print(f"✅ DashScope API Key: 已配置 ({api_key[:15]}...)")
    else:
        print("⚠️  DashScope API Key: 未配置（将使用降级模式）")
    
    # 检查七牛云配置
    qiniu = config.get('qiniu', {})
    if qiniu.get('access_key') and qiniu.get('secret_key'):
        print(f"✅ 七牛云配置：已配置 (bucket: {qiniu.get('bucket')})")
    else:
        print("⚠️  七牛云配置：未配置（无法上传云端）")
    
    return True


def main():
    """主函数"""
    print("="*60)
    print("Agent File Cloud - 依赖和配置检查")
    print("="*60)
    print()
    
    dep_ok = check_dependencies()
    config_ok = check_config()
    
    print()
    print("="*60)
    if dep_ok and config_ok:
        print("✅ 系统就绪！")
    elif dep_ok:
        print("⚠️  依赖完整，配置不完整（部分功能受限）")
    else:
        print("❌ 系统未就绪，请先安装必需依赖")
    print("="*60)
    
    return 0 if dep_ok else 1


if __name__ == "__main__":
    sys.exit(main())
