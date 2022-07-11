class RobotState:

	def __init__(self):
		self.init_state = {
			"carryingItem": False,
			"currentLocation": "home base",
			"canTravel": True
		}


class Program:

	def __init__(self):
		self.reset()

	def reset(self):
		self.ltl_properties = []
		self.recordings = []
		self.main_recording = None

	def get_recordings(self):
		return self.recordings

	def add_recording(self, recording):
		'''
		Purpose of this method is to add a recording to the program.
		In doing so, the program itself is updated.
		'''
		self.recordings.append(recording)
		if self.main_recording is None:
			self.main_recording = recording
		print(self)

	def write_result(self, path):
		s = str(self)
		with open(path, "w") as outfile:
			outfile.write(s)

	def __str__(self):
		s = ""
		for recording in self.recordings:
			sketch = recording.plan
			s += "PROGRAM\ninit: {}\n".format(sketch.init_waypoint.label)
			for label, wp in sketch.waypoints.items():
				s += "\n"
				s += str(wp)
		return s
