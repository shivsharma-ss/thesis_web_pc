import argparse
import json
import os
import sys
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

logger = logging.getLogger('webjsondatagetter_log')

def setup_django():
    import django
    from django.conf import settings

    # Add the parent directory to the PYTHONPATH
    project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_path not in sys.path:
        sys.path.append(project_path)
    
    logger.info(f"Parent path added to sys.path: {project_path}")

    # Explicitly set the current working directory to the parent directory
    os.chdir(project_path)
    logger.info(f"Current working directory set to parent path: {project_path}")

    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modbus_project.settings')
    django.setup()
    logger.info("Django setup completed")

try:
    from modbus_project.config import (
        DEFAULT_TOOL_IP_ADDRESS, DEFAULT_USERNAME, DEFAULT_PASSWORD, 
        DEFAULT_MODULE_NAME, DEFAULT_CONFIG_JSON_FILE_PATH, 
        DEFAULT_LOG_FILE_PATH, MAX_RETRIES
    )
except ImportError:
    logger.warning("Django settings not found. Setting up Django.")
    setup_django()
    from modbus_project.config import (
        DEFAULT_TOOL_IP_ADDRESS, DEFAULT_USERNAME, DEFAULT_PASSWORD, 
        DEFAULT_MODULE_NAME, DEFAULT_CONFIG_JSON_FILE_PATH, 
        DEFAULT_LOG_FILE_PATH, MAX_RETRIES
    )

class CustomError(Exception):
    pass

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=chrome_options)
    return driver

def login(driver, url, username, password):
    logger.info('Logging in to %s', url)
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'txtUsername')))
    
    username_field = driver.find_element(By.ID, 'txtUsername')
    password_field = driver.find_element(By.ID, 'txtPassword')
    login_button = driver.find_element(By.ID, 'btnLogin')

    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button.click()
    
    time.sleep(5)
    logger.info('Logged in successfully')

def fetch_json_data(driver, url):
    logger.info('Fetching JSON data from %s', url)
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))
    json_content = driver.find_element(By.TAG_NAME, 'pre').text
    return json_content

def filter_json_content(json_content, module_name):
    logger.info('Filtering JSON data for module %s', module_name)
    data = json.loads(json_content)
    filtered_data = [entry for entry in data if entry.get('module') == module_name]
    return json.dumps(filtered_data, indent=4)

def save_json_to_file(json_content, file_path):
    logger.info('Saving JSON data to %s', file_path)
    with open(file_path, 'w') as file:
        file.write(json_content)
    logger.info('JSON data saved to %s', file_path)

def save_ip_address(ip_address, log_file_path):
    logger.info('Logging IP address %s to %s', ip_address, log_file_path)
    with open(log_file_path, 'a') as log_file:
        log_file.write(f"{datetime.now()}: {ip_address}\n")
    logger.info('IP address %s logged to %s with timestamp', ip_address, log_file_path)

def main(ip_address, username, password, module_name, file_path, log_file_path):
    driver = setup_driver()
    retries = 0
    while retries < MAX_RETRIES:
        try:
            login_url = f'https://{ip_address}/login'
            json_url = f'https://{ip_address}/BS350/BMS/modules'
            login(driver, login_url, username, password)
            json_content = fetch_json_data(driver, json_url)
            filtered_content = filter_json_content(json_content, module_name)
            save_json_to_file(filtered_content, file_path)
            save_ip_address(ip_address, log_file_path)
            break
        except CustomError as e:
            logger.error('CustomError occurred: %s', e)
            retries += 1
            logger.info('Retrying... (%d/%d)', retries, MAX_RETRIES)
            time.sleep(5)  # Wait for a while before retrying
        except Exception as e:
            logger.error('An error occurred: %s', e)
            retries += 1
            logger.info('Retrying... (%d/%d)', retries, MAX_RETRIES)
            time.sleep(5)  # Wait for a while before retrying
        finally:
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch and filter JSON data from a website.')
    parser.add_argument('--ip_address', type=str, default=DEFAULT_TOOL_IP_ADDRESS, help='The IP address of the target website')
    parser.add_argument('--username', type=str, default=DEFAULT_USERNAME, help='The username for login')
    parser.add_argument('--password', type=str, default=DEFAULT_PASSWORD, help='The password for login')
    parser.add_argument('--module_name', type=str, default=DEFAULT_MODULE_NAME, help='The module name to filter the JSON data')
    parser.add_argument('--file_path', type=str, default=DEFAULT_CONFIG_JSON_FILE_PATH, help='The path where the JSON data should be saved')
    parser.add_argument('--log_file_path', type=str, default=DEFAULT_LOG_FILE_PATH, help='The path where the IP address should be logged')

    args = parser.parse_args()
    main(args.ip_address, args.username, args.password, args.module_name, args.file_path, args.log_file_path)
