<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Personal Data Vault

LibreAssistant ships with a personal data vault for storing information generated
by plugins or uploaded by users. The vault encrypts records at rest and requires
explicit consent before any personal data is persisted.

## Consent Workflow

1. Clients request or revoke consent through `POST /api/v1/consent/{user_id}`.
2. The server records the flag and denies vault operations until consent is set.
3. Users may inspect their current status via `GET /api/v1/consent/{user_id}`.

## Storage Format

Vault entries are stored as JSON objects containing the original payload and
metadata such as timestamps and plugin identifiers. The entire file is encrypted
and associated with the user identifier supplied in the API call.

## Key Rotation

Encryption keys are generated per user and kept in the keyring. Administrators
rotate keys by replacing the stored key material and re‑encrypting existing
records. During rotation, the service reads each entry with the old key and
writes it back with the new key without exposing plaintext outside the
application process.

## Security Implications

- **Limited Access** – vault APIs reject requests without consent, preventing
  silent data collection.
- **Encrypted Records** – JSON payloads are encrypted using the user's key to
  mitigate disk exposure.
- **Auditing** – all vault operations are logged, allowing operators to review
  accesses and deletions.
- **Export & Deletion** – users may export or purge their data, supporting data
  portability and the right to be forgotten.

