#!/usr/bin/env python3

import rospy
import rospkg
import json
from tabula_msgs.msg import Recording, AvailableEntities
from std_msgs.msg import Empty
from pipeline import *
import test_parser
import threading

class Controller:

	def __init__(self):
		rospy.init_node("synthesizer", anonymous=True)
		rospy.Subscriber("synthesizer/recording", Recording, self.receive_recording, ())
		self.avail_ent_pub = rospy.Publisher("synthesizer/available_entity_request", Empty, queue_size=10)
		rospy.Subscriber("synthesizer/available_entity_receive", AvailableEntities, self.receive_available_entities, ())
		self.pipeline = Pipeline({"regions": {}})
		print("initialized synthesizer node")

		# init the pipeline with a dummy world and no entities
		# self.pipeline = Pipeline({"regions": {}})

		# state
		self.entities_received = False
		self.entity_request_lock = threading.Lock()

		# begin waiting process for entities
		thread = threading.Thread(target=self.request_available_entities)
		thread.daemon = True		# Daemonize thread
		thread.start()

	def request_available_entities(self):
		while True:
			self.entity_request_lock.acquire()
			received = False
			if self.entities_received:
				received = True
			self.entity_request_lock.release()
			print("Sending request for available entities...")
			msg = Empty()
			self.avail_ent_pub.publish(msg)
			time.sleep(3)
			if received:
				break
		print("Available entities received.")

	def receive_available_entities(self, msg, args):
		print("...receiving entities...")
		self.entity_request_lock.acquire()
		self.entities_received = True
		self.entity_request_lock.release()
		new_avail_ents = {}
		for entity in msg.entities:
			name = entity.name
			categories = entity.categories
			_class = entity.entity_class
			new_avail_ents[name] = {"categories": categories, "class": _class}
		self.pipeline.update_available_entities(new_avail_ents)

	def receive_recording(self, msg, args):
		_, _, world = test_parser.parse()
		print(msg)
		nl = msg.utt;
		traj = [msg.trace]
		raw_world = json.loads(msg.world_json)
		world = {"regions": {}}
		for region in raw_world["serRegions"]:
			name = region["name"]
			world["regions"][name] = {"name": name, "objects": []}
			self.create_world_dict_helper(region["objects"], world["regions"][name]["objects"])
		self.pipeline.reload_world(world)
		self.pipeline.load_user_input(nl, traj)
		self.pipeline.sketch()
		self.pipeline.parse_nl()
		self.pipeline.plan()
		print(self.pipeline.program)

	def create_world_dict_helper(self, raw_objects, objects):
		for obj in raw_objects:
			obj_dict = {"name": obj["name"], "objects": []}
			self.create_world_dict_helper(obj["objects"], obj_dict["objects"])
			objects.append(obj_dict)

if __name__ == "__main__":
	ctrl = Controller()
	rospy.spin()