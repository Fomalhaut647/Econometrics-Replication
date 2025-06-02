#!/usr/bin/env python3
"""
Test script for check.py
"""

import os
import sys
from pathlib import Path

def test_data_exists():
    """Test if data file exists"""
    data_files = ['public.dat', 'FLAT', 'data.txt', 'njpa_data.txt', 'flat_data.txt']
    found_files = []
    
    for filename in data_files:
        if Path(filename).exists():
            found_files.append(filename)
    
    if found_files:
        print(f"✓ Found data file(s): {', '.join(found_files)}")
        return True
    else:
        print("✗ No data files found")
        return False

def test_imports():
    """Test if all required packages can be imported"""
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError:
        print("✗ pandas not available")
        return False
    
    try:
        import numpy as np
        print("✓ numpy imported successfully")
    except ImportError:
        print("✗ numpy not available")
        return False
    
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        print("✓ statsmodels imported successfully")
    except ImportError:
        print("✗ statsmodels not available")
        return False
    
    try:
        from scipy import stats
        print("✓ scipy imported successfully")
    except ImportError:
        print("✗ scipy not available")
        return False
    
    return True

def test_check_module():
    """Test if check.py can be imported"""
    try:
        import check
        print("✓ check.py module imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Error importing check.py: {e}")
        return False

def run_quick_test():
    """Run a quick test of the main functionality"""
    try:
        import check
        
        # Test data reading function
        if Path('public.dat').exists():
            df = check.read_data('public.dat')
            if df is not None:
                print(f"✓ Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
                
                # Test variable creation
                df = check.calculate_derived_variables(df)
                print("✓ Derived variables calculated successfully")
                
                # Check if key variables exist
                key_vars = ['EMPTOT', 'DEMP', 'PCHEMPC', 'gap', 'nj', 'bk', 'kfc', 'roys', 'wendys']
                missing_vars = [var for var in key_vars if var not in df.columns]
                
                if not missing_vars:
                    print("✓ All key derived variables created")
                    return True
                else:
                    print(f"✗ Missing variables: {missing_vars}")
                    return False
            else:
                print("✗ Failed to load data")
                return False
        else:
            print("⚠ No data file found for testing")
            return True
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False

def main():
    """Main test function"""
    print("Testing check.py program...")
    print("=" * 50)
    
    # Test 1: Check imports
    print("\n1. Testing package imports:")
    imports_ok = test_imports()
    
    # Test 2: Check data file
    print("\n2. Testing data file availability:")
    data_ok = test_data_exists()
    
    # Test 3: Check module import
    print("\n3. Testing check.py module:")
    module_ok = test_check_module()
    
    # Test 4: Quick functionality test
    print("\n4. Quick functionality test:")
    if imports_ok and module_ok:
        func_ok = run_quick_test()
    else:
        func_ok = False
        print("⚠ Skipping functionality test due to previous failures")
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"Data file: {'✓ PASS' if data_ok else '✗ FAIL'}")
    print(f"Module import: {'✓ PASS' if module_ok else '✗ FAIL'}")
    print(f"Functionality: {'✓ PASS' if func_ok else '✗ FAIL'}")
    
    if all([imports_ok, data_ok, module_ok, func_ok]):
        print("\n🎉 ALL TESTS PASSED! The program should work correctly.")
        print("Run 'python check.py' to execute the full analysis.")
    else:
        print("\n⚠ Some tests failed. Please check the requirements and fix any issues.")
        if not imports_ok:
            print("   - Install missing packages with: pip install -r requirements.txt")
        if not data_ok:
            print("   - Ensure the data file (public.dat) is in the current directory")

if __name__ == "__main__":
    main() 