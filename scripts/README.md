# Scripts Directory

This directory contains development and operational utilities for AI Utilities.

## 🚀 Provider Tools

The main consolidated tool for provider management:

```bash
# Run health check
python scripts/provider_tools.py --health-check

# Run diagnostics
python scripts/provider_tools.py --diagnose

# Detect changes
python scripts/provider_tools.py --detect-changes

# Run all checks
python scripts/provider_tools.py --all
```

### Features:
- **Provider Health Monitoring**: Check status and response times
- **Diagnostics**: Environment, connectivity, and configuration checks
- **Change Detection**: Alert on provider changes and issues
- **CI/CD Integration**: Suitable for automated testing

## 🛠️ Setup Scripts

### Environment Management
- `backup_env.sh` - Backup current environment
- `restore_env.sh` - Restore from backup
- `ci_provider_check.sh` - CI/CD provider validation

### Provider Setup
- `fastchat_setup.py` - FastChat provider setup
- `text_generation_webui_setup.py` - Text Generation WebUI setup

## 📊 Monitoring & Testing

### Monitoring Scripts (`monitoring/`)
- `monitor_providers.py` - Multi-provider testing
- `monitor_providers_system.py` - System-level monitoring
- `probe_*.py` - Integration probes for various providers:
  - `probe_free_apis.py` - Free cloud API probing
  - `probe_fastchat_integration.py` - FastChat local server probing
  - `probe_local_providers.py` - Local AI provider probing
  - `probe_simple_free_api.py` - Simple free API probing
  - `probe_text_generation_webui_integration.py` - Text Generation WebUI probing
- `validate_*.py` - Bug prevention and critical validation

### Utilities
- `coverage_summary.py` - Test coverage analysis
- `dashboard.py` - Monitoring dashboard
- `webui_api_helper.py` - WebUI API utilities
- `import_diagnostic.py` - Import diagnostics

## 🧪 Usage Examples

### Quick Health Check
```bash
python scripts/provider_tools.py --health-check
```

### Full Diagnostics
```bash
python scripts/provider_tools.py --diagnose
```

### Provider Probing
```bash
# Probe free APIs
python scripts/monitoring/probe_free_apis.py

# Probe local providers
python scripts/monitoring/probe_local_providers.py

# Probe FastChat integration
python scripts/monitoring/probe_fastchat_integration.py

# Probe Text Generation WebUI
python scripts/monitoring/probe_text_generation_webui_integration.py
```

### CI/CD Integration
```bash
# In CI pipeline
python scripts/provider_tools.py --all
python scripts/ci_provider_check.sh
```

## 📁 Output Files

The tools generate the following reports:
- `provider_health_report.json` - Health check results
- `provider_diagnostic_report.json` - Diagnostic results  
- `provider_change_report.json` - Change detection results
- `provider_health.json` - Persistent status tracking

## 🔧 Configuration

Most tools use environment variables for configuration:

```bash
# Required for OpenAI
export OPENAI_API_KEY=your-key

# Required for Groq
export GROQ_API_KEY=your-key

# Optional: Create .env file
echo "OPENAI_API_KEY=your-key" > .env
echo "GROQ_API_KEY=your-key" >> .env
```

## 🚨 Notes

- These are **development/ops tools**, not part of the core library
- They depend on `ai_utilities` but are not included in the package
- Scripts are excluded from the PyPI package distribution
- Use these for local development, testing, and CI/CD integration
