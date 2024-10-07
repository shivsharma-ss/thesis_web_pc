# modbus_project/config.py

import configparser
import os

config = configparser.ConfigParser()

# Define the path to config.ini
config_ini_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

# Read config.ini file
config.read(config_ini_path)

# Get default values
DEFAULT_SERVER_IP_ADDRESS = config['DEFAULT']['DEFAULT_SERVER_IP_ADDRESS']
DEFAULT_SERVER_PORT = config.getint('DEFAULT', 'DEFAULT_SERVER_PORT')
DEFAULT_TOOL_IP_ADDRESS = config['DEFAULT']['DEFAULT_TOOL_IP_ADDRESS']
DEFAULT_USERNAME = config['DEFAULT']['DEFAULT_USERNAME']
DEFAULT_PASSWORD = config['DEFAULT']['DEFAULT_PASSWORD']
DEFAULT_MODULE_NAME = config['DEFAULT']['DEFAULT_MODULE_NAME']
DEFAULT_CONFIG_JSON_FILE_PATH = config['DEFAULT']['DEFAULT_CONFIG_JSON_FILE_PATH']
DEFAULT_LOG_FILE_PATH = config['DEFAULT']['DEFAULT_LOG_FILE_PATH']
DEFAULT_INPUT_BIT_ARRAY_LENGTH = config.getint('DEFAULT', 'DEFAULT_INPUT_BIT_ARRAY_LENGTH')
DEFAULT_OUTPUT_BIT_ARRAY_LENGTH = config.getint('DEFAULT', 'DEFAULT_OUTPUT_BIT_ARRAY_LENGTH')
MAX_RETRIES = config.getint('DEFAULT', 'MAX_RETRIES')

# Get current values
CURRENT_SERVER_IP_ADDRESS = config['CURRENT'].get('CURRENT_SERVER_IP_ADDRESS', DEFAULT_SERVER_IP_ADDRESS)
CURRENT_SERVER_PORT = config['CURRENT'].getint('CURRENT_SERVER_PORT', DEFAULT_SERVER_PORT)
CURRENT_TOOL_IP_ADDRESS = config['CURRENT'].get('CURRENT_TOOL_IP_ADDRESS', DEFAULT_TOOL_IP_ADDRESS)
CURRENT_TOOL_MODULE_NAME = config['CURRENT'].get('CURRENT_TOOL_MODULE_NAME', DEFAULT_MODULE_NAME)
CURRENT_INPUT_BIT_ARRAY_LENGTH = config['CURRENT'].getint('CURRENT_INPUT_BIT_ARRAY_LENGTH', DEFAULT_INPUT_BIT_ARRAY_LENGTH)
CURRENT_OUTPUT_BIT_ARRAY_LENGTH = config['CURRENT'].getint('CURRENT_OUTPUT_BIT_ARRAY_LENGTH', DEFAULT_OUTPUT_BIT_ARRAY_LENGTH)
OK_COUNTER = config['CURRENT'].getint('OK_COUNTER', 0)

def update_current_config(section, key, value):
    config.set(section, key, value)
    with open(config_ini_path, 'w') as configfile:
        config.write(configfile)

def get_current_config(section, key):
    config.read(config_ini_path)  # Re-read the config file to get the latest values
    return config.get(section, key)

# Example usage to update CURRENT_SERVER_IP_ADDRESS
# update_current_config('CURRENT', 'CURRENT_SERVER_IP_ADDRESS', '192.168.88.253')
