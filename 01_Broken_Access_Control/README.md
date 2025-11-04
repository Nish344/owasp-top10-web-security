# 01 Broken Access Control

This folder contains lab writeups for the **01 Broken Access Control** category.

### Progress

- Completed: **13** / **13**

### Labs

- ✅ [Insecure Direct Object References Can Be Exploited](Insecure%20Direct%20Object%20References%20Can%20Be%20Exploited.md) — `IDOR-Chat-Transcript-001` — _Insecure-Direct-Object-References, IDOR, Path-Traversal-Like, File-Access, Credential-Leak_
- ✅ [Method-Based Access Control Can Be Circumvented](Method-Based%20Access%20Control%20Can%20Be%20Circumvented.md) — `Method-Access-Bypass-001` — _Broken-Access-Control, HTTP-Method, Verb-Tampering, GET-vs-POST, Authorization-Bypass_
- ✅ [Multi-step Process with Missing Access Control on Final Step](Multi-step%20Process%20with%20Missing%20Access%20Control%20on%20Final%20Step.md) — `Multi-Step-Role-Upgrade-001` — _Broken-Access-Control, Business-Logic-Flaw, Missing-Authorization, Session-Reuse, Admin-Privilege-Escalation_
- ✅ [Referer-Based Access Control Can Be Spoofed](Referer-Based%20Access%20Control%20Can%20Be%20Spoofed.md) — `Referer-Bypass-001` — _Broken-Access-Control, Referer-Spoofing, Header-Tampering, Admin-Bypass, Privilege-Escalation_
- ✅ [URL-Based Access Control Can Be Circumvented](URL-Based%20Access%20Control%20Can%20Be%20Circumvented.md) — `URL-Access-Bypass-001` — _Broken-Access-Control, Admin-Panel, X-Original-URL, Front-End-Routing, Access-Control-Bypass_
- ✅ [Unprotected Admin Functionality with Unpredictable URL](Unprotected%20Admin%20Functionality%20with%20Unpredictable%20URL.md) — `Unprotected-Admin-Panel-002` — _Broken-Access-Control, Admin-Panel, Info-Disclosure, Client-Side-Code_
- ✅ [Unprotected Admin Functionality](Unprotected%20Admin%20Functionality.md) — `Unprotected-Admin-Panel-001` — _Broken-Access-Control, Admin-Panel, Info-Disclosure, Robots.txt_
- ✅ [User ID Controlled by Request Parameter](User%20ID%20Controlled%20by%20Request%20Parameter%20.md) — `Horizontal-Privilege-Escalation-001` — _Broken-Access-Control, Horizontal-Privilege-Escalation, ID-Parameter, API-Key-Disclosure_
- ✅ [User ID Controlled by Request Parameter with Data Leakage in Redirect](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Data%20Leakage%20in%20Redirect.md) — `IDOR-Data-Leakage-Redirect-001` — _Broken-Access-Control, IDOR, Data-Leakage, Redirect-Response, API-Key-Disclosure_
- ✅ [User ID Controlled by Request Parameter with Password Disclosure](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Password%20Disclosure.md) — `IDOR-Password-Disclosure-001` — _Broken-Access-Control, IDOR, Password-Disclosure, Horizontal-Privilege-Escalation, Admin-Access_
- ✅ [User ID Controlled by Request Parameter with Unpredictable User IDs](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Unpredictable%20User%20IDs.md) — `Horizontal-Privilege-Escalation-GUID-001` — _Broken-Access-Control, Horizontal-Privilege-Escalation, IDOR, GUID-User-ID, API-Key-Disclosure_
- ✅ [User Role Can Be Modified in User Profile](User%20Role%20Can%20Be%20Modified%20in%20User%20Profile.md) — `RoleID-JSON-Tamper-001` — _Broken-Access-Control, Mass-Assignment, JSON-Tampering, Privilege-Escalation, Insecure-Deserialization_
- ✅ [User Role Controlled by Request Parameter](User%20Role%20Controlled%20by%20Request%20Parameter.md) — `Role-Parameter-001` — _Broken-Access-Control, Admin-Panel, Cookie-Manipulation, Horizontal-Privilege-Escalation_

### Cheatsheet / Quick Notes

**Category summary**  
Broken Access Control — server fails to enforce proper authorization, allowing users to access or perform actions they shouldn't. Focus on endpoint logic, method handling, hidden/unlinked routes, and any client-side controls.

---

## Quick reconnaissance checklist
- [ ] Crawl & map endpoints (Burp Spider / ffuf / gobuster).  
- [ ] Inspect client JS / Single Page App routing for hidden endpoints / role checks.  
- [ ] Check `robots.txt`, sitemap, `.git`, backups, and client-side comments for admin links.  
- [ ] Test all HTTP verbs (GET, POST, PUT, DELETE, PATCH, OPTIONS).  
- [ ] Locate parameters that control identity or role (`id`, `user_id`, `role`, `isAdmin`, `admin`).  
- [ ] Capture and manipulate cookies / tokens (session cookie, JWTs).  
- [ ] Try horizontal & vertical privilege escalation (ID swapping, role tampering).  
- [ ] Search for `X-Original-URL`, `X-Forwarded-*`, and other proxy headers.

---

## High-level tactics & payloads
- Method tampering: `X-HTTP-Method-Override` / change method via `POST` vs `GET`.  
- Header-based bypasses: `X-Original-URL`, `X-Rewrite-URL`, `X-Forwarded-Host`, `X-Forwarded-For`.  
- Parameter tampering: change numeric/string IDs, remove/replace auth params, add `?isAdmin=1`.  
- Cookie/JWT tampering: change `role` or `isAdmin` claims; test unsigned token acceptance.  
- URL guessing / discovery: `ffuf`/`gobuster` with admin wordlists and common extensions.

Quick commands
```bash
# Fuzz for hidden endpoints
ffuf -u https://TARGET/FUZZ -w /usr/share/wordlists/Discovery/Web-Content/common.txt -mc 200,301,302,403 -t 50

# Fuzz for admin pages from robots.txt or wordlist
gobuster dir -u https://TARGET -w admin-words.txt -x php,html,asp -t 40

# Simple ID swap example
curl -s -b cookies.txt "https://TARGET/profile?id=2" | sed -n '1,120p'

```


### Lab-specific methods 

| Lab                                                      | Focus                                                                      | Detection / Checks                                                                                                | Exploit / Payload (example)                                                    | PoC (short request)                                                                                                            | Notes / Mitigation                                                                                         |
| -------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Method-Based Access Control Can Be Circumvented          | HTTP method / verb tampering                                               | Try same endpoint with GET/POST/PUT/DELETE; test `X-HTTP-Method-Override`; inspect server logs/responses per verb | `X-HTTP-Method-Override: DELETE` or send GET instead of POST                   | `POST /admin/delete-user HTTP/1.1\nHost: target\nCookie: session=...\nX-HTTP-Method-Override: DELETE`                          | Enforce auth per method; canonicalize method; deny method override headers by default                      |
| URL-Based Access Control Can Be Circumvented             | Header-based routing / proxy header injection (`X-Original-URL`)           | Send harmless path but add `X-Original-URL: /admin`; compare responses; test `X-Rewrite-URL`, `X-Forwarded-*`     | `X-Original-URL: /admin` or `X-Rewrite-URL: /admin`                            | `GET /index HTTP/1.1\nHost: target\nCookie: session=...\nX-Original-URL: /admin`                                               | Only trust proxy headers from known proxies; validate & canonicalize; strip untrusted headers              |
| Unprotected Admin Functionality with Unpredictable URL   | Discovery of obscure/unlinked admin URL                                    | Inspect `robots.txt`, JS bundles, source maps, sitemap, service-worker, build artifacts; fuzz UUID-like paths     | Fuzz admin-like names or UUIDs (e.g., `/admin-<hex>/`)                         | `GET /admin-3f1b2e/ HTTP/1.1\nHost: target\nCookie: session=...`                                                               | Hiding is not auth — require server-side auth, RBAC, MFA, IP allowlists                                    |
| Unprotected Admin Functionality                          | Admin endpoints missing auth                                               | Curl `/admin` and inspect response; test as anonymous and low-priv user; check for management forms               | Direct access to `/admin` with session cookie or unauthenticated               | `GET /admin HTTP/1.1\nHost: target\nCookie: session=...`                                                                       | Require auth & RBAC checks; return 401/403 for unauthenticated; audit admin endpoints                      |
| User ID Controlled by Request Parameter                  | ID / `user_id` parameter tampering (horizontal/vertical)                   | Enumerate `id` values; compare responses (size, fields); use automated fuzzing/scripts                            | Change `?id=2` → `?id=3` or loop `1..N`                                        | `GET /account?id=3 HTTP/1.1\nHost: target\nCookie: session=...`                                                                | Enforce object-level access control server-side; derive ownership server-side                              |
| User Role Controlled by Request Parameter                | Role tampering via query param / cookie / JWT claim                        | Inspect cookies & JWT claims; attempt to change `role` cookie or claim; test weak JWT signing                     | Cookie tamper: `role=admin`; JWT claim change (lab-only)                       | `GET /admin/dashboard HTTP/1.1\nHost: target\nCookie: session=...; role=admin`                                                 | Derive role server-side; always verify JWT signature & claims; never trust client-set role                 |
| IDOR-Data-Leakage-Redirect-001                           | IDOR via redirect (data in Location/Referer)                               | Inspect `Location` headers and subsequent redirects; manipulate `id` and follow redirects                         | Tamper `?id=12345` → `?id=67890` to force redirect exposing other user info    | `GET /view?id=12345 HTTP/1.1\nHost: target\nCookie: session=...\n— check Location: /preview?user=67890`                        | Don’t include PII/tokens in URLs; check ownership before redirect; use opaque tokens                       |
| Horizontal-Privilege-Escalation-GUID-001                 | Horizontal IDOR with GUID-like IDs                                         | Fuzz/replace GUID `userId` params; compare status / size / timing differences                                     | Swap GUIDs (brute/guess) to fetch other users’ data.                           | `GET /profile?userId=3fa85f64-... HTTP/1.1\nHost: target\nCookie: session=...`                                                 | Enforce object-level auth; use unguessable IDs + rate-limit + logging                                      |
| Vertical-Privilege-Escalation (role change / admin-only) | Elevation from normal user → admin actions                                 | Look for admin-only endpoints (`/admin/*`), try elevated parameters like `isAdmin=1` or `role=admin`              | Add `isAdmin=true` or call admin endpoint directly                             | `POST /user/update HTTP/1.1\nHost: target\nCookie: session=...\nContent-Type: application/json\n\n{"userId":5,"isAdmin":true}` | Ignore client-supplied privilege fields; perform role checks server-side; validate session roles           |
| Mass Assignment / Parameter Pollution                    | Overwriting server-side object properties via JSON/params                  | Review server JSON fields; try adding unexpected fields (`isAdmin`, `role`, `accountType`)                        | Send extra property in JSON body to set sensitive flags                        | `POST /users/5 HTTP/1.1\nContent-Type: application/json\n\n{"name":"X","isAdmin":true}`                                        | Implement allowlists for assignable fields; use DTOs/serializers that ignore unknown fields                |
| Broken CORS / Origin-based Access Control                | CORS misconfiguration allows JS from attacker origin                       | Test `Origin` header variations; check `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials`       | Set `Origin: https://evil.com` and test if allowed; then use XHR to exfiltrate | `OPTIONS /api/user/5 HTTP/1.1\nOrigin: https://evil.com\nAccess-Control-Request-Method: GET`                                   | Only allow trusted origins; do not return `*` with credentials; validate CORS server-side                  |
| Forced Browsing / Unlinked Resource Discovery            | Discover hidden endpoints, backups, S3 keys, old admin pages               | Use wordlists, fuzzers (ffuf, dirb), check backups, `.git`, archives, sitemap                                     | Access discovered endpoints (e.g., `/backup/db.sql`, `/admin_old/`)            | `GET /backup/db.sql HTTP/1.1\nHost: target`                                                                                    | Remove/back up sensitive files off-server; require auth for all sensitive resources; use WAF/rate-limiting |
| Race Condition / TOCTOU Access Control Bypass            | Concurrent requests to change resource ownership/perform privileged action | Attempt parallel/rapid requests to transfer ownership / create resources; monitor inconsistent state              | Send two nearly simultaneous `POST`/`PATCH` requests to flip ownership         | (pseudo) run two parallel `POST /transfer` requests with different `to_user` values                                            | Use atomic server-side operations, transactions, optimistic locking, server-side checks                    |
