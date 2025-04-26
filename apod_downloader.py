#!/usr/bin/env python3
"""
NASA APOD Image Downloader

This script downloads images from NASA's Astronomy Picture of the Day (APOD) website,
with configurable options for date ranges, output directory, and more.

Usage:
    python apod_downloader.py [options]

Requirements:
    - requests
    - tqdm
    - python-dateutil
"""

import os
import sys
import json
import argparse
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
from dateutil import parser as date_parser
from tqdm import tqdm

class APODDownloader:
    """Downloads images from NASA's Astronomy Picture of the Day (APOD) website."""
    
    BASE_URL = "https://api.nasa.gov/planetary/apod"
    
    def __init__(self, api_key="DEMO_KEY", output_dir="apod_images", 
                 max_workers=5, timeout=30, retry_attempts=3):
        """
        Initialize the APOD Downloader.
        
        Args:
            api_key (str): NASA API key. Use "DEMO_KEY" for limited access.
            output_dir (str): Directory to save images.
            max_workers (int): Maximum number of concurrent downloads.
            timeout (int): Timeout for requests in seconds.
            retry_attempts (int): Number of retry attempts for failed requests.
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_apod_data(self, date=None, start_date=None, end_date=None):
        """
        Get APOD data for a specific date or date range.
        
        Args:
            date (str, optional): Single date in YYYY-MM-DD format.
            start_date (str, optional): Start date in YYYY-MM-DD format for a range.
            end_date (str, optional): End date in YYYY-MM-DD format for a range.
            
        Returns:
            dict or list: APOD data for the requested date(s).
        """
        params = {'api_key': self.api_key}
        
        if date:
            params['date'] = date
        elif start_date and end_date:
            params['start_date'] = start_date
            params['end_date'] = end_date
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(
                    self.BASE_URL, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    print(f"Failed to fetch APOD data after {self.retry_attempts} attempts: {e}")
                    return None
                print(f"Attempt {attempt+1} failed, retrying...")
    
    def download_image(self, url, filename):
        """
        Download an image from a URL and save it to a file.
        
        Args:
            url (str): URL of the image to download.
            filename (Path): Path to save the image.
            
        Returns:
            bool: True if download was successful, False otherwise.
        """
        if filename.exists():
            print(f"File already exists: {filename}")
            return True
            
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.get(url, stream=True, timeout=self.timeout)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filename, 'wb') as f, tqdm(
                    desc=filename.name,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress_bar:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))
                return True
            except requests.exceptions.RequestException as e:
                if attempt == self.retry_attempts - 1:
                    print(f"Failed to download {url} after {self.retry_attempts} attempts: {e}")
                    return False
                print(f"Attempt {attempt+1} failed, retrying...")
    
    def get_date_range(self, start_date, end_date):
        """
        Generate a list of dates between start_date and end_date.
        
        Args:
            start_date (datetime): Start date.
            end_date (datetime): End date.
            
        Returns:
            list: List of date strings in YYYY-MM-DD format.
        """
        date_list = []
        delta = end_date - start_date
        
        for i in range(delta.days + 1):
            date = start_date + timedelta(days=i)
            date_list.append(date.strftime("%Y-%m-%d"))
        
        return date_list
    
    def process_apod_entry(self, entry):
        """
        Process a single APOD entry and download its image.
        
        Args:
            entry (dict): APOD data entry.
            
        Returns:
            dict: Result of the download operation.
        """
        result = {
            'date': entry.get('date'),
            'title': entry.get('title'),
            'success': False
        }
        
        # Skip videos
        if entry.get('media_type') != 'image':
            result['reason'] = f"Skipped media type: {entry.get('media_type')}"
            return result
        
        # Get the image URL
        image_url = entry.get('hdurl') or entry.get('url')
        if not image_url:
            result['reason'] = "No image URL found"
            return result
        
        # Parse the URL to get the file extension
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        _, ext = os.path.splitext(path)
        
        if not ext:
            ext = '.jpg'  # Default extension
        
        # Create a filename with date and title
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in entry.get('title', ''))
        safe_title = safe_title.replace(' ', '_')
        filename = self.output_dir / f"{entry.get('date')}_{safe_title}{ext}"
        
        # Download the image
        success = self.download_image(image_url, filename)
        result['success'] = success
        
        if success:
            result['filename'] = str(filename)
        else:
            result['reason'] = "Download failed"
        
        return result
    
    def download_date_range(self, start_date, end_date, save_metadata=True):
        """
        Download APOD images for a date range.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.
            save_metadata (bool): Whether to save metadata as JSON files.
            
        Returns:
            list: Results of download operations.
        """
        start_date_obj = date_parser.parse(start_date).date()
        end_date_obj = date_parser.parse(end_date).date()
        
        # Check if the date range is too large
        delta = end_date_obj - start_date_obj
        if delta.days > 100:
            # Split the date range into chunks of 100 days
            results = []
            current_start = start_date_obj
            while current_start <= end_date_obj:
                current_end = min(current_start + timedelta(days=99), end_date_obj)
                chunk_results = self._download_date_chunk(
                    current_start.strftime("%Y-%m-%d"),
                    current_end.strftime("%Y-%m-%d"),
                    save_metadata
                )
                results.extend(chunk_results)
                current_start = current_end + timedelta(days=1)
            return results
        else:
            return self._download_date_chunk(start_date, end_date, save_metadata)
    
    def _download_date_chunk(self, start_date, end_date, save_metadata):
        """
        Download APOD images for a chunk of dates (up to 100 days).
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.
            save_metadata (bool): Whether to save metadata as JSON files.
            
        Returns:
            list: Results of download operations.
        """
        print(f"Fetching APOD data from {start_date} to {end_date}...")
        data = self.get_apod_data(start_date=start_date, end_date=end_date)
        
        if not data:
            print("No data returned from API")
            return []
        
        # Ensure data is a list
        if isinstance(data, dict):
            data = [data]
        
        print(f"Found {len(data)} APOD entries. Starting downloads...")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_entry = {executor.submit(self.process_apod_entry, entry): entry for entry in data}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_entry), total=len(data), desc="Downloading"):
                entry = future_to_entry[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Save metadata if requested
                    if save_metadata and result.get('success'):
                        metadata_file = Path(result.get('filename')).with_suffix('.json')
                        with open(metadata_file, 'w') as f:
                            json.dump(entry, f, indent=2)
                    
                except Exception as e:
                    print(f"Error processing {entry.get('date')}: {e}")
                    results.append({
                        'date': entry.get('date'),
                        'title': entry.get('title'),
                        'success': False,
                        'reason': str(e)
                    })
        
        return results
    
    def download_single_date(self, date, save_metadata=True):
        """
        Download APOD image for a single date.
        
        Args:
            date (str): Date in YYYY-MM-DD format.
            save_metadata (bool): Whether to save metadata as JSON files.
            
        Returns:
            dict: Result of the download operation.
        """
        print(f"Fetching APOD data for {date}...")
        data = self.get_apod_data(date=date)
        
        if not data:
            print("No data returned from API")
            return {'date': date, 'success': False, 'reason': "No data returned from API"}
        
        print(f"Found APOD entry for {date}. Starting download...")
        
        result = self.process_apod_entry(data)
        
        # Save metadata if requested
        if save_metadata and result.get('success'):
            metadata_file = Path(result.get('filename')).with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        return result
    
    def download_latest(self, save_metadata=True):
        """
        Download the latest APOD image.
        
        Args:
            save_metadata (bool): Whether to save metadata as JSON files.
            
        Returns:
            dict: Result of the download operation.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return self.download_single_date(today, save_metadata)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Download NASA Astronomy Picture of the Day (APOD) images.')
    
    # Date selection options
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument('--date', help='Download image for specific date (YYYY-MM-DD)')
    date_group.add_argument('--start-date', help='Start date for range (YYYY-MM-DD)')
    date_group.add_argument('--latest', action='store_true', help='Download only the latest image')
    date_group.add_argument('--random', action='store_true', help='Download a random image from the archive')
    
    parser.add_argument('--end-date', help='End date for range (YYYY-MM-DD, requires --start-date)')
    parser.add_argument('--last-days', type=int, help='Download images from the last N days')
    
    # Output options
    parser.add_argument('--output-dir', default='apod_images', help='Directory to save images (default: apod_images)')
    parser.add_argument('--no-metadata', action='store_true', help='Do not save metadata JSON files')
    
    # API options
    parser.add_argument('--api-key', default='DEMO_KEY', help='NASA API key (default: DEMO_KEY)')
    
    # Performance options  
    parser.add_argument('--max-workers', type=int, default=5, help='Maximum number of concurrent downloads (default: 5)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--retry-attempts', type=int, default=3, help='Number of retry attempts (default: 3)')
    
    return parser.parse_args()

def main():
    """Main function to run the APOD downloader."""
    args = parse_arguments()
    
    downloader = APODDownloader(
        api_key=args.api_key,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        timeout=args.timeout,
        retry_attempts=args.retry_attempts
    )
    
    save_metadata = not args.no_metadata
    
    # Handle different download modes
    if args.date:
        result = downloader.download_single_date(args.date, save_metadata)
        if result['success']:
            print(f"Successfully downloaded image for {args.date} to {result['filename']}")
        else:
            print(f"Failed to download image for {args.date}: {result.get('reason')}")
    
    elif args.start_date:
        if not args.end_date:
            print("Error: --end-date is required when using --start-date")
            sys.exit(1)
        
        results = downloader.download_date_range(args.start_date, args.end_date, save_metadata)
        
        successful = sum(1 for r in results if r['success'])
        print(f"\nDownload complete. Successfully downloaded {successful} of {len(results)} images.")
    
    elif args.last_days:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=args.last_days - 1)
        
        results = downloader.download_date_range(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            save_metadata
        )
        
        successful = sum(1 for r in results if r['success'])
        print(f"\nDownload complete. Successfully downloaded {successful} of {len(results)} images.")
    
    elif args.latest:
        result = downloader.download_latest(save_metadata)
        if result['success']:
            print(f"Successfully downloaded latest image to {result['filename']}")
        else:
            print(f"Failed to download latest image: {result.get('reason')}")
    
    elif args.random:
        # Get a random date between the first APOD (June 16, 1995) and today
        first_apod = datetime(1995, 6, 16).date()
        today = datetime.now().date()
        days_since_first = (today - first_apod).days
        
        import random
        random_days = random.randint(0, days_since_first)
        random_date = (first_apod + timedelta(days=random_days)).strftime("%Y-%m-%d")
        
        print(f"Selected random date: {random_date}")
        result = downloader.download_single_date(random_date, save_metadata)
        
        if result['success']:
            print(f"Successfully downloaded random image from {random_date} to {result['filename']}")
        else:
            print(f"Failed to download random image from {random_date}: {result.get('reason')}")
    
    else:
        # Default behavior: download today's image
        result = downloader.download_latest(save_metadata)
        if result['success']:
            print(f"Successfully downloaded latest image to {result['filename']}")
        else:
            print(f"Failed to download latest image: {result.get('reason')}")

if __name__ == "__main__":
    main()