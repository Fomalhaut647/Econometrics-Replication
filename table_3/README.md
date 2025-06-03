# Table 3 Replication

This directory contains the Python script to replicate Table 3 from Card and Krueger (1994) "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania".

## Files

- `replicate.py`: Main Python script for replicating Table 3
- `README.md`: This documentation file
- `standard_output.md`: Reference output provided for comparison
- `output.md`: Generated output from running the replication script

## Script Description

The `replicate.py` script reproduces Table 3: "Average Employment per Store Before and After the Rise in New Jersey Minimum Wage". The script:

1. **Reads the data** from `../data/public.dat` using fixed-width format parsing according to the codebook
2. **Calculates Full-Time Equivalent (FTE) employment** using the formula: FTE = EMPFT + NMGRS + 0.5 * EMPPT
3. **Handles store closures** appropriately:
   - Permanently closed stores (STATUS2 == 3): FTE2 set to 0
   - Temporarily closed stores (STATUS2 == 2): FTE2 treated as missing for rows 1-4, set to 0 for row 5
4. **Creates wage groups** for New Jersey stores based on Wave 1 starting wages:
   - Low wage: exactly $4.25 per hour
   - Mid wage: $4.26 to $4.99 per hour  
   - High wage: $5.00 or more per hour
5. **Calculates statistics** for 5 different specifications:
   - Row 1: FTE employment before (Wave 1), all available observations
   - Row 2: FTE employment after (Wave 2), all available observations
   - Row 3: Change in mean FTE employment
   - Row 4: Change in mean FTE employment, balanced sample of stores
   - Row 5: Change in mean FTE employment, setting FTE at temporarily closed stores to 0

## Dependencies

The script requires the following Python packages:

- pandas
- numpy
- pathlib (part of Python standard library)

## How to Run

1. Ensure you have Python 3.x installed with the required dependencies
2. Navigate to the `table_3/` directory
3. Run the script:

```bash
python replicate.py
```

The script will:
- Read the data from `../data/public.dat`
- Process the data and calculate all required statistics
- Generate `output.md` with the replicated table in Markdown format
- Print progress messages to the console

## Output

The script generates `output.md` containing Table 3 in Markdown table format with:
- Means and standard errors (in parentheses) for each group and specification
- Differences between groups with their standard errors
- Comprehensive footnotes explaining the methodology

## Notes

- All standard errors are calculated as the standard error of the mean (sample standard deviation divided by square root of sample size)
- The script handles missing data appropriately by excluding stores with missing employment data from relevant calculations
- The balanced sample consists of stores with valid employment data in both Wave 1 and Wave 2
