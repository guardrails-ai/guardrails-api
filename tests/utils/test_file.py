"""Unit tests for guardrails_api.utils.file module."""
import unittest
import tempfile
import os
from guardrails_api.utils.file import get_file_contents


class TestGetFileContents(unittest.TestCase):
    """Test cases for the get_file_contents function."""

    def setUp(self):
        """Set up temporary test files."""
        self.temp_files = []

    def tearDown(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except Exception:
                pass

    def create_temp_file(self, content):
        """Helper to create a temporary file with content."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write(content)
        temp_file.close()
        self.temp_files.append(temp_file)
        return temp_file.name

    def test_get_file_contents_existing_file(self):
        """Test reading contents of an existing file."""
        content = "Hello, World!"
        file_path = self.create_temp_file(content)

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        # Read the file handle
        file_content = result.read()
        self.assertEqual(file_content, content)
        result.close()

    def test_get_file_contents_multiline_file(self):
        """Test reading contents of a multiline file."""
        content = "Line 1\nLine 2\nLine 3"
        file_path = self.create_temp_file(content)

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        file_content = result.read()
        self.assertEqual(file_content, content)
        result.close()

    def test_get_file_contents_empty_file(self):
        """Test reading contents of an empty file."""
        file_path = self.create_temp_file("")

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        file_content = result.read()
        self.assertEqual(file_content, "")
        result.close()

    def test_get_file_contents_non_existing_file(self):
        """Test that non-existing file returns None."""
        result = get_file_contents("/path/to/non/existing/file.txt")
        self.assertIsNone(result)

    def test_get_file_contents_with_special_characters(self):
        """Test reading file with special characters."""
        content = "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?"
        file_path = self.create_temp_file(content)

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        file_content = result.read()
        self.assertEqual(file_content, content)
        result.close()

    def test_get_file_contents_with_unicode(self):
        """Test reading file with unicode characters."""
        content = "Unicode: 你好世界 🌍 café"
        file_path = self.create_temp_file(content)

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        file_content = result.read()
        self.assertEqual(file_content, content)
        result.close()

    def test_get_file_contents_returns_file_handle(self):
        """Test that function returns a file handle object."""
        content = "Test content"
        file_path = self.create_temp_file(content)

        result = get_file_contents(file_path)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'read'))
        self.assertTrue(hasattr(result, 'close'))
        result.close()


if __name__ == "__main__":
    unittest.main()
