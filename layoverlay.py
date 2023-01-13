#!/bin/python
'''
An application that pops up an image when a bound key is held long enough.
It includes a configuration window and SUDO password dialog.

________________
 W I N D O W S |
================
def add_overlay_window(device, code, history=[]):
    Dialog for adding new overlay bindings to the overlay list
def config_window():
    Configuration window that makes binding keys easy and allows
    adjustments to the transparency, popup delay, and image 
    scaling settings
def overlay_window(devices, overlays, codes):
    Popup overlay window that shows a image when a bound keys is held long
    enough

____________________________________
# U T I L I T Y  F U N C T I O N S |
====================================
def load_options(fn='options.cfg'):
    Load configuration data using Pickle
def perf(message=None):
    Measures time passage between last two calls to Perf()
def run_process(cmd, sudo=True):
    Run a process with sudo access priviledges
def save_options(fn='options.cfg'):
    Save configuration data using Pickle
def setup_devices(overlays, scale):
    Takes a list of overlay bindings, loads the images, and sets up
    necessary evdev device handlers and data structures.
'''
import sys, os, pickle, time
from evdev import InputDevice, list_devices, UInput, ecodes as ec
from select import select
import PySimpleGUI as sg, subprocess as sp
from PIL import Image
from io import BytesIO

icon = b'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'
font = ('Arial', 15)
sg.set_options(font=font, icon=icon)
sg.theme('BlueMono')
PLAYBACK_KEYS = False # Enable this if the overlay steals keyboard focus on your platform
options = dict(
    overlays={},
    delay=40,
    alpha=80,
    position=(None, None),
    last_folder=None,
    last_device=None,
    scale=25 )

# =============
# W I N D O W S
def add_overlay_window(device, code, history=[]):
    '''
    Window that lets user to add a new overlay binding to the overlay list
    '''
    layout = [
        [sg.Text('Device', size=12), sg.In(device, key='device')],
        [sg.Text('Code', size=12), sg.In(code, key='code')],
        [sg.Text('Image', size=12), sg.In('', key='image'), sg.Button('Browse')],
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
            except Exception as e:
                sg.popup_error(f'Image/Parameter Error\n{e}')
                return
            return values['device'], code, values['image']
        elif event == 'Browse':
            results = image_browser(options['last_folder']
                    or os.path.split(__file__)[0])
            if results:
                window['image'].update(results)
                options['last_folder'] = os.path.split(results)[0]
        elif event == 'Cancel':
            break
    window.close()

def config_window():
    '''
    Configuration window that makes binding keys easy and offers
    adjustments to the transparency, popup delay, and image 
    scaling.
    '''
    # update text values for scale and delay sliders
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

    # get device list and create data structures
    device_list = sorted(list_devices(), key=lambda x: x.lower())
    devices = {dev.fd: dev for dev in map(InputDevice, device_list)}
    devnames = {dev.name: dev for dev in map(InputDevice, device_list)}
    names = sorted(list(devnames.keys()), key=lambda x: x.lower())
    overlays = options['overlays']
    items = list(overlays.keys())
    
    # find name of last selected device if it exists
    device = code = name = None
    if options['last_device']:
        for name in devnames:
            if options['last_device'] == devnames[name].path:
                selected = name
                device = devnames[selected]
                break

    # configure and display window
    buttons = 'Remove', 'Add'
    layout = [
        [sg.Text('Device:', size=12), sg.Combo(names, name or 'select device', key='device',
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

    # handle window events
    while True:
        event, values = window.read(100)
        if event == sg.WIN_CLOSED:
            break
        elif event in ('scale', 'delay'):
            update_sliders(window, values)
        elif event == 'device':            
            device = devnames[values['device']]
            options['last_device'] = device.path
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
                return setup_devices(overlays, scale)
            else:
                sg.popup_error('No bindings have been configured!')
                continue

        # handle keyboard events
        if device:
            while True:
                event = device.read_one()
                if event:            
                    if event.type == ec.EV_KEY and event.value == 1:
                        if not code:
                            window['Add'].update(disabled=False)
                        code = event.code
                        lastkey = f"{code} - {ec.KEY.get(code, '')}"
                        window['lastkey'].update(lastkey)
                else:
                    break
    window.close()

def overlay_window(devices, overlays, codes):
    '''
    Popup overlay window that shows a image when a bound keys is held long enough
    '''
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

def image_browser(path):
    '''
    File browser with image previews
    '''
    IMAGE_TYPES = ['.'+x for x in ('png jpg jpeg gif webp').split()]
    PATH_LENGTH = 40
    BOX_HEIGHT = 15
    IMAGE_WIDTH = int(PATH_LENGTH*font[1]*.75)

    def get_listing(path, window=None):
        folders = []; files = []
        path = os.path.normpath(path)
        for f in sorted(os.listdir(path), key=lambda x:x.lower().lstrip('.')):
            p = os.path.join(path, f)
            if os.path.isdir(p):
                folders.append('/'+f)
            elif os.path.splitext(f)[1] in IMAGE_TYPES:
                files.append(f)

        p = path
        parents = [path[-PATH_LENGTH:]]
        while True:
            p = os.path.normpath(os.path.join(p, '..'))
            parents.append(p[-PATH_LENGTH:])
            if p == os.path.sep:
                break
        items = folders+files
        if window != None:
            window['List'].update(items)
            window['PARENTS'].update(parents[0] or '/', values=parents[1:])
        return items, parents
        
    cfont = font[0], font[1]+1
    items, parents = get_listing(path)
    llayout = [[sg.Combo(parents[1:], size=PATH_LENGTH, font=cfont,
                    default_value=parents[0], key='PARENTS',
                    enable_events=True, readonly=True),
                sg.Button('?'),
                sg.Push(), sg.Button('^', key='UP')],
            [sg.Listbox(items, size = (PATH_LENGTH, BOX_HEIGHT), expand_x=True,
                    key='List', enable_events=True, bind_return_key=True)],
            [sg.Push(), sg.Button('Cancel'), sg.Button('Okay')]]
    rlayout = [[sg.Image(size=(IMAGE_WIDTH, 10), pad=(0,0), expand_y=True, key='IMAGE')]]
    layout = [[sg.Column(llayout), sg.Column(rlayout)]]

    window = sg.Window('File Chooser', layout, modal=True,
             return_keyboard_events=True, finalize=True)
    IMAGE_HEIGHT = int(window.size[1] *.95)
    IMAGE_SIZE = (IMAGE_WIDTH, IMAGE_HEIGHT)
    scroller = get_scroller(window['List'])
    window.bind("<BackSpace>", "UP")
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == 'UP':
            path = os.path.normpath(os.path.join(path, '..'))
            items, parents = get_listing(path, window)
        elif event == 'PARENTS':
            v = values[event]
            if v in parents:
                index = parents.index(v)
                for _ in range(index):
                    path = os.path.normpath(os.path.join(path, '..'))
            else:
                path = path
            items, parents = get_listing(path, window)
        elif event == '?':
            t = sg.popup_get_text('', title='Enter Path')
            if t and os.path.isdir(t):
                path = os.path.normpath(t)
                items, parents = get_listing(path, window)
        elif event == 'List':
            clicked = values[event][0]
            if clicked.startswith('/'):
                p = os.path.join(path, values[event][0][1:])
                if os.path.isdir(p):
                    path = p
                    items, parents = get_listing(path, window)
            elif os.path.splitext(clicked)[1].lower() in IMAGE_TYPES:
                p = os.path.join(path, clicked)
                im = Image.open(p)
                w, h = im.size
                ratio = min(IMAGE_WIDTH/w, IMAGE_HEIGHT/h)
                im = im.resize((int(w*ratio), int(h*ratio)), Image.Resampling.LANCZOS)
                bio = BytesIO()
                im.save(bio, format="PNG")
                window['IMAGE'].update(size=IMAGE_SIZE, data=bio.getvalue())
        elif event[1] == ':':
            scroller(event[0], items)
        elif event.startswith('slash:'):
            scroller('/', items)
        elif event == 'Okay':
            if values['List']:
                window.close()
                return os.path.join(path, values['List'][0])
            break
    window.close()

def get_scroller(element):
    '''
    Used by image_browser() to allow selection by spelling filenames
    '''
    def scroll_to_index(key, data, col=None):
        nonlocal last_press, keys_pressed
        if not data:
            return
        c = key.lower()
        ti = time.perf_counter()
        if ti - last_press < Key_DELAY:
            keys_pressed += c
        else:
            keys_pressed = c
        last_press = ti
        if col == None:
            for i, item in enumerate(data):
                if keys_pressed < item.lower():
                    break
        else:
            for i, row in enumerate(data):
                if keys_pressed < row[col].lower():
                    break
        perc = i / len(data)
        element.set_vscroll_position(perc)
        if isinstance(element, sg.Table):
            element.update(select_rows=[i])
        elif isinstance(element, sg.Listbox):
            #element.set_value(i)
            element.update(set_to_index=i)
    Key_DELAY = 1
    keys_pressed = ''
    last_press = 0
    return scroll_to_index

# ================================
# U T I L I T Y  F U N C T I O N S
def load_options(fn='options.cfg'):
    '''
    Load configuration data using Pickle
    '''
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

def perf(message=None):
    '''
    Measures time passage between last two calls to Perf()
    '''
    if message:
        dif = time.perf_counter()-perf.last
        print(f'{message}: {dif*1000:0.0f}')
    perf.last = time.perf_counter()
perf.last = 0

def run_process(cmd, sudo=True):
    '''
    Run a process with sudo access priviledges
    '''
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

def save_options(fn='options.cfg'):
    '''
    Save configuration data using Pickle
    '''
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

def setup_devices(overlays, scale):
    '''
    Takes a list of overlay bindings, loads the images, and sets up necessary
    evdev device handlers and data structures.
    '''
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
