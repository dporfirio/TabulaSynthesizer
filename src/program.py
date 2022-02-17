import json
import copy


class ActionData:

	'''
	Singleton Storage Class
	'''
	__instance = None

	@staticmethod
	def get_instance():
		if ActionData.__instance is None:
			ActionData()
		return ActionData.__instance

	def __init__(self):
		self.action_primitives = None
		if ActionData.__instance is not None:
			raise Exception("ActionData is a singleton!")
		else:
			ActionData.__instance = self
		self.action_primitives = None
		with open("action_primitives.json", "r") as infile:
			self.action_primitives = json.load(infile)


class WorldState:

	def __init__(self):
		self.state = {}


class RobotState:

	def __init__(self):
		self.init_state = {
			"carryingItem": False,
			"currentLocation": "home base",
			"canTravel": True
		}


class Program:

	def __init__(self):
		self.waypoints = {}

	def add_waypoint(self, wp_label, prev_wp_label=None):
		if wp_label not in self.waypoints:
			self.waypoints[wp_label] = Waypoint(wp_label)
		if prev_wp_label is not None:
			wp = self.waypoints[wp_label]
			prev_wp = self.waypoints[prev_wp_label]
			if not any([if_exec.is_same_trans(wp) for if_exec in prev_wp.if_execs]):
				prev_wp.if_execs.append(IfExec(wp))


class Waypoint:

	def __init__(self, label):
		self.label = label
		self.precondition = Condition([{}])
		#self.calculate_trajectory_action = Action("calculateTrajectory", {"destination": label})
		self.move_action = Action("moveTo", {"destination": label})
		self.postmove_actions = PostMoveActions()
		self.if_execs = []


class Condition:

	def __init__(self, dnf):
		self._or = dnf


class PostMoveActions:

	def __init__(self):
		self.actions = [ActionHole()]


class ConditionHole:

	def __init__(self):
		pass


class ActionHole:

	def __init__(self):
		pass


class Action:

	def __init__(self, name, args):
		action_data = ActionData.get_instance().action_primitives[name]
		self.name = name
		self.args = args
		self.precondition = self.create_action_conditions(action_data["preconditions"])
		self.postcondition = self.create_action_conditions(action_data["postconditions"])
		self.verbsets = action_data["verbnet"]
		self.synsets = action_data["synsets"]

	def create_action_conditions(self, raw_conditions):
		conditions = copy.copy(raw_conditions)
		for condition_name, condition_val in raw_conditions.items():
			# case 1: val is a string
			if type(condition_val) == str:
				if len(condition_val) > 0 and condition_val[0] == "$":
					argname = condition_val[1:]
					argval = self.args[argname]
					conditions[condition_name] = argval
		return Condition([conditions])


class IfExec:

	def __init__(self, wp):
		self.conditional = ConditionHole()
		self.waypoint = wp

	def is_same_trans(self, other_wp):
		if self.waypoint == other_wp:
			return True
		return False
