# User ID Controlled by Request Parameter with Unpredictable User IDs  

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Horizontal-Privilege-Escalation-GUID-001  
**Source**: PortSwigger   
**Date_Completed**: 2025-10-28  
**Tag**: `Broken-Access-Control`, `Horizontal-Privilege-Escalation`, `IDOR`, `GUID-User-ID`, `API-Key-Disclosure`  

---

## Executive summary

The application uses Globally Unique Identifiers (GUIDs) for user identification, making direct enumeration of user IDs impractical. However, a horizontal privilege escalation vulnerability exists on the user account page, where the `id` parameter is client-controlled and not validated against the authenticated user's identity. By discovering `carlos`'s GUID via a clickable blog post link (which exposes the GUID in the URL), an attacker can log in as `wiener:peter` and modify the `id` parameter to `carlos`'s GUID, retrieving his API key. This demonstrates an Insecure Direct Object Reference (IDOR) vulnerability, bypassing the obscurity provided by GUIDs.

**Result:** Discovered `carlos`'s GUID via blog post → logged in as `wiener` → changed `id` to `carlos`'s GUID → retrieved `carlos`’s API key.  
**Severity (subjective):** Medium — allows unauthorized access to peer user data despite GUID usage.  
**Recommended immediate action:** Enforce server-side authorization to restrict access to user-specific data based on the authenticated session, regardless of ID format.

---

## Objective

Exploit the horizontal privilege escalation vulnerability to obtain and submit the API key for the user `carlos` by discovering his GUID and using it in the account page request.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Modern browser, Burp Suite (optional for intercepting requests).  
* Notes: Credentials provided: `wiener:peter`. User IDs are GUIDs (e.g., UUID format).

---

## Discovery 

1. Browsed the application to locate a blog post authored by `carlos`.  
2. Clicked on `carlos`'s profile or post link, observing the URL contained his GUID as a parameter (e.g., `?id=550e8400-e29b-41d4-a716-446655440000`).  
3. Noted `carlos`'s GUID for later use.  
4. Logged in using credentials `wiener:peter` and navigated to the account page, which used the same `id` parameter (e.g., `?id=<wiener-guid>`).  
5. Modified the `id` parameter to `carlos`'s GUID.  
6. Loaded the modified URL and retrieved `carlos`’s API key from the page.

> Finding: GUIDs provide obscurity but not security; the `id` parameter is not validated server-side, enabling IDOR via exposed references in blog links.

---

## Reproduction steps 

1. Access the application and search for or browse to a blog post by `carlos`.  
2. Click on `carlos`'s name or profile link → note the GUID in the URL (e.g., `https://<YOUR-LAB-ID>.web-security-academy.net/user?id=550e8400-e29b-41d4-a716-446655440000`).  
3. Log in to the application using credentials `wiener:peter`.  
4. Navigate to the account page (e.g., `https://<YOUR-LAB-ID>.web-security-academy.net/my-account?id=<wiener-guid>`).  
5. Modify the URL by replacing the `id` parameter with `carlos`'s GUID.  
6. Load the updated URL (e.g., `https://<YOUR-LAB-ID>.web-security-academy.net/my-account?id=550e8400-e29b-41d4-a716-446655440000`).  
7. Locate and copy `carlos`’s API key from the page.  
8. Submit the API key as the solution via the lab interface.

---

## Observed impact

* Authenticated user can access another user’s sensitive data (API key) using their GUID.  
* Potential for horizontal privilege escalation across all user accounts via exposed GUIDs in public links.  
* Risk of API key misuse (e.g., unauthorized API access, data exfiltration).  
* GUIDs do not prevent IDOR if references are leaked in application features like blogs.

---

## Root cause analysis

* **Primary cause:** The server does not validate the `id` parameter (GUID) against the authenticated user’s identity, allowing access to any user’s data.  
* **Secondary cause / contributing factor:** GUIDs exposed in public-facing URLs (e.g., blog posts), providing a discovery vector for IDOR attacks; lack of server-side authorization checks.

---

## Risk assessment

* **Likelihood:** Medium — GUIDs are unpredictable, but discovery is feasible via application features (e.g., blog links); parameter manipulation is trivial.  
* **Impact**: Medium — exposes peer user data (e.g., API keys) but not system-level access.  
* **Overall risk**: Medium.  
  Optionally map to CVSS: Preliminary estimate in the **Medium** range (e.g., CVSS base score ~5.5–6.5) due to horizontal data exposure requiring GUID discovery.

---

## Remediation 

### Immediate / short-term  

1. Restrict `id` parameter to the authenticated user’s GUID on the server side.  
2. Return `403 Forbidden` if the `id` does not match the session user.

### Medium-term 

1. **Enforce server-side authorization**: Validate `id` against the logged-in user’s GUID.  
   ```python
   if request.args.get('id') != current_user.guid:
       abort(403)
   ```
2. Avoid exposing GUIDs in public URLs (e.g., use slugs or non-sensitive identifiers in blog links).  
3. Implement input validation to ensure `id` is a valid GUID format.  
4. Add CSRF protection for account page requests.

### Long-term / defensive controls

1. Use role-based access control (RBAC) to limit data visibility.  
2. Add audit logging for account page access with mismatched GUIDs.  
3. Monitor for suspicious `id` parameter changes or GUID exposures.  
4. Add automated tests to detect horizontal escalation, including GUID-based IDOR.  
5. Conduct regular access control reviews, focusing on unpredictable IDs.

---

## Detection & verification guidance 

* Test the account page with `id` set to another user’s GUID → must return `403`.  
* Verify server validates `id` against the session user’s GUID.  
* Scan code for direct use of `id` without authorization checks.  
* Use Burp Suite to manipulate `id` and check responses.  
* Add CI test:  
  ```bash
  curl -b "session=wiener" "/my-account?id=<carlos-guid>" → expect 403
  ```

---

## Suggested tests to add

* Integration test: `GET /my-account?id=<other-guid>` → `403` for non-matching user.  
* Security test: Non-admin cannot access peer user data via `id`.  
* GUID exposure test: Public links do not leak sensitive GUIDs.  
* Logging test: Mismatched `id` access logs an event.  
* Fuzz test: Inject invalid GUIDs → proper error handling.

---

## References & further reading

* OWASP Top Ten — Broken Access Control  
* OWASP Authorization Cheat Sheet  
* PortSwigger: Insecure Direct Object References (IDOR)  
* General guidance: Validate all user-controlled IDs (including GUIDs) against authenticated identity; avoid exposing them unnecessarily.

---

## Notes & lessons learned

* **GUIDs obscure but do not secure** — attackers can discover them via application leaks (e.g., URLs).  
* **IDOR remains a risk** even with unpredictable IDs if validation is absent.  
* **API keys are sensitive** — protect with strict, session-bound access controls.  
* Public features (blogs, profiles) can be enumeration vectors; audit for ID exposures.

---

## Evidence & validation 

* Blog post link exposed `carlos`'s GUID.
<img width="947" height="399" alt="Screenshot 2025-10-28 175846" src="https://github.com/user-attachments/assets/6f5a2247-b784-494c-9618-93591bb66c32" />
* Original URL: `/my-account?id=<wiener-guid>` → shows `wiener`’s data.  
* Modified URL: `/my-account?id=<carlos-guid>` → shows `carlos`’s API key.
<img width="947" height="367" alt="Screenshot 2025-10-28 175958" src="https://github.com/user-attachments/assets/23f67ced-7fa6-4584-8bb7-9dc71d654911" />
* API key submitted → lab completed.
<img width="946" height="394" alt="Screenshot 2025-10-28 175748" src="https://github.com/user-attachments/assets/1ed488ce-eba2-45e3-abb7-722f5c60ccec" />


---

> **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
