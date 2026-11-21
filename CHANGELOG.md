# Changelog

## 1.2.0 — Profile, admin details, and UI refinements

- Added user profile editing for full name and username, plus password changes with current-password verification.
- Added administrator profile editing for username and password with current-password verification.
- Made user and administrator identity blocks in their sidebars clickable profile shortcuts.
- Expanded administrator user details with itemized income and expense records across months, including month filters.
- Replaced the browser-native month input with a responsive month/year picker.
- Improved the monthly Expense Limit editor and Create Administrator form layouts.
- Simplified the user login/register screen for small displays.
- Added light/dark theme controls to both login screens and retained the selected theme locally.
- Reworked the Moki mark as a cat mascot to reflect the app's name.


## 1.1.0

- Added a dedicated administrator portal at `/admin` with separate administrator accounts and sessions.
- Added admin overview statistics, user management, user status changes, password reset, soft deletion, and administrator creation.
- Switched user authentication from email to username; account passwords require at least 6 characters.
- Removed the obsolete Expense Standards feature and its legacy table.
- Added month selection to Dashboard, Income, Expenses, and Expense Limits.
- Added the Income Allocation donut chart, showing expense descriptions and Remaining Income against total income.
- Preserved historical transaction and Expense Limit data during the v1 database migration; old sessions are invalidated during the authentication upgrade.
- Added a Vercel FastAPI entry point and same-origin React/FastAPI deployment configuration.
