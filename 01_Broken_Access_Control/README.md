# 01 Broken Access Control

This folder contains lab writeups for the **01 Broken Access Control** category.

### Progress

- Completed: **9** / **13**

### Labs

- ✅ [Method-Based Access Control Can Be Circumvented](Method-Based%20Access%20Control%20Can%20Be%20Circumvented.md) — `Method-Access-Bypass-001` — _Broken-Access-Control, HTTP-Method, Verb-Tampering, GET-vs-POST, Authorization-Bypass_
- ✅ [URL-Based Access Control Can Be Circumvented](URL-Based%20Access%20Control%20Can%20Be%20Circumvented.md) — `URL-Access-Bypass-001` — _Broken-Access-Control, Admin-Panel, X-Original-URL, Front-End-Routing, Access-Control-Bypass_
- ✅ [Unprotected Admin Functionality with Unpredictable URL](Unprotected%20Admin%20Functionality%20with%20Unpredictable%20URL.md) — `Unprotected-Admin-Panel-002` — _Broken-Access-Control, Admin-Panel, Info-Disclosure, Client-Side-Code_
- ✅ [Unprotected Admin Functionality](Unprotected%20Admin%20Functionality.md) — `Unprotected-Admin-Panel-001` — _Broken-Access-Control, Admin-Panel, Info-Disclosure, Robots.txt_
- ✅ [User ID Controlled by Request Parameter](User%20ID%20Controlled%20by%20Request%20Parameter%20.md) — `Horizontal-Privilege-Escalation-001` — _Broken-Access-Control, Horizontal-Privilege-Escalation, ID-Parameter, API-Key-Disclosure_
- ✅ [User ID Controlled by Request Parameter with Data Leakage in Redirect](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Data%20Leakage%20in%20Redirect.md) — `IDOR-Data-Leakage-Redirect-001` — _Broken-Access-Control, IDOR, Data-Leakage, Redirect-Response, API-Key-Disclosure_
- ✅ [User ID Controlled by Request Parameter with Password Disclosure](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Password%20Disclosure.md) — `IDOR-Password-Disclosure-001` — _Broken-Access-Control, IDOR, Password-Disclosure, Horizontal-Privilege-Escalation, Admin-Access_
- ✅ [User ID Controlled by Request Parameter with Unpredictable User IDs](User%20ID%20Controlled%20by%20Request%20Parameter%20with%20Unpredictable%20User%20IDs.md) — `Horizontal-Privilege-Escalation-GUID-001` — _Broken-Access-Control, Horizontal-Privilege-Escalation, IDOR, GUID-User-ID, API-Key-Disclosure_
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

### Lab-specific methods (quick lookup)

| Lab | Focus | Detection / Checks | Exploit / Payload (example) | PoC (short request) | Notes / Mitigation |
|---|---|---|---|---|---|
| Method-Based Access Control Can Be Circumvented | HTTP method / verb tampering | Try same endpoint with GET/POST/PUT/DELETE; test `X-HTTP-Method-Override`; observe differing behavior by verb | `X-HTTP-Method-Override: DELETE` or send GET instead of POST | `POST /admin/delete-user HTTP/1.1\nHost: target\nCookie: session=...\nX-HTTP-Method-Override: DELETE` | Enforce server-side auth for each method; canonicalize method and deny unknown overrides |
| URL-Based Access Control Can Be Circumvented | Header-based routing / proxy header injection (`X-Original-URL`) | Send harmless path but add `X-Original-URL: /admin`; compare responses; test `X-Rewrite-URL`, `X-Forwarded-*` | `X-Original-URL: /admin` or `X-Rewrite-URL: /admin` | `GET /index HTTP/1.1\nHost: target\nCookie: session=...\nX-Original-URL: /admin` | Only trust proxy headers from known reverse proxies; validate and canonicalize proxy headers |
| Unprotected Admin Functionality with Unpredictable URL | Discovery of obscure/unlinked admin URL | Inspect `robots.txt`, JS bundles, service-worker, source maps, build files; fuzz for UUID-like paths | Fuzz admin-like names or UUIDs (e.g., `/admin-<hex>/`) | `GET /admin-3f1b2e/ HTTP/1.1\nHost: target\nCookie: session=...` | Hiding URLs isn't auth; require server-side auth and additional access controls (IP allowlists/MFA) |
| Unprotected Admin Functionality | Admin endpoints missing auth | `curl /admin` and inspect response; check `robots.txt`/sitemap for admin links; view pages for forms/actions | Direct access to `/admin` with session cookie | `GET /admin HTTP/1.1\nHost: target\nCookie: session=...` | Require auth & RBAC checks on admin endpoints; return 401/403 instead of admin pages to unauthenticated users |
| User ID Controlled by Request Parameter | ID / user_id parameter tampering (horizontal/vertical) | Enumerate `id` values; look for unique content markers; use Burp Intruder or scripts to compare responses | Change `?id=2` → `?id=3` or `?id=1..N` loops | `GET /account?id=3 HTTP/1.1\nHost: target\nCookie: session=...` | Verify ownership server-side (object-level access control); do not rely on client-provided ids for auth |
| User Role Controlled by Request Parameter | Role tampering via query param / cookie / JWT claim | Inspect cookies & JWT claims; attempt to change `role` cookie or claim; test `alg:none` or weak signing only in labs | Cookie tamper: `role=admin`; JWT claim change (lab-only) | `GET /admin/dashboard HTTP/1.1\nHost: target\nCookie: session=...; role=admin` | Derive role from server-side session or verify JWT signature and claims; reject client-controlled role values |
| IDOR-Data-Leakage-Redirect-001           | IDOR via redirect (data in Location/Referer) | Inspect `Location`/redirects for user identifiers or tokens; change `id` and follow redirect. | Tamper `?id=12345` → `?id=67890` to force redirect exposing other user info. | `GET /view?id=12345 HTTP/1.1\nHost: target\nCookie: session=...\n— check Location: /preview?user=67890`   | Don’t include PII/tokens in URLs; server-side ownership checks before redirect; use short-lived opaque tokens; set strict `Referrer-Policy`. |
| Horizontal-Privilege-Escalation-GUID-001 | Horizontal IDOR with GUID-like IDs           | Fuzz/replace GUID `userId` params; look for response differences (status/size/timing).        | Swap GUIDs (brute/guess) to fetch other users’ data.                         | `GET /profile?userId=3fa85f64-... HTTP/1.1\nHost: target\nCookie: session=...` — change GUID and compare. | Enforce object-level auth server-side; make IDs unguessable; rate-limit/enforce logging to detect enumeration.                               |
