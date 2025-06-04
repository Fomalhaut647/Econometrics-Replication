#!/usr/bin/env python3
"""
Card 和 Krueger (1994) 论文中表格9的复制脚本
"最低工资与就业：新泽西州和宾夕法尼亚州快餐业的案例研究"

此脚本基于表格4的模型4，创建三个扩展模型进行对比分析。
"""

import sys
import os

# 添加根目录到Python路径以导入utility模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import utility as util
import statsmodels.formula.api as smf
import numpy as np


def create_additional_variables(df):
    """
    创建表格9需要的额外变量
    """
    df = df.copy()

    # 创建新泽西州且起薪为$4.25的虚拟变量
    # 当wave1的起薪是4.25$且在新泽西州时等于1，否则等于0
    # 使用nj变量(新泽西州=1)和WAGE_ST变量(起薪)
    df['nj_wage425'] = ((df['WAGE_ST'] == 4.25) & (df['nj'] == 1)).astype(int)

    # 创建GAP的二次项
    df['gap_squared'] = df['gap'] ** 2

    return df


def run_regressions(df):
    """
    运行表格9的三个回归模型
    """
    results = {}

    # 模型 (i): 基础模型 - 与表格4的模型(iv)相同
    # DEMP ~ GAP + 连锁店和所有权控制变量
    model1 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model1'] = model1

    # 模型 (ii): 基础模型 + 新泽西州$4.25起薪虚拟变量
    model2 = smf.ols('DEMP ~ gap + bk + kfc + roys + CO_OWNED + nj_wage425', data=df).fit()
    results['model2'] = model2

    # 模型 (iii): 基础模型 + GAP二次项
    model3 = smf.ols('DEMP ~ gap + gap_squared + bk + kfc + roys + CO_OWNED', data=df).fit()
    results['model3'] = model3

    return results


def calculate_turning_point_analysis(model3):
    """
    计算model3的拐点并与基准值进行比较
    """
    # 获取系数
    gap_coef = model3.params.get('gap', None)
    gap_squared_coef = model3.params.get('gap_squared', None)

    if gap_coef is None or gap_squared_coef is None:
        return None

    # 计算拐点: 对于二次函数 y = ax + bx^2，拐点在 x = -a/(2b)
    if gap_squared_coef != 0:
        turning_point = -gap_coef / (2 * gap_squared_coef)
    else:
        turning_point = None

    # 计算基准比较值: (5.05-4.25)/4.25
    benchmark = (5.05 - 4.25) / 4.25

    analysis = {
        'turning_point': turning_point,
        'benchmark': benchmark,
        'gap_coef': gap_coef,
        'gap_squared_coef': gap_squared_coef
    }

    return analysis


def format_table(results, sample_size):
    """
    将结果格式化为与标准表格布局一致的表格9
    """
    # 表格标题
    title = "**TABLE 9-EXTENDED MODELS FOR CHANGE IN EMPLOYMENT**"

    # 提取系数和标准误
    def get_coef_se(model, var):
        if var in model.params.index:
            coef = model.params[var]
            se = model.bse[var]
            return coef, se
        return None, None

    # 初始化表格数据
    table_data = []

    # 第1行: 初始工资差距
    row1 = ['1. Initial wage gap<sup>a</sup>']
    gap_coef1, gap_se1 = get_coef_se(results['model1'], 'gap')
    gap_coef2, gap_se2 = get_coef_se(results['model2'], 'gap')
    gap_coef3, gap_se3 = get_coef_se(results['model3'], 'gap')

    row1.extend([
        util.format_coefficient(gap_coef1, gap_se1) if gap_coef1 is not None else "",
        util.format_coefficient(gap_coef2, gap_se2) if gap_coef2 is not None else "",
        util.format_coefficient(gap_coef3, gap_se3) if gap_coef3 is not None else ""
    ])
    table_data.append(row1)

    # 第2行: 新泽西州$4.25起薪虚拟变量
    row2 = ['2. NJ dummy for $4.25 starting wage<sup>b</sup>']
    nj425_coef2, nj425_se2 = get_coef_se(results['model2'], 'nj_wage425')

    row2.extend([
        "",  # 模型1中没有此变量
        util.format_coefficient(nj425_coef2, nj425_se2) if nj425_coef2 is not None else "",
        ""  # 模型3中没有此变量
    ])
    table_data.append(row2)

    # 第3行: GAP二次项
    row3 = ['3. Initial wage gap squared<sup>c</sup>']
    gap2_coef3, gap2_se3 = get_coef_se(results['model3'], 'gap_squared')

    row3.extend([
        "",  # 模型1中没有此变量
        "",  # 模型2中没有此变量
        util.format_coefficient(gap2_coef3, gap2_se3) if gap2_coef3 is not None else ""
    ])
    table_data.append(row3)

    # 第4行: 连锁店和所有权控制变量
    row4 = ['4. Controls for chain and ownership<sup>d</sup>']
    row4.extend(['yes', 'yes', 'yes'])
    table_data.append(row4)

    # 第5行: R-squared
    row5 = ['5. R-squared']
    row5.extend([
        f"{results['model1'].rsquared:.3f}",
        f"{results['model2'].rsquared:.3f}",
        f"{results['model3'].rsquared:.3f}"
    ])
    table_data.append(row5)

    # 第6行: 回归标准误
    row6 = ['6. Standard error of regression']
    row6.extend([
        f"{results['model1'].scale ** 0.5:.2f}",
        f"{results['model2'].scale ** 0.5:.2f}",
        f"{results['model3'].scale ** 0.5:.2f}"
    ])
    table_data.append(row6)

    # 第7行: 控制变量的F检验概率值
    row7 = ['7. Probability value for controls<sup>e</sup>']
    chain_controls = ['bk', 'kfc', 'roys', 'CO_OWNED']

    p_val1 = util.calculate_f_test_pvalue(results['model1'], chain_controls)
    p_val2 = util.calculate_f_test_pvalue(results['model2'], chain_controls)
    p_val3 = util.calculate_f_test_pvalue(results['model3'], chain_controls)

    row7.extend([
        f"{p_val1:.2f}" if p_val1 is not None else "",
        f"{p_val2:.2f}" if p_val2 is not None else "",
        f"{p_val3:.2f}" if p_val3 is not None else ""
    ])
    table_data.append(row7)

    # 第8行: 新增变量的F检验概率值
    row8 = ['8. Probability value for additional variable<sup>f</sup>']

    # 模型2中新增变量的t检验转换为F检验
    t_stat2 = results['model2'].tvalues.get('nj_wage425', None)
    p_val_add2 = results['model2'].pvalues.get('nj_wage425', None)

    # 模型3中新增变量的t检验转换为F检验
    t_stat3 = results['model3'].tvalues.get('gap_squared', None)
    p_val_add3 = results['model3'].pvalues.get('gap_squared', None)

    row8.extend([
        "",  # 模型1没有新增变量
        f"{p_val_add2:.2f}" if p_val_add2 is not None else "",
        f"{p_val_add3:.2f}" if p_val_add3 is not None else ""
    ])
    table_data.append(row8)

    # 创建 markdown 表格
    header = "| Independent variable                       | Model (i)   | Model (ii)  | Model (iii) |"
    separator = "| :----------------------------------------- | :---------- | :---------- | :---------- |"

    table_lines = [title, "", header, separator]
    for row in table_data:
        line = f"| {row[0]:<42} | {' | '.join(f'{cell:<11}' for cell in row[1:])} |"
        table_lines.append(line)

    # 添加拐点分析
    turning_analysis = calculate_turning_point_analysis(results['model3'])
    if turning_analysis:
        table_lines.extend([
            "",
            "**TURNING POINT ANALYSIS FOR MODEL (III)**",
            "",
            f"Turning point of quadratic function: {turning_analysis['turning_point']:.4f}" if turning_analysis[
                                                                                                   'turning_point'] is not None else "Turning point: undefined (no quadratic term)",
            f"Benchmark comparison value [(5.05-4.25)/4.25]: {turning_analysis['benchmark']:.4f}",
            "",
            f"Gap coefficient: {turning_analysis['gap_coef']:.4f}",
            f"Gap squared coefficient: {turning_analysis['gap_squared_coef']:.6f}",
            "",
            "Interpretation:",
            f"- The quadratic relationship peaks/troughs at a wage gap of {turning_analysis['turning_point']:.4f}" if
            turning_analysis[
                'turning_point'] is not None else "- No clear turning point due to zero quadratic coefficient",
        ])

        if turning_analysis['turning_point'] is not None:
            if turning_analysis['turning_point'] > turning_analysis['benchmark']:
                table_lines.append(
                    f"- This turning point ({turning_analysis['turning_point']:.4f}) is HIGHER than the benchmark ({turning_analysis['benchmark']:.4f})")
            elif turning_analysis['turning_point'] < turning_analysis['benchmark']:
                table_lines.append(
                    f"- This turning point ({turning_analysis['turning_point']:.4f}) is LOWER than the benchmark ({turning_analysis['benchmark']:.4f})")
            else:
                table_lines.append(
                    f"- This turning point ({turning_analysis['turning_point']:.4f}) is EQUAL to the benchmark ({turning_analysis['benchmark']:.4f})")

            table_lines.append(
                f"- Difference: {abs(turning_analysis['turning_point'] - turning_analysis['benchmark']):.4f}")

    # 添加注释
    notes = [
        "",
        f"Notes: Standard errors are given in parentheses. The sample consists of {sample_size} stores with available data on employment and starting wages in waves 1 and 2. The dependent variable in all models is change in FTE employment. The mean and standard deviation of the dependent variable are {results['model1'].model.endog.mean():.3f} and {results['model1'].model.endog.std():.3f}, respectively. All models include an unrestricted constant (not reported).",
        "",
        "<sup>a</sup> Proportional increase in starting wage necessary to raise starting wage to new minimum rate. For stores in Pennsylvania the wage gap is 0.",
        "<sup>b</sup> Dummy variable equals 1 for New Jersey stores with starting wage of $4.25 in wave 1, 0 otherwise.",
        "<sup>c</sup> Square of the initial wage gap variable.",
        "<sup>d</sup> Three dummy variables for chain type and whether or not the store is company-owned are included.",
        "<sup>e</sup> Probability value of joint F test for exclusion of chain and ownership control variables.",
        "<sup>f</sup> Probability value for t-test of additional variable (converted from t-statistic)."
    ]

    return "\n".join(table_lines + notes)


def main():
    """
    主函数，用于复制表格9
    """
    # 使用utility模块加载和处理数据
    df = util.read_data()
    df = util.create_basic_derived_variables(df)

    # 创建分析样本
    sample = util.create_analysis_sample(df)

    # 创建表格9需要的额外变量
    sample = create_additional_variables(sample)

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