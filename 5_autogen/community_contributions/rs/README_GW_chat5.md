# GW_chat5 - European Health Information Gateway Chat Application

A modular Python application that provides a chat interface for the WHO European Health Information Gateway using AutoGen agents.

## Structure

The application is divided into three main modules:

### 1. GW_chat5_db.py
Database functions for searching health indicators and managing country information.

**Key Functions:**
- `search_ind_name()` - Search indicators by name with partial matching
- `search_indicators_advanced()` - Advanced search with exact/partial matching options
- `get_country_full_name()` - Get full country name from ISO3 code
- `load_countries_data()` - Load European countries data
- `load_country_groups_data()` - Load country groups data

### 2. GW_chat5_API.py
WHO API functions for data fetching, SSL handling, and visualization.

**Key Functions:**
- `create_who_ssl_context()` - Handle SSL certificate issues for WHO API
- `fetch_who_measure_data()` - Fetch data from WHO European Health Information Gateway API
- `parse_who_json_to_dataframe()` - Convert API response to pandas DataFrame
- `create_plot()` - Create and upload data visualizations to Dropbox
- `upload_and_display_image()` - Upload images and return direct URLs

### 3. GW_chat5_UI.py
Main UI application with Gradio interface and AutoGen agent integration.

**Key Functions:**
- `setup_environment()` - Load environment variables and initialize OpenAI
- `create_system_prompt()` - Create system prompt for AutoGen agent
- `create_autogen_agent()` - Configure AutoGen assistant agent
- `chat()` - Handle chat interactions
- `main()` - Launch the Gradio interface

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file:
```
OPENAI_API_KEY=your_openai_api_key
DROPBOX_ACCESS_TOKEN=your_dropbox_token
# OR use OAuth credentials:
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
DROPBOX_REFRESH_TOKEN=your_refresh_token
```

3. Ensure required data files are in `intro/` directory:
- `ind.db` - SQLite database with health indicators
- `euro_countries.json` - European countries data
- `euro_cntry_grp.json` - Country groups data
- `cntry_grp_map.csv` - Country group mapping
- `about.txt` - Gateway information

## Usage

Run the main application:
```bash
python GW_chat5_UI.py
```

The application will launch a Gradio web interface where users can:
- Ask questions about health indicators
- Request data visualizations
- Search for specific health metrics
- Compare data across countries and regions

## Features

- **SSL Bypass**: Handles WHO API certificate issues automatically
- **AutoGen Integration**: Uses AI agents for intelligent responses
- **Data Visualization**: Creates and uploads charts to Dropbox
- **Modular Design**: Clean separation of concerns
- **Error Handling**: Comprehensive error handling throughout
- **Documentation**: Well-documented functions with type hints

## Example Queries

- "Plot Life Expectancy at Birth for Denmark and the WHO European Region"
- "Show me data about maternal mortality rates"
- "Compare health indicators between EU members and WHO European Region"
- "Find indicators related to life expectancy"

## Dependencies

- pandas: Data manipulation and analysis
- matplotlib: Plotting and visualization
- requests: HTTP requests with SSL handling
- gradio: Web interface
- openai: OpenAI API integration
- autogen-agentchat: AutoGen agent framework
- dropbox: Image storage and sharing
