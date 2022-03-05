#!/usr/bin/env python3

import rospy
import rospkg
from tabula_msgs.msg import Recording
from pipeline import *
import test_parser

class Controller:

	def __init__(self):
		rospy.init_node("synthesizer", anonymous=True)
		rospy.Subscriber("synthesizer/recording", Recording, self.receive_recording, ())
		self.pipeline = Pipeline()
		print("initialized synthesizer node")

	def receive_recording(self, msg, args):
		_, _, world = test_parser.parse()
		print(msg)
		nl = msg.utt;
		traj = [msg.trace]
		pipeline = Pipeline()
		pipeline.load_user_input(nl, traj)
		pipeline.load_world(world)
		pipeline.sketch()
		pipeline.parse_nl()
		pipeline.plan()
		print(pipeline.program)


if __name__ == "__main__":
	ctrl = Controller()
	rospy.spin()