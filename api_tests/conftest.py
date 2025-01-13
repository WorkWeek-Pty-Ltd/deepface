import os
import time
import json
import subprocess
import requests
import pytest
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def wait_for_fly_machine():
    """Check Fly.io machine status and wait if it's being replaced."""
    max_retries = 5
    retry_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(['fly', 'status', '-a', 'deepface-workweek-dev', '--json'], 
                                 capture_output=True, text=True, check=True)
            status = json.loads(result.stdout)
            
            # Check if any machine is in 'replacing' state
            machines = status.get('Machines', [])
            if not machines:
                print("No machines found, waiting...")
                time.sleep(retry_delay)
                continue
                
            replacing = any(machine.get('state') == 'replacing' for machine in machines)
            if not replacing:
                print("Machine is ready")
                return True
                
            print("Machine is being replaced, waiting...")
            time.sleep(retry_delay)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error checking machine status: {e}")
            time.sleep(retry_delay)
    
    print("Timed out waiting for machine to be ready")
    return False

@pytest.fixture(scope="session", autouse=True)
def ensure_machine_ready():
    """Fixture to ensure Fly.io machine is ready before running tests."""
    if not wait_for_fly_machine():
        pytest.skip("Fly.io machine not ready")

@pytest.fixture(scope="session")
def api_url():
    """Get the API URL from environment variable or use default."""
    return os.getenv("API_BASE_URL", "https://deepface-workweek-dev.fly.dev")

@pytest.fixture(scope="session")
def api_key():
    """Get the API key from environment variable."""
    api_key = os.getenv("API_KEY_DEV")
    if not api_key:
        pytest.fail("API_KEY_DEV environment variable not set")
    return api_key

@pytest.fixture(scope="session")
def headers(api_key):
    """Create headers with API key."""
    return {"X-API-Key": api_key}

@pytest.fixture(scope="session")
def session():
    """Create a session that will be reused across tests."""
    session = requests.Session()
    session.verify = False  # Disable SSL verification
    return session

def get_github_raw_url(path):
    """Get the raw GitHub URL for a test image."""
    return f"https://raw.githubusercontent.com/WorkWeek-Pty-Ltd/deepface/main/tests/{path}" 