import json
from .models import Signal

def load_config():
    with open('C:\Users\SHS1MT.DE\Desktop\web\log_files\modules.json', 'r') as file:
        data = json.load(file)
        for item in data:
            Signal.objects.update_or_create(
                name=item['signal'],
                port=item['port'],
                defaults={'direction': item['direction'], 'state': 0}
            )
