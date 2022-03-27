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
		print("getting idle")
		return Action("idle", {})

class WorldState:

	'''
	Singleton Storage Class
	'''
	__instance = None

	@staticmethod
	def get_instance():
		if WorldState.__instance is None:
			print("ERROR: world state not initialized.")
			exit()
		return WorldState.__instance

	def __init__(self, world):
		self.world = world
		self.fill_world()
		WorldState.__instance = self

	def fill_world(self):
		'''
		Each object in the world should store a reference to its parent.
		Each object in the world should be directly accessible.
		'''
		regdata_to_scan = copy.copy(self.world["regions"])
		for regstr, regdata in regdata_to_scan.items():
			regdata["parent"] = ""
			self.fill_world_helper(regdata)

	def fill_world_helper(self, obj_data, parent=None):
		if obj_data["name"] not in self.world["regions"]:
			self.world["regions"][obj_data["name"]] = obj_data
			obj_data["parent"] = parent

		if len(obj_data["objects"]) == 0:
			return

		for obj in obj_data["objects"]:
			self.fill_world_helper(obj, parent=obj_data["name"])

	def is_entity_within_region(self, entstr, regstr):
		obj_data = self.world["regions"][regstr]["objects"]
		return self.find_nested_obj(obj_data, entstr)

	def find_nested_obj(self, obj_data_list, entstr):
		
		in_inner_obj = False
		for obj_data in obj_data_list:

			# base case
			if obj_data["name"] == entstr:
				return True

			in_inner_obj = in_inner_obj or self.find_nested_obj(obj_data["objects"], entstr)
		return in_inner_obj


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
		self.init_waypoint = None
		self.waypoints = {}

	def overwrite(self, act_seq):
		self.reset()
		curr_acts = []
		wp = None
		prev_wp_label = None
		print(act_seq)
		for i, act in enumerate(act_seq):
			if act.name == "moveTo":
				if wp is not None:
					wp.postmove_actions = copy.copy(curr_acts)
				self.add_waypoint_from_trace(act.args["destination"].label.name, prev_wp_label)
				wp = self.waypoints[act.args["destination"].label.name]
				if prev_wp_label is None:
					self.init_waypoint = wp
				prev_wp_label = wp.label
				curr_acts.clear()
			elif wp is None:
				continue
			elif i == len(act_seq) - 1:
				curr_acts.append(act)
				wp.postmove_actions = copy.copy(curr_acts)
			else:
				curr_acts.append(act)

	def insert_new_waypoint(self, start_label, new_label, end_label):
		print(start_label)
		print(new_label)
		print(end_label)
		wp = Waypoint(new_label)
		self.waypoints[new_label] = wp
		# modify any existing fields as necessary
		if start_label is not None and end_label is not None:
			start_wp = self.waypoints[start_label]
			end_wp = self.waypoints[end_label]
			for ie in start_wp.if_execs:
				if ie.is_same_trans(end_wp):
					ie.waypoint = wp
		elif start_label is not None:
			# this will be for later
			start_wp = self.waypoints[start_label]
			start_wp.if_execs.append(IfExec(wp))
		# set new wp fields
		if end_label is not None:
			end_wp = self.waypoints[end_label]
			wp.if_execs.append(IfExec(end_wp))
		# set init if necessary
		if start_label is None:
			self.init_waypoint = wp
		return wp

	def change_wp_label(self, wp, new_label):
		old_label = wp.label
		wp.label = new_label
		del self.waypoints[old_label]
		self.waypoints[new_label] = wp

	def add_waypoint_from_trace(self, wp_label, prev_wp_label):
		if wp_label not in self.waypoints:
			self.waypoints[wp_label] = Waypoint(wp_label)
			self.add_postconditions_from_world(self.waypoints[wp_label])
		if self.init_waypoint is None:
			self.init_waypoint = self.waypoints[wp_label]
		if prev_wp_label is not None:
			wp = self.waypoints[wp_label]
			prev_wp = self.waypoints[prev_wp_label]
			if not any([if_exec.is_same_trans(wp) for if_exec in prev_wp.if_execs]):
				prev_wp.if_execs.append(IfExec(wp))

	def add_postconditions_from_world(self, wp):
		'''
		postconditions on the moveTo command may be affected based on 
		the robot's location
		'''
		move_action = wp.move_action
		move_post = move_action.postcondition
		conditions = move_post._or[0]
		items_at_wp = move_action.name

	def write_result(self, path):
		s = str(self)
		with open(path, "w") as outfile:
			outfile.write(s)

	def __str__(self):
		s = "PROGRAM\ninit: {}\n".format(self.init_waypoint.label)
		for label, wp in self.waypoints.items():
			s += "\n"
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
		s += "  >> acts {}\n".format(" : ".join([str(act) for act in self.postmove_actions]))
		for ie in self.if_execs:
			s += "  goto >> {}".format(str(ie))
		return s


class Condition:

	def __init__(self, dnf):
		self._or = dnf

	def __str__(self):
		return str(self._or)


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
		if self.label.equals(other.label):
			return True
		return False

class ParamFilled(Param):

	def __init__(self, label):
		super().__init__(is_filled=True)
		self.label = label

	def __str__(self):
		s = "Param:\n"
		s += str(self.label)
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
		#print(self.name)
		#print(self.postcondition)
		self.verbsets = action_data["verbnet"]
		self.synsets = action_data["synsets"]

	def create_action_conditions(self, raw_conditions):
		conditions = copy.copy(raw_conditions)
		for condition_name, condition_val in raw_conditions.items():
			# case 1: val is an int
			if type(condition_val) == int:
				argname = self.argnames[condition_val]
				argval = self.args[argname]
				conditions[condition_name] = argval.label.name if argval.filled else condition_val
		return Condition([conditions])

	def is_superset(self, other):
		'''
		One action is a superset of another action if:
			- they are equal
			- the first action has holes that the other can fill
			- a "destination" arg of the original action contains the "destination" of the other
		'''
		world_st = WorldState.get_instance()
		if self.name != other.name:
			return False
		for arg, argval in self.args.items():
			other_argval = other.args[arg]
			if argval.hole:
				continue
			if arg == "destination":
				#print(other_argval.label.name)
				#print(argval.label.name)
				#print(world_st.world)
				#exit()
				if other_argval.label.name != argval.label.name and\
				   not world_st.is_entity_within_region(other_argval.label.name, argval.label.name):
					return False
			elif not argval.label.equals(other_argval.label):
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
