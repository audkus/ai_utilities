# Security Guide for AI Utilities

This guide covers security considerations and best practices for using AI Utilities in production environments.

## 🔒 Security Overview

AI Utilities is designed with security as a primary consideration, handling sensitive data such as API keys, user prompts, and AI responses. This guide helps ensure secure deployment and operation.

## 🛡️ Security Checklist

### ✅ API Key Management

- **Environment Variables**: Store API keys in environment variables, not in code
- **No Hardcoded Keys**: Never commit API keys to version control
- **Key Rotation**: Regularly rotate API keys and update environment variables
- **Access Control**: Limit API key permissions to minimum required scope
- **Audit Trail**: Monitor API key usage and access patterns

```bash
# ✅ Secure - use environment variables
export AI_API_KEY="your-api-key-here"

# ❌ Insecure - hardcoded in code
API_KEY = "sk-1234567890abcdef"  # NEVER do this
```

### ✅ Input Validation

- **Prompt Sanitization**: Validate and sanitize user inputs before processing
- **Length Limits**: Set reasonable limits on prompt and response lengths
- **Content Filtering**: Implement content filtering for malicious inputs
- **Encoding Safety**: Ensure proper handling of special characters and encoding

```python
# ✅ Secure input validation
def validate_prompt(prompt: str) -> str:
    if len(prompt) > 10000:
        raise ValueError("Prompt too long")
    if not prompt.strip():
        raise ValueError("Empty prompt")
    return prompt.strip()

# Use validated input
safe_prompt = validate_prompt(user_input)
response = client.ask(safe_prompt)
```

### ✅ Data Protection

- **Encryption in Transit**: All API communications use HTTPS/TLS
- **No Sensitive Logging**: Avoid logging API keys, prompts, or responses
- **Cache Security**: Ensure cached data is properly protected
- **Memory Cleanup**: Clear sensitive data from memory when no longer needed

```python
# ✅ Secure logging configuration
import logging

# Configure logging to exclude sensitive data
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger.info("AI request processed")  # ✅ Safe
# logger.info(f"Prompt: {prompt}")  # ❌ Unsafe - logs sensitive data
```

### ✅ Network Security

- **TLS Verification**: Ensure SSL certificate verification is enabled
- **Proxy Support**: Use secure proxy configurations when required
- **Timeout Configuration**: Set appropriate timeouts to prevent hanging
- **Rate Limiting**: Respect provider rate limits to avoid blocking

```python
# ✅ Secure client configuration
settings = AiSettings(
    api_key="your-key",
    timeout=30,  # Prevent hanging requests
    # TLS verification is enabled by default
)
client = AiClient(settings)
```

### ✅ Error Handling

- **No Information Leakage**: Avoid exposing internal details in error messages
- **Secure Defaults**: Use secure default configurations
- **Graceful Degradation**: Handle failures without exposing sensitive data
- **Audit Logging**: Log security events without sensitive information

```python
# ✅ Secure error handling
try:
    response = client.ask(prompt)
except ProviderError as e:
    logger.error(f"AI provider error: {e.code}")  # ✅ Safe - no sensitive data
    # Don't log the full exception which might contain sensitive info
    raise AIServiceError("Service temporarily unavailable")
```

## 🔐 API Key Security Best Practices

### Environment Variable Management

```bash
# Production environment setup
export AI_API_KEY="sk-proj-actual-key-here"
export AI_MODEL="gpt-4"
export AI_CACHE_ENABLED="true"
```

### Docker Security

```dockerfile
# ✅ Secure Docker configuration
FROM python:3.9-slim

# Create non-root user
RUN useradd -m -u 1000 aiuser
USER aiuser

# Set environment variables (use secrets management in production)
ENV AI_API_KEY=""
ENV PYTHONUNBUFFERED=1

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Run application
CMD ["python", "app.py"]
```

### Kubernetes Security

```yaml
# ✅ Secure Kubernetes configuration
apiVersion: v1
kind: Secret
metadata:
  name: ai-utilities-secrets
type: Opaque
stringData:
  AI_API_KEY: "sk-proj-actual-key-here"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-app
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: ai-app
        image: ai-app:latest
        envFrom:
        - secretRef:
            name: ai-utilities-secrets
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 🛡️ Input Validation and Sanitization

### Prompt Validation

```python
import re
from typing import Optional

class PromptValidator:
    """Validates and sanitizes user prompts for security."""
    
    MAX_PROMPT_LENGTH = 10000
    ALLOWED_PATTERN = re.compile(r'^[\w\s\.\,\!\?\;\:\-\\"\'\(\)\[\]\{\}]+$')
    
    @classmethod
    def validate(cls, prompt: str) -> str:
        """Validate and sanitize a prompt."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            raise ValueError(f"Prompt too long (max {cls.MAX_PROMPT_LENGTH} chars)")
        
        # Remove potentially dangerous characters
        sanitized = prompt.strip()
        
        # Basic pattern matching (customize based on your needs)
        if not cls.ALLOWED_PATTERN.match(sanitized):
            raise ValueError("Prompt contains invalid characters")
        
        return sanitized
    
    @classmethod
    def extract_metadata(cls, prompt: str) -> dict:
        """Extract safe metadata from prompt for logging."""
        return {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "has_numbers": bool(re.search(r'\d', prompt)),
            "language": "en"  # Could be detected with libraries
        }

# Usage example
validator = PromptValidator()
safe_prompt = validator.validate(user_input)
metadata = validator.extract_metadata(safe_prompt)
logger.info(f"Processing prompt: {metadata}")
```

### Response Filtering

```python
class ResponseFilter:
    """Filters AI responses for sensitive information."""
    
    SENSITIVE_PATTERNS = [
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card numbers
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
    ]
    
    @classmethod
    def filter_response(cls, response: str) -> str:
        """Filter sensitive information from responses."""
        filtered = response
        for pattern in cls.SENSITIVE_PATTERNS:
            filtered = re.sub(pattern, '[REDACTED]', filtered, flags=re.IGNORECASE)
        return filtered
    
    @classmethod
    def scan_for_secrets(cls, response: str) -> list:
        """Scan for potential secrets in response."""
        secrets = []
        for i, pattern in enumerate(cls.SENSITIVE_PATTERNS):
            matches = re.findall(pattern, response, flags=re.IGNORECASE)
            if matches:
                secrets.append({"type": f"pattern_{i}", "count": len(matches)})
        return secrets

# Usage example
filtered_response = ResponseFilter.filter_response(ai_response)
secrets = ResponseFilter.scan_for_secrets(ai_response)
if secrets:
    logger.warning(f"Potential secrets found in response: {secrets}")
```

## 🔍 Security Monitoring

### Audit Logging

```python
import json
import hashlib
from datetime import datetime

class SecurityAuditor:
    """Handles security audit logging."""
    
    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = log_file
    
    def log_request(self, user_id: str, prompt_hash: str, model: str, success: bool):
        """Log an AI request for audit purposes."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "prompt_hash": prompt_hash,  # Hash, not actual prompt
            "model": model,
            "success": success,
            "event_type": "ai_request"
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    
    def hash_prompt(self, prompt: str) -> str:
        """Create a hash of the prompt for logging (don't store the prompt)."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

# Usage example
auditor = SecurityAuditor()
prompt_hash = auditor.hash_prompt(user_input)
auditor.log_request(user_id="user123", prompt_hash=prompt_hash, model="gpt-4", success=True)
```

### Rate Limiting and Abuse Detection

```python
from collections import defaultdict
from time import time
from typing import Dict

class AbuseDetector:
    """Detects potential abuse or unusual usage patterns."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user exceeds rate limits."""
        now = time()
        # Clean old requests (older than 1 minute)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] 
            if now - req_time < 60
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def detect_suspicious_patterns(self, user_id: str, prompt: str) -> bool:
        """Detect suspicious usage patterns."""
        # Check for extremely long prompts
        if len(prompt) > 50000:
            return True
        
        # Check for rapid successive requests
        recent_requests = self.requests.get(user_id, [])
        if len(recent_requests) > 10:
            # More than 10 requests in the last minute is suspicious
            return True
        
        return False

# Usage example
abuse_detector = AbuseDetector()
if not abuse_detector.check_rate_limit(user_id):
    raise RateLimitError("Too many requests")
```

## 🚨 Incident Response

### Security Incident Response Plan

1. **Detection**: Monitor for unusual patterns, API key misuse, data exposure
2. **Assessment**: Evaluate impact and scope of the incident
3. **Containment**: Rotate API keys, disable affected accounts
4. **Investigation**: Analyze logs, identify root cause
5. **Recovery**: Implement fixes, restore services
6. **Prevention**: Update security measures, improve monitoring

### Emergency Procedures

```python
class EmergencySecurity:
    """Emergency security procedures."""
    
    @staticmethod
    def revoke_api_key():
        """Immediately revoke current API key."""
        # Implementation depends on provider
        # For OpenAI: https://platform.openai.com/api-keys
        logger.critical("API key revocation initiated")
    
    @staticmethod
    def enable_maintenance_mode():
        """Enable maintenance mode to stop all AI requests."""
        # Set global flag or environment variable
        os.environ["AI_MAINTENANCE_MODE"] = "true"
        logger.critical("Maintenance mode enabled")
    
    @staticmethod
    def backup_audit_logs():
        """Create emergency backup of audit logs."""
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy("security_audit.log", f"security_audit_backup_{timestamp}.log")
        logger.info("Audit logs backed up")
```

## 📋 Security Configuration Checklist

### Before Production Deployment

- [ ] API keys stored in environment variables, not code
- [ ] Input validation implemented for all user inputs
- [ ] Logging configured to exclude sensitive data
- [ ] Error messages don't expose internal details
- [ ] HTTPS/TLS enabled for all communications
- [ ] Rate limiting configured appropriately
- [ ] Audit logging enabled and working
- [ ] Security monitoring and alerting set up
- [ ] Access controls implemented for production systems
- [ ] Backup and recovery procedures tested

### Regular Security Tasks

- [ ] Review API key usage and rotate if needed
- [ ] Monitor audit logs for suspicious activity
- [ ] Update dependencies to latest secure versions
- [ ] Test security controls and procedures
- [ ] Review and update security documentation
- [ ] Conduct security assessments and penetration testing

## 🔗 Additional Resources

- [OWASP AI Security Guidelines](https://owasp.org/www-project-ai-security-and-privacy-guide/)
- [OpenAI API Security Best Practices](https://platform.openai.com/docs/overview)
- [Python Security Guidelines](https://docs.python.org/3/library/security.html)

---

**Remember**: Security is an ongoing process, not a one-time setup. Regular reviews and updates are essential for maintaining security in production environments.
