#!/bin/python
import sys, os, pickle, time
from evdev import InputDevice, list_devices, UInput, ecodes as ec
from select import select
import PySimpleGUI as sg, subprocess as sp
from PIL import Image
from io import BytesIO

options = dict(
    overlays={},
    delay=40,
    alpha=80,
    position=(None, None),
    scale=25 )

# measure performance between 2 points
def perf(message=None):
    if message:
        dif = time.perf_counter()-perf.last
        print(f'{message}: {dif*1000:0.0f}')
    perf.last = time.perf_counter()
perf.last = 0

PLAYBACK_KEYS = False # Enable this if the overlay steals keyboard focus on your platform

def run_process(cmd, sudo=True):
    # GET AND VERIFY LINUX SUDO PASSWORD
    if sudo and sys.platform == 'linux':
        password = getattr(run_process, 'password', '')
        if password:
            cmd = ['sudo', '-kS', '-p', ""] + cmd
        else:
            for _ in range(3):
                results = sg.popup_get_text('Enter your ROOT password',
                    title='Validation', size=45, password_char='*')
                if results:
                    try:
                        r = sp.run(('sudo', '-vkS'), capture_output=True,
                                input=(results+'\n').encode(), timeout=1)
                    except: continue
                    if not r.returncode:
                        password = (results + '\n').encode()
                        run_process.password = password
                        cmd = ['sudo', '-kS', '-p', ""] + cmd
                        break
            else:
                sudo = False

    # OPEN PROCESS AND SEND PASSWORD
    outp = []; count = 0
    p = sp.Popen(cmd, stdin=sp.PIPE)
    p.communicate(input=password)
    p.kill()

def overlay_window(devices, overlays, codes):
    delay = 10
    image = list(overlays.values())[0] # get first image
    layout = [[sg.Image(image.getvalue(), key='image')]]
    menu = ['Config', 'Exit']
    pos = options['position']
    alpha = (75*(options['alpha']/100)+25)/100
    sleep = 50
    delay = 2000 * (options['delay']/100)
    delay /= 50
    window = sg.Window('Overlay', layout, finalize=True, margins=(0,0), no_titlebar=True,
            alpha_channel=alpha, grab_anywhere=True, right_click_menu=menu,
            location=pos)
    window.hide()
    pressed = None
    pressed_for = clicked = 0
    key_hold = []
    ui = UInput()

    while True:
        ev, values = window.read(sleep)
        if ev in (sg.WIN_CLOSED, 'Exit'):
            break            
        
        if pressed != None:
            pressed_for += 1
            if pressed_for > delay:
                window.un_hide()

        r, w, x = select(devices, [], [])
        for fd in r:
            for event in devices[fd].read():
                if event.type == ec.EV_KEY:
                    if event.value == 1:
                        if event.code in codes[fd]: # a key was pressed
                            pressed_for = 0
                            pressed = event.code
                            key = (devices[fd].path, event.code)
                            window['image'].update(data=overlays[key].getvalue())
                        elif pressed_for > delay:
                            # add keys to list
                            key_hold.append(event.code)
                    elif event.value == 0 and event.code == pressed:
                        window.hide()
                        if key_hold and PLAYBACK_KEYS: # send keyheld keys
                            ui.write(ec.EV_KEY, pressed, 1)
                            for key in key_hold:
                                ui.write(ec.EV_KEY, key, 1)
                            for key in key_hold:
                                ui.write(ec.EV_KEY, key, 0)
                            ui.write(ec.EV_KEY, pressed, 0)
                            key_hold.clear()
                            ui.syn()
                        pressed = None

    options['position'] = window.current_location()
    window.close()

def config_window():
    def update_sliders(window, values, force=False):
        if force or values['scale'] != options['scale']:
            if values:
                options['scale'] = values['scale']
            scale = 4 * (options['scale']/100)
            if abs(scale-1) < .15: scale = 1
            window['scaletxt'].update(f'{scale:0.1f}x')
        if force or values['delay'] != options['delay']:
            if values:
                options['delay'] = values['delay']
            delay = 2000 * (options['delay']/100)
            window['delaytxt'].update(f'{delay:0.0f}ms')

    device_list = sorted(list_devices(), key=lambda x: x.lower())
    devices = {dev.fd: dev for dev in map(InputDevice, device_list)}
    devnames = {dev.name: dev for dev in map(InputDevice, device_list)}
    names = sorted(list(devnames.keys()), key=lambda x: x.lower())
    overlays = options['overlays']
    items = list(overlays.keys())

    sg.set_options(font=('Arial', 16))
    sg.theme('BlueMono')
    buttons = 'Remove', 'Add'
    layout = [
        [sg.Text('Device:', size=12), sg.Combo(names, 'select device', key='device',
                enable_events=True, readonly=True)],
        [sg.Text('Last Key:', size=12), sg.Text('', key='lastkey')],
        [sg.Listbox(items, size=(60,8), key='list')],
        [sg.Text('Transparency', size=12), sg.Slider((1,100), options['alpha'],
                orientation='h', key='alpha', disable_number_display=True),
                sg.Push()] + [sg.Button(b, size=8) for b in buttons],
        [sg.Text('Popup Delay', size=12), sg.Slider((1, 100), options['delay'],
                disable_number_display=True, orientation='h', key='delay', enable_events=True),
                sg.Text('', key='delaytxt')],
        [sg.Text('Image Size', size=12), sg.Slider((1, 100), options['scale'], 
                key='scale', orientation='h', disable_number_display=True, enable_events=True),
                sg.Text('', key='scaletxt'), sg.Push(), sg.Button('Start', size=8)] ]

    window = sg.Window('Keyboard Overlayer', layout, finalize=True)
    update_sliders(window, None, True)
    window['Add'].update(disabled=True)
    device = code = None

    while True:
        event, values = window.read(100)
        if event == sg.WIN_CLOSED:
            break
        elif event in ('scale', 'delay'):
            update_sliders(window, values)
        elif event == 'device':            
            device = devnames[values['device']]
            window['lastkey'].update('press a key')
        elif event == 'Add':
            results = add_overlay_window(device.path, str(code))
            if results:
                options['changed'] = True
                ndev, ncode, nimage = results
                image_name = os.path.splitext(os.path.split(nimage)[1])[0]
                desc = f'{ndev} - {ncode} - {image_name}'
                overlays[desc] = results
                items.append(desc)
                window['list'].update(items)
        elif event == 'Remove':
            sel = values['list']
            if sel:
                options['changed'] = True
                overlays.pop(sel[0])
                items.remove(sel[0])
                window['list'].update(items)

        elif event == 'Start':
            options['alpha'] = values['alpha']
            options['delay'] = values['delay']
            options['overlays'] = overlays
            scale = 4 * (options['scale']/100)
            if abs(scale-1) < .15: scale = 1

            options['scale'] = values['scale']
            save_options()
            if overlays:
                window.close()
                return config_devices(overlays, scale)
            else:
                sg.popup_error('No bindings have been configured!')
                continue

        if device:
            while True:
                event = device.read_one()
                if event:            
                    if event.type == ec.EV_KEY and event.value == 1:
                        if not code:
                            window['Add'].update(disabled=False)
                        code = event.code
                        lastkey = f"{code} - {ec.KEY.get(code, '')} {event.type}"
                        window['lastkey'].update(lastkey)
                else:
                    break
    window.close()

def config_devices(overlays, scale):
    def loadimg(path):
        im = Image.open(path)
        im = im.resize( (int(scale * s) for s in im.size), Image.Resampling.LANCZOS )
        bio = BytesIO()
        im.save(bio, format="PNG")
        return bio

    values = list(overlays.values())
    # Get each unique device path (ex. /dev/input/input1)
    device_paths = list(set([i[0] for i in values]))
    # Generate device objects for each unique device path and map them to their uid
    devices = map(InputDevice, device_paths)
    devices = {dev.fd: dev for dev in devices}
    # Load each unique image and map them to their file path
    images = {path: loadimg(path) for path in set([i[2] for i in values])}
    # map each image overlay to a 2-tuple (devpath, scancode)
    overlays = {(i[0], i[1]): images[i[2]] for i in values}
    # map every scancode to each device uid
    codes = {}
    for dev in devices.values():
       path = dev.path
       codes[dev.fd] = [i[1] for i in overlays if i[0] == path]
    return devices, overlays, codes


def add_overlay_window(device, code, history=[]):
    layout = [
        [sg.Text('Device', size=12), sg.In(device, key='device')],
        [sg.Text('Code', size=12), sg.In(code, key='code')],
        [sg.Text('Image', size=12), sg.In('', key='image'), sg.FileBrowse()],
        [sg.Push(), sg.Button('Cancel'), sg.Button('Add')] ]

    window = sg.Window('Add Overlay', layout, modal=True)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == 'Add':
            window.close()
            try:
                code = int(values['code'])
                Image.open(values['image'])
            except:
                sg.popup_error('Image/Parameter Error')
                return
            return values['device'], code, values['image']
        elif event == 'Cancel':
            break
    window.close()

def terminate():
    pg.quit()
    exit()

def load_options(fn='options.cfg'):
    try:
        with open(fn, 'rb') as inp:
            loaded = pickle.load(inp)
            options.update(loaded)
    except:
        print('Error loading options.cfg')
        if os.path.isfile(fn):
            os.remove(fn)
    options['changed'] = False
    load_options.loaded = options.copy()
def save_options(fn='options.cfg'):
    if options != load_options.loaded:
        print('Options changed: saving')
        with open(fn, 'wb') as outp:
            try:
                pickle.dump(options, outp)
                outp.close()
            except:
                print('Error saving options')
    else:
        print('Options unchanged')

if __name__ == '__main__':
    test = list_devices()
    if test:
        config = 'layoverlay.cfg'
        load_options()
        while True:
            config = config_window()
            if config:
                overlay_window(*config)
            else:
                break
    else:
        cmd = ['python', __file__]
        run_process(cmd)
