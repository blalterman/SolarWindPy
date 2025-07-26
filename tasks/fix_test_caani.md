# Fix test_caani

Assigned to: blalterman

Unskipping `test_caani` raises a `KeyError` for the `scalar` column. The test validates the combined Alfvén speed and anisotropy calculation. Debug how `Plasma.caani` generates its return values and ensure the `scalar` component is properly derived or excluded.

Steps:
1. Remove the skip decorator from `test_caani`.
2. Run the test suite to observe the failure.
3. Inspect the internals of `Plasma.caani`, especially the use of `Plasma.afsq`.
4. Fix column handling or adjust the expected output in the test.
5. Confirm the repaired code passes all tests.
