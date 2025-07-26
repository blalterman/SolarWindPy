# Fix test_pth

Assigned to: blalterman

The `test_pth` test is currently skipped because expected and actual DataFrames differ across several species. Unskip the test and investigate why `Plasma.pth` returns a DataFrame with mismatched shape. Update the implementation or test so that the data frames match.

Steps:
1. Remove the `@pytest.mark.skip` decorator from `test_pth` in `tests/test_plasma.py`.
2. Run the test suite to reproduce the failure.
3. Trace the computation of plasma thermal pressure in `Plasma.pth` for each species.
4. Correct the implementation or adjust the expected result in the test.
5. Add regression tests if needed and ensure all tests pass.
