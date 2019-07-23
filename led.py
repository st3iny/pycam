import argparse
import inspect
import time
import usb


# usb code

# nzxt smart device (H500i led and fan controller)
vendor_id = 0x1e71
product_id = 0x1714


def get_device():
    """ return device handle """
    dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if dev is None:
        raise ValueError('device not found')
    return dev


def claim(dev):
    """ assert control over device """
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)


def declaim(dev):
    """ return control over device to kernel """
    usb.util.dispose_resources(dev)
    if not dev.is_kernel_driver_active(0):
        dev.attach_kernel_driver(0)


def write(packet1, packet2):
    """ send packet to dev """
    assert len(packet1) == 65
    assert len(packet2) == 65

    dev = get_device()
    claim(dev)
    dev.write(1, packet1)
    time.sleep(0.05)
    dev.write(1, packet2)
    declaim(dev)


# settings

LED_COUNT = 20


# modes

class PresetMode:
    """ modes that accept one universal color for all leds """
    FIXED = 0
    FADING = 1
    SPECTRUM_WAVE = 2
    MARQUEE = 3
    COVERING_MARQUEE = 4
    ALTERNATING = 5
    PULSE = 6
    BREATHING = 7
    # ALERT = 8
    CANDLE = 9
    # RPM = 11
    WINGS = 12
    # WAVE = 13
    # AUDIO = 14


class CustomMode:
    """ modes where each led can be set to a different color """
    FIXED = 0
    FADING = 1
    MARQUEE = 3
    COVERING_MARQUEE = 4
    PULSE = 6
    BREATHING = 7
    WINGS = 12
    WAVE = 13


# animation settings

class Speed:
    """ animation speed """
    SLOWEST = 0
    SLOW = 1
    NORMAL = 2
    FAST = 3
    FASTEST = 4


class Direction:
    """ animation direction """
    FORWARD = 0
    BACKWARD = 1


# base functions

def set_led_preset(mode, index=0, r=0, g=0, b=255, speed=0, direction=0, option_byte=0,
                   led_group_size=0):
    """ repeat given color for each led """
    colors = [(r, g, b)] * LED_COUNT
    set_led(mode, colors, index, speed, direction, option_byte, led_group_size)


def set_led(mode, colors, index=0, speed=0, direction=0, option_byte=0, led_group_size=0):
    """ low level led interface """
    if len(colors) > 20:
        raise ValueError(f'too many colors (there are only {LED_COUNT} leds)')

    # resort colors to grb and flatten them to a 1d list
    colors = [(g, r, b) for r, g, b in colors]
    colors_flat = [item for rgb in colors for item in rgb]

    # build packets
    packet1 = [
        2,
        75,
        mode,
        (direction << 4) | (option_byte << 3),
        (index << 5) | (led_group_size << 3) | speed,
    ] + colors_flat[:57]  # last 3 bytes can't be used for colors

    packet2 = [3] + colors_flat[57:]

    def fill(data):
        """ fill list with zeroes to length 65 """
        if len(data) < 65:
            data += [0] * (65 - len(data))

    fill(packet1)
    fill(packet2)

    write(bytes(packet1), bytes(packet2))


# modes

modes = list()


def mode(func):
    """ mode decorator for generating help """
    modes.append(func)
    return func


@mode
def off():
    """ turn off all leds """
    array = [2, 75] + [0] * 63
    array2 = [3] + [0] * 64

    write(bytes(array), bytes(array2))


@mode
def fixed(color):
    """ fixed color for all leds """
    r, g, b = color
    set_led_preset(mode=PresetMode.FIXED, r=r, g=g, b=b)


@mode
def breathing(*colors, speed=Speed.NORMAL):
    """ fade brightness in, out and then change color """
    for i, (r, g, b) in enumerate(colors):
        set_led_preset(mode=PresetMode.BREATHING, index=i, r=r, g=g, b=b, speed=speed)


@mode
def fading(*colors, speed=Speed.NORMAL):
    """ fade between given colors """
    for i, (r, g, b) in enumerate(colors):
        set_led_preset(mode=PresetMode.FADING, index=i, r=r, g=g, b=b, speed=speed)


@mode
def marquee(color, speed=Speed.NORMAL, direction=Direction.FORWARD, size=3):
    """ moving row of leds """
    if size < 3 or size > 6:
        raise ValueError('size has to be between 3 and 6')

    r, g, b = color
    set_led_preset(
        mode=PresetMode.MARQUEE, r=r, g=g, b=b, speed=speed, direction=direction,
        led_group_size=size - 3,
    )


@mode
def covering_marquee(*colors, speed=Speed.NORMAL, direction=Direction.FORWARD):
    """ marquee consisting of multiple colors """
    for i, (r, g, b) in enumerate(colors):
        set_led_preset(
            mode=PresetMode.COVERING_MARQUEE, index=i, r=r, g=g, b=b, speed=speed,
            direction=direction,
        )


@mode
def pulse(*colors, speed=Speed.NORMAL):
    """ fade color out and then show next color with full brightness """
    for i, (r, g, b) in enumerate(colors):
        set_led_preset(mode=PresetMode.PULSE, index=i, r=r, g=g, b=b, speed=speed)


@mode
def spectrum_wave(speed=Speed.NORMAL, direction=Direction.FORWARD):
    """ (hard coded) rgb marquee """
    set_led_preset(mode=PresetMode.SPECTRUM_WAVE, speed=speed, direction=direction)


@mode
def alternating(color1, color2, speed=Speed.NORMAL, direction=Direction.FORWARD, size=3,
                moving=False):
    """ alternate led rows between two colors """
    if size < 3 or size > 6:
        raise ValueError('size has to be between 3 and 6')

    r1, g1, b1 = color1
    set_led_preset(
        mode=PresetMode.ALTERNATING, index=0, r=r1, g=g1, b=b1, speed=speed, direction=direction,
        led_group_size=size - 3, option_byte=int(moving),
    )
    r2, g2, b2 = color2
    set_led_preset(
        mode=PresetMode.ALTERNATING, index=1, r=r2, g=g2, b=b2, speed=speed, direction=direction,
        led_group_size=size - 3, option_byte=int(moving),
    )


@mode
def wings(color, speed=Speed.NORMAL):
    """ symmetric marquee (looks like flapping wings) """
    r, g, b = color
    set_led_preset(PresetMode.WINGS, r=r, g=g, b=b, speed=speed)


@mode
def candle(color):
    """ flickering candle """
    r, g, b = color
    set_led_preset(PresetMode.CANDLE, r=r, g=g, b=b)


# custom modes

@mode
def custom_fixed(*colors):
    """ set each led to a fixed color """
    set_led(mode=CustomMode.FIXED, colors=colors)


@mode
def custom_breathing(*colors, speed=Speed.NORMAL):
    """ breating but with a different color for each led """
    set_led(mode=CustomMode.BREATHING, colors=colors)


@mode
def custom_wave(*colors, speed=Speed.NORMAL):
    """ marquee with different colors for each led """
    set_led(mode=CustomMode.WAVE, colors=colors, speed=speed)


# cli

def main(mode, colors, **kwargs):
    """ led cli """
    # convert given mode to callable function
    if mode not in globals():
        raise ValueError('invalid mode given')

    # call led api
    kwargs = {key: value for key, value in kwargs.items() if value is not None}
    globals()[mode](*colors, **kwargs)


if __name__ == '__main__':
    def color(arg):
        """ return rgb tuple from comma separated string """
        return map(int, arg.split(','))

    # generate mode help
    all_flags = ('speed', 'direction', 'size', 'moving')
    mode_table = list()
    for mode in modes:
        signature = inspect.signature(mode)
        flags = filter(lambda param: param in all_flags, signature.parameters)
        flags_string = ', '.join(flags)
        mode_table.append([f'  {mode.__name__}', f'{mode.__doc__[1:-1]} ({flags_string})'])

    # format mode help table
    max_length = 23
    for entry in mode_table:
        max_length = max(max_length, len(entry[0]))
    header = 'modes (allowed flags):'
    mode_help = [header] + [entry[0].ljust(max_length) + entry[1] for entry in mode_table]

    # construct argument parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Control NZXT smart device leds.',
        epilog='\n'.join(mode_help),
    )
    parser.add_argument('mode', type=str, help='led mode')
    parser.add_argument('colors', nargs='*', type=color,
                        help='colors as rgb comma separated string (eg. 255,0,0)')
    parser.add_argument('--size', type=int, choices=(3, 4, 5, 6),
                        help='set led row length (for some modes)')
    parser.add_argument('--moving', action='store_const', const=True,
                        help='only works for alternating')
    parser.add_argument(
        '--backward', action='store_const', const=Direction.BACKWARD, dest='direction',
        help='play animation backwards (only works for some modes)',
    )

    # speed flags
    speed_group = parser.add_mutually_exclusive_group()
    speed_group.add_argument(
        '--speed', choices=(Speed.SLOWEST, Speed.SLOW, Speed.NORMAL, Speed.FAST, Speed.FASTEST),
        type=int,
        help='set animation speed (defaults to medium speed and only works for some modes)',
    )
    speed_group.add_argument('--slowest', action='store_const', const=Speed.SLOWEST, dest='speed',
                             help='animation speed')
    speed_group.add_argument('--slow', action='store_const', const=Speed.SLOW, dest='speed',
                             help='animation speed')
    speed_group.add_argument('--fast', action='store_const', const=Speed.FAST, dest='speed',
                             help='animation speed')
    speed_group.add_argument('--fastest', action='store_const', const=Speed.FASTEST, dest='speed',
                             help='animation speed')

    args = parser.parse_args()

    # call cli main function
    main(args.mode, args.colors, speed=args.speed, direction=args.direction, size=args.size,
         moving=args.moving)
