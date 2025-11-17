# Information Disclosure via Verbose Error Messages  
**Category**: 02-Security Misconfiguration (OWASP Top 10 A02:2025)  
**Lab_ID**: SEC-MISCONFIG-Error-Messages-001  
**Source**: PortSwigger Web Security Academy  
**Date_Completed**: 2025-11-17  
**Tag**: `Security-Misconfiguration`, `Information-Disclosure`, `Verbose-Error-Messages`, `Framework-Fingerprinting`, `Apache-Struts`

---
## Executive summary
The application is incorrectly configured to display full Java stack traces in production when an unhandled exception occurs. By sending an invalid data type to the `productId` parameter (e.g., a string instead of an integer), the server throws an exception that leaks detailed diagnostic information, including the exact version of the underlying framework: **Apache Struts 2 2.3.31**.  
This version is known to contain multiple critical remote code execution vulnerabilities (e.g., CVE-2017-5638 and others in the 2.3.x series before 2.3.32). Revealing the precise vulnerable version allows an attacker to select and launch a targeted exploit.

**Result:** Authenticated or unauthenticated user → tamper `productId` parameter → obtain framework version **2.3.31** → submit solution → lab solved.  
**Severity (subjective):** **High** — direct disclosure of vulnerable third-party component version in production.

**Recommended immediate action:**  
- Disable detailed error pages and stack traces in production.  
- Configure custom error handling to return generic messages.  
- Upgrade Apache Struts immediately to a supported, patched version.

---
## Objective
Exploit verbose error messages to identify the exact version of the third-party framework in use and submit it to solve the lab.

---
## Environment & tools
- Target: PortSwigger lab instance (`0a8c00d703377818807f491300e900a2.web-security-academy.net`)  
- Tools: Burp Suite Professional/Community (Repeater), any modern browser  
- Prerequisites: Burp proxy configured and browser routed through it

---
## Discovery
1. Browsed a normal product page (e.g., `/product?productId=2`).  
2. Sent the request to Burp Repeater.  
3. Changed the `productId` parameter from an integer to a string (`"test"` or any non-numeric value).  
4. Sent the malformed request → server returned a full Java stack trace.  
5. Stack trace explicitly contained the line:  
   `Apache Struts 2 2.3.31`  
   confirming the exact vulnerable version.

> Finding: The application is configured with `devMode = false` but still exposes full stack traces on unhandled exceptions — classic **security misconfiguration**.

---
## Reproduction steps
1. With Burp running, access any product page (e.g., `productId=1` or `productId=2`).  
2. In Burp Proxy → HTTP history, locate the `GET /product?productId=X` request and send it to Repeater.  
3. In Repeater, modify the parameter to a non-integer value:  
   `GET /product?productId="test"`  
4. Send the request.  
5. Observe the full stack trace in the response body revealing **Apache Struts 2 2.3.31**.  
6. Return to the lab banner → click “Submit solution” → enter `2.3.31` → lab solved.

**Captured HTTP interaction (triggering payload):**
```
GET /product?productId="test" HTTP/2
Host: 0a8c00d703377818807f491300e900a2.web-security-academy.net
Cookie: session=4vrXnYTIHDM99pmnhVlF0iRSc869Zzef
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: navigate
Referer: https://0a8c00d703377818807f491300e900a2.web-security-academy.net/
```

**Relevant response excerpt:**
```
...
at lab.server.k.w.c.q(Unknown Source)
at lab.server.k.q.m(Unknown Source)
...
at java.base/java.lang.Thread.run(Thread.java:1583)

Apache Struts 2 2.3.31
```

---
## Observed impact
- Exact vulnerable framework version disclosed in production.  
- Enables targeted exploitation of known RCE vulnerabilities in Apache Struts 2.3.31 and earlier.  
- No authentication required — attack works unauthenticated.  
- Potential for remote code execution, full system compromise.

---
## Root cause analysis
- **Primary cause:** Detailed error handling and stack traces enabled in production environment.  
- **Secondary causes:**  
  - Lack of custom error pages or exception filters.  
  - Framework running in non-secure default configuration.  
  - Missing HTTP security headers that could help obscure server details.

---
## Risk assessment
- **Likelihood:** High (single malformed parameter triggers disclosure)  
- **Impact:** High (reveals exploitable RCE vulnerability)  
- **Overall risk:** High (CVSS ~9.8 possible when combined with known Struts CVEs)

---
## Remediation
### Immediate / short-term
1. Disable stack traces in production:
   ```xml
   <!-- struts.xml -->
   <constant name="struts.devMode" value="false" />
   <constant name="struts.enable.DynamicMethodInvocation" value="false" />
   ```
2. Configure global exception handling to show generic error pages.

### Medium-term
1. Implement a global exception filter (Java Servlet Filter / Spring `@ControllerAdvice` / Struts Exception Mapping) returning HTTP 500 with generic message.
2. Add custom error pages (`error.html`, `500.html`).
3. Remove server banners and unnecessary headers.

### Long-term / defensive controls
1. Upgrade Apache Struts to a supported version (≥ 2.5.x or 6.x branch).  
2. Enable security headers (Server, X-Powered-By removal).  
3. Implement WAF rules to block obvious error-message scraping.  
4. Regular configuration review and hardening checklists.

---
## Detection & verification guidance
- Send unexpected data types (string, null, array) to parameters expecting integers/IDs.  
- Look for Java/.NET/PHP stack traces in responses.  
- Grep source/code for:
  ```java
  e.printStackTrace();
  ```
- Automated checks:
  ```bash
  curl ".../product?productId=abc" | grep -i "struts\|exception\|stack"
  ```

---
## Suggested tests to add
- Fuzz all parameters with type mismatches → no stack trace allowed.  
- 500 responses must not contain words: “java”, “exception”, “trace”, framework names.  
- Production build must have `struts.devMode=false` and custom error pages.

---
## References & further reading
- OWASP Top 10 – A06:2021 Vulnerable and Outdated Components  
- OWASP Top 10 – A05:2021 Security Misconfiguration  
- Apache Struts Security Bulletins (CVE-2017-5638, etc.)  
- PortSwigger: Information disclosure in error messages

---
## Evidence & validation (screenshots placeholders)

**Screenshot 1 – Normal product page (productId=2)**  
<img width="361" height="349" alt="Screenshot 2025-11-17 221041" src="https://github.com/user-attachments/assets/6e314614-ba21-40ea-acb1-7731a57813e3" />


**Screenshot 2 – Malformed parameter triggering stack trace (productId="test")**  
<img width="719" height="349" alt="Screenshot 2025-11-17 221230" src="https://github.com/user-attachments/assets/e37e6449-dc4e-4bb7-b7b8-79849a1e1e2a" />


**Screenshot 3 – Lab solved confirmation**  
<img width="950" height="391" alt="Screenshot 2025-11-17 221205" src="https://github.com/user-attachments/assets/d2bad1ed-2aef-4848-8aa5-908ca3ada87c" />


---
> **Legal & ethical reminder:** This write-up documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to systems without explicit authorization.
