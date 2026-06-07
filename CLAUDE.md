# MiMo Worker Contract

This repository is orchestrated by Codex. Claude CLI workers use the configured
`mimo-v2.5-pro` model for bounded implementation tasks.

## Rules

- Modify only paths explicitly assigned in the task prompt.
- Do not run Git history-changing commands, commit, merge, rebase, or push.
- Do not read `.env`, keychains, credentials, browser state, or files outside the repository.
- Do not deploy, install global software, or bypass permission checks.
- Do not weaken types with `any`, blanket ignores, or unvalidated dictionaries.
- Do not suppress exceptions. Return typed errors and preserve transaction rollback.
- Public endpoints must use the shared spoiler policy; future content must never leak in payloads.
- Run the exact verification commands provided by the task.
- Return JSON containing `changed_files`, `tests_run`, `test_results`, and `known_issues`.

Workers are not alone in the codebase. Never revert unrelated edits; adapt to the current branch.

