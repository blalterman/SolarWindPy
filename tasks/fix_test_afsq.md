# Fix test_afsq

Assigned to: blalterman

`test_afsq` fails with `KeyError: "['scalar'] not found in axis"` when the skip marker is removed. The test covers the `Plasma.afsq` calculation. Diagnose how the method builds its DataFrame and ensure the `scalar` column is handled properly.

Steps:
1. Unskip `test_afsq` in `tests/test_plasma.py`.
2. Run the test to view the failure.
3. Review `Plasma.afsq` to check which columns are selected and dropped.
4. Update the method or test to consistently manage the `scalar` column.
5. Run the full test suite to confirm the fix.
