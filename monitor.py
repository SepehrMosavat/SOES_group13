###########################################################################################################
# This snippet is intended to be used with the main project files for monitoring/debugging purposes only. #
# This is NOT part of the actual project.																  #
###########################################################################################################

import paho.mqtt.client as mqtt
import threading
import time
import os


BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on
NODE_TIMEOUT_PERIOD = 1 #In seconds
client = mqtt.Client()
nodeOneStatus="N/A"
nodeTwoStatus="N/A"
nodeThreeStatus="N/A"
nodeOneTimeoutCounter = 0
nodeTwoTimeoutCounter = 0
nodeThreeTimeoutCounter = 0
nodeOneRunsApp = "-------"
nodeTwoRunsApp = "-------"
nodeThreeRunsApp = "-------"
	
def on_disconnect(client, userdate, flags, rc):
	print("Subcscriber disconnected...")

def on_connect(client, userdata, flags, rc):
	#print("Connected with result code " + str(rc))
	client.subscribe("debug_channel/1", 0)
	client.subscribe("debug_channel/2", 0)
	client.subscribe("debug_channel/3", 0)

def on_message(client, userdata, msg):
	decodedData = bytes.decode(msg.payload) #Decoded MQTT message, need parsing
	global nodeOneStatus
	global nodeTwoStatus
	global nodeThreeStatus
	global nodeOneTimeoutCounter
	global nodeTwoTimeoutCounter
	global nodeThreeTimeoutCounter
	global nodeOneRunsApp
	global nodeTwoRunsApp
	global nodeThreeRunsApp
	if decodedData == "N1W":
		nodeOneStatus = "Awake"
		nodeOneTimeoutCounter = 0
	elif decodedData == "N1S":
		nodeOneStatus = "Asleep"
		nodeOneTimeoutCounter = 0
	if decodedData == "N2W":
		nodeTwoStatus = "Awake"
		nodeTwoTimeoutCounter = 0
	elif decodedData == "N2S":
		nodeTwoStatus = "Asleep"
		nodeTwoTimeoutCounter = 0
	if decodedData == "N3W":
		nodeThreeStatus = "Awake"
		nodeThreeTimeoutCounter = 0
	elif decodedData == "N3S":
		nodeThreeStatus = "Asleep"
		nodeThreeTimeoutCounter = 0
	if decodedData == "N1AT":
		nodeOneRunsApp = "Running"
	elif decodedData == "N1AF":
		nodeOneRunsApp = "-------"
	if decodedData == "N2AT":
		nodeTwoRunsApp = "Running"
	elif decodedData == "N2AF":
		nodeTwoRunsApp = "-------"
	if decodedData == "N3AT":
		nodeThreeRunsApp = "Running"
	elif decodedData == "N3AF":
		nodeThreeRunsApp = "-------"

	
	
	
def mqttSubscriber():	
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect(BROKER_IP,1883,60)
	client.loop_forever()

t1 = threading.Thread(target=mqttSubscriber, args=())
t1.daemon = True
t1.start()

while True:
	os.system('cls')
	print("Node 1:\t\t Node2:\t\t Node 3:")
	print(nodeOneStatus + "\t\t " + nodeTwoStatus + "\t\t " + nodeThreeStatus + "\t\t")
	print("========================================")
	print(nodeOneRunsApp + "\t\t " + nodeTwoRunsApp + "\t " + nodeThreeRunsApp + "\t\t")
	if nodeOneTimeoutCounter > (NODE_TIMEOUT_PERIOD * 5):
		nodeOneStatus = "N/A"
		nodeOneRunsApp = "-------"
	if nodeTwoTimeoutCounter > (NODE_TIMEOUT_PERIOD * 5):
		nodeTwoStatus = "N/A"
		nodeTwoRunsApp = "-------"
	if nodeThreeTimeoutCounter > (NODE_TIMEOUT_PERIOD * 5):
		nodeThreeStatus = "N/A"
		nodeThreeRunsApp = "-------"
	nodeOneTimeoutCounter += 1
	nodeTwoTimeoutCounter +=1
	nodeThreeTimeoutCounter += 1
	time.sleep(0.2)
