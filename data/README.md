data/ 包含5个与 _Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania_ 相关的文件：

* `` `public.dat` `` 一个ASCII（平面文件）数据集（410个观测值）
* `` `codebook` `` `public.dat`数据的ASCII码本
* `` `check.sas` `` 一个SAS程序的ASCII版本，用于读取数据并创建一些关键的制表
* `` `survey1.nj` `` 第一轮调查的文本版本
* `` `survey2.nj` `` 第二轮调查的文本版本

---

# NJ-PA Data Analysis - Python Version

This is a Python translation of the original SAS `check.sas` program for analyzing NJ-PA employment data.

## Overview

The program performs comprehensive data analysis including:
- Data input and validation
- Variable creation and transformations
- Descriptive statistics and frequency tables
- Group comparisons (by state and wage categories)
- Regression analysis examining employment changes

## Requirements

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages:
- pandas (data manipulation)
- numpy (numerical computing)
- scipy (statistical functions)
- statsmodels (regression analysis)
- pathlib (file path handling)

## Data File

The program uses the `public.dat` file included in this directory. It also supports these alternative file names:
- `public.dat` (default)
- `FLAT`
- `data.txt` 
- `njpa_data.txt`
- `flat_data.txt`

The data file contains space-separated values with 47 variables including employment data, wages, and store characteristics for two survey waves.

## Quick Start

1. **Test the setup** (recommended first step):
   ```bash
   python test_check.py
   ```
   This will verify that all dependencies are installed and the data file is accessible.

2. **Run the full analysis**:
   ```bash
   python check.py
   ```

## Files Included

- `check.py` - Main analysis program (Python version of check.sas)
- `test_check.py` - Test script to verify setup
- `requirements.txt` - Python package dependencies
- `public.dat` - Data file
- `README.md` - This documentation

## Output

The program generates the following analyses:

1. **Frequency Tables**: Distribution of categorical variables (chains, state, status, etc.)
2. **Descriptive Statistics**: Summary statistics for all variables
3. **Table 2**: Statistics by NJ/PA state
4. **Table 3**: Employment changes by state and wage categories  
5. **Closed Stores Analysis**: List of stores that closed between waves
6. **Table 4**: Regression analysis of employment changes

## Key Variables Created

The program creates several derived variables:

- `EMPTOT`: Total employment (full-time + 0.5×part-time + managers)
- `DEMP`: Change in employment between waves
- `PCHEMPC`: Percent change in employment
- `gap`: Wage gap relative to minimum wage (5.05)
- `nj`: New Jersey indicator (1=NJ, 0=PA)
- Chain indicators: `bk`, `kfc`, `roys`, `wendys`
- `CLOSED`: Store closure indicator
- `ICODE`: Store classification by state and wage level

## Regression Models

The program fits 10 regression models examining:

1. **Employment change models (DEMP)**:
   - Model 1: DEMP ~ gap
   - Model 2: DEMP ~ gap + chain controls
   - Model 3: DEMP ~ gap + chain + location controls
   - Model 4: DEMP ~ nj
   - Model 5: DEMP ~ nj + chain controls

2. **Percent employment change models (PCHEMPC)**:
   - Model 6: PCHEMPC ~ gap
   - Model 7: PCHEMPC ~ gap + chain controls
   - Model 8: PCHEMPC ~ gap + chain + location controls
   - Model 9: PCHEMPC ~ nj
   - Model 10: PCHEMPC ~ nj + chain controls

## Troubleshooting

If you encounter issues:

1. **Missing packages**: Run `pip install -r requirements.txt`
2. **Data file not found**: Ensure `public.dat` is in the same directory
3. **Import errors**: Check that you're using Python 3.6 or later
4. **Runtime errors**: Run the test script first: `python test_check.py`

## Notes

- The program handles missing data appropriately
- Error handling is included for all regression models
- Output matches the structure and content of the original SAS program
- All variable transformations replicate the SAS logic exactly
- The analysis subset for regression excludes stores with missing employment change data or invalid wage transitions