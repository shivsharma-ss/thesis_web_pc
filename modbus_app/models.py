# modbus_app/models.py
from django.db import models

class Signal(models.Model):
    id = models.IntegerField(primary_key=True)  # Use AutoField instead of IntegerField
    name = models.CharField(max_length=255, blank=True, null=True)
    port = models.IntegerField()
    direction = models.CharField(max_length=3)  # "in" or "out"
    state = models.IntegerField(default=0)  # 0 or 1

    class Meta:
        unique_together = ('id', 'name', 'port')

    def __str__(self):
        return self.name or f"Unnamed Signal {self.id}"
