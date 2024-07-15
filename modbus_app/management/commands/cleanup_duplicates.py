from django.core.management.base import BaseCommand
from modbus_app.models import Signal
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean up duplicate Signals by name and port'

    def handle(self, *args, **kwargs):
        duplicates = (
            Signal.objects.values('name', 'port')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        for duplicate in duplicates:
            signals = Signal.objects.filter(
                name=duplicate['name'],
                port=duplicate['port']
            )
            signals_to_delete = signals[1:]  # Keep the first occurrence
            for signal in signals_to_delete:
                signal.delete()
        
        self.stdout.write(self.style.SUCCESS('Successfully cleaned up duplicate signals.'))
