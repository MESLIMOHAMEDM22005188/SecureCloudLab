# Secret exposure response procedure

If a credential, token, private key, or other secret is found in Git:

1. **Revoke or rotate immediately.** Treat it as compromised; deleting the line or rewriting Git history does not make a leaked credential safe.
2. **Contain access.** Disable the affected identity or key, review permissions, and check whether the credential was used.
3. **Investigate.** Review provider audit logs (for AWS, CloudTrail and relevant service logs) from the earliest possible exposure time. Record findings without copying the secret into tickets or chat.
4. **Remove from the repository.** Remove the secret from tracked files and, where appropriate, coordinate a history rewrite. Coordinate with collaborators before force-pushing. Assume forks, caches, logs, and clones may retain it.
5. **Replace safely.** Use GitHub Actions secrets or an approved secret manager. Prefer short-lived role-based credentials over static access keys.
6. **Verify and document.** Re-run the secret scanner, confirm rotation, record impact and remediation, and add a regression test or narrow scanner rule if needed.

Never paste the secret into an issue, commit message, remediation report, or support request. Do not rely on history rewriting instead of rotation.
