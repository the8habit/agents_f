"""
GW_chat5_API.py - WHO API functions for European Health Information Gateway

This module contains functions for interacting with the WHO European Health 
Information Gateway API, including SSL handling, data fetching, and visualization.
"""

import requests
import json
import ssl
import urllib3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from io import BytesIO
import dropbox
import os
from typing import Dict, List, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from GW_chat5_db import get_country_full_name


def create_who_ssl_context():
    """
    Create a custom SSL context for WHO API connections that handles missing intermediate certificates.
    
    This is a workaround for the WHO server not sending the complete certificate chain.
    The server certificate is valid but missing intermediate certificates.
    
    Returns:
        ssl.SSLContext: Configured SSL context with relaxed verification
    """
    # Create SSL context with custom settings for WHO domain
    ssl_context = ssl.create_default_context()
    
    # Disable hostname checking and certificate verification for WHO domains
    # This is necessary because the server doesn't send complete certificate chain
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Suppress SSL warnings for this specific case
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    return ssl_context


def fetch_who_measure_data(indicator_code: str, country_groups: List[str] = None, 
                          countries: List[str] = None) -> Dict[str, Any]:
    """
    Fetch data from WHO European Health Information Gateway API for a specific measure.
    
    Args:
        indicator_code (str): The measure code (e.g., 'hfa_43')
        country_groups (List[str], optional): List of country group codes (e.g., ['WHO_EURO', 'EU_MEMBERS'])
        countries (List[str], optional): List of country ISO codes (e.g., ['ITA', 'MDA'])
    
    Returns:
        Dict[str, Any]: Parsed JSON data from the 'data' field, or empty dict if error
    """
    base_url = "https://dw.euro.who.int/api/v3/measures/"
    url = f"{base_url}{indicator_code}"
    
    # Build filter parameters
    filter_parts = []
    
    if country_groups:
        country_groups_str = ",".join(country_groups)
        filter_parts.append(f"COUNTRY_GRP:{country_groups_str}")
    
    if countries:
        countries_str = ",".join(countries)
        filter_parts.append(f"COUNTRY:{countries_str}")
    
    # Manually construct URL to avoid automatic encoding of colons
    if filter_parts:
        filter_string = ";".join(filter_parts)
        url = f"{url}?filter={filter_string}"
    
    # Create browser-like headers to avoid 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://gateway.euro.who.int/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }
    
    try:
        # Create a session to maintain cookies from the beginning
        session = requests.Session()
        
        # Create custom SSL context for WHO connections
        ssl_context = create_who_ssl_context()
        
        # Configure session to use custom SSL context
        adapter = HTTPAdapter()
        session.mount('https://', adapter)
        
        # First access the main WHO Data Warehouse site to establish session
        main_url = "https://dw.euro.who.int"
        print(f"Establishing session with {main_url}...")
        session.get(main_url, headers=headers, timeout=30, verify=False)
        
        # Then make the API request using the established session
        print(f"Making API request to {url}...")
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        json_data = response.json()
        
        # Return the 'data' field from the JSON response
        return json_data.get("data", {})
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}


def parse_who_data_structure(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse and format WHO API data structure for easier analysis.
    
    Args:
        data (Dict[str, Any]): Raw data from WHO API (json_data["data"])
    
    Returns:
        List[Dict[str, Any]]: List of formatted data records
    """
    if not data:
        return []
    
    # Handle different possible data structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # If data is a dict, look for common keys that contain the actual data
        for key in ["values", "observations", "data", "records"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        # If no list found, return the dict as a single item
        return [data]
    
    return []


def parse_who_json_to_dataframe(json_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Parse WHO API JSON response and extract data into a pandas DataFrame.
    
    Args:
        json_data (Dict[str, Any]): Raw JSON response from WHO API (can be dict or list)
    
    Returns:
        pd.DataFrame: DataFrame with extracted data
    """
    if not json_data:
        return pd.DataFrame()
    
    # Handle both dict and list inputs
    if isinstance(json_data, list):
        # If json_data is already a list, use it directly
        data_records = json_data
    elif isinstance(json_data, dict):
        # If json_data is a dict, extract the data array
        data_records = json_data.get("data", [])
    else:
        return pd.DataFrame()
    
    if not data_records:
        return pd.DataFrame()
    
    # List to store flattened records
    flattened_records = []
    
    for record in data_records:
        if not isinstance(record, dict):
            continue
            
        # Extract dimensions (metadata about the record)
        dimensions = record.get("dimensions", {})
        
        # Extract value information
        value_info = record.get("value", {})
        
        # Create a flattened record
        flattened_record = {
            # Extract dimension fields
            "COUNTRY": dimensions.get("COUNTRY", ""),
            "COUNTRY_GRP": dimensions.get("COUNTRY_GRP", ""),
            "SEX": dimensions.get("SEX", ""),
            "YEAR": dimensions.get("YEAR", ""),
            
            # Extract value fields
            "VALUE_DISPLAY": value_info.get("display", ""),
            "VALUE_NUMERIC": value_info.get("numeric", None),
            
            # Keep original record for reference
            "RAW_RECORD": record
        }
        
        # Add any other dimension fields that might exist
        for key, value in dimensions.items():
            if key not in ["COUNTRY", "COUNTRY_GRP", "SEX", "YEAR"]:
                flattened_record[f"DIM_{key}"] = value
        
        flattened_records.append(flattened_record)
    
    # Create DataFrame
    df = pd.DataFrame(flattened_records)
    
    # Convert numeric columns to appropriate types
    if not df.empty:
        # Convert YEAR to integer if possible
        df["YEAR"] = pd.to_numeric(df["YEAR"], errors='coerce').astype('Int64')
        
        # Convert VALUE_NUMERIC to float
        df["VALUE_NUMERIC"] = pd.to_numeric(df["VALUE_NUMERIC"], errors='coerce')
        
        # Sort by COUNTRY and YEAR for better organization
        df = df.sort_values(["COUNTRY", "YEAR"], na_position='last')
    
    return df


def upload_image_to_dropbox(image_data: bytes, filename: str) -> str:
    """
    Upload image to Dropbox and return shareable link.
    
    Args:
        image_data (bytes): Image data as bytes
        filename (str): Filename for the uploaded image
    
    Returns:
        str: Shareable link URL or error message
    """
    try:
        # Try OAuth with refresh token first (recommended)
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
        
        if app_key and app_secret and refresh_token:
            # Use OAuth with refresh token (automatically refreshes when expired)
            dbx = dropbox.Dropbox(
                app_key=app_key,
                app_secret=app_secret,
                oauth2_refresh_token=refresh_token
            )
        else:
            # Fallback to simple access token (will expire after 4 hours)
            access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
            if not access_token:
                return "Error: DROPBOX_ACCESS_TOKEN or OAuth credentials not found in environment variables"
            dbx = dropbox.Dropbox(access_token)
        
        # Upload file to Dropbox app folder
        dbx.files_upload(image_data, f'/{filename}')
        
        # Create shareable link
        shared_link = dbx.sharing_create_shared_link_with_settings(f'/{filename}')
        
        # Return the URL
        return shared_link.url
        
    except dropbox.exceptions.AuthError as e:
        return f"Dropbox authentication error: {str(e)}"
    except dropbox.exceptions.ApiError as e:
        return f"Dropbox API error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def get_direct_image_url_from_dropbox(file_path: str) -> str:
    """
    Get direct image URL from Dropbox using temporary link.
    
    Args:
        file_path (str): Path to the file in Dropbox
    
    Returns:
        str: Direct URL or error message
    """
    try:
        # Try OAuth with refresh token first (recommended)
        app_key = os.getenv('DROPBOX_APP_KEY')
        app_secret = os.getenv('DROPBOX_APP_SECRET')
        refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
        
        if app_key and app_secret and refresh_token:
            dbx = dropbox.Dropbox(
                app_key=app_key,
                app_secret=app_secret,
                oauth2_refresh_token=refresh_token
            )
        else:
            access_token = os.getenv('DROPBOX_ACCESS_TOKEN')
            if not access_token:
                return "Error: DROPBOX_ACCESS_TOKEN or OAuth credentials not found"
            dbx = dropbox.Dropbox(access_token)
            
        # Get temporary direct link (valid for 4 hours)
        result = dbx.files_get_temporary_link(file_path)
        if result and hasattr(result, 'link'):
            return result.link
        else:
            return "Error: Could not get temporary link"
        
    except Exception as e:
        return f"Error getting direct URL: {str(e)}"


def upload_and_display_image(image_data: bytes, filename: str) -> str:
    """
    Complete workflow: upload to Dropbox and return direct image URL.
    
    Args:
        image_data (bytes): Image data as bytes
        filename (str): Filename for the uploaded image
    
    Returns:
        str: Direct URL for display
    """
    # Upload to Dropbox
    dropbox_url = upload_image_to_dropbox(image_data, filename)
    
    if dropbox_url.startswith("Error:"):
        return dropbox_url
    
    # Get direct temporary link for better chat display
    file_path = f"/{filename}"
    direct_url = get_direct_image_url_from_dropbox(file_path)
    
    if direct_url.startswith("Error:"):
        # Fallback to URL conversion method
        import re
        if "dropbox.com/scl/fi/" in dropbox_url:
            match = re.search(r'/scl/fi/([^/]+)/', dropbox_url)
            if match:
                file_id = match.group(1)
                direct_url = f"https://dl.dropboxusercontent.com/scl/fi/{file_id}/"
        elif "dropbox.com/s/" in dropbox_url:
            direct_url = dropbox_url.replace("www.dropbox.com/s/", "dl.dropboxusercontent.com/s/")
            direct_url = direct_url.split("?")[0]
        else:
            direct_url = dropbox_url
    
    # Return direct URL for chat display
    return direct_url


def create_plot(indicator_code: str, indicator_name: str, countries: List[str] = None, 
                country_groups: List[str] = None) -> str:
    """
    Create a plot from WHO API data and upload to Dropbox.
    
    Args:
        indicator_code (str): The measure code (e.g., 'hfa_43')
        indicator_name (str): Display name for the indicator (e.g., 'Life Expectancy at Birth')
        countries (List[str], optional): List of country ISO3 codes (e.g., ['ITA', 'MDA', 'DNK'])
        country_groups (List[str], optional): List of country group codes (e.g., ['WHO_EURO', 'EU_MEMBERS'])
    
    Returns:
        str: Direct URL to the uploaded plot image or error message
    """
    try:
        # Get raw JSON data
        print(f"Fetching data for {indicator_name}...")
        raw_data = fetch_who_measure_data(indicator_code, country_groups, countries)
        
        if not raw_data:
            return "Error: No data received from WHO API"
        
        # Parse to DataFrame
        print("Parsing data to DataFrame...")
        df = parse_who_json_to_dataframe(raw_data)
        
        if df.empty:
            return "Error: No data available for the specified parameters"
        
        # Create the plot
        print("Creating plot...")
        plt.figure(figsize=(12, 7))
        
        # Define colors for different lines
        colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#7209B7', '#048A81', '#F77F00', '#8B5A2B', '#2D5016', '#6A0572']
        
        plot_entities = []
        entity_labels = []
        
        # Handle countries
        if countries and 'COUNTRY' in df.columns:
            country_data = df[df['COUNTRY'].isin(countries)]
            for country in countries:
                if country in country_data['COUNTRY'].values:
                    plot_entities.append(('COUNTRY', country))
                    country_name = get_country_full_name(country)
                    entity_labels.append(country_name)
        
        # Handle country groups
        if country_groups and 'COUNTRY_GRP' in df.columns:
            group_data = df[df['COUNTRY_GRP'].isin(country_groups)]
            for group in country_groups:
                if group in group_data['COUNTRY_GRP'].values:
                    plot_entities.append(('COUNTRY_GRP', group))
                    entity_labels.append(f"{group} (Group)")
        
        # If no specific entities requested, plot all available
        if not plot_entities:
            if 'COUNTRY' in df.columns:
                unique_countries = df['COUNTRY'].unique()
                for country in unique_countries:
                    if country:  # Skip empty
                        plot_entities.append(('COUNTRY', country))
                        country_name = get_country_full_name(country)
                        entity_labels.append(country_name)
        
        # Plot lines for each entity
        for i, (entity_type, entity_value) in enumerate(plot_entities):
            if entity_type == 'COUNTRY':
                entity_data = df[df['COUNTRY'] == entity_value].copy()
            else:  # COUNTRY_GRP
                entity_data = df[df['COUNTRY_GRP'] == entity_value].copy()
            
            entity_data = entity_data.sort_values('YEAR')
            
            if not entity_data.empty and 'VALUE_NUMERIC' in entity_data.columns:
                color = colors[i % len(colors)]
                label = entity_labels[i] if i < len(entity_labels) else entity_value
                
                plt.plot(entity_data['YEAR'], entity_data['VALUE_NUMERIC'], 
                        marker='o', linewidth=2, markersize=4, 
                        color=color, label=label)
                
                # Add value labels on data points (every few points to avoid clutter)
                for idx, row in entity_data.iterrows():
                    if idx % 3 == 0:  # Show every 3rd point
                        plt.annotate(f'{row["VALUE_NUMERIC"]:.1f}', 
                                   (row['YEAR'], row['VALUE_NUMERIC']), 
                                   textcoords="offset points", 
                                   xytext=(0,8), ha='center', fontsize=8)
        
        # Customize the plot
        title_parts = []
        if countries:
            title_parts.append(f"Countries: {', '.join(countries)}")
        if country_groups:
            title_parts.append(f"Groups: {', '.join(country_groups)}")
        
        if title_parts:
            title = f'{indicator_name}\n({", ".join(title_parts)})'
        else:
            title = f'{indicator_name} by Country/Group'
            
        plt.title(title, fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Year', fontsize=11)
        plt.ylabel(indicator_name, fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Set x-axis to show years properly
        if 'YEAR' in df.columns:
            years = sorted(df['YEAR'].dropna().unique())
            if len(years) > 10:
                # Show every nth year if too many
                step = max(1, len(years) // 10)
                plt.xticks(years[::step])
            else:
                plt.xticks(years)
        
        plt.tight_layout()
        
        # Save to BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_data = buffer.getvalue()
        plt.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_indicator = indicator_code.replace('/', '_').replace(' ', '_')
        filename = f"{safe_indicator}_{timestamp}.png"
        
        # Upload to Dropbox and get direct URL
        print("Uploading to Dropbox...")
        direct_url = upload_and_display_image(image_data, filename)
        
        if direct_url.startswith("Error:"):
            return direct_url
        
        print(f"Plot created and uploaded successfully!")
        return direct_url
        
    except Exception as e:
        return f"Error creating plot: {str(e)}"
