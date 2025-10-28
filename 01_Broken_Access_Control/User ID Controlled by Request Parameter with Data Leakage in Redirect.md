# User ID Controlled by Request Parameter with Data Leakage in Redirect  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: IDOR-Data-Leakage-Redirect-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-10-28  
**Tag**: `Broken-Access-Control`, `IDOR`, `Data-Leakage`, `Redirect-Response`, `API-Key-Disclosure`  

---

## Executive summary

The application contains a horizontal privilege escalation vulnerability on the account page, where the `id` parameter is client-controlled and not validated against the authenticated user's identity. When the `id` is changed to `carlos`, the server redirects to the home page with a `302` response, but the response body unexpectedly leaks `carlos`’s API key. This data leakage in the redirect response allows an attacker to obtain sensitive information. Logging in as `wiener:peter` and manipulating the request via Burp Repeater exposed this flaw, enabling retrieval of `carlos`’s API key.

**Result:** Logged in as `wiener` → changed `id=wiener` to `id=carlos` → redirect response leaked `carlos`’s API key.  
**Severity (subjective):** Medium — allows unauthorized access to peer user data via unintended response leakage.  
**Recommended immediate action:** Remove sensitive data from redirect response bodies; enforce server-side authorization on the `id` parameter.

---

## Objective

Exploit the access control vulnerability to obtain and submit the API key for the user `carlos` by leveraging data leakage in a redirect response.

---

## Environment & tools

* Target: PortSwigger lab instance (`0af300090388214b81a32a34002c006b.web-security-academy.net`).  
* Tools: Modern browser, Burp Suite (Repeater, Proxy).  
* Notes: Credentials provided: `wiener:peter`. Session cookie: `wU4L1q6RsFMXraQYvpAS8Xaw8v0SeG4f`.

---

## Discovery 

1. Logged in using credentials `wiener:peter` and navigated to the account page (e.g., `GET /my-account?id=wiener`).  
2. Sent the request to **Burp Repeater**.  
3. Modified the `id` parameter from `wiener` to `carlos`.  
4. Sent the modified request → received a `302 Redirect` to the home page.  
5. Observed the response body contained `carlos`’s API key, despite the redirect.

> Finding: The server leaks sensitive data in the redirect response body when the `id` parameter is tampered with, indicating an IDOR vulnerability with inadequate response sanitization.

---

## Reproduction steps 

1. Log in to the application using credentials `wiener:peter`.  
2. Navigate to the account page (e.g., `GET /my-account?id=wiener`).  
3. Use **Burp Suite Proxy** to intercept the request.  
4. Send the request to **Burp Repeater**.  
5. Modify the `id` parameter to `carlos` (e.g., `GET /my-account?id=carlos`).  
6. Send the request → note the `302 Redirect` response.  
7. Inspect the response body to extract `carlos`’s API key.  
8. Submit the API key as the solution via the lab interface.

**Captured Burp Suite HTTP interaction :**

**Request:**
```
GET /my-account?id=carlos HTTP/2
Host: 0af300090388214b81a32a34002c006b.web-security-academy.net
Cookie: session=wU4L1q6RsFMXraQYvpAS8Xaw8v0SeG4f
Sec-Ch-Ua: "Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
Dnt: 1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Sec-Fetch-Site: none
Sec-Fetch-Mode: navigate
Sec-Fetch-User: ?1
Sec-Fetch-Dest: document
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Priority: u=0, i
```

**Response:**
```
HTTP/2 302 Found
Location: https://0af300090388214b81a32a34002c006b.web-security-academy.net/
Content-Type: text/html
Content-Length: 150

<html><body>You are not authorized to view this page. Redirecting to home...<br>API Key for carlos: <API_KEY_HERE></body></html>
```

> Note: The exact response body format may vary, but it contains the leaked API key.

---

## Observed impact

* Authenticated user can access another user’s sensitive data (API key) via redirect response leakage.  
* Potential for horizontal privilege escalation across all user accounts.  
* Risk of API key misuse (e.g., unauthorized API access, data exfiltration).  
* Affects confidentiality due to unintended data exposure in redirects.

---

## Root cause analysis

* **Primary cause:** The server does not validate the `id` parameter against the authenticated user’s identity, allowing access to any user’s data.  
* **Secondary cause / contributing factor:** Sensitive data (API key) is included in the redirect response body, which is not sanitized or stripped before sending.

---

## Risk assessment

* **Likelihood:** Medium — requires request interception and parameter manipulation, but no advanced enumeration needed.  
* **Impact**: Medium — exposes peer user data (e.g., API keys) but not system-level access.  
* **Overall risk**: Medium.  
  Optionally map to CVSS: Preliminary estimate in the **Medium** range (e.g., CVSS base score ~5.5–6.5) due to data leakage requiring specific conditions.

---

## Remediation 

### Immediate / short-term  

1. Remove all sensitive data from redirect response bodies.  
2. Return a blank or minimal body with `302 Redirect` responses.

### Medium-term  

1. **Enforce server-side authorization**: Validate `id` against the logged-in user’s identity.  
   ```python
   if request.args.get('id') != current_user.id:
       return redirect(url_for('home'), code=302)
   ```
2. Use a redirect status (e.g., `303 See Other`) without a body for unauthorized access.  
3. Implement input validation to restrict `id` to the session user.  
4. Add CSRF protection for account page requests.

### Long-term / defensive controls

1. Use role-based access control (RBAC) to limit data visibility.  
2. Add audit logging for account page access attempts with mismatched IDs.  
3. Monitor for suspicious `id` parameter changes or unexpected redirect bodies.  
4. Add automated tests to detect data leakage in redirects.  
5. Conduct regular access control and response sanitization reviews.

---

## Detection & verification guidance  

* Test the account page with `id` set to another user’s ID → must redirect without leaking data.  
* Verify redirect responses (`302`, `301`) have no sensitive data in the body.  
* Use Burp Suite to manipulate `id` and inspect redirect responses.  
* Scan code for redirect logic that includes user data.  
* Add CI test:  
  ```bash
  curl -b "session=wiener" "/my-account?id=carlos" → expect 302 with empty body
  ```

---

## Suggested tests to add

* Integration test: `GET /my-account?id=otheruser` → `302` with no API key in body.  
* Security test: Non-admin cannot access peer user data via `id`.  
* Redirect test: All `302` responses have minimal or no body.  
* Logging test: Unauthorized `id` access attempts logged.  
* Fuzz test: Inject invalid `id` values → no data leakage.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Authorization Cheat Sheet  
* PortSwigger: Insecure Direct Object References (IDOR)  
* RFC 7231: HTTP/1.1 Semantics and Content — Redirects  
* General guidance: Sanitize redirect responses; validate all user-controlled IDs.

---

## Notes & lessons learned

* **Redirects can leak data** — always strip sensitive information from response bodies.  
* **IDOR persists** even with redirects if validation is missing.  
* **Burp Repeater is key** for testing parameter manipulation and response analysis.  
* **API keys are critical** — protect with strict access and response controls.  
* Assume attackers will inspect all response parts, including redirects.

---

## Evidence & validation 

* Original URL: `/my-account?id=wiener` → shows `wiener`’s data.  
* Modified URL: `/my-account?id=carlos` → `302 Redirect` with `carlos`’s API key in body.
<img width="715" height="344" alt="Screenshot 2025-10-28 181214" src="https://github.com/user-attachments/assets/e144e63b-8298-4706-b404-5be5965350c8" />
* API key submitted → lab completed.
<img width="950" height="344" alt="Screenshot 2025-10-28 181142" src="https://github.com/user-attachments/assets/0d55ad67-ec3f-4b02-8768-4c9dab70da23" />


---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
