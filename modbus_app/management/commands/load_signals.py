# modbus_app/management/commands/load_signals.py

import os
import json
import logging
from django.core.management.base import BaseCommand
from modbus_app.models import Signal
import modbus_project.config as config

# Configure logging
logger = logging.getLogger('load_signals')

class Command(BaseCommand):
    help = 'Load signals from a JSON file'

    def handle(self, *args, **options):
        file_path = config.DEFAULT_CONFIG_JSON_FILE_PATH  # Update to use the config path
        logger.info('Starting to load signals from JSON file')
        logger.debug(f'Configuration file path: {file_path}')

        if not os.path.exists(file_path):
            logger.error(f'File "{file_path}" does not exist.')
            return

        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                logger.info(f'Successfully loaded JSON data from "{file_path}"')
        except json.JSONDecodeError as e:
            logger.error(f'Error decoding JSON file "{file_path}": {e}')
            return
        except Exception as e:
            logger.error(f'Unexpected error reading file "{file_path}": {e}')
            return

        try:
            existing_signals = list(Signal.objects.values('id', 'name', 'port'))
            logger.info(f'Fetched {len(existing_signals)} existing signals from the database')
        except Exception as e:
            logger.error(f'Error fetching existing signals from database: {e}')
            return

        existing_pairs = {(sig['id'], sig['name'], sig['port']) for sig in existing_signals}
        new_pairs = {(item['id'], item.get('signal', ''), item['port']) for item in data}
        logger.debug(f'Existing signal pairs: {existing_pairs}')
        logger.debug(f'New signal pairs from JSON: {new_pairs}')

        if existing_pairs != new_pairs:
            try:
                Signal.objects.all().delete()
                logger.info('Deleted all existing signals in the database')
                for item in data:
                    Signal.objects.create(
                        id=item['id'],
                        name=item.get('signal', ''),  # Use empty string if no name is provided
                        port=item['port'],
                        direction=item['direction'],
                        state=0  # Initialize state to 0
                    )
                logger.info(f'Inserted {len(data)} new signals into the database')
                logger.info(f'Successfully loaded signals from "{file_path}".')
            except Exception as e:
                logger.error(f'Error inserting new signals into database: {e}')
                return
        else:
            logger.info('No changes detected. Signals are up-to-date.')

        logger.info('Completed loading signals from JSON file')
