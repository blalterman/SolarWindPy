# Fix test_drop_species

Assigned to: blalterman

`test_drop_species` is skipped with the comment "Not yet implemented". When temporarily unskipped, it fails with `AttributeError` or `NotImplementedError` depending on the class used. Implement dropping of individual species from a `Plasma` instance and update the test accordingly.

Steps:
1. Remove the skip decorator from `test_drop_species`.
2. Run the test to see the current exceptions.
3. Implement `Plasma.drop_species` so it removes selected species and returns an updated object.
4. Adjust the tests to match the intended API and handle edge cases (e.g., empty plasma).
5. Run all tests to verify the method works across species combinations.
