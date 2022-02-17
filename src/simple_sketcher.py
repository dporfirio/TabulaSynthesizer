from program import *


class SimpleSketcher:

	def __init__(self):
		pass

	def sketch(self, trajectories):
		prog = Program()
		for trajectory in trajectories:
			for wp_label in trajectory:
				prog.add_waypoint(wp_label)
		return prog