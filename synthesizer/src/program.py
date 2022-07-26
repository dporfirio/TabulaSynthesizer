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
		self.waypoints = {}

		# recording id counter
		self.counter = 0

	def get_recordings(self):
		return self.recordings

	def add_recording(self, recording):
		'''
		Purpose of this method is to add a recording to the program.
		In doing so, the program itself is updated.
		'''
		if self.main_recording is None:
			print("Added first recording.")
			self.main_recording = recording
			self.waypoints[self.main_recording] = []
			for wp in self.main_recording.get_plan().waypoints:
				self.waypoints[self.main_recording].append(wp)
		else:
			print("Added another recording.")
			# combine with other recordings
			new_init_wp = recording.get_plan().init_waypoint
			# type is 'branch', 'else', or 'tap'
			# the default is TAP
			_type = "tap"
			# find a matching waypoint
			for old_recording in self.recordings:
				to_break = False
				print('in recordings...')
				for old_wp_label, old_wp in old_recording.get_plan().waypoints.items():
					print("looking at wp labels...")
					if new_init_wp.label == old_wp_label:
						print("found label match...")
						for act in old_wp.postmove_actions:
							print("iterating through acts...")
							if act._type == "conditional":
								print("found conditional")
								act.jump.append(recording)
								to_break = True
								break
					if to_break:
						break
				if to_break:
					break

		recording._id = self.counter
		self.counter += 1
		self.recordings.append(recording)
		print(self)

	def write_result(self, path):
		s = str(self)
		with open(path, "w") as outfile:
			outfile.write(s)

	def __str__(self):
		s = ""
		for recording in self.recordings:
			sketch = recording.plan
			s += "PROGRAM ({}, {})\ninit: {}\n".format(recording._id, "main" if recording == self.main_recording else "branch", sketch.init_waypoint.label)
			if sketch.branch_condition is not None:
				s += "branch condition: {}\n".format(sketch.branch_condition)
			for label, wp in sketch.waypoints.items():
				s += "\n"
				s += str(wp)
		return s
