# Cryptography, Passwords, and Secrets Interview Cheat Sheet

[Study index](README.md) · Related: [authentication](Authentication_Authorization.md), [tenant/security operations](Multi_Tenancy_Security.md).

Use maintained cryptographic libraries and provider-managed key systems. Mathematical examples are for explanation, never production implementations.

## Contents

Focused follow-ups: [Encoding mechanisms](#what-encoding-really-does) · [Hashing mechanisms and algorithms](#what-hashing-really-does) · [Encryption mechanisms and algorithms](#what-encryption-really-does) · [bcrypt internals and verifier format](#how-bcrypt-works-and-what-the-stored-string-contains) · [Password algorithm comparison](#how-do-the-other-password-algorithms-differ) · [Shamir worked example](#shamir-algorithm-a-small-worked-example).

- [1. Hashing vs. encryption vs. encoding vs. signing?](#1-hashing-vs-encryption-vs-encoding-vs-signing)
- [2. How are passwords stored in a database?](#2-how-are-passwords-stored-in-a-database)
- [3. Salt vs. pepper? Why doesn't hashing stop brute force?](#3-salt-vs-pepper-why-doesnt-hashing-stop-brute-force)
- [4. What is bcrypt, and why is its input limit important?](#4-what-is-bcrypt-and-why-is-its-input-limit-important)
- [5. How should password reset work?](#5-how-should-password-reset-work)
- [6. Symmetric vs. asymmetric encryption and envelope encryption?](#6-symmetric-vs-asymmetric-encryption-and-envelope-encryption)
- [7. What is Shamir's Secret Sharing?](#7-what-is-shamirs-secret-sharing)
- [8. How do you rotate a database credential without downtime?](#8-how-do-you-rotate-a-database-credential-without-downtime)
- [References](#references)

## 1. Hashing vs. encryption vs. encoding vs. signing?

| Mechanism | Purpose | Reversible? / secret | Example |
|---|---|---|---|
| Encoding | Represent bytes in another format | Reversible without a key | Base64, base64url |
| Cryptographic hash | Fixed-size digest; compare content | No decryption key; collisions theoretically exist | SHA-256 |
| Password KDF/hash | Make password guessing expensive | One-way verification; salt plus tunable cost | Argon2id, scrypt, bcrypt, PBKDF2 |
| Encryption | Confidentiality | Decrypt with appropriate key | AES-GCM |
| MAC | Integrity/authenticity among shared-key holders | Shared secret | HMAC-SHA-256 |
| Digital signature | Integrity/authenticity verifiable by public key | Private signing key; public verification key | Ed25519, RSA-PSS |

**Scenario:** passwords must be verified, not recovered, so use a password hashing scheme. A third-party API credential must be recovered to call the provider, so use a vault/encryption. A JWT signature does not make its payload confidential.

**Dig deeper:** a plain hash does not prove who sent a message; an attacker can replace data and digest. Encryption without authenticated integrity can permit tampering. Non-cryptographic routing hashes are not password protection.

### What encoding really does

Encoding changes representation so data can be stored or transported correctly. It supplies no secret protection.

- **UTF-8:** maps Unicode text to bytes; a character may use multiple bytes.
- **Hex/Base16:** represents each byte as two hexadecimal characters; doubles the character count.
- **Base64:** groups bytes into 6-bit values mapped to 64 printable characters; generally grows data by about one third, plus padding.
- **Base64url:** uses `-` and `_` instead of Base64's `+` and `/`; padding rules depend on the protocol. JWT segments omit `=` padding.
- **Percent encoding:** represents bytes such as a space as `%20` for URL components. It is unrelated to encryption.

```python
import base64
import hashlib
raw = b"hello"
assert base64.b64encode(raw) == b"aGVsbG8="
assert base64.b64decode(b"aGVsbG8=") == raw  # no secret key
assert raw.hex() == "68656c6c6f"
assert hashlib.sha256(raw).hexdigest() == (
    "2cf24dba5fb0a30e26e83b2ac5b9e29e"
    "1b161e5c1fa7425e73043362938b9824"
)
```

Base64 and hex can represent plaintext, ciphertext or a hash. Seeing Base64 does not tell you which one is inside. Encoding is not compression either. [Base encodings specification](https://www.rfc-editor.org/rfc/rfc4648).

### What hashing really does

A cryptographic hash deterministically maps arbitrary-length bytes to a digest. SHA-256 produces 256 bits (32 bytes), often displayed as 64 hex characters. Secure hashes aim to resist finding an input for a chosen digest (**preimage**), another input for an existing input's digest (**second preimage**), or any two distinct inputs with the same digest (**collision**).

There is no decryption operation or key for a plain hash. Because many inputs map to a finite output space, a digest does not uniquely encode the original input. Yet attackers can guess candidates and hash them; hashing `password123` with SHA-256 does not make it hard to discover through guessing. Small input changes usually produce very different digests, but this property alone does not establish security.

| Algorithm/family | Mechanism / suitable role | Interview caveat |
|---|---|---|
| SHA-256 / SHA-512 (SHA-2) | Fast cryptographic digest built from block processing and compression functions | Good for digesting data; too fast alone for password storage |
| SHA3-256 | Keccak sponge construction; 256-bit digest | Different construction from SHA-2; also not a password KDF |
| MD5 / SHA-1 | Older digest algorithms | Collision-broken; avoid for new cryptographic integrity/signature designs |
| CRC32 / language object hashes | Checksums or hash-table/routing helpers | Not designed to resist a malicious attacker |

A file digest detects accidental changes, but an attacker who can replace both file and digest can replace both. Use an authenticated source, HMAC or a digital signature when authenticity matters. A plain hash is not proof of authorship. [NIST hash standards](https://csrc.nist.gov/projects/hash-functions).

### What encryption really does

Encryption transforms plaintext into ciphertext using a key; authorized decryption recovers the plaintext. Unlike a password hash, encrypted data is intended to be recovered. Modern authenticated encryption with associated data (**AEAD**) also detects tampering and can authenticate unencrypted metadata.

```text
AEAD encrypt(key, nonce, plaintext, associated_data) -> ciphertext + authentication tag
AEAD decrypt(key, nonce, ciphertext, associated_data, tag) -> plaintext OR failure
```

A nonce is an algorithm-specific per-operation value, normally stored openly with the ciphertext. It is not the secret key. Its uniqueness/randomness requirements depend on the algorithm. The tag detects changes; associated data is authenticated but not encrypted. Never accept decrypted output after authentication failure.

| Algorithm / construction | What it does | Practical caveat |
|---|---|---|
| AES-GCM | AES block cipher with Galois/Counter Mode; AEAD for bulk data | Never reuse a nonce with the same key; use library-approved sizes and limits |
| ChaCha20-Poly1305 | Stream cipher plus authenticator; AEAD for bulk data | Also requires unique nonces per key and correct library use |
| RSA-OAEP | Asymmetric encryption of small messages/keys | Not for bulk files; encryption padding differs from signature padding |
| ECDH / X25519 | Establish shared key material using private/public keys | Key agreement, not standalone encryption or authentication; use a complete authenticated protocol |

AES keys commonly have 128 or 256 bits; a bigger key does not fix nonce misuse, leaked keys or missing authorization. Older DES/3DES and ECB-mode examples are not suitable defaults for new designs. Use maintained protocols/libraries rather than assembling primitives. [OWASP cryptographic storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html), [ChaCha20-Poly1305](https://www.rfc-editor.org/rfc/rfc8439).

### MAC vs. signature: “Is signing encryption with a private key?”

No. A digital signature is a distinct algorithmic operation, not generic private-key encryption. The verifier checks a signature with a public key; it does not decrypt a hidden message. HMAC combines a secret key with a hash construction to authenticate bytes; all shared-key holders can create valid MACs. An unkeyed `SHA256(message)` cannot provide that property.

**End-to-end example:** UTF-8 encodes a JSON document into bytes; AES-GCM encrypts those bytes; Base64 makes the resulting binary ciphertext convenient to transport. A signature or MAC can authenticate a message in the chosen protocol. Passwords instead use a salted password KDF because verification, rather than recovery, is the goal.

**Interview answer:** “Encoding changes representation and anyone can decode it. Encryption hides data and is reversible with a key. Hashing creates a one-way digest, but weak inputs can still be guessed. Password hashing deliberately makes those guesses costly. MACs and signatures establish integrity/authenticity, not confidentiality.”

## 2. How are passwords stored in a database?

Store a password verifier containing algorithm identifier, cost parameters, random salt, and derived hash—not plaintext or reversible encryption. At login, the library recomputes/verifies using stored parameters. On successful login, upgrade an outdated verifier using current policy.

```python
# Django example: configured PASSWORD_HASHERS controls algorithm and parameters.
from django.contrib.auth.hashers import make_password, check_password
stored = make_password("example-only-not-a-real-password")
assert check_password("example-only-not-a-real-password", stored)
# For a real User: user.set_password(raw_password); user.save()
# Do not assign a raw password directly to user.password.
```

| Scheme | Practical position | Tradeoff |
|---|---|---|
| Argon2id | Preferred modern choice when supported | Memory/CPU costs must fit authentication capacity |
| scrypt | Memory-hard alternative | Parameter/library support |
| bcrypt | Established legacy deployments | Input-length constraints; cost tuning; migration planning |
| PBKDF2 | Broad support, including compliance-driven use | CPU-based cost; tune using approved implementation/policy |

Use library-generated salts. Benchmark under concurrent load and rate-limit login to avoid turning expensive verification into easy resource exhaustion. [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

**Dig deeper:** why is SHA-256(password) too fast? What changes after a DB breach? How can you migrate users whose plaintext passwords you do not know?

## 3. Salt vs. pepper? Why doesn't hashing stop brute force?

A salt is random and normally stored with each verifier; it prevents identical passwords producing reusable identical verifiers and defeats broad precomputed tables. A pepper is an additional application secret kept outside the password DB, ideally in a managed secret system. Its loss or rotation creates recovery/migration challenges.

Hashing does not prevent guessing: it raises per-guess cost. Users still need strong credentials, compromised-password defenses, account protections, and MFA where appropriate. Avoid arbitrary home-grown combinations of hash functions or naïve pre-hashing around bcrypt.

**Dig deeper:** if the application and pepper are compromised too, what protection remains? How do you rotate a pepper without knowing old passwords? Where is the algorithm/work factor stored?

## 4. What is bcrypt, and why is its input limit important?

bcrypt is an adaptive password hashing scheme, not encryption. Many implementations have a **72-byte input limit**, with rejection or truncation depending on library behavior/version. Unicode characters can occupy multiple bytes. Your validation and migration policy must respect the exact library, without silently accepting equivalent truncated inputs.

For an existing system, identify verifier versions and library behavior before changing policy. Prefer a well-supported password framework's migration path rather than inventing one. [OWASP bcrypt caveats](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).

**Dig deeper:** why does “increase cost forever” degrade legitimate login and enable DoS? What happens when several replicas share an authentication load spike?

### How bcrypt works and what the stored string contains

bcrypt derives from Blowfish's expensive key setup, commonly called **EksBlowfish**. It combines password and random salt with a tunable work factor, repeatedly performs expensive key setup, and derives a fixed output. Although it uses cipher machinery internally, its password-storage interface is one-way verification; there is no “decrypt bcrypt” operation. [Original bcrypt paper](https://www.usenix.org/legacy/events/usenix99/provos/provos.pdf).

```text
Typical 60-character bcrypt verifier, schematic (not a valid hash):
$2b$12$<22-character salt><31-character derived checksum>
 |   |           |                    |
version       random salt       password-derived output
     logarithmic cost
```

The cost parameter governs approximately `2^cost` expensive setup iterations. Moving from cost 12 to 13 roughly doubles work on the same implementation/hardware; it does not add one millisecond. bcrypt includes a 128-bit salt encoded with its own Base64 alphabet/conventions, not ordinary Base64url. Store the complete library-produced verifier.

At registration, the library generates a salt and verifier. At login, its verification API extracts version, cost and salt, recomputes from the submitted password, and safely compares. Two hashes of the same password normally differ because salts differ; comparing newly generated hash strings directly is wrong. A database thief already knows the salt and cost and can attempt offline guesses, each paying the cost.

### How do the other password algorithms differ?

| Scheme | Core idea | Main tuning dimensions |
|---|---|---|
| Argon2id | Memory-hard construction combining data-independent and data-dependent addressing | Memory, time/iterations and parallelism |
| scrypt | Memory-hard derivation using a large memory structure | CPU/memory cost and parallelization parameters |
| bcrypt | Blowfish-derived expensive key setup; limited memory footprint | Logarithmic CPU work factor; input-length constraints |
| PBKDF2-HMAC-SHA-256 | Repeated HMAC-based derivation | Iteration count and output length; not memory-hard |

Prefer Argon2id for new password storage when supported by the framework/policy. Tune measured latency and peak concurrent resource use using current guidance; do not memorize a cost as permanently safe. Migrate on successful login by verifying the old hash and rehashing the supplied password with the new policy. Hashes cannot be converted to a new password scheme as if the original plaintext were known. [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [Argon2 specification](https://www.rfc-editor.org/rfc/rfc9106).

**Follow-ups:** salt is public and per verifier; pepper is a separately stored secret. Neither substitutes for a suitable password KDF. A nonce belongs to an encryption/protocol operation, while salt belongs to derivation; do not treat these terms as interchangeable.

## 5. How should password reset work?

Issue an unpredictable, short-lived, single-use reset token over an approved channel. Store a verifier/hash of the high-entropy token; bind it to user and purpose; consume it atomically. High-entropy random tokens differ from low-entropy human passwords and do not need the same expensive password KDF in every design.

```sql
-- Illustrative atomic consumption: application checks expiry and binds user/purpose.
UPDATE password_resets SET consumed_at = CURRENT_TIMESTAMP
WHERE token_hash = :digest AND consumed_at IS NULL
  AND expires_at > CURRENT_TIMESTAMP
RETURNING user_id;
```

Avoid logging reset URLs/tokens and do not leak account existence unnecessarily. Define whether password changes invalidate other sessions and refresh tokens.

**Dig deeper:** two simultaneous submissions must not both consume the token. Do you rate-limit creation and verification separately? How do you prevent token disclosure through referrers/analytics?

## 6. Symmetric vs. asymmetric encryption and envelope encryption?

| Choice | Fit | Cost / risk |
|---|---|---|
| Symmetric authenticated encryption | Bulk data | Key distribution and unique nonce requirements |
| Asymmetric cryptography | Key exchange, wrapping, signatures | Slower; algorithm/padding and key handling matter |
| Envelope encryption | Per-object data key wrapped by a KMS key | KMS access/rotation/recovery and metadata management |

Envelope flow: generate data key → encrypt data with an authenticated scheme → wrap key through KMS → store ciphertext, wrapped key, nonce, algorithm/version, and required metadata. Decryption requires both authorized KMS access and correct metadata. Never reuse an AES-GCM nonce with the same key.

**Dig deeper:** encryption at rest does not stop an authorized-but-compromised app reading records. How are key access and data access separated? How do you recover old backups after key rotation? A key deletion can make data unrecoverable.

## 7. What is Shamir's Secret Sharing?

Split a secret into `n` shares such that any `k` can reconstruct it; fewer than `k` reveal no information about it under the scheme's assumptions. It is threshold secret splitting, not the same as encrypting data or obtaining consensus.

**Conceptual example:** a 3-of-5 scheme creates five points on a random degree-2 polynomial over a finite field; its constant term encodes the secret. Any three points determine that polynomial. Ordinary real-number interpolation is not a secure implementation.

| Design | Benefit | Tradeoff |
|---|---|---|
| One administrator holds key | Simple operations | Single compromise/loss point |
| 3-of-5 shares held independently | Tolerates two missing shares; requires threshold cooperation | Custody, verification, recovery rehearsal; three compromised shares expose secret |
| KMS/HSM-backed unseal | Automated operation | Trust/dependency shifts to managed key system |

HashiCorp Vault can use Shamir shares for manual unseal; auto-unseal deployments use a different seal/recovery-key workflow. Do not claim that Oracle OCI Vault uses the same operator unseal procedure. [Vault seal model](https://developer.hashicorp.com/vault/docs/concepts/seal).

**Dig deeper:** where does reconstruction happen? Who can observe the reconstructed secret? Shares need secure distribution and independent custody; basic Shamir sharing does not itself authenticate a malicious share.

### Shamir algorithm: a small worked example

For a `k`-of-`n` scheme, represent secret `s` in a suitable finite field, choose `k-1` uniformly random coefficients, and build `f(x) = s + a1*x + ... + a(k-1)*x^(k-1)`. Give each participant a distinct nonzero `x` and `f(x)`. Reconstruct `f(0)` using finite-field Lagrange interpolation from any `k` valid shares.

Toy 2-of-3 arithmetic over the field modulo 17:

```text
Secret s = 5; random coefficient a = 3
f(x) = (5 + 3*x) mod 17
Shares: (1,8), (2,11), (3,14)
Using the first two: a = (11 - 8)/(2 - 1) = 3 mod 17
s = 8 - 3*1 = 5 mod 17
```

One share `(1,8)` is compatible with every possible secret in this field: for each candidate `s`, a coefficient can satisfy `s+a=8 mod 17`. With a uniformly random coefficient, that share reveals no information about `s`. Division in a finite field means multiplying by a modular inverse, not floating-point division.

This tiny field is solely for mental arithmetic. Real implementations require suitable fields, secure randomness, secret serialization and vetted share handling. Shares are polynomial evaluations, not slices of the original key; concatenating shares does not reconstruct the secret. Basic sharing also does not authenticate shares, enforce organizational independence, or avoid exposing a secret once reconstructed. [Shamir's original paper](https://doi.org/10.1145/359168.359176).

**Interview answer:** “Shamir uses a random polynomial whose constant term is the secret. A threshold number of points reconstructs it with finite-field interpolation; fewer reveal no information under the assumptions. It is threshold secret sharing, separate from encryption, password hashing or multisignature approval.”

## 8. How do you rotate a database credential without downtime?

Use versioned credentials or overlapping principals where the database/provider permits. Create new credential → publish new version → refresh application clients/pools → verify use → revoke old credential after a bounded transition. Exact sequence depends on whether the provider supports simultaneous credentials.

**Failure cases:** stale workers, connection pools retaining old credentials, scale-out using an old image/config, rollback to old software, Vault outage mid-rotation, and the rotation job crashing after an external change. Persist rotation state and reconcile actual provider state rather than assuming each step ran exactly once.

**Measure:** credential version adoption, rotation age, retrieval errors, auth failures, revocation latency, and audit coverage. Avoid secret contents in metric labels or logs.

**Resume drill:** explain which secrets your OCI framework held, how services authenticated to Vault, how recovery worked, and how a partial rotation was detected and repaired.

## References

- [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Django password management](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/)
- [OWASP cryptographic storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [OWASP forgot-password guidance](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- [Vault seal/unseal](https://developer.hashicorp.com/vault/docs/concepts/seal)
- [OCI Vault overview](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm)
