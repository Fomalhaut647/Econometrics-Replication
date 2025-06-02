# Card and Krueger (1994) Table 2 复现程序

## 简介

本程序用于复现经典论文 Card, David and Alan B. Krueger (1994) "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania" 中的 **Table 2: Means of Key Variables**。

## 文件说明

- `table2_analysis.py`: 主程序文件，用于计算和输出Table 2的统计结果
- `data/public.dat`: 原始数据文件（410个观测值）
- `data/codebook`: 数据变量的详细说明文档
- `data/README.md`: 数据文件和计算要求的中文说明

## 使用方法

### 依赖包安装

```bash
pip install pandas numpy scipy
```

### 运行程序

```bash
python table2_analysis.py
```

## 程序功能

程序按照论文要求计算以下三个部分：

### 第一部分：店铺类型的分布 (Percentages)
计算NJ和PA两州中各类型店铺所占的百分比：
- a. Burger King
- b. KFC  
- c. Roy Rogers
- d. Wendy's
- e. Company-owned (公司自营)

### 第二部分：Wave 1 的均值
计算第一轮调查数据的均值和标准误：
- a. FTE employment: 全职员工数量(含管理人员)加上兼职员工数量乘以0.5
- b. Percentage full-time employees: 全职员工百分比
- c. Starting wage: 起始工资
- d. Wage = $4.25 (percentage): 时薪为$4.25的员工百分比
- e. Price of full meal: 套餐价格(汽水+薯条+主食)
- f. Hours open (weekday): 工作日营业时间
- g. Recruiting bonus: 招聘奖金

### 第三部分：Wave 2 的均值
计算第二轮调查数据的均值和标准误：
- a-g. 与Wave 1相同的变量
- e. Wage = $5.05 (percentage): 时薪为$5.05的员工百分比（新增）
- h. Recruiting bonus: 招聘奖金

## 数据处理说明

根据论文要求：
1. **永久关闭的店铺**（STATUS2=3）：员工数设为0
2. **暂时关闭的店铺**（STATUS2=2,4,5）：按缺失值处理
3. **t统计量**：用于检验NJ和PA两州之间差异的统计显著性

## 主要结果解读

程序输出显示：

1. **店铺分布**：两州快餐店类型分布相对均衡
2. **Wave 1**：两州在工资水平上差异不大，但NJ的套餐价格显著更高
3. **Wave 2**：NJ实施最低工资提高后，起始工资显著上升（从4.61升至5.08），同时$5.05工资占比达到89%，而PA基本保持不变

这些结果支持了Card and Krueger的核心发现：最低工资提高并没有导致就业减少，反而在某些指标上有所改善。

## 技术细节

- 使用固定宽度文件解析方式读取`public.dat`
- 根据codebook精确定义各变量的列位置
- 采用Welch's t-test进行两组独立样本比较（不假设方差相等）
- 对于比例变量，使用两比例差异的z检验

## 联系方式

如有问题或建议，请参考原始论文和数据文档。 