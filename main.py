import paho.mqtt.client as mqtt
import threading
import time
import random

#Declaration of global constants.
NODE_ID = 1 #Node ID, as an integer, one of the unique properties of each node.
BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on

#Declaration of global variables
client = mqtt.Client()
nodeMasterCounter = 0 #Counter to keep track of elapsed time
nodeIsAwake = True #Each node is assumed to be awake on startup
nodeSleepBeginning = 5 #Node will enter sleep mode after this amount of time has passed, 5 is the default value, will change on each wakeup randomly
nodeSleepDuration = 5 #Node will be asleep for this duration, 5 is the default value, will change on each wakeup randomly
neighbourNodeSleepDuration = -1 #Duration of sleep mode receieved from an adjacent node. -1 by default, until a valid incoming message has been received
nodeRunsApp = True #This flag determines whether the applicaion is being run on the current node. ONLY ONE node runs the application at any instance of time
globalApplicationState = 0 #Application (a simple counter) starts from 0. This value is an integer


# methods to set the MQTT connection
def on_disconnect(client, userdate, flags, rc):
	print("Subcscriber disconnected...")

def on_connect(client, userdata, flags, rc):
	#print("Connected with result code " + str(rc))
	client.subscribe("node_comm/" + str(NODE_ID), 0) #Each node subscribes to its own topic, functioning as incoming channel. This topic is used for synchronization of nodes
	client.subscribe("node_comm/app/" + str(NODE_ID), 0) #Each node subscribes to its own topic, functioning as incoming channel. This topic is used for application related data transmission among the nodes


def on_message(client, userdata, msg):
	global neighbourNodeSleepDuration
	decodedData = bytes.decode(msg.payload) #Decoded MQTT message, need parsing
	#Beginning of message parser
	if decodedData[0] == '$': #Check the first character of the incoming message for consistancy
		decodedData=decodedData[1:] #Remove the first character from the string
	dataList=decodedData.split(",") #dataList=[<Neighbour Node ID>,<Neighbour Node Sleep Duration]
	#End of parser
	if neighbourNodeSleepDuration == -1 and nodeMasterCounter >=6: #If the node has not yet received a schedule from a neighbour node AND the node has been awake for at least 3 seconds
		neighbourNodeSleepDuration = dataList[1]
		nodeSleepDuration = neighbourNodeSleepDuration
		nodeSleep(nodeSleepDuration)
	
def mqttSubscriber():	
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect(BROKER_IP,1883,60)
	client.loop_forever()

def sendDebugData():
	#All nodes publish debug information to this channel, but NONE of the nodes subscribes to it
	if nodeIsAwake == True:
		client.publish("debug_channel/" + str(NODE_ID), "N" + str(NODE_ID) + "W")
	else:
		client.publish("debug_channel/" + str(NODE_ID), "N" + str(NODE_ID) + "S")
	if nodeRunsApp == True:
		client.publish("debug_channel/" + str(NODE_ID), "N" + str(NODE_ID) + "AT")
	else:
		client.publish("debug_channel/" + str(NODE_ID), "N" + str(NODE_ID) + "AF")


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
	nodeSleepDuration = random.randint(5,10)
	#print("$$$$$$$$$$",nodeSleepBeginning, nodeSleepDuration)
	neighbourNodeSleepDuration = -1
	nodeMasterCounter = 0
	nodeIsAwake = True #Node awakens
	
def sendMessageToAdjacentNodes(msg): #For sending synchronization messages
	if NODE_ID == 1:
		client.publish("node_comm/2", msg)
	else:
		client.publish("node_comm/" + str(NODE_ID-1), msg)
		client.publish("node_comm/" + str(NODE_ID+1), msg)
		
def sendApplicationMessage(msg): #For sending application related messages, e.g. the app state
	if NODE_ID == 1:
		client.publish("node_comm/app/2", msg)
	else:
		client.publish("node_comm/app/" + str(NODE_ID-1), msg)
		client.publish("node_comm/app/" + str(NODE_ID+1), msg)

def nodeApplication(): ####### Each node runs the application here, on a separate thread ########
	global nodeRunsApp
	global globalApplicationState

t1 = threading.Thread(target=mqttSubscriber, args=())
t2 = threading.Thread(target=nodeApplication, args=())
t1.daemon = True
t2.daemon = True
t1.start()
t2.start()

#########################################################
#Variable definition/initialization for the main loop
#########################################################

nodeMasterCounter = 0 #Counter to keep track of elapsed time


while True: #Main loop, main thread
	sendDebugData()
	if nodeIsAwake == True and nodeMasterCounter == (nodeSleepBeginning * 2): #Each second will be 2 counter increments
		nodeSleep(nodeSleepDuration) #Node initiates its sleep routine
	if nodeIsAwake == False and nodeMasterCounter == (nodeSleepDuration *2):
		nodeWakeup() #Node initiates its wakeup routine
	nodeMasterCounter += 1
	print(nodeMasterCounter) #For debug purposes, will be omitted later on
	time.sleep(0.5)
		client.publish("debug_channel/" + str(NODE_ID), "Node " + str(NODE_ID) + " awake!")
	else:
		client.publish("debug_channel/" + str(NODE_ID), "Node " + str(NODE_ID) + " asleep!")

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
	nodeSleepDuration = random.randint(5,10)
	print("$$$$$$$$$$",nodeSleepBeginning, nodeSleepDuration)
	neighbourNodeSleepDuration = -1
	nodeMasterCounter = 0
	nodeIsAwake = True #Node awakens
	
def sendMessageToAdjacentNodes(msg):
	if NODE_ID == 1:
		client.publish("node_comm/2", msg)
	else:
		client.publish("node_comm/" + str(NODE_ID-1), msg)
		client.publish("node_comm/" + str(NODE_ID+1), msg)


t1 = threading.Thread(target=mqttSubscriber, args=())
t1.daemon = True
t1.start()

#########################################################
#Variable definition/initialization for the main loop
#########################################################

nodeMasterCounter = 0 #Counter to keep track of elapsed time


while True: #Main loop, main thread
	sendDebugData()
	if nodeIsAwake == True and nodeMasterCounter == (nodeSleepBeginning * 2): #Each second will be 2 counter increments
		nodeSleep(nodeSleepDuration) #Node initiates its sleep routine
	if nodeIsAwake == False and nodeMasterCounter == (nodeSleepDuration *2):
		nodeWakeup() #Node initiates its wakeup routine
	nodeMasterCounter += 1
	print(nodeMasterCounter) #For debug purposes, will be omitted later on
	time.sleep(0.5)
