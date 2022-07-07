from program import *


class SimpleSketcher:

	def __init__(self):
		pass

	def sketch(self, trajectory):
		prog = Program()
		prev_wp_label = None
		for wp_label in trajectory:
			prog.add_waypoint_from_trace(wp_label, prev_wp_label)
			prev_wp_label = wp_label
		return prog