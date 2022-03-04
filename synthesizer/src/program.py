import json
import copy
import os
from entities import *


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
		self.init = None
		if ActionData.__instance is not None:
			raise Exception("ActionData is a singleton!")
		else:
			ActionData.__instance = self
		self.action_primitives = None
		dir_path = os.path.dirname(os.path.realpath(__file__))
		# print(dir_path)
		# dir_path = dir_path[:dir_path.index("ctrl.py")]
		with open("{}/action_primitives.json".format(dir_path), "r") as infile:
			self.action_primitives = json.load(infile)
			self.init = copy.copy(self.action_primitives["init"])
			del self.action_primitives["init"]

	def get_idle(self):
		return Action("idle", {})

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
		self.init_waypoint = None
		self.waypoints = {}

	def add_waypoint_from_trace(self, wp_label, prev_wp_label):
		if wp_label not in self.waypoints:
			self.waypoints[wp_label] = Waypoint(wp_label)
		if self.init_waypoint is None:
			self.init_waypoint = self.waypoints[wp_label]
		if prev_wp_label is not None:
			wp = self.waypoints[wp_label]
			prev_wp = self.waypoints[prev_wp_label]
			if not any([if_exec.is_same_trans(wp) for if_exec in prev_wp.if_execs]):
				prev_wp.if_execs.append(IfExec(wp))

	def __str__(self):
		s = "PROGRAM\ninit: {}\n".format(self.init_waypoint.label)
		for label, wp in self.waypoints.items():
			s += str(wp)
		return s


class Waypoint:

	def __init__(self, label):
		self.label = label
		self.precondition = Condition([{}])
		#self.calculate_trajectory_action = Action("calculateTrajectory", {"destination": label})
		entity_data = EntityData.get_instance()
		category = entity_data.obj2category[label][0]
		entity = entity_data.get_entity(category, label)
		self.move_action = Action("moveTo", {"destination": ParamFilled(entity)})
		self.postmove_actions = []
		self.if_execs = []

	def __str__(self):
		s = "waypoint: {}\n".format(self.label)
		for ie in self.if_execs:
			s += "  >> {}\n".format(str(ie))
		s += "  acts {}\n".format(" : ".join([str(act) for act in self.postmove_actions]))
		return s


class Condition:

	def __init__(self, dnf):
		self._or = dnf


class ConditionHole:

	def __init__(self):
		pass


class Param:

	def __init__(self, is_filled):
		self.filled = is_filled
		self.hole = not self.filled

	def equals(self, other):
		if self.hole and other.hole:
			return True
		if self.label == other.label:
			return True
		return False

class ParamFilled(Param):

	def __init__(self, label):
		super().__init__(is_filled=True)
		self.label = label

	def __str__(self):
		s = "Param:\n"
		s += self.label.name
		return s

class ParamHole(Param):

	def __init__(self):
		super().__init__(is_filled=False)


class Action:

	def __init__(self, name, args):
		action_data = ActionData.get_instance().action_primitives[name]
		self.name = name
		self.args = args
		self.argnames = sorted(list(self.args.keys()))
		self.precondition = self.create_action_conditions(action_data["preconditions"])
		self.postcondition = self.create_action_conditions(action_data["postconditions"])
		self.verbsets = action_data["verbnet"]
		self.synsets = action_data["synsets"]

	def create_action_conditions(self, raw_conditions):
		conditions = copy.copy(raw_conditions)
		for condition_name, condition_val in raw_conditions.items():
			# case 1: val is a string
			if type(condition_val) == int:
				argname = self.argnames[condition_val]
				argval = self.args[argname]
				conditions[condition_name] = argval
		return Condition([conditions])

	def is_superset(self, other):
		if self.name != other.name:
			return False
		for arg, argval in self.args.items():
			other_argval = other.args[arg]
			if argval.hole:
				continue
			if argval.label != other_argval.label:
				return False
		return True

	def __str__(self):
		s = "ACTION: {} : {}".format(self.name, [str(argval) for argname, argval in self.args.items()])
		return s

	def equals(self, other):
		if self.name != other.name:
			return False
		same_args = True
		for argname, argval in self.args.items():
			if not argval.equals(other.args[argname]):
				same_args = False
				break
		return same_args

class IfExec:

	def __init__(self, wp):
		self.conditional = ConditionHole()
		self.waypoint = wp

	def is_same_trans(self, other_wp):
		if self.waypoint == other_wp:
			return True
		return False

	def __str__(self):
		return "{}\n".format(self.waypoint.label)
