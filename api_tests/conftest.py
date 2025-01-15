import os
import time
import json
import logging
import subprocess
import requests
import pytest
import urllib3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def wait_for_fly_machine(app_name="deepface-workweek-dev"):
    """Check Fly.io machine status and wait if it's being replaced or starting."""
    max_retries = 10  # Increased from 5 to 10
    retry_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            # Get machine status
            logger.info(f"Checking machine status (attempt {attempt + 1}/{max_retries})")
            result = subprocess.run(['flyctl', 'machines', 'list', '-a', app_name, '--json'], 
                                 capture_output=True, text=True, check=True)
            machines = json.loads(result.stdout)
            
            if not machines:
                logger.warning(f"No machines found, waiting... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                continue
            
            # Log all machine states for debugging
            machine_states = {machine['id']: machine['state'] for machine in machines}
            logger.info(f"Current machine states: {machine_states}")
            
            # If any machine is running, we're good
            if any(machine['state'] == 'started' for machine in machines):
                logger.info("Found a running machine, ready to proceed")
                return True
            
            # If any machine is starting or replacing, wait
            if any(machine['state'] in ['starting', 'replacing'] for machine in machines):
                logger.info("Machine is starting or being replaced, waiting...")
                time.sleep(retry_delay)
                continue
            
            # If all machines are stopped, try to start one
            if all(machine['state'] == 'stopped' for machine in machines):
                logger.warning("All machines stopped, attempting to start one...")
                # Get the first stopped machine
                machine_id = machines[0]['id']
                try:
                    logger.info(f"Starting machine {machine_id}")
                    start_result = subprocess.run(
                        ['flyctl', 'machines', 'start', machine_id, '-a', app_name],
                        capture_output=True, text=True, check=True
                    )
                    logger.info(f"Start command output: {start_result.stdout}")
                    time.sleep(retry_delay)  # Wait for machine to start
                    continue
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error starting machine {machine_id}: {e}")
                    logger.error(f"Command stderr: {e.stderr}")
            
            logger.warning(f"Unexpected machine state(s), waiting...")
            time.sleep(retry_delay)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking machine status: {e}")
            logger.error(f"Command stdout: {e.stdout}")
            logger.error(f"Command stderr: {e.stderr}")
            time.sleep(retry_delay)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            time.sleep(retry_delay)
    
    logger.error("Timed out waiting for machine to be ready")
    return False

@pytest.fixture(scope="session", autouse=True)
def ensure_machine_ready(api_url):
    """Fixture to ensure Fly.io machine is ready before running tests."""
    logger.info("Ensuring Fly.io machine is ready before running tests")
    
    # Determine which app to check based on the API URL
    if 'deepface-workweek-dev.' in api_url:
        app_name = "deepface-workweek-dev"
    elif 'deepface-workweek-staging.' in api_url:
        app_name = "deepface-workweek-staging"
    else:
        app_name = "deepface-workweek"  # Production
        
    if not wait_for_fly_machine(app_name):
        logger.error("Skipping tests as Fly.io machine is not ready")
        pytest.skip("Fly.io machine not ready")
    logger.info("Fly.io machine is ready, proceeding with tests")

@pytest.fixture(scope="session")
def api_url():
    """Get the API URL from environment variable or use default."""
    url = os.getenv("API_BASE_URL", "https://deepface-workweek-dev.fly.dev")
    logger.info(f"Using API URL: {url}")
    return url

@pytest.fixture(scope="session")
def api_key(api_url):
    """Get the API key from environment variable based on the environment."""
    # Determine which environment we're testing based on subdomain
    if 'deepface-workweek-dev.' in api_url:
        env_var = "API_KEY_DEV"
    elif 'deepface-workweek-staging.' in api_url:
        env_var = "API_KEY_STAGING"
    else:
        env_var = "API_KEY"  # Production
    
    logger.info(f"Using API key from environment variable: {env_var}")
    api_key = os.getenv(env_var)
    if not api_key:
        logger.error(f"{env_var} environment variable not set")
        pytest.fail(f"{env_var} environment variable not set")
    logger.info("API key loaded successfully")
    return api_key

@pytest.fixture(scope="session")
def headers(api_key):
    """Create headers with API key."""
    headers = {"X-API-Key": api_key}
    logger.debug("Created request headers with API key")
    return headers

@pytest.fixture(scope="session")
def session():
    """Create a session that will be reused across tests."""
    session = requests.Session()
    session.verify = False  # Disable SSL verification
    logger.info("Created reusable session with SSL verification disabled")
    return session

def get_github_raw_url(path):
    """Get the raw GitHub URL for a test image."""
    url = f"https://raw.githubusercontent.com/WorkWeek-Pty-Ltd/deepface/main/tests/{path}"
    logger.debug(f"Generated GitHub raw URL: {url}")
    return url 