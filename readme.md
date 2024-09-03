# Cuneiform for Valuation Risk API Download Script Documentation

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Script Configuration](#script-configuration)
5. [Running the Script](#running-the-script)
6. [Understanding the Output](#understanding-the-output)
7. [Troubleshooting](#troubleshooting)

## Overview

This Python script automates the process of downloading valuation results from the Cuneiform for Valuation Risk API. It supports downloading files for multiple asset types and snap times in a single run.

## Prerequisites

1. Python 3.6 or higher installed on your system.
2. Required Python packages:
   - requests
   - pandas
   
   Install these packages using pip:
   ```
   pip install requests pandas
   ```
3. API credentials (key and secret) for the Cuneiform for Valuation Risk platform.
4. Access to the appropriate API endpoint (production or metadata).

## Initial Setup

Before configuring the script, you need to obtain API credentials:

1. Log into your account on the Cuneiform for Valuation Risk platform at [https://metadata.cfvr.io/](https://metadata.cfvr.io/)
2. Click on _Account_ in the bottom left of the screen.
3. Click on the grey user icon in the small pop up that appears. This should lead you to a page with API Keys.
4. Click on _Create API Key_.
5. Select the `read_write` option for all relevant asset classes, choose a name for the key pair and click _Create_.
6. Copy both the _Access Key_ and the _Access Secret_. You'll need these for the script configuration.

Note: If you're using a different environment, replace the URL with the appropriate one provided by your Cuneiform administrator.

## Script Configuration

After obtaining your API credentials, configure the script by updating the following parameters in the `if __name__ == "__main__":` section at the bottom of the script:

1. `mode`: Set this to either "prod" or "metadata" depending on which environment you're accessing.
2. `api_key`: Your API key (Access Key) for the Cuneiform for Valuation Risk platform.
3. `api_secret`: Your API secret (Access Secret) for the Cuneiform for Valuation Risk platform.
4. `snap_date`: The date for which you want to download data (format: "YYYY-MM-DD").
5. `snap_times`: A list of snap times for which you want to download data (e.g., ["London 4 PM", "New York 4 PM"]).
6. `client`: The name of the client for which you're downloading data.
7. `asset_types`: A list of asset types you want to download (e.g., ["Swaptions", "Caps & Floors", "Forwards", "Options"]).

Example configuration:

```python
mode = "metadata" # Change this to "prod" or "metadata" as needed
api_url = get_api_base_url(mode)
api_key = "your_api_key_here"
api_secret = "your_api_secret_here"
snap_date = "2024-03-14"
snap_times = ["London 4 PM", "New York 4 PM"]
client = "YourClientName"
asset_types = ["Swaptions", "Caps & Floors", "Forwards", "Options"]
```

## Running the Script

1. Save the script to a file, e.g., `valuation_results_download.py`.
2. Open a terminal or command prompt.
3. Navigate to the directory containing the script.
4. Run the script using Python:
   ```
   python valuation_results_download.py
   ```

## Understanding the Output

The script will process each asset type and snap time, attempting to download the corresponding files. For each file, you'll see one of the following outputs:

- Success message: `Downloaded file for [Asset Name] - [Sub Asset]: [Filename] successfully downloaded`
- Skip message (no results): `Skipping [Asset Name] - [Sub Asset] - no valuation results found`
- Error message: `Error processing [Asset Name] - [Sub Asset]: [Error details]. Skipping.`

Downloaded files will be saved in the same directory as the script, with filenames in the format:
`[Client]_[TraceName]_[SnapDate]_[SnapTime]_[ResultType].csv`

## Troubleshooting

If you encounter issues:

1. **API Credentials**: Ensure your API key and secret are correct and have the necessary permissions.
2. **Network Issues**: Check your internet connection and any firewall settings that might block the script.
3. **Missing Data**: If files are skipped due to missing valuation results, verify that the data exists for the specified date and time.
4. **Python Environment**: Make sure you have the required Python version and packages installed.

For persistent issues, contact Cuneiform for Valuation Risk support, providing:
- The exact error message
- The script version
- The API endpoint you're using (prod or metadata)
- The asset types and snap times you're trying to download

**Remember: Always keep your API credentials secure and never share them publicly or with unauthorized individuals.**
