# NASA APOD Image Downloader

A Python script to download images from NASA's Astronomy Picture of the Day (APOD) website with configurable options.

## Description

This tool allows you to download high-quality astronomy images from NASA's popular APOD service. It supports downloading images for specific dates, date ranges, the most recent images, or even random images from the archive.

Features:

- Download images for a specific date
- Download images for a range of dates
- Download images from the last N days
- Download the latest image
- Download a random image from the archive
- Concurrent downloads for improved performance
- Save metadata along with images
- Configurable output directory and other options

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/apod-downloader.git
   cd apod-downloader
   ```

2. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

    Alternatively, you can install the dependencies directly:

    ```bash
    pip install requests tqdm python-dateutil
    ```

3. Make the script executable (optional, for Unix-based systems):

   ```bash
   chmod +x apod_downloader.py
   ```

## Usage

### Basic Usage

Download today's APOD image:

```bash
python apod_downloader.py
```

### Command Line Options

```
usage: apod_downloader.py [-h] [--date DATE | --start-date START_DATE | --latest | --random]
                         [--end-date END_DATE] [--last-days LAST_DAYS]
                         [--output-dir OUTPUT_DIR] [--no-metadata]
                         [--api-key API_KEY] [--max-workers MAX_WORKERS]
                         [--timeout TIMEOUT] [--retry-attempts RETRY_ATTEMPTS]

Download NASA Astronomy Picture of the Day (APOD) images.

options:
  -h, --help            show this help message and exit
  --date DATE           Download image for specific date (YYYY-MM-DD)
  --start-date START_DATE
                        Start date for range (YYYY-MM-DD)
  --latest              Download only the latest image
  --random              Download a random image from the archive
  --end-date END_DATE   End date for range (YYYY-MM-DD, requires --start-date)
  --last-days LAST_DAYS
                        Download images from the last N days
  --output-dir OUTPUT_DIR
                        Directory to save images (default: apod_images)
  --no-metadata         Do not save metadata JSON files
  --api-key API_KEY     NASA API key (default: DEMO_KEY)
  --max-workers MAX_WORKERS
                        Maximum number of concurrent downloads (default: 5)
  --timeout TIMEOUT     Request timeout in seconds (default: 30)
  --retry-attempts RETRY_ATTEMPTS
                        Number of retry attempts (default: 3)
```

### Examples

Download image for a specific date:

```bash
python apod_downloader.py --date 2023-04-15
```

Download images for a date range:

```bash
python apod_downloader.py --start-date 2023-01-01 --end-date 2023-01-31
```

Download images from the last 7 days:

```bash
python apod_downloader.py --last-days 7
```

Download a random image from the archive:

```bash
python apod_downloader.py --random
```

Specify a custom output directory:

```bash
python apod_downloader.py --output-dir my_apod_images
```

Download with your own NASA API key:

```bash
python apod_downloader.py --api-key YOUR_API_KEY_HERE
```

Download without saving metadata JSON files:

```bash
python apod_downloader.py --no-metadata
```

Increase the number of concurrent downloads:

```bash
python apod_downloader.py --start-date 2023-01-01 --end-date 2023-03-31 --max-workers 10
```

## Output

Images are saved in the specified output directory (default: `apod_images/`) with filenames in the format:

```
YYYY-MM-DD_Title_Of_The_Image.ext
```

For each image, a JSON metadata file with the same name but `.json` extension is also saved (unless `--no-metadata` is specified).

## NASA API Key

The script uses NASA's `DEMO_KEY` by default, which has rate limits. For better performance, [register for a free NASA API key](https://api.nasa.gov/) and use it with the `--api-key` option.

Rate limits for `DEMO_KEY`:

- Hourly limit: 30 requests per IP address per hour
- Daily limit: 50 requests per IP address per day

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.
