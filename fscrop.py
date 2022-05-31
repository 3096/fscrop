import bisect
import os
import sys
from collections import namedtuple

import cv2 as cv
import keyboard as keyboard

if os.name == 'nt':
    from win32gui import GetWindowText, GetForegroundWindow

IMAGE_EXT = '.png'
WINDOW_NAME = "fscrop"
GUIDELINE_COLOR = (0x77, 0x77, 0x77)
TASKBAR_RATIO = 24

in_path = sys.argv[1]
out_dir = sys.argv[2]

controls = namedtuple('Controls',
                      ['prev', 'next', 'save', 'quit',
                       'rule_of_thirds', 'v_center', 'h_center', 'taskbar', 'hide_lines'])
controls.prev = (30, 'left')
controls.next = (32, 'right')
controls.save = (31, 'enter')
controls.quit = (27, 'esc')
controls.rule_of_thirds = 33
controls.v_center = 34
controls.h_center = 35
controls.taskbar = 20
controls.hide_lines = 18

guideline_controls = (
    controls.rule_of_thirds,
    controls.v_center,
    controls.h_center,
    controls.taskbar
)

presets = [
    # (899, 0, 5523, 2312)
]

img, show_x, show_y, show_w, show_h, full_w, full_h = None, 0, 0, 0, 0, 0, 0
mouse_x, mouse_y = 0, 0
do_render = True

guide_lines_enabled = {control: False for control in guideline_controls}
hide_all_guidelines = False

dir_path = os.path.dirname(in_path)
images = sorted(filter(
    lambda file: os.path.isfile(file) and file.endswith(IMAGE_EXT),
    [os.path.join(dir_path, dir_ent) for dir_ent in os.listdir(dir_path)]
))
cur_image_index = bisect.bisect_left(images, in_path)


def load_image():
    global img, show_x, show_y, show_w, show_h, full_w, full_h
    img = cv.imread(images[cur_image_index])
    full_w, full_h = img.shape[1], img.shape[0]
    show_x, show_y, show_w, show_h = 0, 0, full_w, full_h


def save_image(path):
    cv.imwrite(os.path.join(path, os.path.basename(images[cur_image_index])),
               img[show_y:show_y + show_h, show_x:show_x + show_w])


def is_focused():
    if os.name == 'nt':
        return GetWindowText(GetForegroundWindow()) == WINDOW_NAME


def set_image_index(image_index):
    global cur_image_index, do_render
    if not is_focused():
        return
    if image_index < 0 or image_index >= len(images):
        return
    cur_image_index = image_index
    load_image()
    do_render = True


def handle_mouse_event(event, x, y, flags, _):
    global mouse_x, mouse_y, show_x, show_y, show_w, show_h, do_render
    if not is_focused():
        return

    if event == cv.EVENT_LBUTTONDOWN or event == cv.EVENT_RBUTTONDOWN:
        mouse_x, mouse_y = x, y
        return

    if flags & cv.EVENT_FLAG_LBUTTON:
        show_x = min(max(0, show_x + mouse_x - x), full_w - show_w)
        show_y = min(max(0, show_y + mouse_y - y), full_h - show_h)

    elif flags & cv.EVENT_FLAG_RBUTTON:
        zoom = mouse_x - x
        show_w = min(max(1, show_w + zoom), full_w - show_x)
        show_h = round(show_w * full_h / full_w)
    else:
        return

    mouse_x, mouse_y = x, y
    do_render = True


def toggle_guidelines(scan_code):
    global do_render, hide_all_guidelines
    if not is_focused():
        return
    guide_lines_enabled[scan_code] = not guide_lines_enabled[scan_code]
    hide_all_guidelines = False
    do_render = True


def toggle_hide_lines():
    global do_render, hide_all_guidelines
    if not is_focused():
        return
    hide_all_guidelines = not hide_all_guidelines
    do_render = True


def use_preset(preset_index):
    global do_render, show_x, show_y, show_w, show_h
    if not is_focused():
        return
    show_x, show_y, show_w, show_h = presets[preset_index]
    do_render = True


keyboard.on_press_key(controls.prev, lambda e: set_image_index(cur_image_index - 1))
keyboard.on_press_key(controls.next, lambda e: set_image_index(cur_image_index + 1))
keyboard.on_press_key(controls.save, lambda e: save_image(out_dir))
keyboard.on_press_key(guideline_controls, lambda e: toggle_guidelines(e.scan_code))
keyboard.on_press_key(controls.hide_lines, lambda e: toggle_hide_lines())
for i, preset in enumerate(presets):
    if i > 10:
        break
    print(i + 49)
    keyboard.on_press_key(str((i + 1) % 10), lambda e: use_preset(i))

cv.namedWindow(WINDOW_NAME, cv.WINDOW_NORMAL)
cv.setWindowProperty(WINDOW_NAME, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
cv.setMouseCallback(WINDOW_NAME, handle_mouse_event)

load_image()

while True:
    if do_render:
        render_img = img[show_y:show_y + show_h, show_x:show_x + show_w].copy()

        if not hide_all_guidelines:
            if guide_lines_enabled[controls.rule_of_thirds]:
                line_cord = show_h // 3
                cv.line(render_img, (0, line_cord), (show_w, line_cord), GUIDELINE_COLOR, 3)
                line_cord *= 2
                cv.line(render_img, (0, line_cord), (show_w, line_cord), GUIDELINE_COLOR, 3)
                line_cord = show_w // 3
                cv.line(render_img, (line_cord, 0), (line_cord, show_h), GUIDELINE_COLOR, 3)
                line_cord *= 2
                cv.line(render_img, (line_cord, 0), (line_cord, show_h), GUIDELINE_COLOR, 3)

            if guide_lines_enabled[controls.v_center]:
                line_cord = show_w // 2
                cv.line(render_img, (line_cord, 0), (line_cord, show_h), GUIDELINE_COLOR, 3)

            if guide_lines_enabled[controls.h_center]:
                line_cord = show_h // 2
                cv.line(render_img, (0, line_cord), (show_w, line_cord), GUIDELINE_COLOR, 3)

            if guide_lines_enabled[controls.taskbar]:
                line_cord = show_h * (TASKBAR_RATIO - 1) // TASKBAR_RATIO
                cv.line(render_img, (0, line_cord), (show_w, line_cord), GUIDELINE_COLOR, 3)

        cv.imshow(WINDOW_NAME, render_img)
        do_render = False

    key = cv.waitKey(1)
    if key == controls.quit[0]:
        break
