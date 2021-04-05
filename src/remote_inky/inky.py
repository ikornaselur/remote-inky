"""Inky e-Ink Display Driver."""
import struct
import time
from typing import List, Optional, Union

import numpy
from PIL import Image
import RPi.GPIO as GPIO
import spidev

BLACK = 0
WHITE = 1
GREEN = 2
BLUE = 3
RED = 4
YELLOW = 5
ORANGE = 6
CLEAN = 7

DESATURATED_PALETTE = [
    [0, 0, 0],
    [255, 255, 255],
    [0, 255, 0],
    [0, 0, 255],
    [255, 0, 0],
    [255, 255, 0],
    [255, 140, 0],
    [255, 255, 255],
]

SATURATED_PALETTE = [
    [57, 48, 57],
    [255, 255, 255],
    [58, 91, 70],
    [61, 59, 94],
    [156, 72, 75],
    [208, 190, 71],
    [177, 106, 73],
    [255, 255, 255],
]

RESET_PIN = 27
BUSY_PIN = 17
DC_PIN = 22

CS0_PIN = 8

UC8159_PSR = 0x00
UC8159_PWR = 0x01
UC8159_POF = 0x02
UC8159_PFS = 0x03
UC8159_PON = 0x04
UC8159_BTST = 0x06
UC8159_DSLP = 0x07
UC8159_DTM1 = 0x10
UC8159_DSP = 0x11
UC8159_DRF = 0x12
UC8159_IPC = 0x13
UC8159_PLL = 0x30
UC8159_TSC = 0x40
UC8159_TSE = 0x41
UC8159_TSW = 0x42
UC8159_TSR = 0x43
UC8159_CDI = 0x50
UC8159_LPD = 0x51
UC8159_TCON = 0x60
UC8159_TRES = 0x61
UC8159_DAM = 0x65
UC8159_REV = 0x70
UC8159_FLG = 0x71
UC8159_AMV = 0x80
UC8159_VV = 0x81
UC8159_VDCS = 0x82
UC8159_PWS = 0xE3
UC8159_TSSET = 0xE5

_SPI_CHUNK_SIZE = 4096
_SPI_COMMAND = 0
_SPI_DATA = 1


class Inky:
    """Inky e-Ink Display Driver."""

    WIDTH = 600
    HEIGHT = 448

    def __init__(
        self: "Inky",
        h_flip: bool = False,
        v_flip: bool = False,
    ) -> None:
        self.resolution = (self.WIDTH, self.HEIGHT)
        self.width = self.cols = self.WIDTH
        self.height = self.rows = self.HEIGHT
        self.border_colour = WHITE
        self.rotation = self.offset_x = self.offset_y = 0

        self.lut = self.colour = "multi"

        self.buf = numpy.zeros((self.rows, self.cols), dtype=numpy.uint8)

        self.dc_pin = DC_PIN
        self.reset_pin = RESET_PIN
        self.busy_pin = BUSY_PIN
        self.cs_pin = CS0_PIN
        self.cs_channel = 0

        self.h_flip = h_flip
        self.v_flip = v_flip

        self._spi_bus = spidev.SpiDev()
        self._gpio = GPIO
        self._setup_gpio()

        self._luts = None

    def _palette_blend(
        self: "Inky", saturation: float, dtype: str = "uint8"
    ) -> List[int]:
        saturation = float(saturation)
        palette: List[int] = []
        for i in range(7):
            rs, gs, bs = [c * saturation for c in SATURATED_PALETTE[i]]
            rd, gd, bd = [c * (1.0 - saturation) for c in DESATURATED_PALETTE[i]]
            if dtype == "uint8":
                palette += [int(rs + rd), int(gs + gd), int(bs + bd)]
            if dtype == "uint24":
                palette += [(int(rs + rd) << 16) | (int(gs + gd) << 8) | int(bs + bd)]
        if dtype == "uint8":
            palette += [255, 255, 255]
        if dtype == "uint24":
            palette += [0xFFFFFF]
        return palette

    def _setup_gpio(self: "Inky") -> None:
        self._gpio.setmode(self._gpio.BCM)
        self._gpio.setwarnings(False)
        self._gpio.setup(self.cs_pin, self._gpio.OUT, initial=self._gpio.HIGH)
        self._gpio.setup(
            self.dc_pin,
            self._gpio.OUT,
            initial=self._gpio.LOW,
            pull_up_down=self._gpio.PUD_OFF,
        )
        self._gpio.setup(
            self.reset_pin,
            self._gpio.OUT,
            initial=self._gpio.HIGH,
            pull_up_down=self._gpio.PUD_OFF,
        )
        self._gpio.setup(self.busy_pin, self._gpio.IN, pull_up_down=self._gpio.PUD_OFF)

        self._spi_bus.open(0, self.cs_channel)
        self._spi_bus.no_cs = True
        self._spi_bus.max_speed_hz = 3000000

        self._gpio_setup = True

    def setup(self: "Inky") -> None:
        """Set up Inky GPIO and reset display."""
        self._gpio.output(self.reset_pin, self._gpio.LOW)
        time.sleep(0.1)
        self._gpio.output(self.reset_pin, self._gpio.HIGH)
        time.sleep(0.1)

        self._busy_wait()
        self._send_command(
            UC8159_TRES, list(struct.pack(">HH", self.width, self.height))
        )
        self._send_command(
            UC8159_PSR,
            [0b11101111, 0x08],
        )
        self._send_command(
            UC8159_PWR,
            [(0x06 << 3) | (0x01 << 2) | (0x01 << 1) | (0x01), 0x00, 0x23, 0x23],
        )
        self._send_command(UC8159_PLL, [0x3C])
        self._send_command(UC8159_TSE, [0x00])
        cdi = (self.border_colour << 5) | 0x17
        self._send_command(UC8159_CDI, [cdi])
        self._send_command(UC8159_TCON, [0x22])
        self._send_command(UC8159_DAM, [0x00])
        self._send_command(UC8159_PWS, [0xAA])
        self._send_command(UC8159_PFS, [0x00])

    def _busy_wait(self: "Inky", timeout: float = 15.0) -> None:
        """Wait for busy/wait pin."""
        t_start = time.time()
        while not self._gpio.input(self.busy_pin):
            time.sleep(0.01)
            if time.time() - t_start >= timeout:
                raise RuntimeError("Timeout waiting for busy signal to clear.")

    def _update(self: "Inky", buf: List[int]) -> None:
        self.setup()

        self._send_command(UC8159_DTM1, buf)
        self._busy_wait()

        self._send_command(UC8159_PON)
        self._busy_wait()

        self._send_command(UC8159_DRF)
        self._busy_wait()

        self._send_command(UC8159_POF)
        self._busy_wait()

    def set_pixel(self: "Inky", x: int, y: int, v: int) -> None:
        self.buf[y][x] = v & 0x07

    def show(self: "Inky") -> None:
        region = self.buf

        if self.v_flip:
            region = numpy.fliplr(region)

        if self.h_flip:
            region = numpy.flipud(region)

        if self.rotation:
            region = numpy.rot90(region, self.rotation // 90)

        buf = region.flatten()

        buf = ((buf[::2] << 4) & 0xF0) | (buf[1::2] & 0x0F)

        self._update(buf.astype("uint8").tolist())

    def set_border(self: "Inky", colour: int) -> None:
        """Set the border colour."""
        if colour in (BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE, CLEAN):
            self.border_colour = colour

    def set_image(self: "Inky", image: Image, saturation: float = 0.5) -> None:
        """Copy an image to the display.

        :param image: PIL image to copy, must be 600x448
        :param saturation: Saturation for quantization palette - higher value results in a more saturated image

        """
        if not image.size == (self.width, self.height):
            raise ValueError(f"Image must be ({self.width}x{self.height}) pixels!")
        if not image.mode == "P":
            palette = self._palette_blend(saturation)
            # Image size doesn't matter since it's just the palette we're using
            palette_image = Image.new("P", (1, 1))
            # Set our 7 colour palette (+ clear) and zero out the other 247 colours
            palette_image.putpalette(palette + [0, 0, 0] * 248)
            # Force source image data to be loaded for `.im` to work
            image.load()
            image = image.im.convert("P", True, palette_image.im)
        self.buf = numpy.array(image, dtype=numpy.uint8).reshape((self.cols, self.rows))

    def _spi_write(self: "Inky", dc: int, values: Union[str, List[int]]) -> None:
        """Write values over SPI.

        :param dc: whether to write as data or command
        :param values: list of values to write

        """
        self._gpio.output(self.cs_pin, 0)
        self._gpio.output(self.dc_pin, dc)

        if isinstance(values, str):
            values = [ord(c) for c in values]

        try:
            self._spi_bus.xfer3(values)
        except AttributeError:
            for x in range(((len(values) - 1) // _SPI_CHUNK_SIZE) + 1):
                offset = x * _SPI_CHUNK_SIZE
                self._spi_bus.xfer(values[offset : offset + _SPI_CHUNK_SIZE])
        self._gpio.output(self.cs_pin, 1)

    def _send_command(
        self: "Inky", command: int, data: Optional[List[int]] = None
    ) -> None:
        """Send command over SPI.

        :param command: command byte
        :param data: optional list of values

        """
        self._spi_write(_SPI_COMMAND, [command])
        if data is not None:
            self._send_data(data)

    def _send_data(self: "Inky", data: List[int]) -> None:
        self._spi_write(_SPI_DATA, data)
