import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from io import StringIO

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fireflies_api import FirefliesAPI

class TestFirefliesAPI(unittest.TestCase):
    """Test cases for the FirefliesAPI class."""
    
    @patch('fireflies_api.os.environ.get')
    def test_init_with_api_key_param(self, mock_env_get):
        """Test initialization with an API key parameter."""
        api = FirefliesAPI(api_key="test_key")
        self.assertEqual(api.api_key, "test_key")
        # Ensure we didn't try to get it from the environment
        mock_env_get.assert_not_called()
        
    @patch('fireflies_api.os.environ.get')
    def test_init_with_env_key(self, mock_env_get):
        """Test initialization with an API key from the environment."""
        mock_env_get.return_value = "env_test_key"
        api = FirefliesAPI()
        self.assertEqual(api.api_key, "env_test_key")
        
    @patch('fireflies_api.os.environ.get')
    @patch('fireflies_api.os.path.exists')
    @patch('fireflies_api.load_dotenv')
    def test_init_with_dotenv_file(self, mock_load_dotenv, mock_path_exists, mock_env_get):
        """Test initialization with an API key from a .env file."""
        # First return None (not in env), then after loading .env, return the key
        mock_env_get.side_effect = [None, "dotenv_test_key"]
        mock_path_exists.return_value = True
        
        api = FirefliesAPI()
        
        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()
        self.assertEqual(api.api_key, "dotenv_test_key")
        
    @patch('fireflies_api.os.environ.get')
    @patch('fireflies_api.os.path.exists')
    def test_init_no_key_available(self, mock_path_exists, mock_env_get):
        """Test initialization with no API key available."""
        mock_env_get.return_value = None
        mock_path_exists.return_value = False
        
        with self.assertRaises(ValueError):
            FirefliesAPI()
            
    @patch('fireflies_api.requests.post')
    def test_execute_query_success(self, mock_post):
        """Test successful execution of a GraphQL query."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"some_field": "test_value"}
        }
        mock_post.return_value = mock_response
        
        api = FirefliesAPI(api_key="test_key")
        result = api.execute_query("query { test }")
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        self.assertEqual(result, {"some_field": "test_value"})
        
    @patch('fireflies_api.requests.post')
    def test_execute_query_http_error(self, mock_post):
        """Test handling of HTTP errors in query execution."""
        # Mock error response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        mock_post.return_value = mock_response
        
        api = FirefliesAPI(api_key="test_key")
        with self.assertRaises(ValueError):
            api.execute_query("query { test }")
            
    @patch('fireflies_api.requests.post')
    def test_execute_query_graphql_error(self, mock_post):
        """Test handling of GraphQL errors in query response."""
        # Mock response with GraphQL errors
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Field does not exist"}],
            "data": None
        }
        mock_post.return_value = mock_response
        
        api = FirefliesAPI(api_key="test_key")
        with self.assertRaises(ValueError):
            api.execute_query("query { test }")
            
    @patch.object(FirefliesAPI, 'execute_query')
    def test_get_recent_transcripts(self, mock_execute_query):
        """Test fetching recent transcripts."""
        # Mock response from execute_query
        mock_execute_query.return_value = {
            "transcripts": [
                {"id": "123", "title": "Test Meeting", "dateString": "2023-01-01"}
            ]
        }
        
        api = FirefliesAPI(api_key="test_key")
        result = api.get_recent_transcripts(limit=5)
        
        # Verify query was executed with correct parameters
        mock_execute_query.assert_called_once()
        self.assertEqual(result[0]["id"], "123")
        
    @patch.object(FirefliesAPI, 'execute_query')
    def test_get_transcript_by_id(self, mock_execute_query):
        """Test fetching a transcript by ID."""
        # Mock response from execute_query
        mock_execute_query.return_value = {
            "transcript": {"id": "123", "title": "Test Meeting"}
        }
        
        api = FirefliesAPI(api_key="test_key")
        result = api.get_transcript_by_id("123")
        
        # Verify query was executed with correct parameters
        mock_execute_query.assert_called_once()
        self.assertEqual(result["id"], "123")
        
    def test_format_transcript_complete(self):
        """Test formatting a complete transcript."""
        # Sample transcript with all data
        transcript = {
            "title": "Test Meeting",
            "dateString": "2023-01-01",
            "summary": {"overview": "This is a test summary"},
            "sentences": [
                {"speaker_name": "Alice", "text": "Hello, how are you?"},
                {"speaker_name": "Bob", "text": "I'm good, thanks!"}
            ]
        }
        
        api = FirefliesAPI(api_key="test_key")
        result = api.format_transcript(transcript)
        
        # Verify formatting
        self.assertIn("=== Test Meeting (2023-01-01) ===", result)
        self.assertIn("Summary: This is a test summary", result)
        self.assertIn("Alice: Hello, how are you?", result)
        self.assertIn("Bob: I'm good, thanks!", result)
        
    def test_format_transcript_processing(self):
        """Test formatting a transcript that's still processing."""
        # Sample transcript without sentences
        transcript = {
            "title": "Processing Meeting",
            "dateString": "2023-01-01",
            "summary": {"overview": "This is a test summary"},
            "sentences": []
        }
        
        api = FirefliesAPI(api_key="test_key")
        result = api.format_transcript(transcript)
        
        # Verify formatting includes processing message
        self.assertIn("=== Processing Meeting (2023-01-01) ===", result)
        self.assertIn("still processing", result)
        self.assertNotIn("Transcript:", result)  # Shouldn't include the transcript section

if __name__ == '__main__':
    unittest.main()