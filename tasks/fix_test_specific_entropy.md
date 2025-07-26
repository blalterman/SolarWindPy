# Fix test_specific_entropy

Assigned to: blalterman

This test fails with `KeyError: 'scalar'` when the skip marker is removed. The issue arises while fetching the scalar component of plasma pressure in `Plasma.specific_entropy`. Determine whether the calculation should include a scalar column or use a different index.

Steps:
1. Unskip `test_specific_entropy` in `tests/test_plasma.py`.
2. Run the test suite to reproduce the KeyError.
3. Trace the calculation of thermal pressure and density within `Plasma.specific_entropy`.
4. Add or adjust the `scalar` component as needed to satisfy the test expectations.
5. Verify all updated tests pass.
