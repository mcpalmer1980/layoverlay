#!/bin/python
import sys, os, pygame as pg
from evdev import InputDevice, list_devices, ecodes
from select import select
from pygame._sdl2.video import Renderer, Window, Texture, Image
import PySimpleGUI as sg
from PIL import Image
from io import BytesIO


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


    device_list = sorted(list_devices(), key=lambda x: x.lower())
    devices = map(InputDevice, device_list)
    devices = {dev.fd: dev for dev in devices}

    for dev in devices.values(): print(dev)
    while True:
        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type == ecodes.EV_KEY and event.value == 1: # is a key and keydown event
                    print(devices[fd].path, event.code)

def window(config):
    devices, overlays = config_devices(config)
    delay = 10
    layout = [[sg.Image('image-alt.png', key='image')]]
    menu = ['Config', 'Exit']
    sg.set_options(font=('Arial', 16))
    window = sg.Window('Overlay', layout, finalize=True, margins=(0,0), no_titlebar=True,
            alpha_channel=.5, grab_anywhere=True, right_click_menu=menu)
    window.hide()
    pressed = None
    pressed_for = 0

    while True:
        sleep = 10 if window._Hidden else 200
        ev, values = window.read(sleep)
        if ev in (sg.WIN_CLOSED, "Exit"):
            break
        
        if pressed != None:
            pressed_for += 1
            if pressed_for > delay:
                window.un_hide()

        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type == ecodes.EV_KEY:
                    if event.value == 1 and event.code in overlays: # a key was pressed
                        pressed_for = 0
                        pressed = event.code
                        window['image'].update(data=overlays[pressed].getvalue())
                    elif event.value == 0 and event.code == pressed:
                        pressed = None
                        window.hide()

def config_window():
    buttons = 'Remove', 'Add', 'Start'
    layout = [
        [sg.Text('Last Key:', size=12), sg.Text('', key='lastkey')],
        [sg.Listbox([], size=(60,8))],
        [sg.Push()] + [sg.Button(b) for b in buttons]]
    window = sg.Window('Keboard Overlayer', layout, finalize=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Start':
            window.close()
            return True
    window.close()


def config_devices(path):
    overlays = {}
    with open(path) as inp:
        size = inp.readline().split()
        device_list = inp.readline().split()
        for l in [l.strip('\n') for l in inp.readlines() if l]:
            key, image = l.split()
            im = Image.open(image)
            bio = BytesIO()
            im.save(bio, format="PNG")
            overlays[int(key)] = bio
    print(device_list, overlays)
    devices = map(InputDevice, device_list)
    devices = {dev.fd: dev for dev in devices}

    return devices, overlays

def terminate():
    pg.quit()
    exit()

if __name__ == '__main__':
    config = 'layoverlay.cfg'
    while True:
        if config_window():
            window(config)
        else:
            break
    exit()


    if len(sys.argv) == 1:
        scan_codes()
    elif os.path.isfile(sys.argv[1]):
        window(sys.argv[1])
        #overlay(sys.argv[1])
    else:
        print('command argument not a config file')