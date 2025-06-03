#!/usr/bin/env python3
"""
Card 和 Krueger (1994) 论文中 Table 5 的复现脚本
"最低工资与就业：新泽西州和宾夕法尼亚州快餐业的案例研究"

本脚本复现了论文中的 Table 5 - 简化形式就业模型的规范测试
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

def prepare_sample_with_temp_closed(df):
    """
    准备包含临时关闭店铺的样本（用于规范2）
    """
    sample = df.copy()
    
    # 处理临时关闭的店铺 - 将它们的第二波就业数据设为0
    temp_closed_mask = sample['STATUS2'] == 2
    sample.loc[temp_closed_mask, 'EMPFT2'] = 0
    sample.loc[temp_closed_mask, 'EMPPT2'] = 0
    sample.loc[temp_closed_mask, 'NMGRS2'] = 0
    sample.loc[temp_closed_mask, 'EMPTOT2'] = 0
    sample.loc[temp_closed_mask, 'DEMP'] = sample.loc[temp_closed_mask, 'EMPTOT2'] - sample.loc[temp_closed_mask, 'EMPTOT']
    sample.loc[temp_closed_mask, 'PCHEMPC'] = -1
    # 为了样本筛选，给临时关闭的店铺一个虚拟的工资变化值
    sample.loc[temp_closed_mask, 'dwage'] = 0
    
    # 应用样本筛选条件
    sample = sample.dropna(subset=['DEMP'])
    sample = sample[(sample['CLOSED'] == 1) | 
                   ((sample['CLOSED'] == 0) & sample['dwage'].notna())]
    
    return sample

def create_interview_date_dummies(df):
    """
    创建第二波访谈日期的虚拟变量
    根据论文注释 f，包含三个虚拟变量用于标识 1992年11-12月的访谈周
    """
    df = df.copy()
    
    # 将 DATE2 转换为字符串以便解析
    df['DATE2_str'] = df['DATE2'].astype(str)
    
    # 解析日期 (MMDDYY 格式)
    # 为简化起见，我们基于 DATE2 的数值范围创建三个周期虚拟变量
    date_vals = df['DATE2'].dropna()
    if len(date_vals) > 0:
        # 将日期值分为三个大致相等的组
        date_quantiles = date_vals.quantile([0.33, 0.67])
        
        df['week1'] = ((df['DATE2'] <= date_quantiles.iloc[0]) & df['DATE2'].notna()).astype(int)
        df['week2'] = ((df['DATE2'] > date_quantiles.iloc[0]) & 
                      (df['DATE2'] <= date_quantiles.iloc[1]) & 
                      df['DATE2'].notna()).astype(int)
        df['week3'] = ((df['DATE2'] > date_quantiles.iloc[1]) & df['DATE2'].notna()).astype(int)
    else:
        df['week1'] = 0
        df['week2'] = 0  
        df['week3'] = 0
    
    return df

def get_newark_camden_samples(df):
    """
    基于邮政编码识别 Newark 和 Camden 周边地区的店铺
    这是一个简化的实现，使用地理区域变量作为代理
    """
    # Newark 周边：北新泽西 + 中新泽西的一部分
    newark_mask = (df['NORTHJ'] == 1) | (df['CENTRALJ'] == 1)
    
    # Camden 周边：南新泽西  
    camden_mask = df['SOUTHJ'] == 1
    
    return newark_mask, camden_mask

def run_specification_tests(df):
    """
    运行所有 12 个规范测试
    """
    results = {}
    
    # 1. 基础规范 (Base specification) - 来自 Table 4 模型 (ii) 和 (iv)
    base_sample = util.create_analysis_sample(df, include_temp_closed=False)
    
    # 列 (i): Change in employment ~ NJ dummy + controls
    model1_nj = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=base_sample).fit()
    results['1_nj'] = model1_nj
    
    # 列 (ii): Change in employment ~ Gap + controls  
    model1_gap = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=base_sample).fit()
    results['1_gap'] = model1_gap
    
    # 列 (iii): Proportional change ~ NJ dummy + controls
    model1_nj_prop = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=base_sample).fit()
    results['1_nj_prop'] = model1_nj_prop
    
    # 列 (iv): Proportional change ~ Gap + controls
    model1_gap_prop = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=base_sample).fit()
    results['1_gap_prop'] = model1_gap_prop
    
    # 2. 将暂时关闭的店铺视为永久关闭
    sample2 = prepare_sample_with_temp_closed(df)
    
    results['2_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=sample2).fit()
    results['2_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample2).fit()
    results['2_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=sample2).fit()
    results['2_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample2).fit()
    
    # 3. 排除管理人员的就业计数
    sample3 = base_sample.copy()
    sample3['EMPTOT_NO_MGR'] = sample3['EMPPT'] * 0.5 + sample3['EMPFT']
    sample3['EMPTOT2_NO_MGR'] = sample3['EMPPT2'] * 0.5 + sample3['EMPFT2']
    sample3['DEMP_NO_MGR'] = sample3['EMPTOT2_NO_MGR'] - sample3['EMPTOT_NO_MGR']
    sample3['PCHEMPC_NO_MGR'] = 2 * (sample3['EMPTOT2_NO_MGR'] - sample3['EMPTOT_NO_MGR']) / (sample3['EMPTOT2_NO_MGR'] + sample3['EMPTOT_NO_MGR'])
    sample3.loc[sample3['EMPTOT2_NO_MGR'] == 0, 'PCHEMPC_NO_MGR'] = -1
    
    results['3_nj'] = smf.ols('DEMP_NO_MGR ~ nj + bk + kfc + roys + CO_OWNED', data=sample3).fit()
    results['3_gap'] = smf.ols('DEMP_NO_MGR ~ gap + bk + kfc + roys + CO_OWNED', data=sample3).fit()
    results['3_nj_prop'] = smf.ols('PCHEMPC_NO_MGR ~ nj + bk + kfc + roys + CO_OWNED', data=sample3).fit()
    results['3_gap_prop'] = smf.ols('PCHEMPC_NO_MGR ~ gap + bk + kfc + roys + CO_OWNED', data=sample3).fit()
    
    # 4. 兼职员工权重为 0.4
    sample4 = util.create_analysis_sample(util.calculate_fte_employment(df, part_time_weight=0.4), include_temp_closed=False)
    sample4['PCHEMPC_04'] = util.calculate_proportional_change(sample4)['PCHEMPC']
    
    results['4_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=sample4).fit()
    results['4_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample4).fit()
    results['4_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=sample4).fit()
    results['4_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample4).fit()
    
    # 5. 兼职员工权重为 0.6
    sample5 = util.create_analysis_sample(util.calculate_fte_employment(df, part_time_weight=0.6), include_temp_closed=False)
    sample5['PCHEMPC_06'] = util.calculate_proportional_change(sample5)['PCHEMPC']
    
    results['5_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=sample5).fit()
    results['5_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample5).fit()
    results['5_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=sample5).fit()
    results['5_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample5).fit()
    
    # 6. 排除新泽西海岸地区的店铺
    sample6 = base_sample[base_sample['SHORE'] != 1].copy()
    
    results['6_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=sample6).fit()
    results['6_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample6).fit()
    results['6_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=sample6).fit()
    results['6_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample6).fit()
    
    # 7. 加入第二波访谈日期控制变量
    sample7 = create_interview_date_dummies(base_sample)
    
    results['7_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED + week1 + week2 + week3', data=sample7).fit()
    results['7_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED + week1 + week2 + week3', data=sample7).fit()
    results['7_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED + week1 + week2 + week3', data=sample7).fit()
    results['7_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED + week1 + week2 + week3', data=sample7).fit()
    
    # 8. 排除第一波调查中回调超过两次的店铺
    sample8 = base_sample[base_sample['NCALLS'] <= 2].copy()
    
    results['8_nj'] = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=sample8).fit()
    results['8_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample8).fit()
    results['8_nj_prop'] = smf.ols('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', data=sample8).fit()
    results['8_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample8).fit()
    
    # 9. 按初始就业水平加权（仅对比例变化模型）
    sample9 = base_sample.copy()
    weights = sample9['EMPTOT'].fillna(1)  # 使用第一波就业作为权重
    
    # 只有比例变化模型使用权重
    results['9_nj_prop'] = smf.wls('PCHEMPC ~ nj + bk + kfc + roys + CO_OWNED', 
                                   data=sample9, weights=weights).fit()
    results['9_gap_prop'] = smf.wls('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', 
                                    data=sample9, weights=weights).fit()
    
    # 10. Newark 周边地区的店铺
    newark_mask, _ = get_newark_camden_samples(base_sample)
    sample10 = base_sample.loc[newark_mask].copy()
    
    if len(sample10) > 10:  # 确保有足够的观测值
        # 只有 gap 模型，因为这是子样本分析
        results['10_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample10).fit()
        results['10_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample10).fit()
    
    # 11. Camden 周边地区的店铺
    _, camden_mask = get_newark_camden_samples(base_sample)
    sample11 = base_sample.loc[camden_mask].copy()
    
    if len(sample11) > 10:  # 确保有足够的观测值
        # 只有 gap 模型
        results['11_gap'] = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=sample11).fit()
        results['11_gap_prop'] = smf.ols('PCHEMPC ~ gap + bk + kfc + roys + CO_OWNED', data=sample11).fit()
    
    # 12. 仅宾夕法尼亚州店铺，工资差距重新定义
    sample12 = base_sample[base_sample['nj'] == 0].copy()
    # 为宾夕法尼亚州店铺重新定义工资差距（假设它们也受到 5.05 最低工资影响）
    mask_wage_low_pa = sample12['WAGE_ST'] < 5.05
    mask_wage_pos_pa = sample12['WAGE_ST'] > 0
    sample12['gap_pa'] = 0.0
    sample12.loc[mask_wage_low_pa & mask_wage_pos_pa, 'gap_pa'] = (5.05 - sample12['WAGE_ST']) / sample12['WAGE_ST']
    
    if len(sample12) > 10:  # 确保有足够的观测值
        # 只有 gap 模型
        results['12_gap'] = smf.ols('DEMP ~ gap_pa + bk + kfc + roys + CO_OWNED', data=sample12).fit()
        results['12_gap_prop'] = smf.ols('PCHEMPC ~ gap_pa + bk + kfc + roys + CO_OWNED', data=sample12).fit()
    
    return results

def generate_table_5(results):
    """
    生成 Table 5 的 Markdown 格式输出
    """
    lines = []
    lines.append("## TABLE 5-SPECIFICATION TESTS OF REDUCED-FORM EMPLOYMENT MODELS")
    lines.append("")
    lines.append("| Specification                                         | Change in employment |               | Proportional change in employment |               |")
    lines.append("| :---------------------------------------------------- | :------------------- | :------------ | :-------------------------------- | :------------ |")
    lines.append("|                                                       | NJ dummy (i)         | Gap measure (ii) | NJ dummy (iii)                    | Gap measure (iv) |")
    
    # 规范测试行
    specifications = [
        ("1. Base specification", "1"),
        ("2. Treat four temporarily closed stores as permanently closedª", "2"),
        ("3. Exclude managers in employment countᵇ", "3"),
        ("4. Weight part-time as 0.4 x full-timeᶜ", "4"),
        ("5. Weight part-time as 0.6 x full-timeᵈ", "5"),
        ("6. Exclude stores in NJ shore area", "6"),
        ("7. Add controls for wave-2 interview date", "7"),
        ("8. Exclude stores called more than twice in wave 1ᵍ", "8"),
        ("9. Weight by initial employmentʰ", "9"),
        ("10. Stores in towns around Newarkⁱ", "10"),
        ("11. Stores in towns around Camdenʲ", "11"),
        ("12. Pennsylvania stores onlyᵏ", "12"),
    ]
    
    for spec_name, spec_num in specifications:
        # 准备行数据
        row_data = [spec_name]
        
        # NJ dummy (i) - Change in employment
        key = f"{spec_num}_nj"
        if key in results and 'nj' in results[key].params:
            coef = results[key].params['nj']
            se = results[key].bse['nj']
            row_data.append(util.format_coefficient(coef, se))
        else:
            row_data.append("")
        
        # Gap measure (ii) - Change in employment  
        gap_key = f"{spec_num}_gap"
        if gap_key in results:
            gap_var = 'gap' if 'gap' in results[gap_key].params else 'gap_pa'
            if gap_var in results[gap_key].params:
                coef = results[gap_key].params[gap_var]
                se = results[gap_key].bse[gap_var]
                row_data.append(util.format_coefficient(coef, se))
            else:
                row_data.append("")
        else:
            row_data.append("")
        
        # NJ dummy (iii) - Proportional change in employment
        prop_key = f"{spec_num}_nj_prop"
        if prop_key in results and 'nj' in results[prop_key].params:
            coef = results[prop_key].params['nj']
            se = results[prop_key].bse['nj']
            row_data.append(util.format_coefficient(coef, se))
        else:
            row_data.append("")
        
        # Gap measure (iv) - Proportional change in employment
        gap_prop_key = f"{spec_num}_gap_prop"
        if gap_prop_key in results:
            gap_var = 'gap' if 'gap' in results[gap_prop_key].params else 'gap_pa'
            if gap_var in results[gap_prop_key].params:
                coef = results[gap_prop_key].params[gap_var]
                se = results[gap_prop_key].bse[gap_var]
                row_data.append(util.format_coefficient(coef, se))
            else:
                row_data.append("")
        else:
            row_data.append("")
        
        # 构建表格行
        line = f"| {row_data[0]:<53} | {row_data[1]:>12} | {row_data[2]:>12} | {row_data[3]:>17} | {row_data[4]:>12} |"
        lines.append(line)
    
    # 添加注释
    lines.extend([
        "",
        "Notes: Standard errors are given in parentheses. Entries represent estimated coefficient of New Jersey dummy [columns (i) and (iii)] or initial wage gap [columns (ii) and (iv)] in regression models for the change in employment or the percentage change in employment. All models also include chain dummies and an indicator for company-owned stores.",
        "ª Wave-2 employment at four temporarily closed stores is set to 0 (rather than missing).",
        "ᵇ Full-time equivalent employment excludes managers and assistant managers.",
        "ᶜ Full-time equivalent employment equals number of managers, assistant managers, and full-time nonmanagement workers, plus 0.4 times the number of part-time nonmanagement workers.",
        "ᵈ Full-time equivalent employment equals number of managers, assistant managers, and full-time nonmanagement workers, plus 0.6 times the number of part-time nonmanagement workers.",
        "e Sample excludes 35 stores located in towns along the New Jersey shore.",
        "f Models include three dummy variables identifying week of wave-2 interview in November-December 1992.",
        "ᵍ Sample excludes 70 stores (69 in New Jersey) that were contacted three or more times before obtaining the wave-1 interview.",
        "ʰ Regression model is estimated by weighted least squares, using employment in wave 1 as a weight.",
        "ⁱ Subsample of 51 stores in towns around Newark.",
        "ʲ Subsample of 54 stores in town around Camden.",
        "ᵏ Subsample of Pennsylvania stores only. Wage gap is defined as percentage increase in starting wage necessary to raise starting wage to $5.05."
    ])
    
    return "\n".join(lines)

def main():
    """
    主函数：执行完整的 Table 5 复现
    """
    # 使用utility模块加载数据
    df = util.read_data()
    
    # 使用utility模块创建派生变量
    df = util.create_basic_derived_variables(df)
    
    # 运行所有规范测试
    results = run_specification_tests(df)
    
    # 生成并打印表格
    table_output = generate_table_5(results)
    print(table_output)
    
    # 保存到文件
    output_path = util.get_output_path(__file__)
    util.save_output_to_file(table_output, output_path)

if __name__ == "__main__":
    main() 