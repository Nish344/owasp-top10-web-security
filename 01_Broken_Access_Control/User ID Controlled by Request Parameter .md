# User ID Controlled by Request Parameter  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Horizontal-Privilege-Escalation-001  
**Source**: PortSwigger  
**Date_Completed**: 2025-10-27  
**Tag**: `Broken-Access-Control`, `Horizontal-Privilege-Escalation`, `ID-Parameter`, `API-Key-Disclosure`  

---

## Executive summary

The application exposes a user account page where sensitive data, such as the API key, is accessible via a request parameter (`id`). The parameter is client-controlled and not properly validated against the authenticated user's identity, allowing horizontal privilege escalation. By logging in as `wiener:peter` and modifying the `id` parameter to `carlos`, an attacker can retrieve `carlos`'s API key. This vulnerability demonstrates inadequate server-side authorization, enabling unauthorized access to another user's data.

**Result:** Logged in as `wiener` → changed `id=wiener` to `id=carlos` → retrieved `carlos`’s API key.  
**Severity (subjective):** Medium — allows unauthorized access to peer user data.  
**Recommended immediate action:** Enforce server-side authorization to restrict access to user-specific data based on the authenticated session.

---

## Objective

Exploit the horizontal privilege escalation vulnerability to obtain and submit the API key for the user `carlos`.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Modern browser, Burp Suite (optional for intercepting requests).  
* Notes: Credentials provided: `wiener:peter`.

---

## Discovery  

1. Logged in using credentials `wiener:peter`.  
2. Navigated to the account page and observed the URL containing a query parameter `id=wiener`.  
3. Hypothesized that changing the `id` parameter might allow access to other users' data.  
4. Modified `id=wiener` to `id=carlos` in the URL.  
5. Loaded the modified URL and retrieved `carlos`’s API key from the page.

> Finding: The `id` parameter is client-controlled and not validated against the authenticated user, enabling horizontal privilege escalation.

---

## Reproduction steps  

1. Log in to the application using credentials `wiener:peter`.  
2. Navigate to the account page (e.g., `https://<YOUR-LAB-ID>.web-security-academy.net/my-account?id=wiener`).  
3. Modify the URL by changing `id=wiener` to `id=carlos`.  
4. Load the updated URL (e.g., `https://<YOUR-LAB-ID>.web-security-academy.net/my-account?id=carlos`).  
5. Locate and copy `carlos`’s API key from the page.  
6. Submit the API key as the solution via the lab interface.

## Observed impact

* Authenticated user can access another user’s sensitive data (API key).  
* Potential for horizontal privilege escalation across all user accounts.  
* Risk of API key misuse (e.g., unauthorized API access, data exfiltration).  
* Affects confidentiality of user-specific information.

---

## Root cause analysis

* **Primary cause:** The server does not validate the `id` parameter against the authenticated user’s identity, allowing access to any user’s data.  
* **Secondary cause / contributing factor:** Lack of server-side authorization checks; relies on client-side parameter control.

---

## Risk assessment

* **Likelihood:** High — the `id` parameter is easily modifiable via browser or proxy tools.  
* **Impact**: Medium — exposes peer user data (e.g., API keys) but not system-level access.  
* **Overall risk**: Medium.  
  Optionally map to CVSS: Preliminary estimate in the **Medium** range (e.g., CVSS base score ~5.0–6.0) due to horizontal data exposure.

---

## Remediation 

### Immediate / short-term 

1. Restrict `id` parameter to the authenticated user’s ID on the server side.  
2. Return `403 Forbidden` if the `id` does not match the session user.

### Medium-term 

1. **Enforce server-side authorization**: Validate `id` against the logged-in user’s identity.  
   ```python
   if request.args.get('id') != current_user.id:
       abort(403)
   ```
2. Use session-bound IDs in the URL or remove `id` parameter entirely.  
3. Implement input validation to whitelist allowed `id` values.  
4. Add CSRF protection for account page requests.

### Long-term / defensive controls

1. Use role-based access control (RBAC) to limit data visibility.  
2. Add audit logging for account page access with mismatched IDs.  
3. Monitor for suspicious `id` parameter changes.  
4. Add automated tests to detect horizontal escalation.  
5. Conduct regular access control reviews.

---

## Detection & verification guidance 

* Test the account page with `id` set to another user’s ID → must return `403`.  
* Verify server validates `id` against the session user.  
* Scan code for direct use of `id` without authorization checks.  
* Use Burp Suite to manipulate `id` and check responses.  
* Add CI test:  
  ```bash
  curl -b "session=wiener" "/my-account?id=carlos" → expect 403
  ```

---

## Suggested tests to add

* Integration test: `GET /my-account?id=otheruser` → `403` for non-matching user.  
* Security test: Non-admin cannot access peer user data via `id`.  
* Session test: `id` parameter ignored if not session-bound.  
* Logging test: Mismatched `id` access logs an event.  
* Fuzz test: Inject random `id` values → all unauthorized.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Authorization Cheat Sheet  
* PortSwigger: Insecure Direct Object References (IDOR)  
* General guidance: Validate all user-controlled IDs against authenticated identity.

---

## Notes & lessons learned

* **Client-controlled IDs are dangerous** — always validate against session data.  
* **Horizontal escalation** is common when access control is parameter-based.  
* **API keys are sensitive** — protect with strict access controls.  
* Assume attackers will tamper with query parameters.

---

## Evidence & validation 

* Original URL: `/my-account?id=wiener` → shows `wiener`’s data.
<img width="951" height="399" alt="Screenshot 2025-10-27 192626" src="https://github.com/user-attachments/assets/26222f95-5812-418a-9e91-9124148ac493" />
* Modified URL: `/my-account?id=carlos` → shows `carlos`’s API key.
<img width="959" height="393" alt="Screenshot 2025-10-27 192522" src="https://github.com/user-attachments/assets/ddd4bf4d-ff46-4e18-9cc9-d68bf83fc280" />
* API key submitted → lab completed.
<img width="949" height="316" alt="Screenshot 2025-10-27 192737" src="https://github.com/user-attachments/assets/ea4a9528-645d-4c65-b6dc-454ff9209a4e" />


---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
