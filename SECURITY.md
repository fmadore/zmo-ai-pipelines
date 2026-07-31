# Security policy

Do not open a public issue containing an API key, personal data, confidential
research material, or an unredacted notebook output. Revoke an exposed key in
Google AI Studio/Cloud immediately and remove it from notebook/widget state.

Report repository vulnerabilities privately to the maintainer through the
security-reporting channel associated with the GitHub repository.

The notebooks execute a helper only after verifying an immutable commit and
SHA-256. If the check fails, stop: do not bypass it by editing out the comparison.
Download a fresh notebook release and compare the repository history.

Google Drive authorization exposes mounted files to notebook code. Review the
notebook, its recorded helper commit, and institutional data-handling approval
before mounting Drive or submitting research material.

