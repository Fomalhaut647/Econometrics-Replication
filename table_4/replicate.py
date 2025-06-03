#!/usr/bin/env python3
"""
Card 和 Krueger (1994) 论文中表格4的复制脚本
"最低工资与就业：新泽西州和宾夕法尼亚州快餐业的案例研究"

此脚本复制了就业变化简化式模型。
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util
import statsmodels.formula.api as smf
import numpy as np

def run_regressions(df):
    """
    运行表格4的五个回归模型
    """
    results = {}

    # 模型 (i): DEMP ~ NJ
    model1 = smf.ols('DEMP ~ nj', data=df).fit()
    results['model1'] = model1

    # 模型 (ii): DEMP ~ NJ + 连锁店和所有权控制变量
    model2 = smf.ols('DEMP ~ nj + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model2'] = model2

    # 模型 (iii): DEMP ~ GAP
    model3 = smf.ols('DEMP ~ gap', data=df).fit()
    results['model3'] = model3

    # 模型 (iv): DEMP ~ GAP + 连锁店和所有权控制变量
    model4 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model4'] = model4

    # 模型 (v): DEMP ~ GAP + 连锁店/所有权 + 区域控制变量
    model5 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED + CENTRALJ + SOUTHJ + PA1 + PA2', data=df).fit()
    results['model5'] = model5

    return results

def format_table(results, sample_size):
    """
    将结果格式化为与标准表格4布局完全一致
    """
    # 首先是表格标题
    title = "**TABLE 4-REDUCED-FORM MODELS FOR CHANGE IN EMPLOYMENT**"

    # 提取系数和标准误
    def get_coef_se(model, var):
        if var in model.params.index:
            coef = model.params[var]
            se = model.bse[var]
            return coef, se
        return None, None

    # 初始化表格数据
    table_data = []

    # 第1行: 新泽西州虚拟变量
    row1 = ['1. New Jersey dummy']
    nj_coef1, nj_se1 = get_coef_se(results['model1'], 'nj')
    nj_coef2, nj_se2 = get_coef_se(results['model2'], 'nj')

    row1.extend([
        util.format_coefficient(nj_coef1, nj_se1) if nj_coef1 is not None else "",
        util.format_coefficient(nj_coef2, nj_se2) if nj_coef2 is not None else "",
        "", "", ""
    ])
    table_data.append(row1)

    # 第2行: 初始工资差距
    row2 = ['2. Initial wage gap<sup>a</sup>']
    row2.extend(["", ""])  # 模型 (i) 和 (ii) 中没有差距变量

    gap_coef3, gap_se3 = get_coef_se(results['model3'], 'gap')
    gap_coef4, gap_se4 = get_coef_se(results['model4'], 'gap')
    gap_coef5, gap_se5 = get_coef_se(results['model5'], 'gap')

    row2.extend([
        util.format_coefficient(gap_coef3, gap_se3) if gap_coef3 is not None else "",
        util.format_coefficient(gap_coef4, gap_se4) if gap_coef4 is not None else "",
        util.format_coefficient(gap_coef5, gap_se5) if gap_coef5 is not None else ""
    ])
    table_data.append(row2)

    # 第3行: 连锁店和所有权控制变量
    row3 = ['3. Controls for chain and ownership<sup>b</sup>']
    row3.extend(['no', 'yes', 'no', 'yes', 'yes'])
    table_data.append(row3)

    # 第4行: 区域控制变量
    row4 = ['4. Controls for region<sup>c</sup>']
    row4.extend(['no', 'no', 'no', 'no', 'yes'])
    table_data.append(row4)

    # 第5行: 回归标准误
    row5 = ['5. Standard error of regression']
    row5.extend([
        f"{results['model1'].scale**0.5:.2f}",
        f"{results['model2'].scale**0.5:.2f}",
        f"{results['model3'].scale**0.5:.2f}",
        f"{results['model4'].scale**0.5:.2f}",
        f"{results['model5'].scale**0.5:.2f}"
    ])
    table_data.append(row5)

    # 第6行: 控制变量的概率值
    row6 = ['6. Probability value for controls<sup>d</sup>']
    row6.append("")  # 模型 (i) 没有控制变量

    # 模型 (ii) 的 F 检验 - 连锁店和所有权控制变量
    chain_controls = ['bk', 'kfc', 'roys', 'CO_OWNED']
    p_val2 = util.calculate_f_test_pvalue(results['model2'], chain_controls)
    row6.append(f"{p_val2:.2f}" if p_val2 is not None else "")

    row6.append("")  # 模型 (iii) 没有控制变量

    # 模型 (iv) 的 F 检验 - 连锁店和所有权控制变量
    p_val4 = util.calculate_f_test_pvalue(results['model4'], chain_controls)
    row6.append(f"{p_val4:.2f}" if p_val4 is not None else "")

    # 模型 (v) 的 F 检验 - 所有控制变量
    all_controls = ['bk', 'kfc', 'roys', 'CO_OWNED', 'CENTRALJ', 'SOUTHJ', 'PA1', 'PA2']
    p_val5 = util.calculate_f_test_pvalue(results['model5'], all_controls)
    row6.append(f"{p_val5:.2f}" if p_val5 is not None else "")

    table_data.append(row6)

    # 创建 markdown 表格
    header = "| Independent variable                       | Model (i)   | Model (ii)  | Model (iii) | Model (iv)  | Model (v)   |"
    separator = "| :----------------------------------------- | :---------- | :---------- | :---------- | :---------- | :---------- |"

    table_lines = [title, "", header, separator]
    for row in table_data:
        line = f"| {row[0]:<42} | {' | '.join(f'{cell:<11}' for cell in row[1:])} |"
        table_lines.append(line)

    # 添加注释
    notes = [
        "",
        f"Notes: Standard errors are given in parentheses. The sample consists of {sample_size} stores with available data on employment and starting wages in waves 1 and 2. The dependent variable in all models is change in FTE employment. The mean and standard deviation of the dependent variable are {results['model1'].model.endog.mean():.3f} and {results['model1'].model.endog.std():.3f}, respectively. All models include an unrestricted constant (not reported).",
        "",
        "<sup>a</sup> Proportional increase in starting wage necessary to raise starting wage to new minimum rate. For stores in Pennsylvania the wage gap is 0.",
        "<sup>b</sup> Three dummy variables for chain type and whether or not the store is company-owned are included.",
        "<sup>c</sup> Dummy variables for two regions of New Jersey and two regions of eastern Pennsylvania are included.",
        "<sup>d</sup> Probability value of joint F test for exclusion of all control variables."
    ]

    return "\n".join(table_lines + notes)

def main():
    """
    主函数，用于复制表格4
    """
    # 使用utility模块加载和处理数据
    df = util.read_data()
    df = util.create_basic_derived_variables(df)
    
    # 创建分析样本
    sample = util.create_analysis_sample(df)

    # 运行回归
    results = run_regressions(sample)

    # 格式化并打印表格
    table_output = format_table(results, len(sample))
    print(table_output)

    # 保存到文件
    output_path = util.get_output_path(__file__)
    util.save_output_to_file(table_output, output_path)

if __name__ == "__main__":
    main()