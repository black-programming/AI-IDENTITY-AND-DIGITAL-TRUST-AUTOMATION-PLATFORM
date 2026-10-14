# Git Branching, Commit Conventions & Security Standards

## 1. Branching Strategy
We adhere to a Trunk-Based Development with Short-Lived Feature Branches workflow:

- `main`: Production-ready release code. Protected branch. Direct pushes prohibited.
- `develop`: Staging and active integration branch.
- `feature/<ticket-or-scope>`: Feature development (e.g., `feature/ocr-paddle-integration`, `feature/rls-evidence-policies`).
- `fix/<issue-name>`: Bug fixes (e.g., `fix/jwt-expiration-handling`).
- `release/vX.Y.Z`: Release stabilization branches.

---

## 2. Commit Message Conventions (Conventional Commits)
All commit messages must adhere to the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <short imperative summary>

[optional body explaining context, why this change was needed]

[optional footer(s), e.g. Closes #123]
```

### Supported Types:
- `feat`: A new feature introduced into the codebase.
- `fix`: A bug fix.
- `docs`: Documentation-only changes (Markdown, guides).
- `style`: Formatting, missing semicolons, whitespace (no functional code changes).
- `refactor`: Code refactoring without changing observable behavior or API contracts.
- `perf`: Performance optimizations.
- `test`: Adding or correcting automated tests.
- `chore`: Build process, package updates, CI/CD, or auxiliary tooling changes.

### Examples:
- `feat(policy): implement deterministic MRZ checksum evaluation`
- `fix(auth): reject expired JWT tokens with 401 Unauthorized`
- `docs(arch): update C4 container diagram with Redis task queue`
- `test(security): add cross-tenant RLS access rejection test`

---

## 3. Secret Management & Prevention Rules
1. **Never Commit Secrets:** Never commit `.env`, private keys (`.pem`, `.key`), database passwords, or the Supabase `service_role` key.
2. **Environment Variable Injection:** All sensitive values must be injected at runtime via environment variables or secret managers (e.g., GitHub Secrets, Azure Key Vault).
3. **Pre-Commit Checks:** Every branch before merging must run static analysis and secret detection tools.
4. **Immediate Revocation:** If a key is accidentally exposed in git history, it must be considered compromised and rotated immediately, followed by repo history sanitization.
