#!/usr/bin/env python3

import os
import sys
import requests
import logging
import traceback
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

    def execute_query(self, query, variables=None):
        """
        Execute a GraphQL query against the Fireflies API.
        
        Args:
            query: The GraphQL query string
            variables: Optional dictionary of variables for the query
            
        Returns:
            The JSON response data or None if the request failed
            
        Raises:
            requests.RequestException: For network-related errors
            ValueError: For API errors or invalid responses
        """
        try:
            if not variables:
                variables = {}
                
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            logger.debug(f"Executing GraphQL query with variables: {variables}")
            
            resp = requests.post(
                GRAPHQL_ENDPOINT, 
                json={"query": query, "variables": variables}, 
                headers=headers
            )
            
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
            
    def get_transcript_by_id(self, transcript_id):
        """
        Get a specific transcript by ID.
        
        Args:
            transcript_id: The ID of the transcript to fetch
            
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
            data = self.execute_query(query, variables)
            if not data:
                logger.warning(f"No data returned for transcript ID: {transcript_id}")
                return None
                
            transcript = data.get("transcript")
            if not transcript:
                logger.warning(f"Transcript not found with ID: {transcript_id}")
                return None
                
            return transcript
        except Exception as e:
            logger.error(f"Error fetching transcript {transcript_id}: {e}")
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
                
            lines = []
            lines.append(f"=== {transcript['title']} ({transcript['dateString']}) ===")
            
            # Safely handle summary
            if transcript.get("summary") is not None:
                overview = transcript["summary"].get("overview", "")
                if overview:
                    lines.append(f"Summary: {overview}\n")
            
            sentences = transcript.get("sentences", [])
            
            # Check if the transcript is still processing
            if not sentences:
                processing_message = f"Note: Meeting '{transcript.get('title', 'Unknown')}' is still processing. Transcript not available yet."
                logger.warning(processing_message)
                lines.append(processing_message)
                return "\n".join(lines)
                
            lines.append("Transcript:")
            logger.info(f"Processing {len(sentences)} sentences")
            
            for s in sentences:
                speaker = s.get("speaker_name", "Unknown")
                text = s.get("text") or s.get("raw_text") or ""
                lines.append(f"{speaker}: {text}")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error formatting transcript: {e}")
            logger.error(traceback.format_exc())
            return f"Error formatting transcript: {str(e)}"