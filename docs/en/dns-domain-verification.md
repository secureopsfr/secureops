# DNS domain verification — User guide

This guide describes the **end-user flow** for proving control of a domain before a **non-passive** scan. The technical specification (API, SQL schema, scan-service assert) is in [VERIFICATION-AUTORISATION.md](../VERIFICATION-AUTORISATION.md).

**In the product:** the same material is available in the Scanner hub as the “DNS verification” help page (`/en/scanner/docs/verification-dns`).

## Summary

1. Enter the URL to scan for any mode other than passive (intrusive, custom, destructive, …).
2. **Generate DNS instructions**: host `_secureops-verify.<domain>` and a unique **TXT value**.
3. Publish the **TXT** record at your DNS provider and wait for propagation.
4. Click **Verify TXT** in SecureOps: the service queries public DNS and validates the proof.
5. While verification is valid (not expired) and bound to your account, matching non-passive scans can run (passive scan does not require this proof).

## See also

- [Intrusive scan documentation (repo)](../verifications/intrusive/README.md) — links to this flow.
- [Environment variables](../VARIABLES-ENVIRONNEMENT.md) — flags and TTLs.
