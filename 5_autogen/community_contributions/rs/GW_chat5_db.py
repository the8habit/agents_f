"""
GW_chat5_db.py - Database functions for European Health Information Gateway

This module contains database-related functions for searching health indicators
and managing country information for the WHO European Health Information Gateway.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any


def search_ind_name(ind_name: str) -> Optional[List[tuple]]:
    """
    Search for health indicators by name using partial matching.
    
    Args:
        ind_name (str): The indicator name to search for (supports partial matching)
    
    Returns:
        Optional[List[tuple]]: List of tuples containing (name, url, indicator_code) 
                              or None if no results found
    """
    try:
        conn = sqlite3.connect("intro/ind.db")
        c = conn.cursor()
        
        # Use wildcards for partial matching and case-insensitive search
        search_pattern = f"%{ind_name.lower()}%"
        c.execute("SELECT name, url, indicator_code FROM indicators WHERE LOWER(name) LIKE ?", 
                 (search_pattern,))
        result = c.fetchall()
        conn.close()
        
        return result if result else None
        
    except Exception as e:
        print(f"Database error in search_ind_name: {e}")
        return None


def search_indicators_advanced(search_term: str, exact_match: bool = False) -> Optional[List[tuple]]:
    """
    Advanced search for health indicators with exact or partial matching options.
    
    Args:
        search_term (str): The term to search for
        exact_match (bool): If True, performs exact match; if False, partial match
    
    Returns:
        Optional[List[tuple]]: List of tuples containing (name, url, indicator_code) 
                              or None if no results found
    """
    try:
        conn = sqlite3.connect("intro/ind.db")
        c = conn.cursor()
        
        if exact_match:
            # Exact match (case-insensitive)
            c.execute("SELECT name, url, indicator_code FROM indicators WHERE LOWER(name) = LOWER(?)", 
                     (search_term,))
        else:
            # Partial match with wildcards
            search_pattern = f"%{search_term.lower()}%"
            c.execute("SELECT name, url, indicator_code FROM indicators WHERE LOWER(name) LIKE ?", 
                     (search_pattern,))
        
        result = c.fetchall()
        conn.close()
        
        return result if result else None
        
    except Exception as e:
        print(f"Database error in search_indicators_advanced: {e}")
        return None


def load_countries_data() -> Dict[str, Any]:
    """
    Load European countries data from JSON file.
    
    Returns:
        Dict[str, Any]: Countries data as dictionary
    """
    try:
        with open("intro/euro_countries.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading countries data: {e}")
        return {}


def load_country_groups_data() -> Dict[str, Any]:
    """
    Load European country groups data from JSON file.
    
    Returns:
        Dict[str, Any]: Country groups data as dictionary
    """
    try:
        with open("intro/euro_cntry_grp.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading country groups data: {e}")
        return {}


def load_country_group_mapping() -> str:
    """
    Load country group mapping from CSV file.
    
    Returns:
        str: CSV content as string
    """
    try:
        with open("intro/cntry_grp_map.csv", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading country group mapping: {e}")
        return ""


def get_country_full_name(iso3_code: str) -> str:
    """
    Get full country name from ISO3 code using the euro_countries data.
    
    Args:
        iso3_code (str): ISO3 country code (e.g., 'ITA', 'MDA')
    
    Returns:
        str: Full country name or ISO3 code if not found
    """
    try:
        countries_data = load_countries_data()
        
        # Find the country by ISO3 code
        for country in countries_data:
            if country.get("iso3") == iso3_code or country.get("code") == iso3_code:
                return country.get("full_name", iso3_code)
        
        # If not found, return the ISO3 code
        return iso3_code
        
    except Exception as e:
        print(f"Error getting country full name: {e}")
        return iso3_code


def load_about_info() -> str:
    """
    Load about information from text file.
    
    Returns:
        str: About information content
    """
    try:
        with open("intro/about.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error loading about info: {e}")
        return ""
