# pycam

Control NZXT smart device leds


## Requirements

* Python3 (not tested with python2)
* PyUSB

This works on linux (pyusb should also work on Windows but I haven't tested it yet) with the 
NZXT Smart Device (inside H500i case for example). You can swap the device and product id in the
code at your own risk.

USB device ids:
* vendor_id = 0x1e71
* product_id = 0x1714

You can find a udev rule file in the repo (`10-nzxt.rules`).

Feel free to hack my code. It should be documented sufficiently.


## Rant

The other day I was really fed up with the NZXT CAM software because it spies on you and only
works on Windows. So I decided to implement a little driver/cli for controlling the leds of the
NZXT Smart Device (led and fan controller inside NZXT H500i case). Turns out there is no linux
driver available for it yet (or maybe I didn't dive deep enough).

Anyways, this has been a fun exercise and I hope it will be useful to someone out there.


## Some findings

The controller supports more custom modes as there are in the official Windows app. The cli 
can set every preset and custom mode from the Windows app. For the more fancy stuff you should 
use python scripts.

A little example for an rgb covering marquee:
```python
import led


r = [(255, 0, 0)] * 10
g = [(0, 255, 0)] * 10
b = [(0, 0, 255)] * 10

program = [
    r + g,
    b + r,
    g + b,
]

for index, step in enumerate(program):
    led.set_led(led.CustomMode.COVERING_MARQUEE, step, index=index, speed=led.Speed.FAST)
```

For each mode in the `CustomMode` enum each led can be controlled independently. For chaining 
different animation steps (for example when using fading or breathing) you just have to increase 
the index by one for each step.
