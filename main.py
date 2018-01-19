import paho.mqtt.client as mqtt
import threading
import time

NODE_ID = 1 #node ID, as an integer, one of the unique properties of each node.
BROKER_IP = "localhost" #MIGHT need to be changed according to the IP address of the machine the code is running on

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
	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_message = on_message
	client.on_disconnect = on_disconnect
	client.connect(BROKER_IP,1883,60)
	client.loop_forever()

t1 = threading.Thread(target=mqttSubscriber, args=())
t1.daemon = True
t1.start()
while True:
	client = mqtt.Client()
	client.connect(BROKER_IP,1883,60)
	client.publish("debug_channel/", "Node " + str(NODE_ID) + " alive!") #All nodes publish debug information to this channel, but NONE of the nodes subscribe to it
	time.sleep(1)
