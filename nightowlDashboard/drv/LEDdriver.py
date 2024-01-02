#/bin/python

import RPi.GPIO as GPIO


IR_LED_PINS = (13,15)

class IReyes:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        for p in IR_LED_PINS:
            GPIO.setup(p, GPIO.OUT)
        self._state = 0

    def toggle(self) -> None:
        self._state = 1
        for p in IR_LED_PINS:
            GPIO.output(p, not GPIO.input(p))
            self._state = self._state & GPIO.input(p)

    def cleanup(self) -> None:
        GPIO.cleanup()

    @property
    def status(self):
        return self._state
