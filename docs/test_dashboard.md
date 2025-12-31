# 🧪 Test Dashboard Documentation

The AI Utilities Test Dashboard provides comprehensive testing visibility with real-time progress, provider coverage analysis, and accurate test reporting for the entire AI utilities ecosystem.

## 📊 Test Dashboard Results

### ✅ Dashboard Self-Tests: 17/17 PASSED
The test dashboard includes its own comprehensive test suite:

```
tests/test_dashboard.py::TestTestDashboard::test_dashboard_initialization PASSED
tests/test_dashboard.py::TestTestDashboard::test_load_env_file PASSED
tests/test_dashboard.py::TestTestDashboard::test_parse_pytest_output_success PASSED
tests/test_dashboard.py::TestTestDashboard::test_parse_pytest_output_with_failures PASSED
tests/test_dashboard.py::TestTestDashboard::test_run_test_suite_success PASSED
tests/test_dashboard.py::TestTestDashboard::test_generate_module_support_matrix PASSED
tests/test_dashboard.py::TestTestDashboard::test_dashboard_with_api_key PASSED
tests/test_dashboard.py::TestTestDashboard::test_full_suite_mode PASSED
tests/test_dashboard.py::TestTestDashboard::test_files_api_focus_mode PASSED
...
========================= 17 passed, 1 warning in 0.07s =========================
```

**Dashboard Test Coverage:**
- ✅ Environment loading and validation
- ✅ Pytest output parsing accuracy
- ✅ Test execution workflows
- ✅ API key detection logic
- ✅ Provider coverage analysis
- ✅ Error handling and edge cases
- ✅ Integration test behavior

### 🌐 Provider-Specific Test Counts

| Provider | Test Count | Test Types | Coverage |
|----------|------------|------------|----------|
| **OpenAI** | 40 tests | Unit, Integration, Live API | ✅ Comprehensive |
| **Groq** | 2 tests | Integration, Live API | ✅ Basic Coverage |
| **Ollama** | 8 tests | Unit, Integration, Local | ✅ Good Coverage |
| **Together** | 7 tests | Integration, Live API | ✅ Good Coverage |
| **OpenRouter** | 4 tests | Integration, Live API | ✅ Basic Coverage |
| **FastChat** | 6 tests | Integration, Local | ✅ Basic Coverage |
| **Text Generation WebUI** | 6 tests | Integration, Local | ✅ Basic Coverage |
| **LM Studio** | 4 tests | Integration, Local | ✅ Basic Coverage |
| **OpenAI Compatible** | 12 tests | Unit, Integration, Capability | ✅ Good Coverage |
| **TOTAL** | **89 tests** | **All Types** | ✅ Complete |

**Test Categories:**
- **Unit Tests**: Core functionality testing
- **Integration Tests**: Real API interaction testing
- **Live API Tests**: Production environment validation
- **Local Provider Tests**: Self-hosted provider testing
- **Capability Tests**: Feature availability validation

## 🚀 Quick Start

```bash
# Run Files API focused tests (default)
python scripts/test_dashboard.py

# Run with integration tests
python scripts/test_dashboard.py --integration

# Run complete project test suite
python scripts/test_dashboard.py --full-suite

# Run full suite with integration tests
python scripts/test_dashboard.py --full-suite --integration
```

## 📊 Dashboard Features

### ✅ Real-Time Test Progress
- **Live test counter**: Shows `1/24`, `2/24`, etc. as tests run
- **Test names displayed**: See which specific test is executing
- **No more stalling**: Clear visibility into test execution
- **Status indicators**: ✅ PASSED, ❌ FAILED, ⏭️ SKIPPED

### 🌐 Complete Provider Coverage
- **9 supported providers**: All providers with integration tests
- **Service availability detection**: Accurate status based on environment
- **Integration test status**: Shows what's actually working
- **Clear requirements**: API keys, local servers, etc.

### 📈 Accurate Test Reporting
- **Grand total display**: `39/45 tests executed` format
- **Detailed breakdown**: Per-category test results
- **Failure analysis**: Clear indication of what needs fixing
- **Production readiness**: Overall project health assessment

## 🎯 Dashboard Modes

### Files API Focus (Default)
```bash
python scripts/test_dashboard.py
```
**What it tests:**
- Files API unit tests (24 tests)
- Files API integration tests (10 tests) 
- Core functionality tests (5 tests)
- Async operations tests (6 tests)
- **Total**: ~45 tests

### Full Suite Mode
```bash
python scripts/test_dashboard.py --full-suite
```
**What it tests:**
- Complete project unit tests (446 tests)
- Integration tests (45+ tests)
- Core functionality tests (5 tests)
- Async operations tests (6 tests)
- **Total**: ~502 tests

### Integration Tests
```bash
python scripts/test_dashboard.py --integration
```
**Requirements:**
```bash
export AI_API_KEY='your-api-key'
export RUN_LIVE_AI_TESTS=1
```

## 🌐 Provider Coverage Analysis

The dashboard automatically detects and reports on all 9 supported providers:

### ✅ Fully Supported Providers
| Provider | Unit Tests | Integration | Status |
|----------|------------|-------------|---------|
| OpenAI | ✅ Working | ✅ API Key Available | ✅ Fully Supported |
| Groq | ✅ Working | ✅ API Key Available | ✅ Fully Supported |
| Together | ✅ Working | ✅ API Key Available | ✅ Fully Supported |
| OpenRouter | ✅ Working | ✅ API Key Available | ✅ Fully Supported |

### 🔄 Local Setup Required
| Provider | Unit Tests | Integration | Status |
|----------|------------|-------------|---------|
| Ollama | ✅ Working | 🔄 Local Required | ✅ Fully Supported |
| LM Studio | ✅ Working | 🔄 Local Required | ✅ Fully Supported |
| OpenAI Compatible | ✅ Working | 🔄 Local Required | ✅ Fully Supported |

### ⚠️ Partially Supported
| Provider | Unit Tests | Integration | Status |
|----------|------------|-------------|---------|
| Text Generation WebUI | ✅ Working | ⚠️ Service Not Installed | ⚠️ Partially Supported |
| FastChat | ✅ Working | ⚠️ Service Not Installed | ⚠️ Partially Supported |

## 📋 Sample Dashboard Output

### Real-Time Progress Display
```
🧪 Running Files API Unit Tests...
   Executing: pytest tests/test_files_api.py -q
   Running tests:
   Found 24 tests
    1/24 ✅ test_upload_file_success
    2/24 ✅ test_upload_file_with_custo...
    3/24 ✅ test_upload_file_nonexistent
   ...
   24/24 ✅ test_uploaded_file_string_r...
   ✅ PASSED: 24/24 passed
```

### Provider Coverage Summary
```
🌐 PROVIDER COVERAGE SUMMARY:
┌─────────────────────────┬────────────────┬────────────────┬────────────────┐
│ Provider                │ Unit Tests     │ Integration    │ Status         │
├─────────────────────────┼────────────────┼────────────────┼────────────────┤
│ OpenAI                  │ ✅ Working      │ ✅ API Key Available │ ✅ Fully Supported │
│ Groq                    │ ✅ Working      │ ✅ API Key Available │ ✅ Fully Supported │
│ Text Generation WebUI   │ ✅ Working      │ ⚠️ Service Not Installed │ ⚠️ Partially Supported │
│ FastChat                │ ✅ Working      │ ⚠️ Service Not Installed │ ⚠️ Partially Supported │
├─────────────────────────┼────────────────┼────────────────┼────────────────┤
│ TOTAL                   │ 9 Providers    │ 7 Fully, 2 Partial │ ✅ Complete     │
└─────────────────────────┴────────────────┴────────────────┴────────────────┘
```

### Test Execution Summary
```
📊 TEST EXECUTION SUMMARY:
┌─────────────────────┬──────────┬──────────┬─────────────┐
│ Category            │ Total    │ Passed   │ Failed      │
├─────────────────────┼──────────┼──────────┼─────────────┤
│ Files API Unit Test │       24 │       24 │            0 │
│ Files Integration T │       10 │        4 │         6 │
│ Core Functionality  │        5 │        5 │            0 │
│ Async Operations    │        6 │        6 │            0 │
├─────────────────────┼──────────┼──────────┼─────────────┤
│ TOTAL               │       45 │       39 │         6 │
└─────────────────────┴──────────┴──────────┴─────────────┘

🎯 **GRAND TOTAL: 39/45 tests executed**
⚠️  6 test failures detected

🚨 PRODUCTION READINESS: ❌ NEEDS FIXES
```

## 🔧 Configuration

### Environment Variables
```bash
# Required for integration tests
export AI_API_KEY='your-openai-key'

# For full integration testing
export RUN_LIVE_AI_TESTS=1

# Optional: Local provider URLs
export LIVE_OLLAMA_URL='http://localhost:11434/v1'
export LIVE_LMSTUDIO_URL='http://localhost:1234/v1'
export LIVE_TEXTGEN_MODEL='your-model'
export LIVE_FASTCHAT_MODEL='your-model'
```

### Dashboard Options
```bash
# Show help
python scripts/test_dashboard.py --help

# Verbose output (detailed test execution)
python scripts/test_dashboard.py --verbose

# Files API focus (default)
python scripts/test_dashboard.py

# Full project suite
python scripts/test_dashboard.py --full-suite

# Include integration tests
python scripts/test_dashboard.py --integration

# Full suite with integration tests
python scripts/test_dashboard.py --full-suite --integration
```

## 🧪 Integration Test Behavior

### Test Skipping (Correct Behavior)
Integration tests are **SKIPPED** (not failed) when:
- Services are not installed (TextGen WebUI, FastChat)
- Local servers are not running (Ollama, LM Studio)
- API keys are not available
- Required environment variables are missing

### Test Running
Tests run when:
- `RUN_LIVE_AI_TESTS=1` is set
- Required services are available
- API keys are configured
- Environment variables are properly set

### Example Integration Test Commands
```bash
# Run with API key (OpenAI, Groq, Together, OpenRouter work)
export AI_API_KEY='your-key'
python scripts/test_dashboard.py --integration

# Run with local services
export LIVE_OLLAMA_URL='http://localhost:11434/v1'
export RUN_LIVE_AI_TESTS=1
python scripts/test_dashboard.py --integration

# Run all integration tests
export AI_API_KEY='your-key'
export RUN_LIVE_AI_TESTS=1
python scripts/test_dashboard.py --full-suite --integration
```

## 📊 Test Categories

### Files API Tests
- **Unit Tests**: Core Files API functionality (24 tests)
- **Integration Tests**: Real API file operations (10 tests)
- **Coverage**: Upload, download, metadata, async operations

### Core Functionality Tests
- **Text Generation**: Basic AI response generation
- **File Operations**: Upload/download capabilities
- **Image Generation**: Image creation functionality
- **Document AI**: Document processing features

### Async Operations Tests
- **Async Text Generation**: Non-blocking text generation
- **Async Image Generation**: Non-blocking image creation
- **Async File Operations**: Non-blocking file operations
- **Error Handling**: Async error management

## 🚨 Troubleshooting

### Integration Tests Not Running
```bash
# Check if API key is set
echo $AI_API_KEY

# Enable integration testing
export RUN_LIVE_AI_TESTS=1

# Run with verbose output
python scripts/test_dashboard.py --integration --verbose
```

### Local Provider Tests Not Running
```bash
# Check if local server is running
curl http://localhost:11434/v1/models

# Set correct URL
export LIVE_OLLAMA_URL='http://localhost:11434/v1'

# Run tests
python scripts/test_dashboard.py --integration
```

### Dashboard Shows "Service Not Installed"
This is correct behavior for:
- Text Generation WebUI
- FastChat

These services are optional and not required for core functionality.

## 📈 Production Readiness

The dashboard provides a clear production readiness assessment:

### ✅ Ready for Merge
- All tests passing
- No critical failures
- Core functionality working
- Integration tests available

### ❌ Needs Fixes
- Test failures detected
- Missing functionality
- Integration issues
- Configuration problems

## 🎯 Best Practices

1. **Run Files API focus** for quick development feedback
2. **Use integration mode** when testing file operations
3. **Run full suite** before major releases
4. **Check provider coverage** to understand what's tested
5. **Monitor real-time progress** for long-running test suites
6. **Review failure details** for debugging information

## 📝 Development Notes

- Dashboard automatically loads `.env` file for environment variables
- Tests are executed in subprocesses for isolation
- Real-time progress is parsed from pytest output
- Provider coverage is detected dynamically
- Integration tests follow pytest best practices (skip when unavailable)

For more information, see:
- [Files API Documentation](files.md)
- [Testing Setup Guide](testing-setup.md)
- [Command Reference](command_reference.md)
