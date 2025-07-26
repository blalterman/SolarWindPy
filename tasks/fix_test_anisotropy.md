# Fix test_anisotropy

Assigned to: blalterman

When unskipped, `test_anisotropy` fails with `KeyError: "['scalar'] not found in axis"`. The test expects the `Plasma.anisotropy` method to drop or ignore the `scalar` component correctly. Investigate the DataFrame operations in this method and adjust either the implementation or the test expectations.

Steps:
1. Remove the skip decorator from `test_anisotropy`.
2. Run the test to reproduce the KeyError.
3. Examine how the `scalar` column is handled in `Plasma.anisotropy`.
4. Modify the method or test to properly process all columns.
5. Ensure the corrected test passes for single and multi-species cases.
