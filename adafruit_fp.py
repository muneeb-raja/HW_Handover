import time
import board
import busio
from digitalio import DigitalInOut, Direction
import adafruit_fingerprint
import serial
import pyaudio
import wave
import requests
import time
from random import randint
import math
import json
import os
import contextlib
import cv2
import sys

## FP Init

uart = serial.Serial("/dev/ttyS0", baudrate=57600, timeout=10)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

## Audio Init
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

## POST Request Init
# defining the api-endpoint
API_ENDPOINT = 'http://175.107.242.90:5007/api/conversation/save'

## Camera Init
# Load the cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

##################################################

def record_audio(audio_length):
    """Record Audio of audio_length secs and then save it"""
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK, exception_on_overflow = False)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    return 1

#################################################
def send_postRequest():
    d_ID = 120
    d_CNIC = randint(100000000000, 9999999999999)
    d_date = math.trunc(time.time())
    d_time = math.trunc(time.time())
    d_convID = int( str(d_time) + str(randint(100, 999)))
    d_filetype = 'wav'
    d_filesize = os.stat('/home/pi/projects/fingerprint307/output.wav').st_size

    fname = '/home/pi/projects/fingerprint307/output.wav'
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        d_duration = duration

    d_convfilepath = 'testtesttest.com/dummy'

    # data to be sent to api
    data = {'id':d_ID,
            'cnic':d_CNIC,
            'date':d_date,
            'time':d_time,
            'conversation_id':d_convID,
            'file_type':d_filetype,
            'file_size':d_filesize,
            'duration':d_duration,
            'conversation_file_path':d_convfilepath,
            'branch_code':112,
            'branch_address':'Islamabad',
            'status':'Active'
    }
    print(data)

    headers = {'content-type' : 'application/json', 'Accept': 'text/plain'}

    # sending post request and saving response as response object
    r = requests.post(url = API_ENDPOINT, json=data)

    # extracting response text
    pastebin_url = r.text
    print("The pastebin URL is:%s"%pastebin_url)

    #print("%s"%r.request.headers)


################################################
def detect_face(cpt):
    # To capture video from webcam.
    try:
        cap = cv2.VideoCapture(0)
    except:
        print("problem opening input stream")
        sys.exit(1)

    print("Capturing image: " , cpt)
    ret, img = cap.read()
    # Convert to grayscale
    if not ret:
        print('sys.exit')
        sys.exit(0)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Detect the faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    print(faces)
    # Draw the rectangle around each face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
    # Display
    #cv2.imshow('img', img)
        cv2.imwrite("image%04i.jpg" %cpt, img)
        cpt +=1
        cap.release()
        return 1
    # Release the VideoCapture object
    cap.release()
    return 0

################################################

## Super-loop
cpt = 0
while True:
    something_detected_or_not = False
    # Wait for finger or face
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")

            print("Templating...", end="", flush=True)
            i = finger.image_2_tz(1)

            if i == adafruit_fingerprint.OK:
                print("Templated")

            something_detected_or_not = True
            break
        if i == adafruit_fingerprint.NOFINGER:
            print(".", end="", flush=True)
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")

        if detect_face(cpt):
            cpt += 1
            something_detected_or_not = True
            break

    if something_detected_or_not == True:
        recording_result = record_audio(10)
        send_postRequest()
        something_detected_or_not = False


###################################################
def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# pylint: disable=too-many-branches
def get_fingerprint_detail():
    """Get a finger print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    print("Getting image...", end="", flush=True)
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No finger detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")
        return False

    print("Templating...", flush=True)
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

    print("Searching...", end="", flush=True)
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    if i == adafruit_fingerprint.OK:
        print("Found fingerprint!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        else:
            print("Other error")
        return False


# pylint: disable=too-many-statements
def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="", flush=True)
        else:
            print("Place same finger again...", end="", flush=True)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="", flush=True)
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="", flush=True)
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="", flush=True)
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True


##################################################


def get_num():
    """Use input() to get a valid number from 1 to 127. Retry till success!"""
    i = 0
    while (i > 127) or (i < 1):
        try:
            i = int(input("Enter ID # from 1-127: "))
        except ValueError:
            pass
    return i


while True:
    print("----------------")
    if finger.read_templates() != adafruit_fingerprint.OK:
        raise RuntimeError("Failed to read templates")
    print("Fingerprint templates:", finger.templates)
    print("e) enroll print")
    print("f) find print")
    print("d) delete print")
    print("----------------")
    c = input("> ")

    if c == "e":
        enroll_finger(get_num())
    if c == "f":
        if get_fingerprint():
            print("Detected #", finger.finger_id, "with confidence", finger.confidence)
        else:
            print("Finger not found")
    if c == "d":
        if finger.delete_model(get_num()) == adafruit_fingerprint.OK:
            print("Deleted!")
        else:
            print("Failed to delete")

