#!/usr/bin/env python3
"""
check.py 的测试脚本
"""

import os
import sys
from pathlib import Path

def test_data_exists():
    """
    测试数据文件是否存在
    """
    data_files = ['public.dat', 'FLAT', 'data.txt', 'njpa_data.txt', 'flat_data.txt'] # 可能的数据文件名列表
    found_files = [] # 找到的文件列表
    
    for filename in data_files: # 遍历文件名列表
        if Path(filename).exists(): # 如果文件存在
            found_files.append(filename) # 添加到找到的文件列表
    
    if found_files: # 如果找到文件
        print(f"✓ 找到数据文件: {', '.join(found_files)}") # 打印成功信息
        return True # 返回 True
    else: # 否则
        print("✗ 未找到数据文件") # 打印错误信息
        return False # 返回 False

def test_imports():
    """
    测试是否可以导入所有必需的包
    """
    try:
        import pandas as pd
        print("✓ pandas 导入成功") # 打印成功信息
    except ImportError: # 捕获导入错误
        print("✗ pandas 不可用") # 打印错误信息
        return False # 返回 False
    
    try:
        import numpy as np
        print("✓ numpy 导入成功") # 打印成功信息
    except ImportError: # 捕获导入错误
        print("✗ numpy 不可用") # 打印错误信息
        return False # 返回 False
    
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        print("✓ statsmodels 导入成功") # 打印成功信息
    except ImportError: # 捕获导入错误
        print("✗ statsmodels 不可用") # 打印错误信息
        return False # 返回 False
    
    try:
        from scipy import stats
        print("✓ scipy 导入成功") # 打印成功信息
    except ImportError: # 捕获导入错误
        print("✗ scipy 不可用") # 打印错误信息
        return False # 返回 False
    
    return True # 所有导入都成功，返回 True

def test_check_module():
    """
    测试是否可以导入 check.py 模块
    """
    try:
        import check
        print("✓ check.py 模块导入成功") # 打印成功信息
        return True # 返回 True
    except ImportError as e: # 捕获导入错误
        print(f"✗ 导入 check.py 时出错: {e}") # 打印错误信息
        return False # 返回 False

def run_quick_test():
    """
    运行快速测试，验证主要功能是否正常工作
    """
    try:
        import check
        
        # 测试数据读取函数
        if Path('public.dat').exists(): # 如果数据文件存在
            df = check.read_data('public.dat') # 读取数据
            if df is not None: # 如果数据读取成功
                print(f"✓ 数据加载成功: {len(df)} 行, {len(df.columns)} 列") # 打印成功信息
                
                # 测试变量创建
                df = check.calculate_derived_variables(df) # 计算衍生变量
                print("✓ 衍生变量计算成功") # 打印成功信息
                
                # 检查关键变量是否存在
                key_vars = ['EMPTOT', 'DEMP', 'PCHEMPC', 'gap', 'nj', 'bk', 'kfc', 'roys', 'wendys'] # 关键变量列表
                missing_vars = [var for var in key_vars if var not in df.columns] # 查找缺失的变量
                
                if not missing_vars: # 如果没有缺失变量
                    print("✓ 所有关键衍生变量已创建") # 打印成功信息
                    return True # 返回 True
                else: # 否则
                    print(f"✗ 缺失变量: {missing_vars}") # 打印错误信息
                    return False # 返回 False
            else: # 如果数据读取失败
                print("✗ 数据加载失败") # 打印错误信息
                return False # 返回 False
        else: # 如果数据文件不存在
            print("⚠ 未找到数据文件进行测试") # 打印警告信息
            return True # 返回 True (在这种情况下数据不存在是预期行为)
    except Exception as e: # 捕获异常
        print(f"✗ 测试期间出错: {e}") # 打印错误信息
        return False # 返回 False

def main():
    """
    主测试函数
    """
    print("正在测试 check.py 程序...") # 打印测试开始信息
    print("=" * 50) # 打印分隔线
    
    # 测试 1: 检查导入
    print("\n1. 正在测试包导入:") # 打印测试阶段信息
    imports_ok = test_imports() # 运行导入测试
    
    # 测试 2: 检查数据文件
    print("\n2. 正在测试数据文件可用性:") # 打印测试阶段信息
    data_ok = test_data_exists() # 运行数据文件测试
    
    # 测试 3: 检查模块导入
    print("\n3. 正在测试 check.py 模块:") # 打印测试阶段信息
    module_ok = test_check_module() # 运行模块导入测试
    
    # 测试 4: 快速功能测试
    print("\n4. 快速功能测试:") # 打印测试阶段信息
    if imports_ok and module_ok: # 如果导入和模块导入都成功
        func_ok = run_quick_test() # 运行快速功能测试
    else: # 否则
        func_ok = False # 功能测试失败
        print("⚠ 由于之前的失败，跳过功能测试") # 打印警告信息
    
    # 总结
    print("\n" + "=" * 50) # 打印分隔线
    print("测试总结:") # 打印总结标题
    print(f"导入: {'✓ PASS' if imports_ok else '✗ FAIL'}") # 打印导入测试结果
    print(f"数据文件: {'✓ PASS' if data_ok else '✗ FAIL'}") # 打印数据文件测试结果
    print(f"模块导入: {'✓ PASS' if module_ok else '✗ FAIL'}") # 打印模块导入测试结果
    print(f"功能性: {'✓ PASS' if func_ok else '✗ FAIL'}") # 打印功能测试结果
    
    if all([imports_ok, data_ok, module_ok, func_ok]): # 如果所有测试都通过
        print("\n🎉 所有测试通过！程序应该能正常工作。") # 打印成功信息
        print("运行 'python check.py' 执行完整的分析。") # 打印提示信息
    else: # 否则
        print("\n⚠ 部分测试失败。请检查要求并修复任何问题。") # 打印警告信息
        if not imports_ok: # 如果导入测试失败
            print("   - 使用以下命令安装缺少的包: pip install -r requirements.txt") # 打印安装命令提示
        if not data_ok: # 如果数据文件测试失败
            print("   - 确保数据文件 (public.dat) 位于当前目录中") # 打印数据文件位置提示

if __name__ == "__main__":
    main() # 如果作为主程序运行，调用 main() 