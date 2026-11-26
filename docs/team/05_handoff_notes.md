# Team Hand-Off Notes (Member 1 — 24i-3112)

## 1. Running Member 1 Unit Tests & JaCoCo Check Locally

From the repository root:

```bash
./mvnw clean test -Dtest="*WhiteBoxTest" jacoco:report jacoco:check
```

*(On Windows PowerShell, use `.\mvnw` instead of `./mvnw`.)*

- Team unit tests live under `tests/team/unit/` (registered via `build-helper-maven-plugin` in `pom.xml`).
- To run the full suite (team unit tests + upstream Testcontainers integration tests, requiring Docker):
  ```bash
  ./mvnw test
  ```

## 2. Running PIT Mutation Testing from a Fresh Machine

The custom business-rule mutator module (`tools/pit-custom-mutators/`) must be installed into your local Maven repository before running PIT:

**Linux / macOS:**
```bash
./mvnw -f tools/pit-custom-mutators/pom.xml clean install
./mvnw test-compile org.pitest:pitest-maven:mutationCoverage
```

**Windows (PowerShell / cmd):**
```powershell
.\mvnw.cmd -f tools/pit-custom-mutators/pom.xml clean install
.\mvnw.cmd test-compile org.pitest:pitest-maven:mutationCoverage
```

Clean-cache verification logs (empty local Maven repository): [`08a_clean_cache_mutator_install.txt`](evidence/08a_clean_cache_mutator_install.txt) and [`08b_clean_cache_pit.txt`](evidence/08b_clean_cache_pit.txt).

## 3. CI Workflow

- Planned for **Task 7** (`.github/workflows/ci.yml`).
