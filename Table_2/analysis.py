#!/usr/bin/env python3
"""
复现 Card and Krueger (1994) 论文 Table 2: Means of Key Variables
使用 public.dat 数据集计算新泽西州和宾夕法尼亚州快餐店的关键变量均值
修复版本：正确处理缺失值
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

def parse_public_dat(filename):
    """
    根据codebook解析public.dat文件
    """
    # 根据codebook定义列的位置和名称
    colspecs = [
        (0, 3),     # SHEET (1-3) -> (0,3)
        (4, 5),     # CHAIN (5-5) -> (4,5) 
        (6, 7),     # CO_OWNED (7-7) -> (6,7)
        (8, 9),     # STATE (9-9) -> (8,9)
        (10, 11),   # SOUTHJ (11-11) -> (10,11)
        (12, 13),   # CENTRALJ (13-13) -> (12,13)
        (14, 15),   # NORTHJ (15-15) -> (14,15)
        (16, 17),   # PA1 (17-17) -> (16,17)
        (18, 19),   # PA2 (19-19) -> (18,19)
        (20, 21),   # SHORE (21-21) -> (20,21)
        (22, 24),   # NCALLS (23-24) -> (22,24)
        (25, 30),   # EMPFT (26-30) -> (25,30)
        (31, 36),   # EMPPT (32-36) -> (31,36)
        (37, 42),   # NMGRS (38-42) -> (37,42)
        (43, 48),   # WAGE_ST (44-48) -> (43,48)
        (49, 54),   # INCTIME (50-54) -> (49,54)
        (55, 60),   # FIRSTINC (56-60) -> (55,60)
        (61, 62),   # BONUS (62-62) -> (61,62)
        (63, 68),   # PCTAFF (64-68) -> (63,68)
        (69, 70),   # MEALS (70-70) -> (69,70)
        (71, 76),   # OPEN (72-76) -> (71,76)
        (77, 82),   # HRSOPEN (78-82) -> (77,82)
        (83, 88),   # PSODA (84-88) -> (83,88)
        (89, 94),   # PFRY (90-94) -> (89,94)
        (95, 100),  # PENTREE (96-100) -> (95,100)
        (101, 103), # NREGS (102-103) -> (101,103)
        (104, 106), # NREGS11 (105-106) -> (104,106)
        (107, 108), # TYPE2 (108-108) -> (107,108)
        (109, 110), # STATUS2 (110-110) -> (109,110)
        (111, 117), # DATE2 (112-117) -> (111,117)
        (118, 120), # NCALLS2 (119-120) -> (118,120)
        (121, 126), # EMPFT2 (122-126) -> (121,126)
        (127, 132), # EMPPT2 (128-132) -> (127,132)
        (133, 138), # NMGRS2 (134-138) -> (133,138)
        (139, 144), # WAGE_ST2 (140-144) -> (139,144)
        (145, 150), # INCTIME2 (146-150) -> (145,150)
        (151, 156), # FIRSTIN2 (152-156) -> (151,156)
        (157, 158), # SPECIAL2 (158-158) -> (157,158)
        (159, 160), # MEALS2 (160-160) -> (159,160)
        (161, 166), # OPEN2R (162-166) -> (161,166)
        (167, 172), # HRSOPEN2 (168-172) -> (167,172)
        (173, 178), # PSODA2 (174-178) -> (173,178)
        (179, 184), # PFRY2 (180-184) -> (179,184)
        (185, 190), # PENTREE2 (186-190) -> (185,190)
        (191, 193), # NREGS2 (192-193) -> (191,193)
        (194, 196), # NREGS112 (195-196) -> (194,196)
    ]
    
    column_names = [
        'SHEET', 'CHAIN', 'CO_OWNED', 'STATE', 'SOUTHJ', 'CENTRALJ', 'NORTHJ', 
        'PA1', 'PA2', 'SHORE', 'NCALLS', 'EMPFT', 'EMPPT', 'NMGRS', 'WAGE_ST', 
        'INCTIME', 'FIRSTINC', 'BONUS', 'PCTAFF', 'MEALS', 'OPEN', 'HRSOPEN', 
        'PSODA', 'PFRY', 'PENTREE', 'NREGS', 'NREGS11', 'TYPE2', 'STATUS2', 
        'DATE2', 'NCALLS2', 'EMPFT2', 'EMPPT2', 'NMGRS2', 'WAGE_ST2', 
        'INCTIME2', 'FIRSTIN2', 'SPECIAL2', 'MEALS2', 'OPEN2R', 'HRSOPEN2', 
        'PSODA2', 'PFRY2', 'PENTREE2', 'NREGS2', 'NREGS112'
    ]
    
    # 读取固定宽度文件
    df = pd.read_fwf(filename, colspecs=colspecs, names=column_names, na_values=['.', ''])
    
    return df

def calculate_fte_employment(empft, emppt, nmgrs):
    """
    计算FTE employment: 全职员工数量(含管理人员)加上兼职员工数量乘以0.5
    修复：正确处理缺失值 - 如果任何一个变量缺失，则返回NaN
    """
    # 如果任何一个变量缺失，返回NaN
    if pd.isna(empft) or pd.isna(emppt) or pd.isna(nmgrs):
        return np.nan
    
    return empft + nmgrs + emppt * 0.5

def calculate_pct_fulltime(empft, emppt, nmgrs):
    """
    计算全职员工百分比 - 修正：只计算EMPFT，不包括管理人员
    根据SAS代码：FRACFT=(EMPFT/EMPTOT)
    """
    # 如果任何一个变量缺失，返回NaN
    if pd.isna(empft) or pd.isna(emppt) or pd.isna(nmgrs):
        return np.nan
    
    total_emp = empft + emppt + nmgrs
    if total_emp == 0:
        return np.nan
    return empft / total_emp * 100

def calculate_wage_percentage(wage, target_wage):
    """
    计算特定工资水平的百分比 - 修正：创建二元指示变量
    根据SAS代码：ATMIN=(WAGE_ST=4.25)，然后计算均值
    """
    if pd.isna(wage):
        return np.nan
    return 100.0 if abs(wage - target_wage) < 0.01 else 0.0

def calculate_price_full_meal(psoda, pfry, pentree):
    """
    计算套餐价格
    """
    if pd.isna(psoda) or pd.isna(pfry) or pd.isna(pentree):
        return np.nan
    return psoda + pfry + pentree

def t_test_independent(data1, data2):
    """
    计算两组独立样本的t检验统计量
    """
    # 移除缺失值
    data1_clean = data1.dropna()
    data2_clean = data2.dropna()
    
    if len(data1_clean) == 0 or len(data2_clean) == 0:
        return np.nan
    
    # 进行独立样本t检验
    t_stat, p_value = stats.ttest_ind(data1_clean, data2_clean, equal_var=False)
    return t_stat

def proportion_test(count1, n1, count2, n2):
    """
    计算两比例差异的t统计量
    """
    if n1 == 0 or n2 == 0:
        return np.nan
    
    p1 = count1 / n1
    p2 = count2 / n2
    p_pooled = (count1 + count2) / (n1 + n2)
    
    if p_pooled == 0 or p_pooled == 1:
        return np.nan
    
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    if se == 0:
        return np.nan
    
    t_stat = (p1 - p2) / se
    return t_stat

def main():
    # 读取数据
    df = parse_public_dat('../data/public.dat')
    
    # 临时调试：检查数据解析
    print("数据解析检查 - 前5行:")
    print(df.head())
    print("\nNJ数据 EMPFT, EMPPT, NMGRS 前5行:")
    nj_temp = df[df['STATE'] == 1]
    print(nj_temp[['EMPFT', 'EMPPT', 'NMGRS']].head())
    
    # 处理Wave 2关闭的店铺
    # 永久关闭的店铺（STATUS2=3）员工数设为0
    permanently_closed = df['STATUS2'] == 3
    df.loc[permanently_closed, ['EMPFT2', 'EMPPT2', 'NMGRS2']] = 0
    
    # 暂时关闭的店铺(STATUS2=2,4,5)设为缺失值
    temporarily_closed = df['STATUS2'].isin([2, 4, 5])
    df.loc[temporarily_closed, ['EMPFT2', 'EMPPT2', 'NMGRS2']] = np.nan
    
    # 创建状态分组 (NJ=1, PA=0)
    nj_data = df[df['STATE'] == 1].copy()
    pa_data = df[df['STATE'] == 0].copy()
    
    print("=" * 80)
    print("Table 2: Means of Key Variables")
    print("Card and Krueger (1994) 复现结果 (修复版)")
    print("=" * 80)
    print()
    
    # 第一部分：店铺类型分布 (Percentages)
    print("第一部分：店铺类型的分布 (Percentages)")
    print("-" * 50)
    print(f"{'Variable':<20} {'NJ':<15} {'PA':<15} {'t-statistic':<12}")
    print("-" * 50)
    
    # 计算各类型店铺的分布
    chains = {
        'a. Burger King': 1,
        'b. KFC': 2, 
        'c. Roy Rogers': 3,
        'd. Wendy\'s': 4
    }
    
    for chain_name, chain_code in chains.items():
        nj_count = (nj_data['CHAIN'] == chain_code).sum()
        pa_count = (pa_data['CHAIN'] == chain_code).sum()
        nj_total = len(nj_data)
        pa_total = len(pa_data)
        
        nj_pct = nj_count / nj_total * 100
        pa_pct = pa_count / pa_total * 100
        
        t_stat = proportion_test(nj_count, nj_total, pa_count, pa_total)
        
        print(f"{chain_name:<20} {nj_pct:>8.1f}%     {pa_pct:>8.1f}%     {t_stat:>8.2f}")
    
    # Company-owned
    nj_co_owned = (nj_data['CO_OWNED'] == 1).sum()
    pa_co_owned = (pa_data['CO_OWNED'] == 1).sum()
    nj_total = len(nj_data)
    pa_total = len(pa_data)
    
    nj_co_pct = nj_co_owned / nj_total * 100
    pa_co_pct = pa_co_owned / pa_total * 100
    
    t_stat = proportion_test(nj_co_owned, nj_total, pa_co_owned, pa_total)
    
    print(f"{'e. Company-owned':<20} {nj_co_pct:>8.1f}%     {pa_co_pct:>8.1f}%     {t_stat:>8.2f}")
    
    print()
    
    # 第二部分：Wave 1 的均值
    print("第二部分：Wave 1 的均值")
    print("-" * 50)
    print(f"{'Variable':<25} {'NJ':<15} {'PA':<15} {'t-statistic':<12}")
    print("-" * 50)
    
    # a. FTE employment (Wave 1)
    nj_data['FTE1'] = nj_data.apply(lambda x: calculate_fte_employment(x['EMPFT'], x['EMPPT'], x['NMGRS']), axis=1)
    pa_data['FTE1'] = pa_data.apply(lambda x: calculate_fte_employment(x['EMPFT'], x['EMPPT'], x['NMGRS']), axis=1)
    
    nj_mean = nj_data['FTE1'].mean()
    nj_se = nj_data['FTE1'].std() / np.sqrt(len(nj_data['FTE1'].dropna()))
    pa_mean = pa_data['FTE1'].mean()
    pa_se = pa_data['FTE1'].std() / np.sqrt(len(pa_data['FTE1'].dropna()))
    t_stat = t_test_independent(nj_data['FTE1'], pa_data['FTE1'])
    
    print(f"{'a. FTE employment':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # b. Percentage full-time employees
    nj_data['PCT_FT1'] = nj_data.apply(lambda x: calculate_pct_fulltime(x['EMPFT'], x['EMPPT'], x['NMGRS']), axis=1)
    pa_data['PCT_FT1'] = pa_data.apply(lambda x: calculate_pct_fulltime(x['EMPFT'], x['EMPPT'], x['NMGRS']), axis=1)
    
    nj_mean = nj_data['PCT_FT1'].mean()
    nj_se = nj_data['PCT_FT1'].std() / np.sqrt(len(nj_data['PCT_FT1'].dropna()))
    pa_mean = pa_data['PCT_FT1'].mean()
    pa_se = pa_data['PCT_FT1'].std() / np.sqrt(len(pa_data['PCT_FT1'].dropna()))
    t_stat = t_test_independent(nj_data['PCT_FT1'], pa_data['PCT_FT1'])
    
    print(f"{'b. % full-time employees':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # c. Starting wage
    nj_mean = nj_data['WAGE_ST'].mean()
    nj_se = nj_data['WAGE_ST'].std() / np.sqrt(len(nj_data['WAGE_ST'].dropna()))
    pa_mean = pa_data['WAGE_ST'].mean()
    pa_se = pa_data['WAGE_ST'].std() / np.sqrt(len(pa_data['WAGE_ST'].dropna()))
    t_stat = t_test_independent(nj_data['WAGE_ST'], pa_data['WAGE_ST'])
    
    print(f"{'c. Starting wage':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # d. Wage = $4.25 (percentage)
    nj_data['WAGE_425_1'] = nj_data['WAGE_ST'].apply(lambda x: calculate_wage_percentage(x, 4.25))
    pa_data['WAGE_425_1'] = pa_data['WAGE_ST'].apply(lambda x: calculate_wage_percentage(x, 4.25))
    
    nj_mean = nj_data['WAGE_425_1'].mean()
    nj_se = nj_data['WAGE_425_1'].std() / np.sqrt(len(nj_data['WAGE_425_1'].dropna()))
    pa_mean = pa_data['WAGE_425_1'].mean()
    pa_se = pa_data['WAGE_425_1'].std() / np.sqrt(len(pa_data['WAGE_425_1'].dropna()))
    t_stat = t_test_independent(nj_data['WAGE_425_1'], pa_data['WAGE_425_1'])
    
    print(f"{'d. Wage = $4.25 (%)':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # e. Price of full meal
    nj_data['MEAL_PRICE1'] = nj_data.apply(lambda x: calculate_price_full_meal(x['PSODA'], x['PFRY'], x['PENTREE']), axis=1)
    pa_data['MEAL_PRICE1'] = pa_data.apply(lambda x: calculate_price_full_meal(x['PSODA'], x['PFRY'], x['PENTREE']), axis=1)
    
    nj_mean = nj_data['MEAL_PRICE1'].mean()
    nj_se = nj_data['MEAL_PRICE1'].std() / np.sqrt(len(nj_data['MEAL_PRICE1'].dropna()))
    pa_mean = pa_data['MEAL_PRICE1'].mean()
    pa_se = pa_data['MEAL_PRICE1'].std() / np.sqrt(len(pa_data['MEAL_PRICE1'].dropna()))
    t_stat = t_test_independent(nj_data['MEAL_PRICE1'], pa_data['MEAL_PRICE1'])
    
    print(f"{'e. Price of full meal':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # f. Hours open (weekday)
    nj_mean = nj_data['HRSOPEN'].mean()
    nj_se = nj_data['HRSOPEN'].std() / np.sqrt(len(nj_data['HRSOPEN'].dropna()))
    pa_mean = pa_data['HRSOPEN'].mean()
    pa_se = pa_data['HRSOPEN'].std() / np.sqrt(len(pa_data['HRSOPEN'].dropna()))
    t_stat = t_test_independent(nj_data['HRSOPEN'], pa_data['HRSOPEN'])
    
    print(f"{'f. Hours open (weekday)':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # g. Recruiting bonus
    nj_bonus_pct = (nj_data['BONUS'] == 1).mean() * 100
    pa_bonus_pct = (pa_data['BONUS'] == 1).mean() * 100
    
    nj_count = (nj_data['BONUS'] == 1).sum()
    pa_count = (pa_data['BONUS'] == 1).sum()
    nj_total = len(nj_data['BONUS'].dropna())
    pa_total = len(pa_data['BONUS'].dropna())
    
    t_stat = proportion_test(nj_count, nj_total, pa_count, pa_total)
    
    print(f"{'g. Recruiting bonus':<25} {nj_bonus_pct:>8.1f}     {pa_bonus_pct:>8.1f}     {t_stat:>8.2f}")
    
    print()
    
    # 第三部分：Wave 2 的均值
    print("第三部分：Wave 2 的均值")
    print("-" * 50)
    print(f"{'Variable':<25} {'NJ':<15} {'PA':<15} {'t-statistic':<12}")
    print("-" * 50)
    
    # a. FTE employment (Wave 2)
    nj_data['FTE2'] = nj_data.apply(lambda x: calculate_fte_employment(x['EMPFT2'], x['EMPPT2'], x['NMGRS2']), axis=1)
    pa_data['FTE2'] = pa_data.apply(lambda x: calculate_fte_employment(x['EMPFT2'], x['EMPPT2'], x['NMGRS2']), axis=1)
    
    nj_mean = nj_data['FTE2'].mean()
    nj_se = nj_data['FTE2'].std() / np.sqrt(len(nj_data['FTE2'].dropna()))
    pa_mean = pa_data['FTE2'].mean()
    pa_se = pa_data['FTE2'].std() / np.sqrt(len(pa_data['FTE2'].dropna()))
    t_stat = t_test_independent(nj_data['FTE2'], pa_data['FTE2'])
    
    print(f"{'a. FTE employment':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # b. Percentage full-time employees
    nj_data['PCT_FT2'] = nj_data.apply(lambda x: calculate_pct_fulltime(x['EMPFT2'], x['EMPPT2'], x['NMGRS2']), axis=1)
    pa_data['PCT_FT2'] = pa_data.apply(lambda x: calculate_pct_fulltime(x['EMPFT2'], x['EMPPT2'], x['NMGRS2']), axis=1)
    
    nj_mean = nj_data['PCT_FT2'].mean()
    nj_se = nj_data['PCT_FT2'].std() / np.sqrt(len(nj_data['PCT_FT2'].dropna()))
    pa_mean = pa_data['PCT_FT2'].mean()
    pa_se = pa_data['PCT_FT2'].std() / np.sqrt(len(pa_data['PCT_FT2'].dropna()))
    t_stat = t_test_independent(nj_data['PCT_FT2'], pa_data['PCT_FT2'])
    
    print(f"{'b. % full-time employees':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # c. Starting wage
    nj_mean = nj_data['WAGE_ST2'].mean()
    nj_se = nj_data['WAGE_ST2'].std() / np.sqrt(len(nj_data['WAGE_ST2'].dropna()))
    pa_mean = pa_data['WAGE_ST2'].mean()
    pa_se = pa_data['WAGE_ST2'].std() / np.sqrt(len(pa_data['WAGE_ST2'].dropna()))
    t_stat = t_test_independent(nj_data['WAGE_ST2'], pa_data['WAGE_ST2'])
    
    print(f"{'c. Starting wage':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # d. Wage = $4.25 (percentage)
    nj_data['WAGE_425_2'] = nj_data['WAGE_ST2'].apply(lambda x: calculate_wage_percentage(x, 4.25))
    pa_data['WAGE_425_2'] = pa_data['WAGE_ST2'].apply(lambda x: calculate_wage_percentage(x, 4.25))
    
    nj_mean = nj_data['WAGE_425_2'].mean()
    nj_se = nj_data['WAGE_425_2'].std() / np.sqrt(len(nj_data['WAGE_425_2'].dropna()))
    pa_mean = pa_data['WAGE_425_2'].mean()
    pa_se = pa_data['WAGE_425_2'].std() / np.sqrt(len(pa_data['WAGE_425_2'].dropna()))
    t_stat = t_test_independent(nj_data['WAGE_425_2'], pa_data['WAGE_425_2'])
    
    print(f"{'d. Wage = $4.25 (%)':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # e. Wage = $5.05 (percentage)
    nj_data['WAGE_505_2'] = nj_data['WAGE_ST2'].apply(lambda x: calculate_wage_percentage(x, 5.05))
    pa_data['WAGE_505_2'] = pa_data['WAGE_ST2'].apply(lambda x: calculate_wage_percentage(x, 5.05))
    
    nj_mean = nj_data['WAGE_505_2'].mean()
    nj_se = nj_data['WAGE_505_2'].std() / np.sqrt(len(nj_data['WAGE_505_2'].dropna()))
    pa_mean = pa_data['WAGE_505_2'].mean()
    pa_se = pa_data['WAGE_505_2'].std() / np.sqrt(len(pa_data['WAGE_505_2'].dropna()))
    t_stat = t_test_independent(nj_data['WAGE_505_2'], pa_data['WAGE_505_2'])
    
    print(f"{'e. Wage = $5.05 (%)':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # f. Price of full meal
    nj_data['MEAL_PRICE2'] = nj_data.apply(lambda x: calculate_price_full_meal(x['PSODA2'], x['PFRY2'], x['PENTREE2']), axis=1)
    pa_data['MEAL_PRICE2'] = pa_data.apply(lambda x: calculate_price_full_meal(x['PSODA2'], x['PFRY2'], x['PENTREE2']), axis=1)
    
    nj_mean = nj_data['MEAL_PRICE2'].mean()
    nj_se = nj_data['MEAL_PRICE2'].std() / np.sqrt(len(nj_data['MEAL_PRICE2'].dropna()))
    pa_mean = pa_data['MEAL_PRICE2'].mean()
    pa_se = pa_data['MEAL_PRICE2'].std() / np.sqrt(len(pa_data['MEAL_PRICE2'].dropna()))
    t_stat = t_test_independent(nj_data['MEAL_PRICE2'], pa_data['MEAL_PRICE2'])
    
    print(f"{'f. Price of full meal':<25} {nj_mean:>8.2f}     {pa_mean:>8.2f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.2f})     ({pa_se:>6.2f})")
    
    # g. Hours open (weekday)
    nj_mean = nj_data['HRSOPEN2'].mean()
    nj_se = nj_data['HRSOPEN2'].std() / np.sqrt(len(nj_data['HRSOPEN2'].dropna()))
    pa_mean = pa_data['HRSOPEN2'].mean()
    pa_se = pa_data['HRSOPEN2'].std() / np.sqrt(len(pa_data['HRSOPEN2'].dropna()))
    t_stat = t_test_independent(nj_data['HRSOPEN2'], pa_data['HRSOPEN2'])
    
    print(f"{'g. Hours open (weekday)':<25} {nj_mean:>8.1f}     {pa_mean:>8.1f}     {t_stat:>8.2f}")
    print(f"{'':25} ({nj_se:>6.1f})     ({pa_se:>6.1f})")
    
    # h. Recruiting bonus
    nj_bonus_pct = (nj_data['SPECIAL2'] == 1).mean() * 100
    pa_bonus_pct = (pa_data['SPECIAL2'] == 1).mean() * 100
    
    nj_count = (nj_data['SPECIAL2'] == 1).sum()
    pa_count = (pa_data['SPECIAL2'] == 1).sum()
    nj_total = len(nj_data['SPECIAL2'].dropna())
    pa_total = len(pa_data['SPECIAL2'].dropna())
    
    t_stat = proportion_test(nj_count, nj_total, pa_count, pa_total)
    
    print(f"{'h. Recruiting bonus':<25} {nj_bonus_pct:>8.1f}     {pa_bonus_pct:>8.1f}     {t_stat:>8.2f}")
    
    print()
    print("=" * 80)
    print("注：")
    print("- 括号内为标准误 (Standard Error)")
    print("- t统计量用于检验NJ和PA之间的差异")
    print("- Wave 2中永久关闭的店铺员工数设为0，暂时关闭的店铺按缺失值处理")
    print("- 修复：正确处理缺失值，不使用fillna(0)")
    print("=" * 80)

if __name__ == "__main__":
    main() 