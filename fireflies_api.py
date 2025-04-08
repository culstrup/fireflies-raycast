#!/usr/bin/env python3

import os
import sys
import requests
import logging
import traceback
import time
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger("fireflies_api")

# API endpoint
GRAPHQL_ENDPOINT = "https://api.fireflies.ai/graphql"

class FirefliesAPI:
    """
    A client for interacting with the Fireflies.ai GraphQL API.
    Handles authentication, API requests, and error handling.
    """

    def __init__(self, api_key=None):
        """
        Initialize the Fireflies API client.
        
        Args:
            api_key: Optional API key. If not provided, will try to load from environment.
        """
        # Load API key from parameter or environment
        self.api_key = api_key or self._load_api_key()
        if not self.api_key:
            logger.error("No API key provided or found in environment")
            raise ValueError("FIREFLIES_API_KEY not set. Please set it in .env file or provide it directly.")
            
        # Create a session with optimized connection pooling
        import urllib3
        
        # Configure connection pooling with higher max connections
        pool_manager = urllib3.PoolManager(
            num_pools=4,              # Use multiple connection pools
            maxsize=10,               # Increase max connections per pool
            timeout=urllib3.Timeout(
                connect=5.0,          # Connection timeout
                read=120.0            # Read timeout (generous for large transcripts)
            ),
            retries=urllib3.Retry(
                total=3,              # Total number of retries
                backoff_factor=0.5,   # Backoff factor between retries
                status_forcelist=[500, 502, 503, 504]  # Retry on these HTTP statuses
            )
        )
        
        # Create a session with the custom connection pool
        self.session = requests.Session()
        
        # Set custom adapter with our pool manager
        adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=10)
        self.session.mount('https://', adapter)
        
        # Update headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        })

    def _load_api_key(self):
        """Load API key from environment variables or .env file."""
        try:
            # Try to load from environment first
            api_key = os.environ.get("FIREFLIES_API_KEY")
            if api_key:
                return api_key
                
            # If not found, try loading from .env file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(script_dir, ".env")
            logger.info(f"Looking for .env file at: {env_path}")
            
            if not os.path.exists(env_path):
                logger.warning(f".env file not found at {env_path}")
                return None
                
            load_dotenv(dotenv_path=env_path)
            api_key = os.environ.get("FIREFLIES_API_KEY")
            
            if api_key:
                logger.info("API key loaded successfully from .env file")
                return api_key
            else:
                logger.warning("API key not found in .env file")
                return None
        except Exception as e:
            logger.error(f"Error loading API key: {e}")
            logger.error(traceback.format_exc())
            return None

    def execute_query(self, query, variables=None, timeout=60):
        """
        Execute a GraphQL query against the Fireflies API.
        
        Args:
            query: The GraphQL query string
            variables: Optional dictionary of variables for the query
            timeout: Timeout in seconds for the API request (default: 60)
                    Set to 60 seconds for maximum reliability - ensures we get all transcripts
            
        Returns:
            The JSON response data or None if the request failed
            
        Raises:
            requests.RequestException: For network-related errors
            ValueError: For API errors or invalid responses
        """
        try:
            if not variables:
                variables = {}
            
            logger.debug(f"Executing GraphQL query with variables: {variables}")
            
            # Use the session for connection pooling
            # Display timeout info
            print(f"FlyCast: Sending API request with {timeout}s timeout...")
            
            start_request = time.time()
            # Set both connect and read timeouts
            timeouts = (min(5, timeout/2), timeout)  # (connect_timeout, read_timeout)
            
            try:
                resp = self.session.post(
                    GRAPHQL_ENDPOINT, 
                    json={"query": query, "variables": variables},
                    timeout=timeouts
                )
                request_time = time.time() - start_request
                print(f"FlyCast: Network request completed in {request_time:.2f}s")
            except requests.exceptions.Timeout:
                logger.error(f"API request timed out after {timeout}s")
                print(f"FlyCast: API request timed out after {timeout}s")
                raise ValueError(f"API request timed out. Consider increasing the timeout value.")
            
            print(f"FlyCast: Received API response with status code {resp.status_code}")
            
            if resp.status_code != 200:
                error_message = f"API request failed with status {resp.status_code}"
                try:
                    error_detail = resp.json()
                    error_message += f": {error_detail.get('errors', [{}])[0].get('message', 'Unknown error')}"
                except:
                    error_message += f": {resp.text[:100]}"
                
                logger.error(error_message)
                raise ValueError(error_message)
            
            data = resp.json()
            
            # Check for GraphQL errors
            if "errors" in data:
                error_messages = [error.get("message", "Unknown GraphQL error") 
                                for error in data.get("errors", [])]
                error_message = "; ".join(error_messages)
                logger.error(f"GraphQL errors: {error_message}")
                raise ValueError(f"GraphQL errors: {error_message}")
                
            return data.get("data")
            
        except requests.RequestException as e:
            logger.error(f"Network error during API request: {e}")
            logger.error(traceback.format_exc())
            raise
        except ValueError:
            # Re-raise ValueError errors (from above)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}")
            logger.error(traceback.format_exc())
            raise ValueError(f"Unexpected error: {str(e)}")
    
    def get_recent_transcripts(self, limit=5, days=7):
        """
        Get a list of recent transcripts.
        
        Args:
            limit: Maximum number of transcripts to return
            days: How many days back to fetch transcripts from
            
        Returns:
            List of transcript objects or empty list if none found
        """
        query = """
        query MyTranscripts($limit: Int) {
          transcripts(limit: $limit, mine: true) {
            id
            title
            dateString
            transcript_url
            summary {
              overview
            }
            sentences {
              text
              raw_text
              speaker_name
            }
          }
        }
        """
        
        variables = {"limit": limit}
        
        try:
            data = self.execute_query(query, variables)
            if not data:
                logger.warning("No data returned from API")
                return []
                
            transcripts = data.get("transcripts", [])
            if not transcripts:
                logger.info("No transcripts found")
            else:
                logger.info(f"Found {len(transcripts)} transcripts")
                
            return transcripts
        except Exception as e:
            logger.error(f"Error fetching recent transcripts: {e}")
            raise ValueError(f"Failed to fetch recent transcripts: {str(e)}")
            
    def get_transcript_by_id(self, transcript_id, timeout=None):
        """
        Get a specific transcript by ID.
        
        Args:
            transcript_id: The ID of the transcript to fetch
            timeout: Optional override for the timeout value (in seconds)
            
        Returns:
            Transcript object or None if not found
        """
        query = """
        query GetTranscript($id: String!) {
          transcript(id: $id) {
            id
            title
            dateString
            transcript_url
            summary {
              overview
            }
            sentences {
              text
              raw_text
              speaker_name
            }
          }
        }
        """
        
        variables = {"id": transcript_id}
        
        try:
            start_time = time.time()
            print(f"FlyCast: Fetching transcript {transcript_id}...")
            data = self.execute_query(query, variables, timeout=timeout)
            if not data:
                logger.warning(f"No data returned for transcript ID: {transcript_id}")
                print(f"FlyCast: No data returned for transcript ID: {transcript_id}")
                return None
                
            transcript = data.get("transcript")
            if not transcript:
                logger.warning(f"Transcript not found with ID: {transcript_id}")
                print(f"FlyCast: Transcript not found with ID: {transcript_id}")
                return None
            
            fetch_time = time.time() - start_time
            logger.debug(f"API fetch for transcript {transcript_id} took {fetch_time:.2f}s")
            print(f"FlyCast: Fetched transcript {transcript_id} in {fetch_time:.2f}s")
            return transcript
        except Exception as e:
            logger.error(f"Error fetching transcript {transcript_id}: {e}")
            print(f"FlyCast: Error fetching transcript {transcript_id}: {e}")
            raise ValueError(f"Failed to fetch transcript {transcript_id}: {str(e)}")
            
    def format_transcript(self, transcript):
        """
        Format a transcript as human-readable text.
        
        Args:
            transcript: Transcript object from the API
            
        Returns:
            Formatted string containing the transcript
        """
        try:
            if not transcript:
                logger.warning("Attempted to format empty transcript")
                return ""
                
            # Pre-allocate approximate memory for lines
            sentences = transcript.get("sentences", [])
            sentence_count = len(sentences)
            
            # Optimize memory usage by pre-allocating
            lines = []
            lines.append(f"=== {transcript['title']} ({transcript['dateString']}) ===")
            
            # Safely handle summary
            if transcript.get("summary") is not None:
                overview = transcript["summary"].get("overview", "")
                if overview:
                    lines.append(f"Summary: {overview}\n")
            
            # Check if the transcript is still processing
            if not sentences:
                processing_message = f"Note: Meeting '{transcript.get('title', 'Unknown')}' is still processing. Transcript not available yet."
                logger.warning(processing_message)
                lines.append(processing_message)
                return "\n".join(lines)
                
            lines.append("Transcript:")
            logger.info(f"Processing {sentence_count} sentences")
            
            # Use list comprehension for better performance with larger transcripts
            lines.extend([
                f"{s.get('speaker_name', 'Unknown')}: {s.get('text') or s.get('raw_text') or ''}"
                for s in sentences
            ])
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error formatting transcript: {e}")
            logger.error(traceback.format_exc())
            return f"Error formatting transcript: {str(e)}"