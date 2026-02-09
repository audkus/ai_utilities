"""Tests for the block_dotenv_writes pre-commit hook."""

import pytest
from tools.precommit.block_dotenv_writes import find_violations


class TestBlockDotenvWrites:
    """Test the pattern matching logic for .env write detection."""

    def test_python_write_patterns(self):
        """Test detection of Python .env write patterns."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,6 @@
+open(".env", "w")
+open('.env.local', 'a')
+Path(".env").write_text("content")
"""
        violations = find_violations(diff)
        assert len(violations) == 3
        assert violations[0] == ("test.py", 1, 'open(".env", "w")')
        assert violations[1] == ("test.py", 2, "open('.env.local', 'a')")
        assert violations[2] == ("test.py", 3, 'Path(".env").write_text("content")')

    def test_python_mode_parameter(self):
        """Test detection of Python write with mode parameter."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+open(".env", mode="w")
+open('.env.prod', mode='a')
"""
        violations = find_violations(diff)
        assert len(violations) == 2
        assert violations[0] == ("test.py", 1, 'open(".env", mode="w")')
        assert violations[1] == ("test.py", 2, "open('.env.prod', mode='a')")

    def test_nodejs_patterns(self):
        """Test detection of Node.js .env write patterns."""
        diff = """diff --git a/test.js b/test.js
index 0000000..1111111 100644
--- a/test.js
+++ b/test.js
@@ -1,3 +1,4 @@
+fs.writeFileSync(".env", "content")
+fs.appendFileSync('.env.local', 'more')
"""
        violations = find_violations(diff)
        assert len(violations) == 2
        assert violations[0] == ("test.js", 1, 'fs.writeFileSync(".env", "content")')
        assert violations[1] == ("test.js", 2, "fs.appendFileSync('.env.local', 'more')")

    def test_shell_patterns(self):
        """Test detection of shell .env write patterns."""
        diff = """diff --git a/test.sh b/test.sh
index 0000000..1111111 100644
--- a/test.sh
+++ b/test.sh
@@ -1,3 +1,6 @@
+echo "KEY=VALUE" > .env
+echo "MORE=data" >> .env.local
+tee .env.prod < config.txt
"""
        violations = find_violations(diff)
        assert len(violations) == 3
        assert violations[0] == ("test.sh", 1, 'echo "KEY=VALUE" > .env')
        assert violations[1] == ("test.sh", 2, 'echo "MORE=data" >> .env.local')
        assert violations[2] == ("test.sh", 3, 'tee .env.prod < config.txt')

    def test_reading_patterns_allowed(self):
        """Test that reading .env files is allowed."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+open(".env", "r")
+open('.env.local')
+Path(".env").read_text()
+load_dotenv()
"""
        violations = find_violations(diff)
        assert len(violations) == 0

    def test_allowed_targets_not_blocked(self):
        """Test that writing to allowed targets is not blocked."""
        diff = """diff --git a/setup.py b/setup.py
index 0000000..1111111 100644
--- a/setup.py
+++ b/setup.py
@@ -1,3 +1,4 @@
+open(".env.example", "w")
+open('.env.template', 'a')
+Path(".env.sample").write_text("content")
"""
        violations = find_violations(diff)
        assert len(violations) == 0

    def test_complex_patterns(self):
        """Test more complex patterns and edge cases."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,6 @@
+open( ".env" , "w" )  # with spaces
+Path('.env.development').write_bytes(data)
+with open('.env.production', 'w') as f:
"""
        violations = find_violations(diff)
        assert len(violations) == 3
        assert violations[0] == ("test.py", 1, 'open( ".env" , "w" )  # with spaces')
        assert violations[1] == ("test.py", 2, "Path('.env.development').write_bytes(data)")
        assert violations[2] == ("test.py", 3, "with open('.env.production', 'w') as f:")

    def test_removed_lines_ignored(self):
        """Test that removed lines (-) are ignored."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
-open(".env", "w")  # This removal should be ignored
+open(".env", "r")  # This addition should be allowed
"""
        violations = find_violations(diff)
        assert len(violations) == 0

    def test_empty_diff(self):
        """Test that empty diff produces no violations."""
        violations = find_violations("")
        assert len(violations) == 0

    def test_no_violations(self):
        """Test diff with no .env patterns."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
+print("hello world")
+x = 1 + 2
+import os
"""
        violations = find_violations(diff)
        assert len(violations) == 0

    def test_multiple_files(self):
        """Test violations across multiple files."""
        diff = """diff --git a/test.py b/test.py
index 0000000..1111111 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,2 @@
+open(".env", "w")
diff --git a/test.js b/test.js
index 0000000..1111111 100644
--- a/test.js
+++ b/test.js
@@ -1,3 +1,2 @@
+fs.writeFileSync(".env", "content")
"""
        violations = find_violations(diff)
        assert len(violations) == 2
        assert violations[0] == ("test.py", 1, 'open(".env", "w")')
        assert violations[1] == ("test.js", 1, 'fs.writeFileSync(".env", "content")')
