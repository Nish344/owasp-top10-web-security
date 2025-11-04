# Referer-Based Access Control Can Be Spoofed  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Referer-Bypass-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-11-04  
**Tag**: `Broken-Access-Control`, `Referer-Spoofing`, `Header-Tampering`, `Admin-Bypass`, `Privilege-Escalation`  

---

## Executive summary

The admin panel protects the role-upgrade endpoint (`GET /admin-roles?username=…&action=upgrade`) by checking the **Referer** header for the exact value `https://…/admin`. No other authorization occurs.  
By copying a legitimate admin request into **Burp Repeater**, replacing the session cookie with a non-admin one, and **keeping the Referer header intact**, any authenticated user can trigger the upgrade action on themselves. The server blindly trusts the spoofable header and promotes the attacker to administrator.

**Result:** `wiener` (non-admin) → `GET /admin-roles?…` with **wiener session + admin Referer** → instantly promoted to admin.  
**Severity (subjective):** Critical — trivial, one-click escalation for every logged-in user.  
**Recommended immediate action:** **Remove Referer-based checks**; enforce **server-side role validation** on every admin request.

---

## Objective

Exploit Referer-based access control to promote the non-admin user `wiener` to administrator.

---

## Environment & tools

* Target: PortSwigger lab instance (`0ad70063037b5470819fa2e2006d009f.web-security-academy.net`).  
* Tools: Burp Suite (Proxy → Repeater), two browser sessions.  
* Notes:  
  - Admin: `administrator:admin`  
  - Victim: `wiener:peter`  
  - Endpoint: `GET /admin-roles?username={target}&action=upgrade`  
  - Only defense: `Referer: https://…/admin`

---

## Discovery  

1. Logged in as **admin** → Admin panel → “Upgrade carlos” → Burp intercepts:  
   ```
   GET /admin-roles?username=carlos&action=upgrade
   Referer: https://0ad7…/admin
   ```  
2. Sent to **Repeater**.  
3. As **wiener**, browsed directly to `/admin-roles?username=wiener&action=upgrade` → **403** (“Missing Referer”).  
4. Pasted **wiener’s session cookie** into the Repeater tab **but left Referer unchanged** → sent → **302 redirect** → success!

> Finding: **Referer is the sole gatekeeper**; the server never checks the user’s role.

---

## Reproduction steps  

1. Log in as `administrator:admin` → upgrade any user → **intercept GET** → send to Repeater.  
2. Open incognito → log in as `wiener:peter` → copy **session** cookie.  
3. In Repeater:  
   - Replace `Cookie: session=…` with wiener’s value  
   - Change `username=carlos` → `username=wiener`  
   - **Leave Referer header exactly as-is**  
4. Click **Send** → response `302` → wiener is now admin.  
5. Refresh `/admin` → lab solved.

**Exploited request (exact copy-paste ready):**
```
GET /admin-roles?username=wiener&action=upgrade HTTP/2
Host: 0ad70063037b5470819fa2e2006d009f.web-security-academy.net
Cookie: session=mld0aoZi1mieHpf4H7cLldZv1PCaFcj9
Referer: https://0ad70063037b5470819fa2e2006d009f.web-security-academy.net/admin
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
```

---

## Observed impact

* **Every authenticated user** can self-promote to admin in **one request**.  
* Full vertical privilege escalation.  
* No CSRF token, no role check, no rate-limit.  
* Real-world equivalent: instant admin takeover on any site using Referer for authz.

---

## Root cause analysis

* **Primary cause:**  
  ```python
  if request.headers.get('Referer', '').endswith('/admin'):
      upgrade_user()   # ← no is_admin() check
  ```  
* **Secondary causes:**  
  - Headers are **100 % client-controlled**.  
  - Confusion between **origin validation** (anti-CSRF) and **authorization**.  
  - GET used for state-changing operation.

---

## Risk assessment

| Likelihood | Impact   | Overall   |
|------------|----------|-----------|
| Very High  | Critical | Critical  |

CVSS v3.1: **9.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)**

---

## Remediation  

### Immediate (5-minute fix)
```python
@app.route('/admin-roles')
def admin_roles():
    if not current_user.is_admin:
        abort(403)
    # ... existing code ...
```

### Medium-term
1. **Delete all Referer checks** for authorization.  
2. Use **CSRF tokens** only for CSRF, never for role checks.  
3. Switch to **POST** with anti-CSRF for mutations.  
4. Add WAF rule (temporary band-aid):  
   ```
   block if path=/admin-roles and header:Referer contains "admin" and not cookie:session=admin_session
   ```

### Long-term
- Central `@admin_required` decorator on every admin route.  
- Audit log every role change (user, IP, headers).  
- Automated test:  
  ```bash
  curl -b "session=wiener" -H "Referer: /admin" "/admin-roles?username=wiener&action=upgrade" → 403
  ```

---

## Detection & verification guidance  

* Search codebase for `.Referer`, `.get('Referer')`, `HTTP_REFERER`.  
* In Burp: **right-click any admin request → “Send to Repeater” → delete Referer → resend** → must 403.  
* Add OWASP ZAP active rule: “Referer Based Authorization”.

---

## Suggested tests to add

| Test | Expected |
|------|----------|
| Non-admin + valid Referer | 403 |
| Admin + missing Referer   | 200 |
| GET with body (upgrade)   | 405 |
| POST upgrade (if added)   | 200 + CSRF check |

---

## References & further reading

* OWASP Top 10 — A01: Broken Access Control  
* PortSwigger: “Referer-based access controls”  
* RFC 7231 §5.5.2: Referer is optional and forgeable  
* Header Security Cheat Sheet: **Never use Referer for authorization**

---

## Notes & lessons learned

* **Referer is NOT an access-control mechanism** — it’s a hint, not a lock.  
* One header = one-click admin.  
* Always **chain** defenses: session → role → CSRF → input validation.  
* Burp Repeater + “Copy session” = instant header-spoof lab solver.

---

## Evidence & validation  

* Direct access without Referer → 403  
* Spoofed Referer + wiener session → 302 → admin panel lists wiener as admin
<img width="721" height="343" alt="Screenshot 2025-11-04 201814" src="https://github.com/user-attachments/assets/a391a5b6-5771-4ac3-bdc6-8d19987ded1b" />

* Lab banner: **SOLVED**
<img width="950" height="377" alt="Screenshot 2025-11-04 201746" src="https://github.com/user-attachments/assets/481c17de-24f7-4b39-87c2-9ac861188d8c" />

---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
