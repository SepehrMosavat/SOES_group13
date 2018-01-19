import paho.mqtt.client as mqtt
import threading
import time

NODE_ID = 1 #Node ID, as an integer, one of the unique properties of each node.
BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on
NODE_IS_AWAKE = True #Each node is assumed to be awake on startup
client = mqtt.Client()


# methods to set the MQTT connection
def on_disconnect(client, userdate, flags, rc):
	print("Subcscriber disconnected...")

def on_connect(client, userdata, flags, rc):
	print("Connected with result code " + str(rc))
	if NODE_ID == 1:
		client.subscribe("node_comm/2", 0) #node 1 connects only to node 2
	else: #other node connect to the two adjacent nodes
		client.subscribe("node_comm/" + str(NODE_ID-1), 0)
		client.subscribe("node_comm/" + str(NODE_ID+1), 0)

def on_message(client, userdata, msg):
	global current_state
	
def mqttSubscriber():	
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect(BROKER_IP,1883,60)
	client.loop_forever()

def sendDebugData():
	#All nodes publish debug information to this channel, but NONE of the nodes subscribes to it
	if NODE_IS_AWAKE == True:
		client.publish("debug_channel/", "Node " + str(NODE_ID) + " awake!")
	else:
		client.publish("debug_channel/", "Node " + str(NODE_ID) + " asleep!")

t1 = threading.Thread(target=mqttSubscriber, args=())
t1.daemon = True
t1.start()

#########################################################
#Variable definition and initialization for the main loop
#########################################################

nodeMasterCounter = 0 #Counter to keep track of elapsed time
nodeSleepBeginning = 5 #Node will enter sleep mode after this amount of time has passed
nodeSleepDuration = 3 #Node will be asleep for this duration
while True: #Main loop, main thread
	sendDebugData()
	if NODE_IS_AWAKE == True and nodeMasterCounter == (nodeSleepBeginning * 2): #Each second will be 2 counter increments
		nodeMasterCounter = 0
		NODE_IS_AWAKE = False #Node goes to sleep
	if NODE_IS_AWAKE == False and nodeMasterCounter == (nodeSleepDuration *2):
		nodeMasterCounter = 0
		NODE_IS_AWAKE = True #Node awakens
	nodeMasterCounter += 1
	print(nodeMasterCounter) #For debug purposes, will be omitted later on
	time.sleep(0.5)
