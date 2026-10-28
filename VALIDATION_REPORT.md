# Blueprint package validation

**Snapshot:** 2026-10-28 · Automated **static** checks passed. This validates the specification files, **not** the working product.

| Measure | Result |
|---|---:|
| openapi operations | 52 |
| openapi paths | 48 |
| ai contract definitions | 22 |
| workflow stages | 25 |
| sql tables | 55 |
| build tickets | 55 |
| acceptance cases | 140 |
| blueprint sections | 24 |

**Validated:** YAML parse, OpenAPI refs and operation IDs, OpenAPI path and security header consistency, AI JSON Schema meta-schema validation, Workflow dependency reference validation, Markdown code-fence and local-link validation, 55 build tickets contiguous, distinct QA case IDs, SQL expected table/invariant static presence.

**Not yet validated:** Actual PostgreSQL DDL migration against a running database, OpenAPI client/server code generation and integration execution, Live provider API authorization, Real video, audio, or human semantic benchmarks, Cloud project provisioning or deployment, Cost or rights verification for an individual series.

**Isolation:** No existing project or account was modified or deployed.
