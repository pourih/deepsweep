import subprocess
import sys
import os

print("=" * 60)
print("DEEPSWEEP COMPLETE INTEGRATED TEST SUITE")
print("=" * 60)

all_passed = True

# 1. Run Issues 1 & 2
print("\n--- Running Tests for Issues #1 & #2 ---")
r1 = subprocess.run([sys.executable, "tests/test_issues.py"], capture_output=True, text=True, encoding="utf-8")
print(r1.stdout)
if r1.returncode != 0:
    all_passed = False

# 2. Run Issues 3, 4 & 5
print("\n--- Running Tests for Issues #3, #4 & #5 ---")
r2 = subprocess.run([sys.executable, "tests/test_issues_3_4_5.py"], capture_output=True, text=True, encoding="utf-8")
print(r2.stdout)
if r2.returncode != 0:
    all_passed = False

# 3. Full Page Load & DOM Verification
print("\n--- Running Full Page Load & Linter Integrity Check ---")
r3 = subprocess.run([sys.executable, "tests/test_full_page.py"], capture_output=True, text=True, encoding="utf-8")
print(r3.stdout)
if r3.returncode != 0:
    all_passed = False

print("=" * 60)
if all_passed:
    print("ALL TESTS PASSED SUCCESSFULLY! ZERO REGRESSIONS.")
else:
    print("SOME TESTS FAILED.")
print("=" * 60)

sys.exit(0 if all_passed else 1)
