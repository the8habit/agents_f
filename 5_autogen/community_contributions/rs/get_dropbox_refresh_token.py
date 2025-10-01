#!/usr/bin/env python3
"""
Script to generate a Dropbox refresh token for long-term authentication.
Run this script once to get a refresh token that never expires.
"""

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

def get_refresh_token():
    """Generate a Dropbox refresh token using OAuth2 flow"""
    
    print("=" * 70)
    print("DROPBOX REFRESH TOKEN GENERATOR")
    print("=" * 70)
    print("\nThis script will help you generate a refresh token for Dropbox.")
    
    # Load environment variables from .env file
    load_dotenv(override=True)
    
    # Try to get app credentials from .env
    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_SECRET')
    
    if app_key and app_secret:
        print(f"\n✅ Found credentials in .env file:")
        print(f"   App Key: {app_key[:10]}...")
        print(f"   App Secret: {app_secret[:10]}...")
    else:
        print("\n⚠️  Could not find DROPBOX_APP_KEY or DROPBOX_APP_SECRET in .env")
        print("\nTo get these:")
        print("1. Go to: https://www.dropbox.com/developers/apps")
        print("2. Select your app (or create a new one)")
        print("3. Go to the 'Settings' tab")
        print("4. Find 'App key' and 'App secret' at the top\n")
        print("=" * 70)
        
        # Get app credentials from user
        app_key = input("\nEnter your Dropbox App Key: ").strip()
        app_secret = input("Enter your Dropbox App Secret: ").strip()
    
    if not app_key or not app_secret:
        print("\n❌ Error: App Key and App Secret are required!")
        return
    
    try:
        # Initialize OAuth flow with offline access (refresh token)
        auth_flow = DropboxOAuth2FlowNoRedirect(
            app_key, 
            app_secret, 
            token_access_type='offline'  # This is key for getting refresh token
        )
        
        # Get the authorization URL
        authorize_url = auth_flow.start()
        
        print("\n" + "=" * 70)
        print("STEP 1: AUTHORIZE THE APP")
        print("=" * 70)
        print(f"\n1. Open this URL in your browser:\n\n   {authorize_url}\n")
        print("2. Click 'Allow' (you might need to log in first)")
        print("3. You'll see an authorization code")
        print("4. Copy that code and paste it below")
        print("\n" + "=" * 70)
        
        # Get authorization code from user
        auth_code = input("\nEnter the authorization code here: ").strip()
        
        if not auth_code:
            print("\n❌ Error: Authorization code is required!")
            return
        
        # Complete the OAuth flow and get tokens
        oauth_result = auth_flow.finish(auth_code)
        
        print("\n" + "=" * 70)
        print("✅ SUCCESS! YOUR CREDENTIALS")
        print("=" * 70)
        print("\nAdd these to your .env file:\n")
        print(f"DROPBOX_APP_KEY={app_key}")
        print(f"DROPBOX_APP_SECRET={app_secret}")
        print(f"DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}")
        print("\n" + "=" * 70)
        print("\nThese credentials will work indefinitely and auto-refresh!")
        print("You can now delete the old DROPBOX_ACCESS_TOKEN from your .env")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you:")
        print("  - Entered the correct App Key and App Secret")
        print("  - Copied the authorization code correctly")
        print("  - Have dropbox package installed: pip install dropbox")

if __name__ == "__main__":
    get_refresh_token()

