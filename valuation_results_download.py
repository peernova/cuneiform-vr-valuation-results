import os
import json
import hmac
import hashlib
from typing import List, Dict, Any
from datetime import datetime
import requests
from requests.exceptions import HTTPError
import pandas as pd
import base64
import gzip
import sys

def create_token(api_key: str, api_secret: str) -> str:
    timestamp = int(datetime.now().timestamp())
    signature_data = f"{timestamp}:{api_key}"
    signature_hmac = hmac.new(api_secret.encode(), signature_data.encode(), hashlib.sha256).hexdigest()
    return f"{timestamp}.{signature_hmac}"

def get_api_base_url(mode: str) -> str:
    urls = {
        "prod": "clearconsensus.io",
        "metadata": "metadata.cfvr.io", 
    }
    return f"https://{urls.get(mode, 'clearconsensus.io')}/apigw/api/v1/"

class Asset:
    def __init__(self, name: str, sub_asset: str, service: str, asset_id: str, trace_name: str):
        self.name = name
        self.sub_asset = sub_asset
        self.service = service
        self.asset_id = asset_id
        self.trace_name = trace_name

    def dict(self):
        return {
            "name": self.name,
            "sub_asset": self.sub_asset,
            "service": self.service,
            "asset_id": self.asset_id,
            "trace_name": self.trace_name
        }

class Download:
    def __init__(self, api_url: str, api_key: str, api_secret: str, snap_date: str, snap_time: str, asset: Asset, client: str):
        self.api_url = api_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.snap_date = snap_date
        self.snap_time = snap_time
        self.asset = asset
        self.client = client
        self.current_status = None
        self.consensus_run_timestamp = None
        self.submission_timestamp = None
        self.download_link = None

    def get_headers(self):
        return {
            "x-api-key": self.api_key,
            "x-api-token": create_token(self.api_key, self.api_secret),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def initialize_download(self):
        self.current_status = self.get_current_status()
        self.consensus_run_timestamp = self.get_consensus_run_timestamp()
        self.submission_timestamp = self.get_submission_timestamp()
        self.download_link = self.generate_download_link()

    def get_current_status(self) -> pd.DataFrame:
        status_url = f"{self.api_url}file-history"
        payload = {
            "client": self.client,
            "asset_id": self.asset.asset_id,
            "file_date": self.snap_date,
            "limit": {"value": 100},
            "offset": 0,
        }
        response = requests.post(status_url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        return self.flatten_json(response.json())

    def get_consensus_run_timestamp(self) -> str:
        if self.current_status is None:
            return None
        self.current_status["Consensus Run Timestamps"] = self.current_status["Consensus Run Timestamps"].apply(lambda x: [pd.to_datetime(ts) for ts in x if ts])
        all_timestamps = [ts for sublist in self.current_status["Consensus Run Timestamps"] for ts in sublist]
        most_recent_timestamp = max(all_timestamps) if all_timestamps else None
        return most_recent_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f") if most_recent_timestamp else None

    def get_submission_timestamp(self) -> str:
        if self.current_status is None or self.consensus_run_timestamp is None:
            return None
        consensus_run_datetime = pd.to_datetime(self.consensus_run_timestamp)
        for _, row in self.current_status.iterrows():
            if consensus_run_datetime in row["Consensus Run Timestamps"]:
                return row["Uploaded Time"] if isinstance(row["Uploaded Time"], str) else row["Uploaded Time"].strftime("%Y-%m-%d %H:%M:%S.%f")
        return None

    def generate_download_link(self) -> str:
        if not all([self.asset.asset_id, self.consensus_run_timestamp, self.submission_timestamp]):
            return None
        get_download_link_url = f"{self.api_url}export"
        payload = {
            "asset_id": self.asset.asset_id,
            "consensus_run_timestamp": self.consensus_run_timestamp,
            "submission_date": self.submission_timestamp,
            "includeHeader": "True",
        }
        response = requests.post(get_download_link_url, headers=self.get_headers(), json=payload)
        response.raise_for_status()
        return response.json().get("data", {}).get("getRequestUrl")

    def download_file(self) -> str:
        if not self.download_link:
            raise ValueError("Download link not available")

        formatted_snap_date = self.snap_date.replace("-", "_")
        suffix = "valuation_results" if self.consensus_run_timestamp else "dq_results"
        filename = f"{self.client}_{self.asset.trace_name}_{formatted_snap_date}_{self.snap_time.replace(' ', '_')}_{suffix}.csv"

        response = requests.get(self.download_link)
        response.raise_for_status()
        expfile_text = response.text
        expfile_b64 = base64.b64decode(expfile_text)
        expfile = gzip.decompress(expfile_b64)

        with open(filename, "wb") as file:
            file.write(expfile)

        return f"{filename} successfully downloaded"

    @staticmethod
    def flatten_json(json_data: Dict[str, Any]) -> pd.DataFrame:
        if "assets" in json_data.get("data", {}):
            flattened_data = [
                {
                    "Asset": asset["name"],
                    "Service": service["name"],
                    "SubAsset": sub_asset["name"],
                    "ID": sub_asset["id"],
                    "TraceName": sub_asset["traceName"],
                }
                for asset in json_data["data"]["assets"]
                for service in asset["services"]
                for sub_asset in service["subAssets"]
            ]
            return pd.DataFrame(flattened_data)
        elif "columns" in json_data.get("data", {}) and "rows" in json_data.get("data", {}):
            columns = [col["columnName"] for col in json_data["data"]["columns"]]
            rows = [row["values"] for row in json_data["data"]["rows"]]
            return pd.DataFrame(rows, columns=columns)
        else:
            raise ValueError("JSON structure not recognized")

def get_asset_list(api_url: str, api_key: str, api_secret: str, snap_time: str) -> pd.DataFrame:
    asset_url = f"{api_url}assets/list"
    payload = {"snap_time": snap_time}
    headers = {
        "x-api-key": api_key,
        "x-api-token": create_token(api_key, api_secret),
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(asset_url, headers=headers, json=payload)
        response.raise_for_status()
        return Download.flatten_json(response.json())
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        print(f"Request URL: {asset_url}")
        print(f"Request headers: {json.dumps(headers, indent=2)}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        raise
    except Exception as err:
        print(f"An error occurred: {err}")
        raise

def download_all_files(api_url: str, api_key: str, api_secret: str, snap_date: str, snap_times: List[str], client: str, asset_types: List[str]):
    for snap_time in snap_times:
        print(f"Processing snap time: {snap_time}")
        asset_list = get_asset_list(api_url, api_key, api_secret, snap_time)
        
        for _, row in asset_list.iterrows():
            asset = Asset(row["Asset"], row["SubAsset"], row["Service"], row["ID"], row["TraceName"])
            if asset.sub_asset not in asset_types:
                continue
            try:
                download_instance = Download(api_url, api_key, api_secret, snap_date, snap_time, asset, client)
                download_instance.initialize_download()
                if download_instance.submission_timestamp:
                    if download_instance.download_link:
                        download_result = download_instance.download_file()
                        print(f"Downloaded file for {asset.name} - {asset.sub_asset}: {download_result}")
                    else:
                        print(f"Download link not available for {asset.name} - {asset.sub_asset}")
                else:
                    print(f"Skipping {asset.name} - {asset.sub_asset} - no valuation results found")
            except Exception as e:
                print(f"Error processing {asset.name} - {asset.sub_asset}: {str(e)}. Skipping.")

if __name__ == "__main__":
    mode = "metadata"  # Change this to "prod" or "metadata" as needed
    api_url = get_api_base_url(mode)
    api_key = "_API_KEY_"
    api_secret = "_API_SECRET_"
    snap_date = "_SNAP_DATE_" # Ex 2024-07-31
    snap_times = ["London 4 PM", "New York 4 PM"]
    client = "_CLIENT_"
    asset_types = ["Swaptions", "Caps & Floors", "Forwards", "Options"]

    if not api_key or not api_secret:
        print("Error: API key or API secret is empty. Please provide valid credentials.")
        sys.exit(1)

    try:
        download_all_files(api_url, api_key, api_secret, snap_date, snap_times, client, asset_types)
    except Exception as e:
        print(f"An error occurred during execution: {str(e)}")