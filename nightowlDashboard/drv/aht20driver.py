#!/usr/bin/env python3

from smbus2 import SMBus
from time import time, sleep

# NOTE: smbus functions require a register byte which is referred to as command byte in the sensor datasheet and here;
#       data blocks can be read from register byte 0x00 (or any byte as it appears, although it seems preferable to avoid reading a command byte)

I2C_BUS_NUMBER  = 1     # I2C bus number (typically 1 for RPi devices)

AHT20_ADDRESS   = 0x38  # I2C address of AHT20
AHT20_INIT      = 0xBE  # initialization command, requires data bytes as per sensor specification, see below
#AHT20_INIT      = 0xE1  # this is the initialization command used by Adafruit
AHT20_TRIGGER   = 0xAC  # trigger measurement, requires data bytes as per sensor specification, see below
AHT20_RESET     = 0xBA  # soft reset command

AHT20_CAL       = 0x08  # calibration status byte; only used for cross-check in driver
AHT20_BUSY      = 0x80  # busy status byte; only used for cross-check in driver


# data bytes
# see AHT20 data sheet for reference
INIT_DATA01 = [0x08, 0x00]
TRIG_DATA01 = [0x33, 0x00]


class AHT20:
    def __init__(self, i2cbus: int = I2C_BUS_NUMBER) -> None:
        sleep(0.04) # wait for sensor self-init
        #self.i2cdevice = SMBus(i2cbus) # establish i2c bus connection
        self._buffer = [0] * 6
        self.reset() # reset sensor
        if not self.calibrate(): # check calibration state
            raise RuntimeError("AHT20: calibration failed")
        self._temp = None
        self._hum = None
    
    def reset(self) -> None:
        """ Soft reset sensor. """
        self._buffer[0] = AHT20_RESET
        with SMBus(I2C_BUS_NUMBER) as sens:
            sens.write_byte(AHT20_ADDRESS, self._buffer[0])
        sleep(0.02)
    
    def calibrate(self) -> bool:
        """ Manually intialize sensor and check calibration status. """
        self._buffer[0] = AHT20_INIT
        self._buffer[1:3] = INIT_DATA01
        self._busywait()
        with SMBus(I2C_BUS_NUMBER) as sens: # ask sensor to initialize
            sens.write_i2c_block_data(AHT20_ADDRESS, self._buffer[0], self._buffer[1:3])
        sleep(0.01)
        self._busywait()
        if not self.status & AHT20_CAL: # compute calibration status
            return False
        return True

    def _busywait(self) -> None:
        """ Internal helper function to wait for sensor action. """
        self._now = time()
        while self.status & AHT20_BUSY: # check if busy
            sleep(0.02)
            if (time() - self._now) > 10:
                raise RuntimeError("AHT20: aborted - received busy signal for 10 seconds")

    @property
    def status(self) -> int:
        """ Obtains status byte from sensor. """
        with SMBus(I2C_BUS_NUMBER) as sens:
            self._buffer[5] = sens.read_byte(AHT20_ADDRESS)
        return self._buffer[5]

    @property
    def temperature(self) -> int:
        #self.measure()
        return self._temp
    
    @property
    def humidity(self) -> int:
        #self.measure()
        return self._hum
    
    def measure(self) -> None:
        self._buffer[0] = AHT20_TRIGGER
        self._buffer[1:3] = TRIG_DATA01
        self._busywait()
        with SMBus(I2C_BUS_NUMBER) as sens:
            sens.write_i2c_block_data(AHT20_ADDRESS, self._buffer[0], self._buffer[1:3])
        self._busywait()
        with SMBus(I2C_BUS_NUMBER) as sens:
            self._buffer = sens.read_i2c_block_data(AHT20_ADDRESS, 0x00, 6) # read six bytes (1 status byte + 5 data bytes)
        self._hum = ((
            (self._buffer[1] << 12) | (self._buffer[2] << 4) | (self._buffer[3] >> 4) # stitch humidity data bytes together
            ) / 2**20) * 100 # convert humidity data; refer to data sheet for details
        self._temp = ((
            ((self._buffer[3] & 0xF) << 16) | (self._buffer[4] << 8) | self._buffer[5] # stitch temperature data bytes together
            ) / 2**20) * 200 - 50 # convert temperature data; refer to data sheet for details