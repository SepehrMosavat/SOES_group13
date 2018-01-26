###########################################################################################################
# This snippet is intended to be used with the main project files for monitoring/debugging purposes only. #
# This is NOT part of the actual project.																  #
###########################################################################################################

import paho.mqtt.client as mqtt
import threading
import time
import os
from colorama import init
init()
from colorama import Fore, Back, Style


BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on
NODE_TIMEOUT_PERIOD = 1 #In seconds
LINE_STRING = "================================================================================================================"
client = mqtt.Client()
nodeStatus = ["N/A"] * 6
nodeTimeOutCounter = [0] * 6
nodeRunsApp = [Back.YELLOW + Fore.WHITE + "-------" + Style.RESET_ALL] * 6
nodeAwakeTime = [0] * 6
nodeAppRunTime = [0] * 6
globalApplicationState = "-------,0"
	
def on_disconnect(client, userdate, flags, rc):
	print("Subcscriber disconnected...")

def on_connect(client, userdata, flags, rc):
	#print("Connected with result code " + str(rc))
	client.subscribe("debug_channel/#", 0)

def on_message(client, userdata, msg):
	global nodeStatus
	global nodeTimeOutCounter
	global nodeRunsApp
	global nodeAwakeTime
	global nodeAppRunTime
	global globalApplicationState
	tempString = ""
	decodedData = bytes.decode(msg.payload) #Decoded MQTT message, need parsing
	msgTopicList = msg.topic.split('/')
	if msgTopicList[1] == "status":
		if decodedData == "Awake":
			tempString = Fore.GREEN + decodedData + Style.RESET_ALL
		else:
			tempString = Fore.RED + decodedData + Style.RESET_ALL
		nodeStatus[int(msgTopicList[2])] = tempString
		nodeTimeOutCounter[int(msgTopicList[2])] = 0
	elif msgTopicList[1] == "application":
		if decodedData == "Running":
			tempString = Back.BLUE + Fore.WHITE + decodedData + Style.RESET_ALL
		else:
			tempString = ""
		nodeRunsApp[int(msgTopicList[2])] = tempString
		nodeTimeOutCounter[int(msgTopicList[2])] = 0
	elif msgTopicList[1] == "application_state":
		globalApplicationState = decodedData
	elif msgTopicList[1] == "stats":
		statsDataList = decodedData.split(',')
		nodeAwakeTime[int(msgTopicList[2])] = statsDataList[0]
		nodeAppRunTime[int(msgTopicList[2])] = statsDataList[1]

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
	tempString = ""
	for i in range(1,6):
		tempString += Back.WHITE + Fore.BLACK + "Node" + str(i) + ":\t\t\t" + Style.RESET_ALL
	print(tempString + "\n")
	tempString = ""
	for i in range(1,6):
		tempString += (nodeStatus[i] + "\t\t\t")
	print(tempString)
	print(LINE_STRING)
	tempString = ""
	for i in range(1,6):
		tempString += (nodeRunsApp[i] + "\t\t\t")
	print(tempString)
	print(LINE_STRING)
	tempString = ""
	for i in range(1,6):
		tempString += "Awake Time:\t\t"
	print(tempString)
	tempString = ""
	for i in range(1,6):
		if int(globalApplicationState.split(',')[1]) == 0:
			percentTempString = "N/A"
		else:
			percentTempString = int((int(nodeAwakeTime[i])/int(globalApplicationState.split(',')[1])*100))
		tempString += (str(nodeAwakeTime[i]) + " (" + str(percentTempString) + " %)" + "\t\t")
	print(tempString)
	print(LINE_STRING)
	tempString = ""
	for i in range(1,6):
		tempString += "App Time:\t\t"
	print(tempString)
	tempString = ""
	for i in range(1,6):
		if int(globalApplicationState.split(',')[1]) == 0:
			percentTempString = "N/A"
		else:
			percentTempString = int((int(nodeAppRunTime[i])/int(globalApplicationState.split(',')[1])*100))
		tempString += (str(nodeAppRunTime[i]) + " (" + str(percentTempString) + " %)" + "\t\t")
	print(tempString)
	print(LINE_STRING)
	print("Node " + str(globalApplicationState.split(',')[0]) + " ==> " + str(globalApplicationState.split(',')[1]))
	for i in range(1,6):
		if nodeTimeOutCounter[i] > (NODE_TIMEOUT_PERIOD):
			nodeStatus[i] = "N/A"
			nodeRunsApp[i] = Back.YELLOW + Fore.WHITE + "-------" + Style.RESET_ALL
		nodeTimeOutCounter[i] += 1
	time.sleep(1)
