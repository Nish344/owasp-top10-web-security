# Information Disclosure via Exposed Debug Page   
**Category**: 06-Security Misconfiguration (OWASP Top 10 A05:2025 – Security Misconfiguration)  
**Lab_ID**: SEC-MISCONFIG-Debug-Page-001  
**Source**: PortSwigger Web Security Academy  
**Date_Completed**: 2025-11-20  
**Tag**: `Security-Misconfiguration, Information-Disclosure, Debug-Page, phpinfo, Secret-Leak, Environment-Variables`

---
## Executive summary
The application leaves an exposed debug file (`/cgi-bin/phpinfo.php`) reachable from the web root. This file, intended only for development, displays the full output of PHP’s `phpinfo()` function. Among hundreds of configuration details, it directly discloses the value of the server-side environment variable `SECRET_KEY`, which is used by the application for signing sessions and encryption.  
An unauthenticated attacker can simply visit the page or discover it via directory brute-forcing and immediately obtain the secret credentials that should never be exposed.

**Result:** Unauthenticated user → directory enumeration → `/cgi-bin/phpinfo.php` → extract `SECRET_KEY` → submit solution → lab solved.  
**Severity (subjective):** Critical — direct exposure of high-value application secret.

**Recommended immediate action:**  
- Immediately delete or block access to all `phpinfo.php`, `debug.php`, `.env`, and similar files in production.  
- Never deploy development/debug tooling to production servers.

---
## Objective
Find the hidden debug page, extract the `SECRET_KEY` environment variable from it, and submit it to solve the lab.

---
## Environment & tools
- Target: `https://0a1f006803445b0781f6b69c00170096.web-security-academy.net/`  
- Tools used:  
  - Gobuster (directory brute-forcing)  
  - Wordlist: `/usr/share/wordlists/dirb/common.txt`  
  - Any modern browser

---
## Discovery
1. Ran lightweight directory enumeration with Gobuster using the common wordlist.  
2. Discovered `/cgi-bin/` returning 200 with directory listing or direct file access.  
3. Manually browsed `/cgi-bin/` → identified `phpinfo.php`.  
4. Accessed `https://0a1f006803445b0781f6b69c00170096.web-security-academy.net/cgi-bin/phpinfo.php`  
5. Searched the massive HTML output for `SECRET_KEY` → found the plaintext value in the “Environment” section.

> Finding: Classic development artifact (`phpinfo.php`) accidentally deployed and publicly accessible in production.

---
## Reproduction steps
1. Launch directory brute-forcing:
   ```bash
   gobuster dir -u https://0a1f006803445b0781f6b69c00170096.web-security-academy.net/ \
   -w /usr/share/wordlists/dirb/common.txt -t 20
   ```
2. Observe `/cgi-bin` returning Status 200.  
3. Visit `https://<lab-url>/cgi-bin/phpinfo.php` in the browser.  
4. Use Ctrl+F → search for `SECRET_KEY`.  
5. Copy the value displayed next to `SECRET_KEY` in the Environment variables table.  
6. Go back to the lab page → “Submit solution” → paste the secret key → lab solved.

**Gobuster output excerpt:**
```
===============================================================
/cgi-bin (Status: 200) [Size:410]
/cgi-bin/ (Status:200) [Size:410]
===============================================================
```

**Direct request to debug file:**
```
GET /cgi-bin/phpinfo.php HTTP/2
Host: 0a1f006803445b0781f6b69c00170096.web-security-academy.net
```

Response contains (among thousands of lines):
```
SECRET_KEY    →    7k9m3q2p8x5v1r6t4w0y9z8a7b6c5d4e3f2g1h
```

---
## Observed impact
- Full server and PHP configuration disclosure (versions, paths, extensions, environment variables).  
- Direct leakage of the application’s primary `SECRET_KEY`.  
- Enables session forgery, token prediction, encryption bypass, and full account takeover.  
- No authentication required — completely unauthenticated attack.

---
## Root cause analysis
- Primary cause: Development/debug file (`phpinfo.php`) deployed to production server.  
- Contributing factors:  
  - Missing or overly permissive web server directory restrictions.  
  - No production hardening checklist.  
  - Lack of automated checks for known dangerous files.

---
## Risk assessment
- Likelihood: High (easily discoverable with any directory scanner)  
 Impact: Critical (direct secret exposure)  
 Overall risk: Critical (CVSS ~9.8 – AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)

---
## Remediation
### Immediate / short-term
1. Delete or chmod 000 the following files if they exist:
   ```
   phpinfo.php, info.php, test.php, debug.php, .env, config.inc.php
   ```
2. Add web-server block rule:
   ```apache
   # Apache
   <LocationMatch "phpinfo\.php|info\.php">
       Deny from all
   </LocationMatch>
   ```

### Medium-term
1. Implement automated production deployment checks:
   ```bash
   grep -r "phpinfo(" ./ | wc -l → must be 0
   ```
2. Use robots.txt + WAF rules to block access to `/cgi-bin/` unless required.

### Long-term / defensive controls
1. Never commit debug files to repository or include them in builds.  
2. Enforce CI/CD pipeline scans for forbidden files.  
3. Store secrets only in proper secret-management systems, never in environment dumps.  
4. Enable automated vulnerability scanners that flag `phpinfo()` exposure.

---
## Detection & verification guidance
- Crawl or fuzz for common debug filenames (`phpinfo.php`, `info.php`, `debug`, `test.php`).  
- Grep codebase and servers:
  ```bash
  find /var/www -name "*phpinfo*" -o -name "*debug*"
  ```
- Add DAST rule: any 200 response > 50 KB containing “PHP Version” and “Environment” → alert.

---
## Suggested tests to add
- Automated check: production servers must not serve `phpinfo.php` (→ 403/404/403).  
- Pipeline test: block merge if `phpinfo()` call is detected.  
- Scanner test: ffuf/gobuster must not discover debug endpoints.

---
## References & further reading
- OWASP Top 10 (2025) – A05: Security Misconfiguration  
- OWASP Cheat Sheet: Information Disclosure  
- “Never deploy phpinfo() to production” – every PHP security guide ever  
- PortSwigger: Information disclosure on debug page

---
## Evidence & validation (screenshots placeholders)

**Screenshot 1 – Gobuster discovering /cgi-bin**  
<img width="959" height="195" alt="Screenshot 2025-11-20 211449" src="https://github.com/user-attachments/assets/198c72a1-f243-4eec-855b-7bf0fc488674" />

**Screenshot 2 – phpinfo.php output showing SECRET_KEY**  
<img width="946" height="404" alt="Screenshot 2025-11-20 211402" src="https://github.com/user-attachments/assets/3e4bc088-3921-44d8-ae5c-32c132e63a89" />

**Screenshot 3 – Lab solved confirmation after submitting SECRET_KEY**  
<img width="947" height="384" alt="Screenshot 2025-11-20 212003" src="https://github.com/user-attachments/assets/90f2e985-5d11-4394-8993-12c1ad8f0cd1" />

---
> **Legal & ethical reminder:** This write-up documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
