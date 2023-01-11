import sys, os, pygame as pg
from evdev import InputDevice, ecodes
from select import select
from pygame._sdl2.video import Renderer, Window, Texture, Image


def scan_codes():
    print(
'''Scan codes will be pressed as you press keys. Note the codes and press CTRL-C to quit
Run <python layoverlay "path/to/config"> to start the overlay daemon
config should like like this:
    640 480                                 # width, height of window
    /dev/input/event5 /dev/input/event10    # device1, device2 etc
    48 image.png                            # scan code, image.file
    32 image.png                            # scan code, image.file
No comments are allowed in config file.''')


    device_list = ('/dev/input/event4', '/dev/input/event15')
    devices = map(InputDevice, ('/dev/input/event4', '/dev/input/event15'))
    devices = {dev.fd: dev for dev in devices}

    for dev in devices.values(): print(dev)
    while True:
        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type == ecodes.EV_KEY and event.value == 1: # is a key and keydown event
                    print(devices[fd].path, event.code)

def overlay(config):
    print('Staring')
    window, renderer, devices, overlays = config_devices(config)
    clock = pg.time.Clock()
    pressed = None

    window.minimize()
    while True:
        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type == ecodes.EV_KEY:
                    if event.value == 2 and event.code in overlays: # a key was pressed
                        overlays[event.code].draw()
                        pressed = event.code
                        window.restore()
                        window.show()
                        window.focus()
                    elif event.value == 0 and event.code == pressed:
                        window.minimize()
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                terminate()
        renderer.present()
        clock.tick(30)

def config_devices(path):
    overlays = {}
    with open(path) as inp:
        size = inp.readline().split()
        window, renderer = set_display(size)
        device_list = inp.readline().split()
        for l in [l.strip('\n') for l in inp.readlines() if l]:
            key, image = l.split()
            texture = Texture.from_surface(renderer, pg.image.load(image))
            overlays[int(key)] = texture
    device_list = ('/dev/input/event4', '/dev/input/event15')
    print(device_list, overlays)
    devices = map(InputDevice, ('/dev/input/event4', '/dev/input/event15'))
    devices = {dev.fd: dev for dev in devices}
    texture.draw()

    return window, renderer, devices, overlays

def set_display(size):
    size = int(size[0]), int(size[1])
    pg.display.init()   
    os.environ['SDL_RENDER_SCALE_QUALITY'] = '2'
    window = Window("Layout Overlay", always_on_top=True, size=size)
    icon = pg.image.load('icon.png')
    window.set_icon(icon)
    renderer = Renderer(window)
    return window, renderer

def terminate():
    pg.quit()
    exit()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        scan_codes()
    elif os.path.isfile(sys.argv[1]):
        overlay(sys.argv[1])
    else:
        print('command argument not a config file')