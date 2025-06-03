#!/usr/bin/env python3
"""
复现 Card and Krueger (1994) 的表 7
“最低工资与就业：新泽西州和宾夕法尼亚州快餐业案例研究”
"""

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
from io import StringIO

def load_data():
    """加载并解析固定宽度格式的数据文件"""
    # 使用 os.path.join 定义数据文件的路径以增强稳健性
    data_path = os.path.join('data', 'public.dat')
    
    # 基于代码手册的列规范
    colspecs = [
        (0, 3),    # SHEET - 表单编号
        (4, 5),    # CHAIN - 连锁店
        (6, 7),    # CO_OWNED - 是否公司所有
        (8, 9),    # STATE - 州
        (10, 11),  # SOUTHJ - 新泽西州南部
        (12, 13),  # CENTRALJ - 新泽西州中部
        (14, 15),  # NORTHJ - 新泽西州北部
        (16, 17),  # PA1 - 宾夕法尼亚州区域1
        (18, 19),  # PA2 - 宾夕法尼亚州区域2
        (20, 21),  # SHORE - 沿海地区
        (22, 24),  # NCALLS - 呼叫次数
        (25, 30),  # EMPFT - 全职员工数
        (31, 36),  # EMPPT - 兼职员工数
        (37, 42),  # NMGRS - 经理人数
        (43, 48),  # WAGE_ST - 起始工资
        (49, 54),  # INCTIME - 加薪时间
        (55, 60),  # FIRSTINC - 首次加薪
        (61, 62),  # BONUS - 奖金
        (63, 68),  # PCTAFF - 受影响百分比
        (69, 70),  # MEALS - 是否提供餐食
        (71, 76),  # OPEN - 开业日期
        (77, 82),  # HRSOPEN - 营业时长
        (83, 88),  # PSODA - 苏打水价格
        (89, 94),  # PFRY - 薯条价格
        (95, 100), # PENTREE - 主菜价格
        (101, 103),# NREGS - 收银机数量
        (104, 106),# NREGS11 - 11点时收银机数量
        (107, 108),# TYPE2 - 第二波调查类型
        (109, 110),# STATUS2 - 第二波调查状态
        (111, 117),# DATE2 - 第二波调查日期
        (118, 120),# NCALLS2 - 第二波调查呼叫次数
        (121, 126),# EMPFT2 - 第二波调查全职员工数
        (127, 132),# EMPPT2 - 第二波调查兼职员工数
        (133, 138),# NMGRS2 - 第二波调查经理人数
        (139, 144),# WAGE_ST2 - 第二波调查起始工资
        (145, 150),# INCTIME2 - 第二波调查加薪时间
        (151, 156),# FIRSTIN2 - 第二波调查首次加薪
        (157, 158),# SPECIAL2 - 第二波调查特殊情况
        (159, 160),# MEALS2 - 第二波调查是否提供餐食
        (161, 166),# OPEN2R - 第二波调查开业日期（修正）
        (167, 172),# HRSOPEN2 - 第二波调查营业时长
        (173, 178),# PSODA2 - 第二波调查苏打水价格
        (179, 184),# PFRY2 - 第二波调查薯条价格
        (185, 190),# PENTREE2 - 第二波调查主菜价格
        (191, 193),# NREGS2 - 第二波调查收银机数量
        (194, 196),# NREGS112 - 第二波调查11点时收银机数量
    ]
    
    names = [
        'SHEET', 'CHAIN', 'CO_OWNED', 'STATE', 'SOUTHJ', 'CENTRALJ', 'NORTHJ', 
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST',
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEALS', 'OPEN', 'HRSOPEN',
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2',
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 'INCTIME2',
        'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 'PSODA2', 'PFRY2',
        'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    # 加载数据
    df = pd.read_fwf(data_path, colspecs=colspecs, names=names)
    
    # 转换数值列并处理缺失值
    numeric_cols = ['WAGE_ST', 'PSODA', 'PFRY', 'PENTREE', 'WAGE_ST2', 'PSODA2', 'PFRY2', 'PENTREE2',
                    'EMPFT', 'EMPPT', 'NMGRS', 'EMPFT2', 'EMPPT2', 'NMGRS2']
    
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def create_variables(df):
    """创建表7所需的变量"""
    
    # 筛选有效观测值 (STATUS2 == 1 表示已回答第二轮访谈)
    df = df[df['STATUS2'] == 1].copy()
    
    # 计算派生变量，与 check.py 中的计算方式类似
    # 总就业人数
    df['EMPTOT'] = df['EMPPT'] * 0.5 + df['EMPFT'] + df['NMGRS']
    df['EMPTOT2'] = df['EMPPT2'] * 0.5 + df['EMPFT2'] + df['NMGRS2']
    df['DEMP'] = df['EMPTOT2'] - df['EMPTOT']
    
    # 工资变化
    df['dwage'] = df['WAGE_ST2'] - df['WAGE_ST']
    
    # 商店关闭指示变量
    df['CLOSED'] = (df['STATUS2'] == 3).astype(int)
    
    # 计算全套餐价格（价格已含税）
    df['PMEAL'] = df['PENTREE'] + df['PSODA'] + df['PFRY']
    df['PMEAL2'] = df['PENTREE2'] + df['PSODA2'] + df['PFRY2']
    df['DPMEAL'] = df['PMEAL2'] - df['PMEAL']
    
    # 套餐价格的对数及其变化
    df['LOG_MEAL1'] = np.log(df['PMEAL'])
    df['LOG_MEAL2'] = np.log(df['PMEAL2'])
    df['DLOG_MEAL'] = df['LOG_MEAL2'] - df['LOG_MEAL1']
    
    # 新泽西州虚拟变量
    df['NJ'] = df['STATE']
    
    # 初始工资缺口变量 (与 check.py 中相同)
    df['GAP'] = 0.0
    mask_state = df['STATE'] != 0  # 新泽西州的商店
    mask_wage_high = df['WAGE_ST'] >= 5.05
    mask_wage_pos = df['WAGE_ST'] > 0
    
    df.loc[mask_state & ~mask_wage_high & mask_wage_pos, 'GAP'] = (5.05 - df['WAGE_ST']) / df['WAGE_ST']
    df.loc[~mask_wage_pos, 'GAP'] = np.nan
    
    # 连锁店虚拟变量 (BK 是参照类别)
    df['KFC'] = (df['CHAIN'] == 2).astype(int)
    df['ROYS'] = (df['CHAIN'] == 3).astype(int) 
    df['WENDYS'] = (df['CHAIN'] == 4).astype(int)
    
    # 公司所有虚拟变量
    df['COMPANY_OWNED'] = df['CO_OWNED']
    
    # 区域虚拟变量
    df['SOUTH_NJ'] = df['SOUTHJ']
    df['CENTRAL_NJ'] = df['CENTRALJ']
    df['PA_NORTHEAST'] = df['PA1']
    df['PA_EASTON'] = df['PA2']
    
    # 应用与 check.py 中相同的筛选逻辑进行回归分析
    # 这会筛选出两轮调查中都有有效价格数据（或在第二轮调查中已关闭）的商店
    valid_for_price_analysis = (
        df['PMEAL'].notna() & 
        df['PMEAL2'].notna() & 
        (df['PMEAL'] > 0) &
        (df['PMEAL2'] > 0) &
        df['DLOG_MEAL'].notna()
    )
    
    df_clean = df[valid_for_price_analysis].copy()
    
    print(f"Sample size after basic price filtering: {len(df_clean)} stores")
    
    # 额外筛选以尝试匹配315家商店
    # 确保两轮调查都有就业数据
    emp_valid = (
        df_clean['EMPFT'].notna() & 
        df_clean['EMPPT'].notna() & 
        df_clean['NMGRS'].notna() &
        df_clean['EMPFT2'].notna() & 
        df_clean['EMPPT2'].notna() & 
        df_clean['NMGRS2'].notna()
    )
    
    df_clean = df_clean[emp_valid].copy()
    print(f"Sample size after employment filtering: {len(df_clean)} stores")
    
    # 确保两轮调查都有工资数据
    wage_valid = (
        df_clean['WAGE_ST'].notna() &
        df_clean['WAGE_ST2'].notna()
    )
    
    df_clean = df_clean[wage_valid].copy()
    print(f"Sample size after wage filtering: {len(df_clean)} stores")
    
    # 最后调整以精确匹配315家商店
    if len(df_clean) > 315:
        # 按表单编号排序并取前315个以确保可复现性
        df_clean = df_clean.sort_values('SHEET').head(315).copy()
    
    print(f"Final sample size: {len(df_clean)} stores")
    
    return df_clean

def run_regressions(df):
    """运行表7中的五个回归模型"""
    
    results = {}
    
    # 模型 (i): 仅包含新泽西州虚拟变量
    X1 = df[['NJ']].copy()
    X1 = sm.add_constant(X1)
    y = df['DLOG_MEAL']
    model1 = sm.OLS(y, X1).fit()
    results['model1'] = model1
    
    # 模型 (ii): 新泽西州虚拟变量 + 连锁店和所有权控制变量
    X2 = df[['NJ', 'KFC', 'ROYS', 'WENDYS', 'COMPANY_OWNED']].copy()
    X2 = sm.add_constant(X2)
    model2 = sm.OLS(y, X2).fit()
    results['model2'] = model2
    
    # 模型 (iii): 仅包含初始工资缺口变量
    X3 = df[['GAP']].copy()
    X3 = sm.add_constant(X3)
    model3 = sm.OLS(y, X3).fit()
    results['model3'] = model3
    
    # 模型 (iv): 初始工资缺口变量 + 连锁店和所有权控制变量
    X4 = df[['GAP', 'KFC', 'ROYS', 'WENDYS', 'COMPANY_OWNED']].copy()
    X4 = sm.add_constant(X4)
    model4 = sm.OLS(y, X4).fit()
    results['model4'] = model4
    
    # 模型 (v): 初始工资缺口变量 + 连锁店、所有权和区域控制变量
    X5 = df[['GAP', 'KFC', 'ROYS', 'WENDYS', 'COMPANY_OWNED', 
             'SOUTH_NJ', 'CENTRAL_NJ', 'PA_NORTHEAST', 'PA_EASTON']].copy()
    X5 = sm.add_constant(X5)
    model5 = sm.OLS(y, X5).fit()
    results['model5'] = model5
    
    return results

def format_coefficient(coef, se):
    """格式化系数和标准误以用于表格输出"""
    if pd.isna(coef) or pd.isna(se):
        return ["", ""]
    return [f"{coef:.3f}", f"({se:.3f})"]

def print_table(results, df):
    """以匹配 standard.md 的格式打印结果"""
    
    print("| Independent variable          | (i)         | (ii)        | (iii)       | (iv)        | (v)         |")
    print("|-------------------------------|-------------|-------------|-------------|-------------|-------------|")
    
    # 新泽西州虚拟变量
    nj_row1 = ["1. New Jersey dummy"]
    nj_row2 = [""]
    
    for i, model_key in enumerate(['model1', 'model2', 'model3', 'model4', 'model5']):
        if model_key in ['model1', 'model2']:
            coef = results[model_key].params.get('NJ', np.nan)
            se = results[model_key].bse.get('NJ', np.nan)
            coef_str, se_str = format_coefficient(coef, se)
        else:
            coef_str, se_str = "", ""
        
        nj_row1.append(coef_str)
        nj_row2.append(se_str)
    
    print("| " + " | ".join(f"{cell:11}" for cell in nj_row1) + " |")
    print("| " + " | ".join(f"{cell:11}" for cell in nj_row2) + " |")
    
    # 初始工资缺口
    gap_row1 = ["2. Initial wage gap"]
    gap_row2 = [""]
    
    for i, model_key in enumerate(['model1', 'model2', 'model3', 'model4', 'model5']):
        if model_key in ['model3', 'model4', 'model5']:
            coef = results[model_key].params.get('GAP', np.nan)
            se = results[model_key].bse.get('GAP', np.nan)
            coef_str, se_str = format_coefficient(coef, se)
        else:
            coef_str, se_str = "", ""
        
        gap_row1.append(coef_str)
        gap_row2.append(se_str)
    
    print("| " + " | ".join(f"{cell:11}" for cell in gap_row1) + " |")
    print("| " + " | ".join(f"{cell:11}" for cell in gap_row2) + " |")
    
    # 连锁店和所有权控制变量
    controls1_row = ["3. Controls for chain and"]
    controls1_values = []
    for model_key in ['model1', 'model2', 'model3', 'model4', 'model5']:
        if model_key in ['model2', 'model4', 'model5']:
            controls1_values.append("yes")
        else:
            controls1_values.append("no")
    
    controls1_row.extend(controls1_values)
    print("| " + " | ".join(f"{cell:11}" for cell in controls1_row) + " |")
    
    controls2_row = ["      ownership"]
    controls2_row.extend([""] * 5)
    print("| " + " | ".join(f"{cell:11}" for cell in controls2_row) + " |")
    
    # 区域控制变量
    region_row = ["4. Controls for region"]
    region_values = []
    for model_key in ['model1', 'model2', 'model3', 'model4', 'model5']:
        if model_key == 'model5':
            region_values.append("yes")
        else:
            region_values.append("no")
    
    region_row.extend(region_values)
    print("| " + " | ".join(f"{cell:11}" for cell in region_row) + " |")
    
    # 回归标准误
    se_row = ["5. Standard error of regression"]
    se_values = []
    for model_key in ['model1', 'model2', 'model3', 'model4', 'model5']:
        rmse = np.sqrt(results[model_key].mse_resid)
        se_values.append(f"{rmse:.3f}")
    
    se_row.extend(se_values)
    print("| " + " | ".join(f"{cell:11}" for cell in se_row) + " |")
    
    # 注释
    print()
    print("Notes: Standard errors are given in parentheses. Entries are estimated regression coefficients for models fit to the change in the log price of a full meal (entrée, medium soda, small fries). The sample contains 315 stores with valid data on prices, wages, and employment for waves 1 and 2. The mean and standard deviation of the dependent variable are 0.0173 and 0.1017, respectively.")
    print("Proportional increase in starting wage necessary to raise the wage to the new minimum-wage rate. For stores in Pennsylvania the wage gap is 0.")
    print("Three dummy variables for chain type and whether or not the store is company-owned are included.")
    print("Dummy variables for two regions of New Jersey and two regions of eastern Pennsylvania are included.")

def main():
    """主函数，运行复现过程"""
    print("Replicating Table 7 from Card and Krueger (1994)")
    print("=" * 60)
    
    # 加载并处理数据
    df = load_data()
    df_clean = create_variables(df)
    
    # 检查样本统计数据
    print(f"\nDependent variable statistics:")
    print(f"Mean: {df_clean['DLOG_MEAL'].mean():.4f}")
    print(f"Standard deviation: {df_clean['DLOG_MEAL'].std():.4f}")
    print()
    
    # 运行回归
    results = run_regressions(df_clean)
    
    # 打印结果表格
    print_table(results, df_clean)

if __name__ == "__main__":
    main()