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
			print("Added first recording.")
			self.main_recording = recording
		else:
			print("Added second recording.")
		print(self)

	def write_result(self, path):
		s = str(self)
		with open(path, "w") as outfile:
			outfile.write(s)

	def __str__(self):
		s = ""
		for recording in self.recordings:
			sketch = recording.plan
			s += "PROGRAM {}\ninit: {}\n".format("(main)" if recording == self.main_recording else "(branch)", sketch.init_waypoint.label)
			if sketch.branch_condition is not None:
				s += "branch condition: {}\n".format(sketch.branch_condition)
			for label, wp in sketch.waypoints.items():
				s += "\n"
				s += str(wp)
		return s
