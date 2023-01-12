# LayOverlay

This program displays overlay images while a certain buttons are being held (shift, alt, etc).

It uses evdev, PIL, and PySimpleGUI. My own version of PySimpleGUI is included but the official version should work as well.

### SUDO IS REQUIRED FOR THE EVDEV MODULE TO ACCESS YOUR INPUT DEVICES!!!

You must install PIL(pillow) and EVDEV for all users so that you can run the script with sudo.

```
sudo pip install pillow  
sudo pip install evdev  
  
sudo ./layoverlay.py  
  -or-  
python layoverlay.py (a password dialog will open)
```
Alternatively, you may add your user account to the input group (or distribution equivalent)

### Usage:

Once you start the program you must setup your key to image bindings.

1. Select the input device(keyboard) from the device dropdown
2. Press the layer/ctrl/alt key that you want to bind
3. Click the **Add** button
4. Click **Browse** and select an image
5. Press **Add** to return to the main config window
6. Add any additional bindings you need
7. Click the **Start** button

A window should flash onto the screen after a second or two. It will reappear when you hold the bound button long enough. The delay may be changed in the main config window.

### Exiting:
Press a button to make the overlay popup, right click on the image, and then select Exit.
