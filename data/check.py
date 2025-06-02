#!/usr/bin/env python3
"""
检查程序，用于输入和检查数据
check.sas 的 Python 版本
输入 NJ-PA 数据的平面文件并进行检查
"""

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path
import os

def read_data(file_path=None):
    """
    读取包含 SAS 程序中定义的所有变量的平面数据文件
    如果没有提供 file_path，将自动查找数据文件
    """
    # 根据 SAS INPUT 语句定义列名
    columns = [
        'SHEET', 'CHAINr', 'CO_OWNED', 'STATEr', 'SOUTHJ', 'CENTRALJ', 'NORTHJ',
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEAL', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2',
        'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    # 如果没有提供文件路径，自动查找数据文件
    if file_path is None:
        file_path = find_data_file()
        if file_path is None:
            print("Error: 未找到数据文件") # 打印错误信息
            return None
    
    try:
        # 首先尝试读取为分隔符为多个空格的值
        df = pd.read_csv(file_path, sep=r'\s+', names=columns, header=None)
        
        # 在可能的情况下转换为数值类型，将 '.' 替换为 NaN
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except:
        # 如果失败，尝试逗号分隔
        try:
            df = pd.read_csv(file_path, names=columns, header=None)
            
            # 在可能的情况下转换为数值类型，将 '.' 替换为 NaN
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except:
            print(f"Error reading file {file_path}") # 打印错误信息
            return None

def find_data_file():
    """
    查找数据文件，支持多种路径和文件名
    """
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 可能的文件名
    possible_files = ['public.dat', 'FLAT', 'data.txt', 'njpa_data.txt', 'flat_data.txt']
    
    # 可能的目录位置
    possible_dirs = [
        script_dir,  # 当前脚本目录
        os.path.join(script_dir, 'data'),  # 脚本目录下的 data 子目录
        os.path.join(script_dir, '..', 'data'),  # 脚本父目录下的 data 目录
        os.getcwd(),  # 当前工作目录
        os.path.join(os.getcwd(), 'data'),  # 当前工作目录下的 data 子目录
    ]
    
    # 在各个可能的位置查找数据文件
    for directory in possible_dirs:
        if os.path.exists(directory):
            for filename in possible_files:
                file_path = os.path.join(directory, filename)
                if os.path.exists(file_path):
                    return file_path
    
    return None

def calculate_derived_variables(df):
    """
    计算 SAS 程序中定义的衍生变量
    """
    # 就业总数
    df['EMPTOT'] = df['EMPPT'] * 0.5 + df['EMPFT'] + df['NMGRS']
    df['EMPTOT2'] = df['EMPPT2'] * 0.5 + df['EMPFT2'] + df['NMGRS2']
    df['DEMP'] = df['EMPTOT2'] - df['EMPTOT']
    
    # 就业百分比变化
    df['PCHEMPC'] = 2 * (df['EMPTOT2'] - df['EMPTOT']) / (df['EMPTOT2'] + df['EMPTOT'])
    df.loc[df['EMPTOT2'] == 0, 'PCHEMPC'] = -1 # 如果 EMPTOT2 为 0，设置 PCHEMPC 为 -1
    
    # 工资变化
    df['dwage'] = df['WAGE_ST2'] - df['WAGE_ST']
    df['PCHWAGE'] = (df['WAGE_ST2'] - df['WAGE_ST']) / df['WAGE_ST']
    
    # Gap 计算
    df['gap'] = 0.0
    mask_state = df['STATEr'] != 0 # 新泽西州的掩码
    mask_wage_high = df['WAGE_ST'] >= 5.05 # 工资高于或等于 5.05 的掩码
    mask_wage_pos = df['WAGE_ST'] > 0 # 工资大于 0 的掩码
    
    df.loc[mask_state & ~mask_wage_high & mask_wage_pos, 'gap'] = (5.05 - df['WAGE_ST']) / df['WAGE_ST'] # 计算差距
    df.loc[~mask_wage_pos, 'gap'] = np.nan # 工资非正数时设置为 NaN
    
    # 创建指示变量
    df['nj'] = df['STATEr'] # 新泽西州指示变量
    df['bk'] = (df['CHAINr'] == 1).astype(int) # Burger King 指示变量
    df['kfc'] = (df['CHAINr'] == 2).astype(int) # KFC 指示变量
    df['roys'] = (df['CHAINr'] == 3).astype(int) # Roy Rogers 指示变量
    df['wendys'] = (df['CHAINr'] == 4).astype(int) # Wendy's 指示变量
    
    # 餐食价格
    df['PMEAL'] = df['PSODA'] + df['PFRY'] + df['PENTREE'] # 第一轮餐食价格总和
    df['PMEAL2'] = df['PSODA2'] + df['PFRY2'] + df['PENTREE2'] # 第二轮餐食价格总和
    df['DPMEAL'] = df['PMEAL2'] - df['PMEAL'] # 餐食价格变化
    
    # 商店状态
    df['CLOSED'] = (df['STATUS2'] == 3).astype(int) # 关闭商店指示变量
    
    # 全职比例
    df['FRACFT'] = df['EMPFT'] / df['EMPTOT'] # 第一轮全职比例
    df['FRACFT2'] = np.where(df['EMPTOT2'] > 0, df['EMPFT2'] / df['EMPTOT2'], np.nan) # 第二轮全职比例 (EMP2>0 时)
    
    # 工资指示变量
    df['ATMIN'] = (df['WAGE_ST'] == 4.25).astype(int) # 第一轮工资等于 4.25 的指示变量
    df['NEWMIN'] = (df['WAGE_ST2'] == 5.05).astype(int) # 第二轮工资等于 5.05 的指示变量
    
    # 创建 ICODE
    conditions = [
        df['nj'] == 0, # PA 商店
        (df['nj'] == 1) & (df['WAGE_ST'] == 4.25), # NJ 商店，低工资
        (df['nj'] == 1) & (df['WAGE_ST'] >= 5.00), # NJ 商店，高工资
        (df['nj'] == 1) & (df['WAGE_ST'] > 4.25) & (df['WAGE_ST'] < 5.00) # NJ 商店，中工资
    ]
    choices = [
        'PA STORE          ',
        'NJ STORE, LOW-WAGE',
        'NJ STORE, HI-WAGE',
        'NJ STORE, MED-WAGE'
    ]
    df['ICODE'] = np.select(conditions, choices, default='NJ STORE, BAD WAGE') # 根据条件设置 ICODE
    
    return df

def frequency_tables(df):
    """
    生成频率表 (相当于 PROC FREQ)
    """
    print("=" * 80) # 打印分隔线
    print("FREQUENCY TABLES") # 打印标题
    print("=" * 80) # 打印分隔线
    
    freq_vars = ['CHAINr', 'STATEr', 'TYPE2', 'STATUS2', 'BONUS', 'SPECIAL2', 'CO_OWNED', 'MEAL', 'MEALS2']
    
    for var in freq_vars: # 遍历变量列表
        if var in df.columns: # 如果变量存在于 DataFrame 中
            print(f"\nFrequency table for {var}:") # 打印变量的频率表标题
            print(df[var].value_counts().sort_index()) # 打印频率表

def descriptive_statistics(df):
    """
    生成描述性统计 (相当于 PROC MEANS)
    """
    print("\n" + "=" * 80) # 打印分隔线
    print("DESCRIPTIVE STATISTICS") # 打印标题
    print("=" * 80) # 打印分隔线
    
    # 第一组变量
    vars1 = ['EMPFT', 'EMPPT', 'NMGRS', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST', 'WAGE_ST2',
             'PCTAFF', 'OPEN', 'OPEN2R', 'HRSOPEN', 'HRSOPEN2',
             'PSODA', 'PFRY', 'PENTREE', 'PSODA2', 'PFRY2', 'PENTREE2',
             'NREGS', 'NREGS11', 'NREGS2', 'NREGS112',
             'SOUTHJ', 'CENTRALJ', 'NORTHJ', 'PA1', 'PA2']
    
    print("\n基本就业和运营变量:") # 打印子标题
    available_vars1 = [var for var in vars1 if var in df.columns] # 筛选出存在的变量
    if available_vars1: # 如果有存在的变量
        print(df[available_vars1].describe()) # 打印描述性统计
    
    # 第二组变量
    vars2 = ['EMPTOT', 'EMPTOT2', 'DEMP', 'PCHEMPC', 'gap', 'PMEAL', 'PMEAL2', 'DPMEAL']
    print(f"\n衍生就业和变化变量:") # 打印子标题
    available_vars2 = [var for var in vars2 if var in df.columns] # 筛选出存在的变量
    if available_vars2: # 如果有存在的变量
        print(df[available_vars2].describe()) # 打印描述性统计
    
    # 第三组变量
    vars3 = ['bk', 'kfc', 'roys', 'wendys', 'CO_OWNED',
             'EMPTOT', 'FRACFT', 'WAGE_ST', 'ATMIN', 'NEWMIN', 'PMEAL', 'HRSOPEN', 'BONUS',
             'EMPTOT2', 'FRACFT2', 'WAGE_ST2', 'PMEAL2', 'HRSOPEN2', 'SPECIAL2']
    
    print(f"\n连锁店指示变量和综合变量:") # 打印子标题
    available_vars3 = [var for var in vars3 if var in df.columns] # 筛选出存在的变量
    if available_vars3: # 如果有存在的变量
        print(df[available_vars3].describe()) # 打印描述性统计

def statistics_by_group(df):
    """
    按 NJ 和 ICODE 分组生成统计数据
    """
    print("\n" + "=" * 80) # 打印分隔线
    print("TABLE 2 - STATISTICS BY NJ") # 打印标题
    print("=" * 80) # 打印分隔线
    
    vars_table2 = ['bk', 'kfc', 'roys', 'wendys', 'CO_OWNED',
                   'EMPTOT', 'FRACFT', 'WAGE_ST', 'ATMIN', 'NEWMIN', 'PMEAL', 'HRSOPEN', 'BONUS',
                   'EMPTOT2', 'FRACFT2', 'WAGE_ST2', 'PMEAL2', 'HRSOPEN2', 'SPECIAL2']
    
    available_vars_table2 = [var for var in vars_table2 if var in df.columns] # 筛选出存在的变量
    if available_vars_table2: # 如果有存在的变量
        grouped_stats = df.groupby('nj')[available_vars_table2].describe() # 按 NJ 分组并计算描述性统计
        print(grouped_stats) # 打印统计结果
    
    print("\n" + "=" * 80) # 打印分隔线
    print("PART OF TABLE 3 - EMPLOYMENT CHANGES BY NJ") # 打印标题
    print("=" * 80) # 打印分隔线
    
    change_vars = ['EMPTOT', 'EMPTOT2', 'DEMP', 'PCHEMPC', 'gap', 'PMEAL', 'PMEAL2', 'DPMEAL'] # 变化变量列表
    available_change_vars = [var for var in change_vars if var in df.columns] # 筛选出存在的变量
    if available_change_vars: # 如果有存在的变量
        nj_stats = df.groupby('nj')[available_change_vars].describe() # 按 NJ 分组并计算描述性统计
        print(nj_stats) # 打印统计结果
    
    print("\n" + "=" * 80) # 打印分隔线
    print("PART OF TABLE 3 - EMPLOYMENT CHANGES BY ICODE") # 打印标题
    print("=" * 80) # 打印分隔线
    
    if available_change_vars: # 如果有存在的变量
        icode_stats = df.groupby('ICODE')[available_change_vars].describe() # 按 ICODE 分组并计算描述性统计
        print(icode_stats) # 打印统计结果

def closed_stores_analysis(df):
    """
    关闭商店分析
    """
    print("\n" + "=" * 80) # 打印分隔线
    print("LISTING OF STORES THAT CLOSED") # 打印标题
    print("=" * 80) # 打印分隔线
    
    closed = df[df['CLOSED'] == 1] # 筛选出关闭的商店
    if not closed.empty: # 如果有关闭的商店
        print(closed[['SHEET', 'EMPTOT', 'EMPTOT2', 'STATUS2']]) # 打印相关信息
    else:
        print("No closed stores found") # 如果没有关闭的商店

def regression_analysis(df):
    """
    执行回归分析 (相当于 PROC REG)
    """
    print("\n" + "=" * 80) # 打印分隔线
    print("TABLE 4 - REGRESSION ANALYSIS") # 打印标题
    print("=" * 80) # 打印分隔线
    
    # 创建用于回归分析的子集
    c1 = df.copy() # 复制 DataFrame
    c1 = c1.dropna(subset=['DEMP']) # 删除 DEMP 缺失的行
    c1 = c1[(c1['CLOSED'] == 1) | ((c1['CLOSED'] == 0) & c1['dwage'].notna())] # 筛选出关闭或工资变化不缺失的商店
    
    print(f"Subset of stores with valid wages 2 waves (or closed W-2): {len(c1)} observations") # 打印子集大小
    
    if len(c1) == 0: # 如果子集为空
        print("No valid observations for regression analysis") # 打印信息
        return # 返回
    
    # 模型 1: DEMP = GAP
    try:
        model1 = smf.ols('DEMP ~ gap', data=c1).fit() # 拟合模型
        print("\nModel 1: DEMP = GAP") # 打印模型标题
        print(model1.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 1: {e}") # 打印错误信息
    
    # 模型 2: DEMP = GAP + BK + KFC + ROYS + CO_OWNED
    try:
        model2 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=c1).fit() # 拟合模型
        print("\nModel 2: DEMP = GAP + BK + KFC + ROYS + CO_OWNED") # 打印模型标题
        print(model2.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 2: {e}") # 打印错误信息
    
    # 模型 3: DEMP = GAP + BK + KFC + ROYS + CENTRALJ + SOUTHJ + PA1 + PA2
    try:
        model3 = smf.ols('DEMP ~ gap + bk + kfc + roys + CENTRALJ + SOUTHJ + PA1 + PA2', data=c1).fit() # 拟合模型
        print("\nModel 3: DEMP = GAP + BK + KFC + ROYS + CENTRALJ + SOUTHJ + PA1 + PA2") # 打印模型标题
        print(model3.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 3: {e}") # 打印错误信息
    
    # 模型 4: DEMP = NJ
    try:
        model4 = smf.ols('DEMP ~ nj', data=c1).fit() # 拟合模型
        print("\nModel 4: DEMP = NJ") # 打印模型标题
        print(model4.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 4: {e}") # 打印错误信息
    
    # 模型 5: DEMP = NJ + BK + KFC + ROYS + CO_OWNED
    try:
        model5 = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=c1).fit() # 拟合模型
        print("\nModel 5: DEMP = NJ + BK + KFC + ROYS + CO_OWNED") # 打印模型标题
        print(model5.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 5: {e}") # 打印错误信息
    
    # 使用就业百分比变化的附加模型
    print("\n" + "=" * 80) # 打印分隔线
    print("MODELS NOT SHOWN IN TABLE 4 USING PERCENT CHG EMP") # 打印标题
    print("=" * 80) # 打印分隔线
    
    # 模型 6: PCHEMPC = GAP
    try:
        model6 = smf.ols('PCHEMPC ~ gap', data=c1).fit() # 拟合模型
        print("\nModel 6: PCHEMPC = GAP") # 打印模型标题
        print(model6.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 6: {e}") # 打印错误信息
    
    # 模型 7: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED
    try:
        model7 = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=c1).fit() # 拟合模型
        print("\nModel 7: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED") # 打印模型标题
        print(model7.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 7: {e}") # 打印错误信息
    
    # 模型 8: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2
    try:
        model8 = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2', data=c1).fit() # 拟合模型
        print("\nModel 8: PCHEMPC = GAP + BK + KFC + ROYS + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2") # 打印模型标题
        print(model8.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 8: {e}") # 打印错误信息
    
    # 模型 9: PCHEMPC = NJ
    try:
        model9 = smf.ols('PCHEMPC ~ nj', data=c1).fit() # 拟合模型
        print("\nModel 9: PCHEMPC = NJ") # 打印模型标题
        print(model9.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 9: {e}") # 打印错误信息
    
    # 模型 10: PCHEMPC = NJ + BK + KFC + ROYS + CO_OWNED
    try:
        model10 = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=c1).fit() # 拟合模型
        print("\nModel 10: PCHEMPC = NJ + BK + KFC + ROYS + CO_OWNED") # 打印模型标题
        print(model10.summary()) # 打印模型摘要
    except Exception as e: # 捕获异常
        print(f"Error in Model 10: {e}") # 打印错误信息

def main():
    """
    运行完整分析的主函数
    """
    print("INPUT FLAT DATA FILE OF NJ-PA DATA AND CHECK") # 打印标题
    print("=" * 80) # 打印分隔线
    
    # 读取和处理数据
    df = read_data() # 读取数据
    if df is None: # 如果读取数据失败
        return # 返回
    
    print(f"数据加载成功") # 打印成功信息
    print(f"Number of observations: {len(df)}") # 打印观测数量
    
    # 计算衍生变量
    df = calculate_derived_variables(df) # 计算衍生变量
    
    # 执行所有分析
    frequency_tables(df) # 生成频率表
    descriptive_statistics(df) # 生成描述性统计
    statistics_by_group(df) # 按组生成统计数据
    closed_stores_analysis(df) # 分析关闭商店
    regression_analysis(df) # 执行回归分析
    
    print("\n" + "=" * 80) # 打印分隔线
    print("ANALYSIS COMPLETE") # 打印完成信息
    print("=" * 80) # 打印分隔线

if __name__ == "__main__":
    main() # 如果作为主程序运行，调用 main() 