# Unprotected Admin Functionality with Unpredictable URL   

**Category**: 01-Broken-Access-Control  
**Lab_ID**: Unprotected-Admin-Panel-002  
**Source**: PortSwigger   
**Date_Completed**: 2025-10-01  
**Tag**: `Broken-Access-Control`, `Admin-Panel`, `Info-Disclosure`, `Client-Side-Code`  


## Executive summary

An administrative interface was disclosed via client-side JavaScript code on the application's home page, revealing an unpredictable URL path. The endpoint was exposed without any authentication or authorization checks, allowing an unauthenticated user to access the admin panel and perform destructive administrative actions — specifically, deleting the `carlos` user account. This issue demonstrates broken access control and information disclosure, highlighting the risks of embedding sensitive paths in client-side code rather than enforcing proper server-side controls.

**Result:** Admin panel path discovered in home page JavaScript → accessed directly → deleted user `carlos`.  
**Severity (subjective):** High — enables unauthenticated administrative actions.  
**Recommended immediate action:** Restrict access to admin endpoints and implement server-side authentication + authorization checks; avoid disclosing sensitive paths in client-side code.

---

## Objective

Locate the administrative interface disclosed within the application's client-side code, verify whether it is protected, and if unprotected, demonstrate the impact by removing the user account `carlos`.

---

## Environment & tools

* Target: PortSwigger lab instance (Apprentice difficulty).  
* Tools: Modern browser and developer tools (e.g., inspect element/source view); Burp Suite used optionally to capture/inspect requests.  
* Notes: No credentials were required to access the admin panel.

---

## Discovery 

1. Loaded the application's home page.  
2. Inspected the page source using browser developer tools (e.g., View Page Source or Elements tab).  
3. Identified a JavaScript snippet that conditionally adds an admin panel link, revealing the unpredictable path (e.g., `/admin-jhc9ve`) hardcoded within the code, even though the condition (`isAdmin = false`) prevents it from rendering in the UI.  
4. Navigating to the disclosed path loaded an administrative interface without authentication or authorization checks.
<img width="746" height="175" alt="Screenshot 2025-10-01 183627" src="https://github.com/user-attachments/assets/c0baeb95-bb88-482b-9cc9-eed0472a4ee9" />
---
> Finding: Client-side JavaScript is an information-disclosure vector — it exposed a sensitive, unpredictable path that should not be relied on for security through obscurity.

---

## Reproduction steps 

1. Open the application base URL in a browser.  
2. View the page source (right-click > View Page Source or use developer tools).  
3. Search the source for keywords like "admin" or "panel" to locate the JavaScript code.  
4. Note the admin path hardcoded in the script (example: `/admin-jhc9ve`).  
5. Append the disclosed path to the base URL and navigate to it.  
6. In the admin UI, locate the user management area, identify user `carlos`, and invoke the delete action.  
7. Verify the user is no longer listed or that the UI returns a successful deletion confirmation.
<img width="944" height="329" alt="Screenshot 2025-10-01 183605" src="https://github.com/user-attachments/assets/46263e93-b5f2-4e42-84c1-777608096e6e" />


**Representative HTTP interaction :**

```
GET / HTTP/1.1
Host: <target>
// Page source contains JS with /admin-jhc9ve

GET /admin-jhc9ve HTTP/1.1
Host: <target>

POST /admin-jhc9ve/users/delete HTTP/1.1
Host: <target>
Content-Type: application/x-www-form-urlencoded

username=carlos
```

---

## Observed impact

* Unauthenticated user can perform administrative operations (delete accounts).  
* Integrity and availability of user data are compromised.  
* Potential for escalated malicious actions: data exfiltration, privilege changes, account takeover, or system disruption.  
* If similar patterns exist for other endpoints, the entire administrative surface could be exploited by any unauthenticated actor.

---

## Root cause analysis

* **Primary cause:** Admin functionality is accessible without authentication/authorization enforcement on the server side.  
* **Secondary cause / contributing factor:** Sensitive path disclosed in client-side JavaScript. While unpredictable URLs provide some obscurity, embedding them in publicly accessible code negates this, making discovery trivial via source inspection. The fundamental issue is missing or incorrect access control on admin endpoints.

---

## Risk assessment

* **Likelihood:** Medium — client-side code is easily inspectable; attackers can use automated tools or manual review to extract paths.  
* **Impact:** High — attacker-controlled deletion of user accounts and other destructive admin actions.  
* **Overall risk:** High.  
  Optionally map to CVSS: a preliminary estimate would likely fall into the **High** range depending on exact scopes and authentication contexts (e.g., CVSS base score ~7–9).

---

## Remediation 

### Immediate / short-term 

1. Remove any references to administrative URLs from client-side code, scripts, or other public assets.  
2. If feasible, restrict admin endpoints to internal IP ranges or via network-level controls while permanent fixes are applied.

### Medium-term 

1. **Enforce authentication**: Require authenticated sessions for any admin pages. Use strong authentication (password + MFA where appropriate).  
2. **Enforce server-side authorization**: Validate user role/privileges on every admin endpoint and action; do not rely on client-side logic or URL obscurity.  
3. **CSRF protection**: Ensure all state-changing admin requests are protected against CSRF (e.g., anti-CSRF tokens validated server-side).  
4. **Use least privilege**: Ensure admin accounts are minimal and database users used by the application have restricted permissions.

### Long-term / defensive controls

1. Implement RBAC (role-based access control) with audit logging for admin operations.  
2. Add monitoring and alerts for admin-panel access and high-risk actions (account deletions, privilege changes).  
3. Add automated tests and CI checks ensuring admin endpoints return 401/403 to unauthenticated requests.  
4. Periodic access reviews and penetration testing focused on access control and client-side disclosures.

---

## Detection & verification guidance 

* Verify that admin routes return `401` or `403` for unauthenticated requests.  
* Ensure no sensitive paths are hardcoded in client-side code; scan JS files for patterns like "/admin".  
* Validate server-side enforcement by simulating unauthenticated requests and attempting actions.  
* Scan repository and deployment artifacts for endpoints with randomized paths and check their access controls.  
* Add an automated CI smoke test: attempt a known admin endpoint without credentials and assert it is blocked.

---

## Suggested tests to add

* Integration test: unauthenticated `GET /admin-<random>` returns `401/403`.  
* Integration test: unauthenticated `POST /admin-<random>/users/delete` returns `401/403` (and does not remove users).  
* Role test: authenticated non-admin user cannot access admin endpoints or perform admin actions.  
* Static analysis test: scan client-side JS for hardcoded admin paths.  
* Logging test: admin actions create an audit record (user, timestamp, action).

---

## References & further reading

* OWASP Top Ten — Broken Access Control (concepts and mitigations)  
* OWASP Client-Side Security Cheat Sheet  
* OWASP Authentication Cheat Sheet & Authorization Guidance  
* General guidance: Avoid embedding sensitive information in client-side code; rely on server-side controls.

---

## Notes & lessons learned

* Client-side code (e.g., JavaScript) can be a source of sensitive information disclosure; always assume it is public and inspectable.  
* URL obscurity (e.g., randomization) is not a substitute for access controls; it only delays discovery.  
* Proper access control and strong authentication are non-negotiable for admin surfaces; implement layered defenses (network restrictions + authentication + authorization + logging).

---

## Evidence & validation 

* Home page source contained JavaScript with hardcoded admin path .  
* Admin UI accessible without prior authentication.  
* Successful deletion of `carlos` verified via admin UI state change / success response.

---

> ⚠️ **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
