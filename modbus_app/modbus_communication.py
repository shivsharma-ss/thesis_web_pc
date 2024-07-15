# modbus_communication.py

from pyModbusTCP.server import DataBank, ModbusServer
from threading import Thread
from time import sleep
import logging
from modbus_project import config

# Setup logging
logger = logging.getLogger('modbus_communication')

data_bank = DataBank()

# Determine IP address and port to use
ip_address = config.CURRENT_SERVER_IP_ADDRESS if config.CURRENT_SERVER_IP_ADDRESS else config.DEFAULT_SERVER_IP_ADDRESS
port = config.CURRENT_SERVER_PORT if config.CURRENT_SERVER_PORT else config.DEFAULT_SERVER_PORT
logger.info(f'IP Address: {ip_address} and Port: {port} in use for Modbus server.')

# Set current IP address and port in config
config.update_current_config('CURRENT', 'CURRENT_SERVER_IP_ADDRESS', ip_address)
config.update_current_config('CURRENT', 'CURRENT_SERVER_PORT', str(port))

# Use default bit array lengths
input_bit_array_length = config.CURRENT_INPUT_BIT_ARRAY_LENGTH if config.CURRENT_INPUT_BIT_ARRAY_LENGTH else config.DEFAULT_INPUT_BIT_ARRAY_LENGTH
output_bit_array_length = config.CURRENT_OUTPUT_BIT_ARRAY_LENGTH if config.CURRENT_OUTPUT_BIT_ARRAY_LENGTH else config.DEFAULT_OUTPUT_BIT_ARRAY_LENGTH
logger.info(f'Writing Bit array lengths in use: Input Array: {input_bit_array_length} , Output Array: {output_bit_array_length} to config file.')

server = None
server_thread = None

def int_to_bit(value, length):
    bin_str = format(value, f'0{length}b')
    return [int(bit) for bit in bin_str]

def bit_to_int(bin_list):
    bin_str = ''.join(str(bit) for bit in bin_list)
    return int(bin_str, 2)

received_bits = ""
previous_bits = ""
updated_bits_callback = None

def set_updated_bits_callback(callback):
    global updated_bits_callback
    updated_bits_callback = callback

def check_for_updates():
    global received_bits, previous_bits
    while True:
        current_state = data_bank.get_holding_registers(2048, 1)
        if current_state:
            bin_list = int_to_bit(current_state[0], length=output_bit_array_length)
            received_bits = "".join(map(str, bin_list))  # Direct bit list without reversing
            if received_bits != previous_bits:
                previous_bits = received_bits
                if updated_bits_callback:
                    updated_bits_callback(received_bits)
        sleep(0.2)  # Check every 20 ms
        logger.info(f'Checking for updates. Current state: {current_state}, Received bits: {received_bits}')

def start_modbus_server(ip_address, port):
    global server, server_thread
    server = ModbusServer(ip_address, port, no_block=True, data_bank=data_bank)
    try:
        server.start()
        logger.info('Modbus server started.')
        server_thread = Thread(target=check_for_updates)
        server_thread.daemon = True
        server_thread.start()
        while True:
            sleep(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        server.stop()
        return False
    return True

def restart_modbus_server(ip_address, port):
    if server:
        logger.info('Stopping Modbus server.')
        server.stop()
        logger.info('Modbus server stopped.')
    success = start_modbus_server(ip_address, port)
    logger.info('New Modbus server started.')
    if success:
        config.update_current_config('CURRENT', 'CURRENT_SERVER_IP_ADDRESS', ip_address)
        config.update_current_config('CURRENT', 'CURRENT_SERVER_PORT', str(port))
        logger.info(f'Writing new Modbus server details: ip: {ip_address} , port: {port} to config file.')
    return success

def write_to_register(bit_array):
    decimal_value = bit_to_int(bit_array)  # Convert bit array to decimal
    data_bank.set_holding_registers(0, [decimal_value])
    logger.info(f'Value written to the data bank (tool): {decimal_value}.')

# Initial server start for independent execution
if __name__ == "__main__":
    modbus_thread = Thread(target=start_modbus_server, args=(ip_address, port))
    modbus_thread.daemon = True
    modbus_thread.start()
    while True:
        sleep(1)
