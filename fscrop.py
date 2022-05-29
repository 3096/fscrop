import bisect
import os
import sys

import cv2 as cv
import keyboard as keyboard

IMAGE_EXT = '.png'
WINDOW_NAME = "fscrop"

img, show_x, show_y, show_w, show_h, full_w, full_h = None, 0, 0, 0, 0, 0, 0
mouse_x, mouse_y = 0, 0
do_render = True

dir_path = os.path.dirname(sys.argv[1])
images = sorted(filter(
    lambda file: os.path.isfile(file) and file.endswith(IMAGE_EXT),
    [os.path.join(dir_path, dir_ent) for dir_ent in os.listdir(dir_path)]
))
cur_image_index = bisect.bisect_left(images, sys.argv[1])


def load_image():
    global img, show_x, show_y, show_w, show_h, full_w, full_h
    img = cv.imread(images[cur_image_index])
    full_w, full_h = img.shape[1], img.shape[0]
    show_x, show_y, show_w, show_h = 0, 0, full_w, full_h


def save_image(path):
    cv.imwrite(os.path.join(path, os.path.basename(images[cur_image_index])),
               img[show_y:show_y + show_h, show_x:show_x + show_w])


def set_image_index(image_index):
    global cur_image_index, do_render
    if image_index < 0 or image_index >= len(images):
        return
    cur_image_index = image_index
    load_image()
    do_render = True


def handle_mouse_event(event, x, y, flags, _):
    global mouse_x, mouse_y, show_x, show_y, show_w, show_h, do_render

    if event == cv.EVENT_LBUTTONDOWN or event == cv.EVENT_RBUTTONDOWN:
        mouse_x, mouse_y = x, y
        return

    if flags & cv.EVENT_FLAG_LBUTTON:
        show_x = min(max(0, show_x + mouse_x - x), full_w - show_w)
        show_y = min(max(0, show_y + mouse_y - y), full_h - show_h)

    elif flags & cv.EVENT_FLAG_RBUTTON:
        zoom = mouse_x - x
        show_w = min(max(1, show_w + zoom), full_w - show_x)
        show_h = show_w * full_h // full_w
    else:
        return

    mouse_x, mouse_y = x, y
    do_render = True


keyboard.on_press_key('left', lambda e: set_image_index(cur_image_index - 1))
keyboard.on_press_key('right', lambda e: set_image_index(cur_image_index + 1))
keyboard.on_press_key('enter', lambda e: save_image(sys.argv[2]))

cv.namedWindow(WINDOW_NAME, cv.WINDOW_NORMAL)
cv.setWindowProperty(WINDOW_NAME, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
cv.setMouseCallback(WINDOW_NAME, handle_mouse_event)

load_image()

while True:
    if do_render:
        cv.imshow(WINDOW_NAME, img[show_y:show_y + show_h, show_x:show_x + show_w])
        do_render = False
    key = cv.waitKey(1)
    if key == 27:
        break
