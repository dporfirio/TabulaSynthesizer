import os
import json
import copy
import time
from nl_data import NLData
from world import World
from entities import *


class Recording:

	def __init__(self, content, user_sequence, planner, nl_parser):
		self.nl_data = NLData(content, nl_parser)
		self.planner = planner

		self.user_sequence = user_sequence
		self.partial_program = None  # type Sketch
		self.plan = None             # also type Sketch

		self._id = -1

	def parse_raw_input(self):
		t1 = time.time()
		self.nl_data.parse_content()
		t2 = time.time()
		plan = self.planner.plan(self)
		t3 = time.time()
		self.plan = Sketch()
		self.plan.create_sketch_from_plan(plan)
		t4 = time.time()
		print(t2 - t1)
		print(t3 - t2)
		print(t4 - t3)

	def create_partial_program_from_user_sequence(self):
		self.partial_program = Sketch()
		self.partial_program.create_partial_program_from_user_sequence(self.user_sequence)

	def add_plan(self, plan):
		self.plan = plan

	def get_user_sequence(self):
		return self.user_sequence

	def get_task_hints(self):
		return self.nl_data.get_task_hints()

	def get_plan(self):
		return self.plan


class Sketch:

	def __init__(self):
		self.waypoints = {}
		self.init_waypoint = None

		# only for non-main sketches
		self.branch_condition = None

	def create_sketch_from_plan(self, plan):
		'''
		Purpose of this method is to add a recording to the program.
		In doing so, the program itself is updated.
		'''
		def action_or_conditional(action):
			if action._type == "conditional" or action._type == "trigger":
				return "conditional"
			return "command"

		wp = None
		prev_wp_label = None
		curr_acts = []
		for i, act in enumerate(plan):
			print(act)
			if act.name == "moveTo":
				if wp is not None:
					wp.postmove_actions = copy.copy(curr_acts)
				act_label = act.args["destination"].label.name
				self.add_waypoint_from_trace(act_label, prev_wp_label)
				wp = self.waypoints[act_label]
				prev_wp_label = act_label
				curr_acts.clear()
			elif wp is None:
				continue
			elif i == len(plan) - 1:
				curr_acts.append(ActionContainer(action_or_conditional(act), act))
				wp.postmove_actions = copy.copy(curr_acts)
			else:
				curr_acts.append(ActionContainer(action_or_conditional(act), act))

		# if necessary, move the conditional in the init waypoint to the branch condition
		if len(self.init_waypoint.postmove_actions) > 0 and self.init_waypoint.postmove_actions[0]._type != "command":
			self.branch_condition = self.init_waypoint.postmove_actions[0].action
			del self.init_waypoint.postmove_actions[0]

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

	def create_partial_program_from_user_sequence(self, user_sequence):
		prev_wp_label = None
		for wp_label in user_sequence:
			self.add_waypoint_from_trace(wp_label, prev_wp_label)
			prev_wp_label = wp_label


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


class ActionContainer:

	def __init__(self, _type, action_or_conditional):
		self._type = _type  # command or conditional

		# if is a single action = None
		self.action = action_or_conditional   # type = action

		# if is a conditional
		self.jump = []   # type = list of recording id's

	def add_jump(self, recording):
		if self._type == "action":
			print("ERROR: cannot add a jump to a non-conditional")
			exit()
		self.jump = recording

	def __str__(self):
		if self._type == "conditional":
			s = "\n          CONTINUE IF: {};\n          ELSE see jumps: ".format(str(self.action))
			for jmp in self.jump:
				s += "\n            {}".format(str(jmp._id))
			return s
		else:
			return str(self.action)


class Action:

	def __init__(self, name, args, _type="command"):
		action_data = ActionData.get_instance().action_primitives[name]
		self.name = name
		self.args = args
		self.argnames = sorted(list(self.args.keys()))
		self.precondition = self.create_action_conditions(action_data["preconditions"])
		self.postcondition = self.create_action_conditions(action_data["postconditions"])
		self.verbsets = action_data["verbnet"]
		self.synsets = action_data["synsets"]

		# determine if this action is a command, trigger, or conditional
		if len(action_data["action_types"]) == 1:
			self._type = action_data["action_types"][0]
		else:
			self._type = _type

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
		world_st = World.get_instance()
		if self.name != other.name:
			return False
		if self._type != other._type:
			return False
		for arg, argval in self.args.items():
			other_argval = other.args[arg]
			if argval.hole:
				continue
			if arg == "destination":
				if other_argval.label.name != argval.label.name and\
				   not world_st.is_entity_within_region(other_argval.label.name, argval.label.name):
					return False
			elif not argval.label.equals(other_argval.label):
				return False
		return True

	def __str__(self):
		s = "ACTION{}: {} : {}".format(" ({})".format(self._type) if self._type != "command" else "", self.name, [str(argval) for argname, argval in self.args.items()])
		return s

	def equals(self, other):
		if self.name != other.name:
			return False
		if self._type != other._type:
			return False
		same_args = True
		for argname, argval in self.args.items():
			if not argval.equals(other.args[argname]):
				same_args = False
				break
		return same_args


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