# Source Code Disclosure via Backup Files  
**Category**: 06-Security Misconfiguration (OWASP Top 10 A05:2025 – Security Misconfiguration)  
**Lab_ID**: SEC-MISCONFIG-Backup-Files-001  
**Source**: PortSwigger Web Security Academy  
**Date_Completed**: 2025-11-21  
**Tag**: `Security-Misconfiguration`, `Information-Disclosure`, `Source-Code-Leak`, `Backup-Files`, `Hardcoded-Credentials`, `Directory-Enumeration`

---
## Executive summary
A hidden `/backup` directory is publicly accessible and contains an editor-generated backup file (`ProductTemplate.java.bak`). This file is a complete copy of the original Java source code, including a **hard-coded database password** in plaintext.  
An unauthenticated attacker can discover the directory via simple brute-forcing, download the `.bak` file, and immediately extract the sensitive credential that should never leave the server.

**Result:** Unauthenticated → Gobuster → `/backup/ProductTemplate.java.bak` → extract DB password → submit → lab solved.  
**Severity (subjective):** **Critical** — full source code + hardcoded production credentials exposed publicly.

**Recommended immediate action:**  
- Delete or block all backup/editor files (`.bak`, `.~`, `.swp`, `.old`, etc.) from production web root.  
- Disable directory listing and block access to `/backup`.

---
## Objective
Locate the leaked source code backup file, extract the hard-coded database password, and submit it to solve the lab.

---
## Environment & tools
- Target: `https://0a1d008903de8be682f61a1300a30027.web-security-academy.net/`  
- Tools:  
  - Gobuster v3.8  
  - Wordlist: `/usr/share/wordlists/dirb/common.txt`  
  - Browser

---
## Discovery
1. Performed lightweight directory enumeration with Gobuster.  
2. Identified `/backup` returning HTTP 200 with a directory listing page (Size: 435).  
3. Manually visited `https://<lab-url>/backup/` → observed listing containing `ProductTemplate.java.bak`.  
4. Downloaded and opened `ProductTemplate.java.bak` → located the line contaning the password.
5. Submitted the password → lab solved instantly.

> Finding: Classic source-code disclosure via leftover backup files in a world-accessible directory.

---
## Reproduction steps
1. Run directory enumeration:
   ```bash
   gobuster dir -u https://0a1d008903de8be682f61a1300a30027.web-security-academy.net/ \
   -w /usr/share/wordlists/dirb/common.txt -t 20
   ```
2. Identify `/backup` (Status: 200).  
3. Browse to `https://0a1d008903de8be682f61a1300a30027.web-security-academy.net/backup/`  
4. Click or directly request `ProductTemplate.java.bak`.  
5. Search file for password-related strings → extract the hard-coded DB password.  
6. Submit the password in the lab interface → solved.

**Key Gobuster output:**
```
/backup (Status: 200) [Size: 435]
```

**Direct request to leaked source:**
```
GET /backup/ProductTemplate.java.bak HTTP/2
Host: 0a1d008903de8be682f61a1300a30027.web-security-academy.net
```

---
## Observed impact
- Full Java source code of a core class publicly downloadable.  
- Hard-coded production database password exposed.  
- Enables direct database access, data theft, ransomware, or full server compromise if credentials are reused.  
- Attack requires zero authentication.

---
## Root cause analysis
- Primary cause: Backup/temporary files (`.bak`) deployed to or left in production web root.  
- Contributing factors:  
  - Directory listing enabled on `/backup`.  
  - No cleanup process after development/deployment.  
  - Lack of file-extension blacklisting on web server.

---
## Risk assessment
- Likelihood: High (standard wordlists contain “backup”)  
- Impact: Critical (hardcoded production credentials)  
- Overall risk: Critical (CVSS ~9.8 – AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)

---
## Remediation
### Immediate / short-term
1. Delete all backup files and the `/backup` directory from production.  
2. Add web-server blocks:
   ```apache
   # Apache example
   RedirectMatch "\.(bak|~|swp|old|tmp)$">
       Deny from all
   </RedirectMatch>
   ```

### Medium-term
1. Disable directory listing globally:
   ```apache
   Options -Indexes
   ```
2. Implement CI/CD scan for forbidden extensions before deploy.

### Long-term / defensive controls
1. Never store secrets in source code — use secret management (Vault, AWS Secrets Manager, etc.).  
2. Add pre-deployment gate:
   ```bash
   grep -r "password.*=" ./src | wc -l → must be 0
   ```
3. Use `.gitattributes` or WAF rules to block backup-file extensions.

---
## Detection & verification guidance
- Fuzz for common backup extensions:
  ```bash
  ffuf -u https://example.com/FUZZ -w backup-extensions.txt -e .bak,.old,.~,.swp
  ```
- Grep repositories and servers:
  ```bash
  find /var/www -name "*.bak" -o -name "*~"
  ```

---
## Suggested tests to add
- Automated test: production server must return 403/404 on any `*.bak`, `*.~`, `*.swp` request.  
- Pipeline test: block deployment if backup files are present.  
- DAST rule: flag any 200 response containing `// Hard-coded` or `password =`.

---
## References & further reading
- OWASP Top 10 (2025) – A05: Security Misconfiguration  
- OWASP Cheat Sheet: Sensitive Data Exposure  
- “Backup and Editor Files” – common hall-of-fame bug class  
- PortSwigger: Source code disclosure via backup files

---
## Evidence & validation (screenshots placeholders)

**Screenshot 1 – Directory listing showing ProductTemplate.java.bak**  
<img width="958" height="289" alt="Screenshot 2025-11-22 090340" src="https://github.com/user-attachments/assets/3271b67b-b419-4fae-a46e-b3f7c852c82d" />

**Screenshot 2 – Leaked source code with hard-coded DB password highlighted**  
<img width="952" height="337" alt="Screenshot 2025-11-22 090317" src="https://github.com/user-attachments/assets/46373e32-bfdc-4c24-b52b-89b97a1e9cdf" />

**Screenshot 3 – Lab solved confirmation after submitting password**  
<img width="949" height="319" alt="Screenshot 2025-11-22 090433" src="https://github.com/user-attachments/assets/b2de5165-c7bd-4870-b7a0-53f058b79bb9" />

---
> **Legal & ethical reminder:** This write-up documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
