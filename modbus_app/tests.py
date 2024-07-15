from django.test import TestCase
from .models import Signal

class SignalModelTest(TestCase):
    def setUp(self):
        Signal.objects.create(name="TestSignal", port=1, direction="in", state=0)

    def test_signal_creation(self):
        signal = Signal.objects.get(name="TestSignal")
        self.assertEqual(signal.name, "TestSignal")
        self.assertEqual(signal.port, 1)
        self.assertEqual(signal.direction, "in")
        self.assertEqual(signal.state, 0)
