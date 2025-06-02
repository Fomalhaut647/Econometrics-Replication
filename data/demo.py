#!/usr/bin/env python3
"""
演示脚本，展示 NJ-PA 最低工资分析的关键结果
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from check import read_data, calculate_derived_variables

def main():
    print("=" * 60) # 打印分隔线
    print("NJ-PA 最低工资研究 - 关键结果") # 打印标题
    print("=" * 60) # 打印分隔线
    
    # 加载和处理数据
    df = read_data() # 读取数据文件，自动查找
    if df is None: # 如果数据加载失败
        print("Error: Could not load data file") # 打印错误信息
        return # 返回
    
    df = calculate_derived_variables(df) # 计算衍生变量
    
    print(f"总观测数: {len(df)}") # 打印总观测数
    print(f"NJ 商店: {df['nj'].sum()}") # 打印新泽西州的商店数量
    print(f"PA 商店: {len(df) - df['nj'].sum()}") # 打印宾夕法尼亚州的商店数量
    
    # 按州划分的汇总统计
    print("\n" + "=" * 60) # 打印分隔线
    print("按州划分的就业变化") # 打印标题
    print("=" * 60) # 打印分隔线
    
    # 创建用于分析的子集 (具有有效就业数据的商店)
    analysis_df = df.copy() # 复制 DataFrame
    analysis_df = analysis_df.dropna(subset=['DEMP']) # 删除 DEMP 缺失的行
    analysis_df = analysis_df[(analysis_df['CLOSED'] == 1) | 
                             ((analysis_df['CLOSED'] == 0) & analysis_df['dwage'].notna())] # 筛选出关闭或工资变化不缺失的商店
    
    print(f"分析样本: {len(analysis_df)} 家商店") # 打印分析样本大小
    
    # 按州划分的汇总
    summary = analysis_df.groupby('nj')[['EMPTOT', 'EMPTOT2', 'DEMP', 'WAGE_ST', 'WAGE_ST2']].agg({
        'EMPTOT': ['count', 'mean'], # 计算 EMPTOT 的计数和均值
        'EMPTOT2': 'mean', # 计算 EMPTOT2 的均值
        'DEMP': 'mean', # 计算 DEMP 的均值
        'WAGE_ST': 'mean', # 计算 WAGE_ST 的均值
        'WAGE_ST2': 'mean' # 计算 WAGE_ST2 的均值
    }).round(2) # 四舍五入到小数点后两位
    
    print("\n按州划分 (0=PA, 1=NJ):") # 打印子标题
    print(summary) # 打印汇总结果
    
    # 关键回归结果
    print("\n" + "=" * 60) # 打印分隔线
    print("关键回归结果") # 打印标题
    print("=" * 60) # 打印分隔线
    
    # 主要的差中之差结果
    try:
        model = smf.ols('DEMP ~ nj', data=analysis_df).fit() # 拟合回归模型
        coeff = model.params['nj'] # 获取 nj 的系数
        pvalue = model.pvalues['nj'] # 获取 nj 的 P 值
        se = model.bse['nj'] # 获取 nj 的标准误
        
        print(f"\n主要结果 - 就业变化 (NJ vs PA):") # 打印子标题
        print(f"系数: {coeff:.3f}") # 打印系数
        print(f"标准误: {se:.3f}") # 打印标准误
        print(f"P-值: {pvalue:.3f}") # 打印 P 值
        print(f"95% 置信区间: [{coeff - 1.96*se:.3f}, {coeff + 1.96*se:.3f}]") # 打印置信区间
        
        if pvalue < 0.05: # 如果 P 值小于 0.05
            print("结果: 在 5% 水平上统计显著") # 打印显著性信息
        else: # 否则
            print("结果: 在 5% 水平上不统计显著") # 打印非显著性信息
            
    except Exception as e: # 捕获异常
        print(f"回归错误: {e}") # 打印错误信息
    
    # 商店关闭分析
    print("\n" + "=" * 60) # 打印分隔线
    print("商店关闭") # 打印标题
    print("=" * 60) # 打印分隔线
    
    closed_stores = df[df['CLOSED'] == 1] # 筛选出关闭的商店
    if not closed_stores.empty: # 如果有关闭的商店
        print(f"总共关闭的商店: {len(closed_stores)}") # 打印关闭商店总数
        closure_by_state = closed_stores.groupby('nj').size() # 按州分组计算关闭数量
        print("按州划分的关闭数:") # 打印子标题
        for state, count in closure_by_state.items(): # 遍历关闭数量
            state_name = "NJ" if state == 1 else "PA" # 获取州名
            print(f"  {state_name}: {count}") # 打印按州划分的关闭数
    else: # 如果没有关闭的商店
        print("数据中未找到商店关闭信息") # 打印信息
    
    # 连锁店分布
    print("\n" + "=" * 60) # 打印分隔线
    print("样本构成") # 打印标题
    print("=" * 60) # 打印分隔线
    
    chain_names = {1: 'Burger King', 2: 'KFC', 3: "Roy Rogers", 4: "Wendy's"} # 连锁店名称映射
    chain_counts = df['CHAINr'].value_counts().sort_index() # 计算连锁店数量并按索引排序
    
    print("按连锁店划分的商店:") # 打印子标题
    for chain_id, count in chain_counts.items(): # 遍历连锁店数量
        if chain_id in chain_names: # 如果连锁店 ID 在映射中
            print(f"  {chain_names[chain_id]}: {count}") # 打印连锁店名称和数量
    
    print("\n" + "=" * 60) # 打印分隔线
    print("分析完成") # 打印完成信息
    print("运行 'python check.py' 获取完整的详细分析") # 打印提示信息
    print("=" * 60) # 打印分隔线

if __name__ == "__main__":
    main() # 如果作为主程序运行，调用 main() 