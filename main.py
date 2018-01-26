import paho.mqtt.client as mqtt
import threading
import time
import random
import os

#Declaration of global constants.
SEND_ATTEMPT = 5 # Number of attempts, before the node decides to send the application in the reverse direction
APP_RUNS_LOCALLY_MIN = 10 #The amount of time each node runs the app locally, before it attempts to forward it to the next node
if 	os.path.basename(__file__) == "MQTT.py":
	NODE_ID = 1 #Node ID, as an integer, one of the unique properties of each node.
elif os.path.basename(__file__) == "MQTT - Kopie.py":
	NODE_ID = 2
elif os.path.basename(__file__) == "MQTT - Kopie (2).py":
	NODE_ID = 3
elif os.path.basename(__file__) == "MQTT - Kopie (3).py":
	NODE_ID = 4
elif os.path.basename(__file__) == "MQTT - Kopie (4).py":
	NODE_ID = 5
elif os.path.basename(__file__) == "MQTT - Kopie (5).py":
	NODE_ID = 6
else:
	NODE_ID = 7
BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on

#Declaration of global variables
client = mqtt.Client()
nodeMasterCounter = 0 #Counter to keep track of elapsed time
nodeIsAwake = True #Each node is assumed to be awake on startup
nodeSleepBeginning = 5 #Node will enter sleep mode after this amount of time has passed, 5 is the default value, will change on each wakeup randomly
nodeSleepDuration = 5 #Node will be asleep for this duration, 5 is the default value, will change on each wakeup randomly
neighbourNodeSleepDuration = -1 #Duration of sleep mode receieved from an adjacent node. -1 by default, until a valid incoming message has been received
if NODE_ID == 1:
	nodeRunsApp = True #This flag determines whether the applicaion is being run on the current node. ONLY ONE node runs the application at any instance of time
else:
	nodeRunsApp = False
globalApplicationState = 0 #Application (a simple counter) starts from 0. This value is an integer
applicationMovesForward = True #App moving direction: 1 -> 2 -> 3
nodeRunsAppLocally = True
applicationLocalCounter = 0
sendAttemptCounter = 0
nodeAwakeTimeCounter = 0 #Used for gathering statistical data about the node
nodeAppRunningTimerCounter = 0 #Used for gathering statistical data about the node


# methods to set the MQTT connection
def on_disconnect(client, userdate, rc):
	print("Subcscriber disconnected...")

def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	client.subscribe("node_comm/" + str(NODE_ID), 0) #Each node subscribes to its own topic, functioning as incoming channel. This topic is used for synchronization of nodes
	client.subscribe("node_comm/app/" + str(NODE_ID), 0) #Each node subscribes to its own topic, functioning as incoming channel. This topic is used for application related data transmission among the nodes


def on_message(client, userdata, msg):
	global neighbourNodeSleepDuration
	global nodeSleepDuration
	global globalApplicationState
	global nodeRunsApp
	global nodeRunsAppLocally
	global applicationMovesForward
	global applicationLocalCounter
	global sendAttemptCounter
	if(msg.topic == "node_comm/" + str(NODE_ID)): ##################NOde sync messages
		decodedData = bytes.decode(msg.payload) #Decoded MQTT message, need parsing
		#print(decodedData)
		#Beginning of message parser
		if decodedData[0] == '$': #Check the first character of the incoming message for consistancy
			decodedData=decodedData[1:] #Remove the first character from the string
		dataList=decodedData.split(",") #dataList=[<Neighbour Node ID>,<Neighbour Node Sleep Duration]
		#End of parser
		if neighbourNodeSleepDuration == -1 and nodeMasterCounter >= 4 and nodeIsAwake == True: #If the node has not yet received a schedule from a neighbour node AND the node has been awake for at least 2 seconds
			neighbourNodeSleepDuration = dataList[1]
			nodeSleepDuration = neighbourNodeSleepDuration
			nodeSleep(nodeSleepDuration)
	elif (msg.topic == "node_comm/app/" + str(NODE_ID)): ###################App forward messages
		if nodeIsAwake == True:
			decodedData = bytes.decode(msg.payload) #Decoded MQTT message, need parsing
			#Beginning of message parser
			if decodedData[0] == '%': #Check the first character of the incoming message for consistancy
				decodedData=decodedData[1:] #Remove the first character from the string
			dataList=decodedData.split(",") #dataList=[<Neighbour Node ID (incoming message)>,<Global app state>]
			#End of parser
			print("Receiving from " + str(dataList[0]))
			if nodeRunsApp == False: #Incoming message from the node currently running the app
				globalApplicationState = int(dataList[1])
				nodeRunsAppLocally = True
				applicationLocalCounter = 0
				nodeRunsApp = True
				if int(dataList[0]) < int(NODE_ID):
					sendApplicationMessage("%" + str(NODE_ID) + "," + str(dataList[1]), False)
					applicationMovesForward = True
				else:
					sendApplicationMessage("%" + str(NODE_ID) + "," + str(dataList[1]), True)
					if NODE_ID != 1:
						applicationMovesForward = False
					else:
						applicationMovesForward = True
			else: #Node is running the app. Incoming message from the NEW node running the app
				nodeRunsApp = False # Hand off successfull
				sendAttemptCounter = 0


def mqttSubscriber():	
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect(BROKER_IP,1883,60)
	client.loop_forever()

def sendDebugData():
	#All nodes publish debug information to this channel, but NONE of the nodes subscribes to it
	global nodeAwakeTimeCounter
	global nodeAppRunningTimerCounter
	while True:
		if nodeIsAwake == True:
			nodeAwakeTimeCounter += 1
		if nodeRunsApp == True:
			nodeAppRunningTimerCounter += 1
		client.publish("debug_channel/stats/" + str(NODE_ID), str(nodeAwakeTimeCounter) + "," + str(nodeAppRunningTimerCounter))
		if nodeIsAwake == True:
			client.publish("debug_channel/status/" + str(NODE_ID), "Awake")
		else:
			client.publish("debug_channel/status/" + str(NODE_ID), "Asleep")
		if nodeRunsApp == True:
			client.publish("debug_channel/application/" + str(NODE_ID) , "Running")
		else:
			client.publish("debug_channel/application/" + str(NODE_ID), "-------")
		if nodeRunsApp == True:
			client.publish("debug_channel/application_state", str(NODE_ID) + "," + str(globalApplicationState))
		time.sleep(1)


def nodeSleep(sleepDuration):
	global nodeMasterCounter
	global nodeIsAwake
	nodeMasterCounter = 0
	sendMessageToAdjacentNodes("$" + str(NODE_ID) + "," + str(sleepDuration)) #Message format: "$<NODE_ID>,<sleepDuration>"
	nodeIsAwake = False #Node goes to sleep

def nodeWakeup():
	global nodeMasterCounter
	global nodeIsAwake
	global neighbourNodeSleepDuration
	global nodeSleepBeginning
	global nodeSleepDuration
	nodeSleepBeginning = random.randint(3,10)
	nodeSleepDuration = random.randint(7,15)
	neighbourNodeSleepDuration = -1
	nodeMasterCounter = 0
	nodeIsAwake = True #Node awakens

def sendMessageToAdjacentNodes(msg): #For sending synchronization messages
	if NODE_ID == 1:
		client.publish("node_comm/2", msg)
	else:
		client.publish("node_comm/" + str(NODE_ID-1), msg)
		client.publish("node_comm/" + str(NODE_ID+1), msg)

def sendApplicationMessage(msg, direction): #For sending application related messages, e.g. the app state, direction: application moving direction
	if nodeIsAwake == True and nodeRunsApp == True:
		if direction == True:
			client.publish("node_comm/app/" + str(NODE_ID+1), msg)
			print ("Sending to " + str(NODE_ID+1))
		else:
			client.publish("node_comm/app/" + str(NODE_ID-1), msg)
			print("Sending to " + str(NODE_ID-1))

def forwardApplication():
	global applicationMovesForward
	global globalApplicationState
	sendApplicationMessage("%" + str(NODE_ID) + "," + str(globalApplicationState), applicationMovesForward)
    
    
def nodeApplication(): ####### Each node runs the application here, on a separate thread ########
	global nodeRunsApp
	global globalApplicationState
	global sendAttemptCounter
	global applicationLocalCounter #Keeps track of the locally-run application
	applicationLocalCounter = 0
	global nodeRunsAppLocally #At first, each node runs the app locally, until the counter has reached 5, then will try to hand the application off
	nodeRunsAppLocally = True
	attemptDelayCounter = 0 #Used to avoid multiple attempts to forward the application
	global applicationMovesForward
	while True:
		if nodeRunsApp == True:
			globalApplicationState += 1
			applicationLocalCounter += 1
			attemptDelayCounter += 1
			if nodeRunsAppLocally == False and nodeIsAwake == True and attemptDelayCounter >=3: #Node TRYS to hand the application off to the next node
				forwardApplication()
				sendAttemptCounter += 1
				attemptDelayCounter = 0
			if sendAttemptCounter > SEND_ATTEMPT and NODE_ID != 1:
				applicationMovesForward = not applicationMovesForward
				sendAttemptCounter = 0
		if applicationLocalCounter > APP_RUNS_LOCALLY_MIN:
			nodeRunsAppLocally = False
		time.sleep(1)

t1 = threading.Thread(target=mqttSubscriber, args=())
t2 = threading.Thread(target=nodeApplication, args=())
t3 = threading.Thread(target=sendDebugData, args=())
t1.daemon = True
t2.daemon = True
t3.daemon = True
t1.start()
t2.start()
t3.start()



#########################################################
#Variable definition/initialization for the main loop
#########################################################

nodeMasterCounter = 0 #Counter to keep track of elapsed time


while True: #Main loop, main thread
	if nodeIsAwake == True and nodeMasterCounter >= (int(nodeSleepBeginning) * 2): #Each second will be 2 counter increments
		nodeSleep(nodeSleepDuration) #Node initiates its sleep routine
	if nodeIsAwake == False and nodeMasterCounter >= (int(nodeSleepDuration) *2):
		nodeWakeup() #Node initiates its wakeup routine
	nodeMasterCounter += 1
	#print(nodeMasterCounter) #For debug purposes, will be omitted later on
	os.system('cls')
	print ("Node " + str(NODE_ID))
	print ("nodeRunsApp: " + str(nodeRunsApp))
	print ("appMovesForward: " + str(applicationMovesForward))
	time.sleep(0.5)
