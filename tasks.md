# Tax App - Task List

Whenever a new feature or fix is requested, it will be added here along with the unit tests that verify it.

## Active Tasks
- [ ] Add your next tasks here!

## Completed Tasks
- [x] Display the Net Investment Income Tax (NIIT) in the frontend UI.
  - **Verification:** Passed `npm run preflight` tests; rendered in `App.jsx` tax breakdowns.
- [x] Add Net Investment Income Tax (NIIT) calculations to the federal tax engine.
  - **Verification:** `backend/tests/test_niit.py` - `test_niit_applied_to_lesser_amount`
- [x] Add unit tests for both single and married filing jointly cases.
  - **Verification:** `backend/tests/test_filing_status.py` - `test_filing_status_differences`
- [x] Fix document upload bug.
- [x] Fix document download bug.
  - **Verification:** `TaxForms.test.jsx` - `should use API_BASE when downloading forms`
- [x] Fix backend test formatting and logic.
- [x] Clear `npm run preflight` checks.
