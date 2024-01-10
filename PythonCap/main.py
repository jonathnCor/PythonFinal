import cv2
import mediapipe as mp
import numpy as np
import rtmidi
from rtmidi.midiconstants import CONTROL_CHANGE
import time

midiout = rtmidi.MidiOut()
midiout.open_port(2)

cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands(static_image_mode=False,
                      max_num_hands=2,
                      min_detection_confidence=0.5,
                      min_tracking_confidence=0.5)
mpDraw = mp.solutions.drawing_utils

# Tempo in seconds
TEMPO = 0.2

# Variables to track the note state and last note
is_note_on = False
last_note = 60


def convert_range(value, in_min, in_max, out_min, out_max):
    l_span = in_max - in_min
    r_span = out_max - out_min
    scaled_value = (value - in_min) / l_span
    scaled_value = out_min + (scaled_value * r_span)
    return int(np.round(scaled_value))


def send_mod(cc=1, value=0):
    mod1 = ([CONTROL_CHANGE | 0, cc, value])
    print(value)
    if value > 0.0:
        midiout.send_message(mod1)


while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    if results.multi_hand_landmarks:
        h, w, c = img.shape
        for hand_landmarks in results.multi_hand_landmarks:
            pink_x = hand_landmarks.landmark[mpHands.HandLandmark.PINKY_TIP].x
            pink_y = hand_landmarks.landmark[mpHands.HandLandmark.PINKY_TIP].y
            if pink_x * w < 540:
                print("Left, MIDI CC DATA")
                v1 = convert_range(pink_y, 1.0, 0.0, 0, 120)
                send_mod(1, v1)
            elif pink_x * w > 540:

                v2 = convert_range(pink_y, 1.0, -1.0, 51, 70)
                if not is_note_on or v2 != last_note:
                    if is_note_on:
                        # Turn off the previous note
                        note_off = [0x80, last_note, 0]
                        midiout.send_message(note_off)
                    # Start the new note
                    note_on = [0x90, v2, 127]
                    midiout.send_message(note_on)
                    is_note_on = True
                    last_note = v2
            mpDraw.draw_landmarks(img, hand_landmarks, mpHands.HAND_CONNECTIONS)
    else:
        if is_note_on:
            print('Right, MIDI Notes Off')
            note_off = [0x80, last_note, 0]
            midiout.send_message(note_off)
            is_note_on = False

    fps = 1
    cv2.putText(img, str(fps), (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (255, 200, 5), 3)
    cv2.imshow("Jonathan", img)
    cv2.waitKey(fps)
