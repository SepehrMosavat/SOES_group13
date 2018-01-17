import paho.mqtt.client as mqtt
import threading
import pyowm
import time
import numpy as np
import matplotlib.pyplot as plt

humidity = 0
temperature = 0
forecastData = "N/A"

def on_disconnect(client, userdate, flags, rc):
	print("Subcscriber disconnected...")
	
def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe("topic/data", 0)
	
def on_message(client, userdata, msg):
	global humidity
	global temperature
	decodedData = bytes.decode(msg.payload)
	#print (decodedData)
	dataList=decodedData.split("\r\n")
	dataValue=float(dataList[0])
	if dataValue < 110:
		humidity = dataValue
	else:
		temperature = dataValue
	#print (str(humidity) + "  " + str(temperature))
	#print(float(dataList[0]))
	
def getWeatherForcast():
	global humidity
	global temperature
	global forecastData
	owm = pyowm.OWM(API_key='02d763427c81b5e9f9b2b17f5d28a1f7')
	observation = owm.weather_at_place('Duisburg,de')
	frcst = owm.daily_forecast('Duisburg,de',limit=1)
	while True:
		fc = frcst.get_forecast()
		for weather in fc:
			#print(weather.get_reference_time('iso'),weather.get_status())
			#print (weather.get_status())
			forecastData = weather.get_status()
			print("Soil Humidity: " + str(humidity) + ",Soil Temperature: " + str(temperature) + ", Weather Forcast: " + forecastData);	
		time.sleep(100)
		
def mqttSubscriber():	
	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect("169.254.107.4",1883,60) #169.254.107.4
	client.loop_forever()
	
def plotTemp():
	global temperature
	global humidity
	plt.suptitle("Temperature & Humidity")
	plt.axis([0, 1000, 0, 350])
	plt.ion()
	for i in range (1000):
		plt.scatter(i, temperature)
		plt.scatter(i, humidity)
		plt.pause(6)
		
def logicFunction():
	global temperature
	global humidity
	global forecastData	
	irrigationFlag = 0
	logFile = open ("log.txt", "a")
	client = mqtt.Client()
	client.connect("169.254.107.4",1883,60)
	while True:
		if forecastData == "Rain":
			print("The weather will be rainy, there will be no irrigation")
			logFile = open ("log.txt", "a")
			logFile.write(time.strftime("%d.%m.%Y @ %H:%M:%S: ") + "The weather will be rainy, there will be no irrigation\n")
			logFile.close()
		else:
			if (temperature > 275 and humidity < 50 and irrigationFlag == 0):
				client.publish("topic/command", "1")
				irrigationFlag = 1
				print("Irrigation started...")
				logFile = open ("log.txt", "a")
				logFile.write(time.strftime("%d.%m.%Y @ %H:%M:%S: ") + "Irrigation started...\n")
				logFile.close()
			elif ( (temperature < 275 or humidity > 50 ) and irrigationFlag == 1):
				client.publish("topic/command", "0")
				irrigationFlag = 0
				print("Irrigation stopped...")
				logFile = open ("log.txt", "a")
				logFile.write(time.strftime("%d.%m.%Y @ %H:%M:%S: ") + "Irrigation stopped...\n")
				logFile.close()
			else:
				print("Current Temp: " + str(temperature) + ", Current Humidity: " + str(humidity) + ", Weather: " + forecastData + "              -- Standing by--")
				logFile = open ("log.txt", "a")
				logFile.write(time.strftime("%d.%m.%Y @ %H:%M:%S: ") + "Current Temp: " + str(temperature) + ", Current Humidity: " + str(humidity) + ", Weather: " + forecastData + "              -- Standing by--\n")
				logFile.close()
		time.sleep(5)
	client.disconnect()
	logFile.close()
	
t1 = threading.Thread(target=getWeatherForcast, args=())
t2 = threading.Thread(target=mqttSubscriber, args=())
t3 = threading.Thread(target=plotTemp, args=())
t4 = threading.Thread(target=logicFunction, args=())
t1.daemon = True
t2.daemon = True
t3.daemon = True
t4.daemon = True
t1.start()
t2.start()
t3.start()
t4.start()
while True:
	time.sleep(1)