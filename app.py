import RPi.GPIO as GPIO
from flask import Flask, render_template, request
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import serial
import serial.tools.list_ports
import time
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

arduinoPortPrefix = "/dev/ttyUSB"

for i in range (0,3):	
	try:
		ser = serial.Serial(arduinoPortPrefix + str(i), 115200, timeout=1)		
		if (ser.isOpen()):
			break
	except:
		pass
			

roomPins = {
    # define actuators GPIOs
    'room1light': {
        'pin': 27,
        'status': 0,
    },
    'room1fan': {
        'pin': 23, # pin 16 = GPIO23, use pin with no hardware pwm to see the effect of soft pwm
        'status': 0,
        'pwm': 33,
    },
}

for v in roomPins.values():
    GPIO.setup(v['pin'], GPIO.OUT)
    GPIO.output(v['pin'], GPIO.LOW)

# ~ fans = []

# ~ for k, fan in roomPins.items():
    # ~ if 'fan' in k:
        # ~ fanX = GPIO.PWM(fan['pin'], 200)
        # ~ fanX.start(0)
        # ~ fans.append(fanX)

app = Flask(__name__, static_url_path='/static')

def makeTemplateData():
    templateData = {}
    for k, v in roomPins.items():
        templateData[k] = v['status']
    return templateData

@app.route("/")
def index():
    templateData = makeTemplateData()
    return render_template('main.html', **templateData)


@app.route("/<deviceName>/<action>")
def action(deviceName, action):
    actuator = roomPins[deviceName]['pin']

    if action == "on":
        if 'light' in deviceName:
            GPIO.output(actuator, GPIO.HIGH)
        roomPins[deviceName]['status'] = 1
        if 'fan' in deviceName:
            a = int(deviceName[4])-1
            fanvalue = roomPins[deviceName]['pwm']
            # fans[a].ChangeDutyCycle(float(fanvalue))
            ser.write(str.encode(str(fanvalue)))
    elif action == "off":
        if 'light' in deviceName:
            GPIO.output(actuator, GPIO.LOW)
        if 'fan' in deviceName:
            numberstr = deviceName[4]
            i = int(numberstr) - 1
            # fans[i].ChangeDutyCycle(0)
            ser.write(str.encode(str(0)))
        roomPins[deviceName]['status'] = 0
        
    templateData = makeTemplateData()

    return render_template('main.html', **templateData)

@app.route("/fanslider/<string:room>", methods=["POST"])
def fanslider(room):
    numberstr = room[-1]
    # Get slider Values
    slider = request.form["Room_"+numberstr+"_Fan_Slider"]
    # slider = document.getElementById("Room_1_Fan_Slider");
    deviceName = "room"+numberstr+"fan"
    roomPins[deviceName]['pwm'] = slider
    # Change duty cycle
    numberint = int(numberstr)
    i = numberint - 1
    # fans[i].ChangeDutyCycle(float(slider))
    print("slider value = " + slider)
#     fanserialsend = '<' + numberstr + ',' + slider + '>'
    fanserialsend = slider
    # ~ fanserialsend = str(i) + slider
    print(str.encode(fanserialsend))
    ser.write(str.encode(fanserialsend))
#     line = ser.readline().decode('utf-8').rstrip()
#     print(line, file=sys.stderr)
    # Give servo some time to move
    time.sleep(1)
    templateData = makeTemplateData()
    return render_template('main.html', **templateData)

@app.route("/aircon/<string:room>/<string:forName>", methods=["GET"])
def aircon(room, forName):
    if "ON_FAN" in forName:
        forName = forName[:-3]
    print(forName)
    os.system("irsend SEND_ONCE MITSUBISHI "+forName)
    templateData = makeTemplateData()
    return render_template('main.html', **templateData)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
