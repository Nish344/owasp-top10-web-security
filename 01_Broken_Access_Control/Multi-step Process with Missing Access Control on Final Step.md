# Multi-step Process with Missing Access Control on Final Step  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Multi-Step-Role-Upgrade-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-11-03  
**Tag**: `Broken-Access-Control`, `Business-Logic-Flaw`, `Missing-Authorization`, `Session-Reuse`, `Admin-Privilege-Escalation`  

---

## Executive summary

The admin panel implements a two-step role-upgrade flow:  
1. Admin selects a user → server renders a **confirmation page** (`/admin-roles`)  
2. Admin clicks **Confirm** → `POST /admin-roles` with `action=upgrade&confirmed=true&username=…`

The **final POST endpoint performs NO authorization check**.  
Any authenticated session can replay a captured “confirmed” request, change the `username` parameter, and instantly become administrator.  
By logging in as `wiener:peter`, hijacking an admin’s confirmed request, and swapping the target username, a regular user self-promotes to admin in one click.

**Result:**  
`wiener` (non-admin) → replayed confirmed POST → `username=wiener` → instant admin.  
**Severity (subjective):** Critical — trivial vertical privilege escalation.  
**Recommended immediate action:** Enforce **admin-only check** on every state-changing endpoint, regardless of UI flow.

---

## Objective

Exploit missing access control on the confirmation step to promote `wiener` to administrator.

---

## Environment & tools

* Target: `0a55007d0461b36d8020a85800bf00e7.web-security-academy.net`  
* Tools: Burp Suite Repeater, two browser windows (normal + incognito)  
* Credentials:  
  - Admin: `administrator:admin`  
  - Victim: `wiener:peter`

---

## Discovery  

1. Logged in as **administrator** → Admin Panel → Upgrade `carlos` → clicked **Confirm**.  
2. Intercepted the final POST in Burp Proxy:  
   ```
   POST /admin-roles
   action=upgrade&confirmed=true&username=carlos
   ```  
3. Sent request to **Repeater**.  
4. Opened incognito → logged in as **wiener** → copied `session` cookie.  
5. Pasted cookie into Repeater tab → changed `username=carlos` → `username=wiener` → **Send**.  
6. Refreshed page → `wiener` now shows **Administrator** role → lab solved.

> Finding: The confirmation endpoint trusts any valid session and the `confirmed=true` flag; **no role check**.

---

## Reproduction steps (copy-paste ready)

1. Log in as **administrator:admin**.  
2. Go to Admin Panel → Upgrade `carlos` → Confirm → **intercept POST** → Send to Repeater.  
3. Open incognito → log in as **wiener:peter** → copy cookie `session=…`.  
4. In Repeater:  
   - Replace `Cookie: session=…` with wiener’s cookie  
   - Change `username=carlos` → `username=wiener`  
   - Click **Send**  
5. Browse to `/my-account` → role = **administrator** → Lab solved.

**Winning request (exact copy)**
```
POST /admin-roles HTTP/2
Host: 0a55007d0461b36d8020a85800bf00e7.web-security-academy.net
Cookie: session=4yDbvCOu7FBAllUzwxZmxGTgBbxg5pka
Content-Length: 45
Content-Type: application/x-www-form-urlencoded

action=upgrade&confirmed=true&username=wiener
```

**Response**
```
HTTP/2 302 Found
Location: /admin-roles
Set-Cookie: role=administrator; Path=/; HttpOnly
```

---

## Observed impact

* Any authenticated user can **self-promote to admin** in one request.  
* Bypasses UI confirmation page entirely.  
* Enables **instant account takeover** of the entire application.

---

## Root cause analysis

* **Primary cause:** Final handler lacks `@require_admin` (or equivalent).  
* **Contributing factors:**  
  - Relies on client-side `confirmed=true` flag.  
  - Re-uses same endpoint for both rendering and mutation.  
  - No session-to-role binding on state-changing actions.

---

## Risk assessment

* **Likelihood:** 100 % — requires only a valid session and one edited parameter.  
* **Impact:** Complete system compromise.  
* **CVSS v3.1:** 9.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)

---

## Remediation  

### Immediate (5-minute fix)
```python
@app.route("/admin-roles", methods=["POST"])
def upgrade_role():
    if not current_user.is_admin:
        abort(403)
    # existing code...
```

### Medium-term
1. Split endpoints:  
   - `GET  /admin/roles/confirm?user=…` → render page  
   - `POST /api/admin/roles/upgrade` → JSON API with role gate  
2. Include **signed CSRF + flow token** bound to admin session.  
3. Rate-limit `/admin-roles` to 1/min per session.

### Long-term
- Centralized policy engine: `authorize(user, "admin:upgrade")`.  
- Audit log every role change (actor, target, IP, user-agent).  
- Automated test:  
  ```bash
  curl -b "wiener_session" -d "action=upgrade&username=wiener" \
       https://lab/admin-roles | grep "Forbidden"
  ```

---

## Detection & verification guidance  

* Send confirmed POST as **wiener** → must receive **403**.  
* Fuzz `username` with other accounts → all 403.  
* Burp “Match and Replace” rule: auto-downgrade `role=administrator` cookies in CI.

---

## Suggested tests to add

```gherkin
Scenario: Non-admin cannot confirm role upgrade
  Given I am logged in as "wiener"
  When I POST to /admin-roles with confirmed=true
  Then response is 403 Forbidden
```

---

## References & further reading

* OWASP API Security Top 10 – **BFLAC** (Broken Function Level Authorization)  
* PortSwigger: “Excessive Trust in Client-Side Controls”  
* OWASP Cheat Sheet: Authorization

---

## Notes & lessons learned

* **Multi-step flows are NOT access controls.**  
* Always protect the **final mutation endpoint**.  
* Never trust hidden fields (`confirmed=true`).  
* “Copy-paste a request” = instant exploit if authZ is missing.

---

## Evidence & validation  

* Admin → captured confirmed POST → Repeater  
* Wiener session + `username=wiener` → 302 + `role=administrator` cookie  
<img width="721" height="341" alt="Screenshot 2025-11-03 214955" src="https://github.com/user-attachments/assets/76acbbcf-cc50-48cc-b84e-c8cc46b34d14" />  

* `/my-account` shows **Administrator** badge  
* Lab auto-completed
<img width="950" height="362" alt="Screenshot 2025-11-03 214934" src="https://github.com/user-attachments/assets/500e2dd7-082f-4cba-9e4e-17db87643afb" />  
 
---

> **Legal & ethical reminder:** Demonstrated only inside PortSwigger’s authorized lab. Never test on production systems without written permission.  
