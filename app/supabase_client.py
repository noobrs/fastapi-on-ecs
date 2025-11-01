import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env.local
env_path = Path(__file__).parent / '.env.local'
load_dotenv(dotenv_path=env_path)

# Get Supabase credentials
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Validate credentials
if not url:
    raise ValueError("NEXT_PUBLIC_SUPABASE_URL is not set in environment variables")
if not key:
    raise ValueError("Supabase key is not set in environment variables")

# Create Supabase client
supabase: Client = create_client(url, key)
