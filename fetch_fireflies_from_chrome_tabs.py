#!/usr/bin/env python3

import os
import sys
import re
import pyperclip
import subprocess
import time
import logging
import traceback
import argparse
from fireflies_api import FirefliesAPI

# Setup logging
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(script_dir, "debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fireflies_script")

def get_chrome_tabs():
    """
    Get URLs from all open Chrome tabs that contain Fireflies.ai URLs.
    
    Returns:
        List of Fireflies URLs found in Chrome tabs
    """
    try:
        logger.info("Getting Chrome tabs with Fireflies URLs")
        apple_script = '''
        tell application "Google Chrome"
            set tabList to {}
            set windowList to every window
            repeat with theWindow in windowList
                set tabList to tabList & (every tab of theWindow whose URL contains "fireflies.ai/view/")
            end repeat
            set urlList to {}
            repeat with theTab in tabList
                set the end of urlList to URL of theTab
            end repeat
            return urlList
        end tell
        '''
        result = subprocess.run(['osascript', '-e', apple_script], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"AppleScript error: {result.stderr}")
            raise RuntimeError(f"Failed to access Chrome tabs: {result.stderr}")
            
        urls = result.stdout.strip().split(", ")
        filtered_urls = [url for url in urls if url]
        logger.info(f"Found {len(filtered_urls)} Chrome tabs with Fireflies URLs")
        logger.debug(f"URLs found: {filtered_urls}")
        return filtered_urls
    except Exception as e:
        logger.error(f"Error getting Chrome tabs: {e}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to get Chrome tabs: {str(e)}")

def extract_transcript_ids(urls):
    """
    Extract transcript IDs from Fireflies URLs.
    
    Args:
        urls: List of Fireflies.ai URLs
        
    Returns:
        List of transcript IDs
    """
    try:
        logger.info("Extracting transcript IDs from URLs")
        transcript_ids = []
        pattern = r"fireflies\.ai/view/.*::([A-Za-z0-9]+)"
        
        for url in urls:
            match = re.search(pattern, url)
            if match:
                transcript_ids.append(match.group(1))
                logger.debug(f"Extracted ID {match.group(1)} from {url}")
            else:
                logger.warning(f"No transcript ID found in URL: {url}")
        
        logger.info(f"Extracted {len(transcript_ids)} transcript IDs")
        return transcript_ids
    except Exception as e:
        logger.error(f"Error extracting transcript IDs: {e}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Failed to extract transcript IDs: {str(e)}")

def attempt_paste():
    """
    Try to paste the content using AppleScript.
    
    Returns:
        Boolean indicating success
    """
    try:
        logger.info("Attempting to paste content with AppleScript")
        paste_result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down'],
            capture_output=True, text=True
        )
        
        if paste_result.returncode != 0:
            logger.error(f"Error pasting content: {paste_result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Exception during paste attempt: {e}")
        return False

def fetch_transcripts_parallel(transcript_ids, api):
    """
    Fetch multiple transcripts in parallel using concurrent.futures.
    
    Args:
        transcript_ids: List of transcript IDs to fetch in the specified order
        api: Initialized FirefliesAPI instance
        
    Returns:
        Dictionary mapping transcript IDs to their transcript data
    """
    if not transcript_ids:
        return {}
    
    try:
        import concurrent.futures
        
        logger.info(f"Fetching {len(transcript_ids)} transcripts in parallel")
        start_time = time.time()
        
        transcripts_dict = {}
        
        # Use ThreadPoolExecutor to fetch transcripts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Create a dictionary mapping futures to transcript IDs
            future_to_id = {
                executor.submit(api.get_transcript_by_id, transcript_id): transcript_id
                for transcript_id in transcript_ids
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_id):
                transcript_id = future_to_id[future]
                try:
                    transcript = future.result()
                    if transcript:
                        transcripts_dict[transcript_id] = transcript
                        logger.debug(f"Successfully fetched transcript: {transcript_id}")
                    else:
                        logger.warning(f"Could not fetch transcript: {transcript_id}")
                except Exception as e:
                    logger.error(f"Error fetching transcript {transcript_id}: {e}")
        
        logger.info(f"Fetched {len(transcripts_dict)} transcripts in {time.time() - start_time:.2f}s")
        return transcripts_dict
    
    except Exception as e:
        logger.error(f"Error fetching transcripts in parallel: {e}")
        logger.error(traceback.format_exc())
        return {}

def main():
    """Main function to fetch Fireflies transcripts from Chrome tabs."""
    try:
        start_time = time.time()
        
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Fetch Fireflies transcripts from Chrome tabs')
        parser.add_argument('--paste', action='store_true', help='Attempt to automatically paste content')
        args = parser.parse_args()
        
        logger.info("Script started")
        
        # Get all Chrome tabs with Fireflies URLs
        try:
            urls = get_chrome_tabs()
            if not urls:
                logger.error("No Fireflies tabs found in Chrome.")
                print("No Fireflies tabs found in Chrome.")
                sys.exit(1)
        except RuntimeError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        
        # Extract transcript IDs
        try:
            transcript_ids = extract_transcript_ids(urls)
            if not transcript_ids:
                logger.error("No valid Fireflies transcript IDs found in Chrome tabs.")
                print("No valid Fireflies transcript IDs found in Chrome tabs.")
                sys.exit(1)
        except RuntimeError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        
        logger.info(f"Found {len(transcript_ids)} Fireflies transcripts in Chrome tabs.")
        print(f"Found {len(transcript_ids)} Fireflies transcripts in Chrome tabs.")
        
        # Initialize Fireflies API
        try:
            api = FirefliesAPI()
        except ValueError as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        
        # Fetch transcripts in parallel
        transcripts_dict = fetch_transcripts_parallel(transcript_ids, api)
        
        # Process transcripts in the original order
        all_transcripts = []
        for transcript_id in transcript_ids:
            if transcript_id in transcripts_dict:
                logger.info(f"Formatting transcript ID: {transcript_id}")
                formatted = api.format_transcript(transcripts_dict[transcript_id])
                all_transcripts.append(formatted)
            else:
                logger.warning(f"Could not fetch transcript with ID: {transcript_id}")
                print(f"Warning: Could not fetch transcript with ID: {transcript_id}")
        
        if not all_transcripts:
            logger.error("Failed to fetch any transcripts")
            print("Failed to fetch any transcripts")
            sys.exit(1)
            
        # Combine all transcripts
        final_text = "\n\n" + "\n\n".join(all_transcripts)
        logger.info(f"Combined {len(all_transcripts)} transcripts, total size: {len(final_text)} characters")
        
        # Copy to clipboard
        logger.info("Copying to clipboard")
        try:
            pyperclip.copy(final_text)
            
            # Add a small delay to ensure the clipboard is updated
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error copying to clipboard: {e}")
            print(f"Error: Failed to copy to clipboard: {str(e)}")
            sys.exit(1)
        
        # Try to paste if requested
        paste_success = False
        if args.paste:
            paste_success = attempt_paste()
            
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Script completed in {total_time:.2f} seconds, copied {len(all_transcripts)} transcripts to clipboard")
        
        if paste_success:
            print(f"Copied and pasted {len(all_transcripts)} Fireflies transcripts successfully in {total_time:.2f} seconds.")
        else:
            # If paste didn't work, it's still in the clipboard
            print(f"Copied {len(all_transcripts)} Fireflies transcripts to clipboard in {total_time:.2f} seconds. Paste manually with Cmd+V.")
            
    except Exception as e:
        logger.error(f"Unexpected error in main function: {e}")
        logger.error(traceback.format_exc())
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()