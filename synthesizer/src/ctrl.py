#!/usr/bin/env python3

import rospy
import rospkg
from tabula_msgs.msg import Recording
from pipeline import *

class Controller:

	def __init__(self):
		rospy.init_node("synthesizer", anonymous=True)
		rospy.Subscriber("synthesizer/recording", Recording, self.receive_recording)
		self.pipeline = Pipeline()
		print("initialized synthesizer node")

	def receive_recording(self, msg, args):
		print("received recording")


if __name__ == "__main__":
	ctrl = Controller()
	rospy.spin()