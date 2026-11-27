# OWASP ZAP Passive Scan Report Summary

- **Scan Mode:** Passive Proxy (Zero active attacks, purely traffic inspection)
- **Total Alerts:** 58
- **High Risk:** 0
- **Medium Risk:** 12
- **Low Risk:** 26
- **Informational:** 20

## Distinct Alert Categories

| Risk Level | Alert Name | Count | CWE ID |
|---|---|---|---|
| **Medium** | Missing Anti-clickjacking Header | 6 | CWE-1021 |
| **Medium** | Content Security Policy (CSP) Header Not Set | 6 | CWE-693 |
| **Informational** | Modern Web Application | 6 | CWE--1 |
| **Low** | X-Content-Type-Options Header Missing | 25 | CWE-693 |
| **Informational** | Information Disclosure - Suspicious Comments | 8 | CWE-615 |
| **Informational** | Information Disclosure - Sensitive Information in URL | 1 | CWE-598 |
| **Informational** | Authentication Request Identified | 3 | CWE--1 |
| **Informational** | Session Management Response Identified | 2 | CWE--1 |
| **Low** | Timestamp Disclosure - Unix | 1 | CWE-497 |
