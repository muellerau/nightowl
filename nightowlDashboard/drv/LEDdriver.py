#!/usr/bin/env python3

import RPi.GPIO as GPIO


IR_LED_PINS = (13,15)

class IReyes:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        for p in IR_LED_PINS:
            GPIO.setup(p, GPIO.OUT)
        self._state = 0

    def toggle(self) -> None:
        for p in IR_LED_PINS:
            GPIO.output(p, not GPIO.input(p))
            self._state = self._state & GPIO.input(p)

    def turn_on(self) -> None:
        self._state = 1
        for p in IR_LED_PINS:
            GPIO.output(p, 1)

    def turn_off(self) -> None:
        self._state = 0
        for p in IR_LED_PINS:
            GPIO.output(p, 0)

    def cleanup(self) -> None:
        GPIO.cleanup()

    @property
    def status(self):
        return self._state
