import copy
import math
import itertools
from program import *


class Planner:

	def __init__(self):
		pass

	def contains_double_loop(self, trace):
		if len(trace) < 2:
			return False
		# test to see if the same loop exists twice
		contains = False
		for i in range(1,math.floor((len(trace)+1)/2)):
			test_loop = trace[len(trace) - i:]
			test_loop.reverse()
			candidate_loop = trace[len(trace) - i*2:len(trace) - i]
			candidate_loop.reverse()
			if test_loop == candidate_loop:
				contains = True
				break
		return contains

	def get_traces(self, curr_wp, holey_traces, curr_trace):
		# analyze curr trace to see if it is a complete trace
		if len(curr_wp.if_execs) == 0:
			if curr_trace not in holey_traces:
				holey_traces.append(curr_trace)
			return
		print("does this trace contain a double loop? {}".format(curr_trace))
		if self.contains_double_loop(curr_trace):
			print("yes")
			if curr_trace not in holey_traces:
				holey_traces.append(curr_trace)
			return

		# continue to add to the curr trace
		for if_exec in curr_wp.if_execs:
			next_wp = if_exec.waypoint
			updated_trace = copy.copy(curr_trace)
			updated_trace.append(next_wp)
			self.get_traces(next_wp, holey_traces, updated_trace)

	def plan(self, sketch, hints):
		# collapse program into transition system
		# this is done to convert the HTS to a TS

		# get a SORTED list of ALL traces with holes (avoid multiple repeats of loops)
		# we can trim prefixes before the first hole by enumerating all possible preconditions
		holey_wp_traces = []
		init_wp = sketch.init_waypoint
		self.get_traces(init_wp, holey_wp_traces, [init_wp])
		holey_traces = []
		for holey_wp_trace in holey_wp_traces:
			holey_trace = []
			for wp in holey_wp_trace:
				temp = {"waypoint": wp, "actions": []}
				temp["actions"].append(wp.move_action)
				for action in wp.postmove_actions:
					temp["actions"].append(action)
				holey_trace.append(temp)
			holey_traces.append(holey_trace)
		holey_traces.sort(key=len)  # from smallest to largest
		print(holey_traces)

		# best_solution = None
		# bad solutions = []
		# n = 1
		best_solution = None
		bad_solutions = []
		n = len(holey_traces)    # change to 1 if slow

		# while there is no solution:
		while best_solution is None:

			# find solution for n traces (avoiding previous bad solutions), prioritizing the traces that have the MOST holes
			traces = holey_traces[:n]
			print(traces[0])
			solution = self.solve(traces[0], hints, sketch)

			# evaluate solution on ALL (non-n) traces
			# todo: UNCOMMENT FOR FASTER SOLVING
			# solution_sat = ...
			solution_sat = True if solution is not None else False

			# if there is a solution, set best solution break!
			if solution_sat:
				best_solution = solution
				break

			# otherwise, add the bad solution to the list of bad solutions, n += 1
			else:
				# UNCOMMENT for better handling of no solution
				#bad_solution.append(...)
				#n += 1
				# temporarily, just re-return the unfilled sketch for manual-filling
				print("returning sketch")
				best_solution = sketch

		return best_solution

	def is_repeat_action(self, act_history, new_act):
		if len(act_history) == 1:
			return False

		# get current "moveTo" and actions after the "moveTo"
		curr_move_to = None
		act_history = copy.copy(act_history)
		act_history.reverse()
		for i, act in enumerate(act_history):
			if act.name == "moveTo":
				curr_move_to = act
				break
		if curr_move_to is None:
			print("ERROR: must have a moveTo action in sequence of actions")
			exit()

		# see if there is a previous "moveTo", determine expected action
		other_move_to = None
		for j in range(i+1, len(act_history)):
			act = act_history[j]
			if act.equals(curr_move_to):
				other_move_to = act
				break

		if other_move_to is None:
			return False
		return True

	def find_previous_moveto(self, rev_act_history):
		curr_move_to = None
		post_actions = []
		for i, act in enumerate(rev_act_history):
			if act.name == "moveTo":
				curr_move_to = act
				break
			post_actions.append(act)
		if curr_move_to is None:
			print("ERROR: must have a moveTo action in sequence of actions")
			exit()
		return curr_move_to, post_actions, i

	def find_matching_moveto(self, rev_act_history, move_to, start_idx):
		other_move_to = None
		cap_acts = []
		for j in range(start_idx+1, len(rev_act_history)):
			act = rev_act_history[j]
			if act.equals(move_to):
				other_move_to = act
				break
			elif act.name == "moveTo":
				cap_acts = []
			else:
				cap_acts.append(act)
		return other_move_to, cap_acts, j

	def is_conflicting_action(self, act_history, new_act):
		if len(act_history) == 1 and new_act.name == "moveTo":
			return False
		elif len(act_history) ==1 and new_act.name != "moveTo":
			return True

		# get current "moveTo" and actions after the "moveTo"
		act_history = copy.copy(act_history)
		act_history.reverse()
		curr_move_to, post_actions, i = self.find_previous_moveto(act_history)
		other_move_to, _, j = self.find_matching_moveto(act_history, curr_move_to, i)

		if other_move_to is None:
			return False

		expected_action = act_history[j - len(post_actions) - 1]
		if not expected_action.equals(new_act):
			return True
		return False

	def get_current_neighbors(self, current):
		neighbors = []
		curr_args = {}
		action_history = list(current[0])
		most_recent_action = action_history[-1]
		for i, arg in enumerate(current[1]):
			curr_args[arg] = current[2][i]
		ap = ActionData.get_instance().action_primitives
		ed = EntityData.get_instance().entities
		for act_name, act_data in ap.items():
			avail_args = []
			for argtype in act_data["argtypes"]:
				avail_args.append(ed[argtype])
			arg_combos = list(itertools.product(*avail_args))
			for arg_combo in arg_combos:
				args = {}
				for i, ent in enumerate(arg_combo):
					argname = act_data["argnames"][i]
					argval = ent
					args[argname] = ParamFilled(argval)
				act = Action(act_name, args)
				all_preconds_sat = True
				updated_args = {}
				for precond_name, precond_val in act.precondition._or[0].items():
					if precond_val != curr_args[precond_name]:
						all_preconds_sat = False
					else:
						post = act.postcondition._or[0]
						pre = act.precondition._or[0]
						updated_args[precond_name] = post[precond_name] if precond_name in post else pre[precond_name]
				if all_preconds_sat:
					updated_act_hist = copy.copy(action_history)
					if self.is_conflicting_action(action_history, act):
						continue
					updated_act_hist.append(act)
					updated_act_hist = tuple(updated_act_hist)
					all_updated_args = copy.copy(curr_args)
					for updated_arg, updated_argval in updated_args.items():
						all_updated_args[updated_arg] = updated_argval
					updated_argvals = tuple([all_updated_args[key] for key in sorted(list(all_updated_args.keys()))])
					neighbors.append((updated_act_hist, current[1], updated_argvals))
		return neighbors

	def reconstruct_path(self, came_from, current):
		total_path = [current[0][-1]]
		while current in list(came_from.keys()):
			current = came_from[current]
			total_path.insert(0, current[0][-1])
		# cap the trace
		act_history = copy.copy(total_path)
		act_history.reverse()
		curr_move_to, _, i = self.find_previous_moveto(act_history)
		other_move_to, cap_acts, _ = self.find_matching_moveto(act_history, curr_move_to, i)
		#print("cap acts")
		#for cap_act in cap_acts:
		#	print(cap_act)
		if other_move_to is not None:
		#	print("other move to is not none")
			act_history = act_history[i:]
			cap_acts.extend(act_history)
		else:
			cap_acts = act_history
		cap_acts.reverse()
		#print("cap acts")
		#for cap_act in cap_acts:
		#	print(cap_act)
		return cap_acts

	def goal_satisfied(self, curr, act_seq, hint_list):
		# is the sequence of actions present in the curr?
		# is the hint_list present in the curr?
		act_history = curr[0]
		act_seq_idx = 0
		hint_list_idx = 0
		for act in act_history:
			if act_seq_idx < len(act_seq) and act_seq[act_seq_idx].is_superset(act):
				act_seq_idx += 1
			if hint_list_idx < len(hint_list) and hint_list[hint_list_idx].is_superset(act):
				hint_list_idx += 1
		if act_seq_idx == len(act_seq) and hint_list_idx == len(hint_list):
			return True
		return False

	def heuristic(self, curr, act_seq, hint_list):
		# how far are we from including the act_seq and hint_list in curr?
		act_history = curr[0]
		act_seq_idx = 0
		hint_list_idx = 0
		empty_wp_penalty = 0
		for i, act in enumerate(act_history):
			if act_seq_idx < len(act_seq) and act_seq[act_seq_idx].is_superset(act):
				act_seq_idx += 1
			if hint_list_idx < len(hint_list) and hint_list[hint_list_idx].is_superset(act):
				hint_list_idx += 1
			if i < len(act_history) - 1 and act.name == "moveTo" and act_history[i+1].name == "moveTo":
				empty_wp_penalty += 1
		val = (len(act_seq) - act_seq_idx) + (len(hint_list) - hint_list_idx) + empty_wp_penalty
		act_str = " : ".join([str(item) for item in curr[0]])
		return val

	def astar(self, start, act_seq, hint_list):
		open_set = [start]
		came_from = {}
		g_score = {}  # if an element is not here, the val is inf
		g_score[start] = 0
		f_score = {}  # if an element is not here, the val is inf
		f_score[start] = self.heuristic(start, act_seq, hint_list)
		while len(open_set) > 0:
			current = open_set[0]
			if self.goal_satisfied(current, act_seq, hint_list):
				return self.reconstruct_path(came_from, current)
			open_set.remove(current)
			neighbors = self.get_current_neighbors(current)
			for neighbor in neighbors:
				tentative_g_score = g_score[current] + (0 if self.is_repeat_action(list(current[0]), neighbor) else 1)
				if tentative_score < g_score[neighbor] if neighbor in g_score else 100000:
					came_from[neighbor] = current
					g_score[neighbor] = tentative_g_score
					f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, act_seq, hint_list)
					if neighbor not in open_set:
						open_set.append(neighbor)
						open_set.sort(key=lambda x: f_score[x])
		return None

	def update_sketch(self, sketch, act_seq):
		curr_acts = []
		wp = None
		for i, act in enumerate(act_seq):
			if act.name == "moveTo":
				if wp is None:
					wp = sketch.waypoints[act.args["destination"].label.name]
					curr_acts.clear()
					continue
				#if i == len(act_seq) - 1:
				#	curr_acts.append(act)
				wp_acts = wp.postmove_actions
				wp.postmove_actions = copy.copy(curr_acts)
				curr_acts.clear()
				wp = sketch.waypoints[act.args["destination"].label.name]
			elif i == len(act_seq) - 1:
				curr_acts.append(act)
				wp_acts = wp.postmove_actions
				wp.postmove_actions = copy.copy(curr_acts)
			else:
				curr_acts.append(act)

	def solve_helper(self, trace, hint_list):
		ad = ActionData.get_instance()
		act_seq = []
		for wp_dict in trace:
			wp = wp_dict["waypoint"]
			act_seq.append(wp.move_action)
			act_seq.extend(wp.postmove_actions)
		# action history, postcondition args, postcondition vals
		#print(" : ".join([str(act) for act in act_seq]))
		#print(" : ".join([str(act) for act in hint_list]))
		start = ((ad.get_idle(),), tuple(key for key in sorted(list(ad.init.keys()))), tuple([ad.init[key] for key in sorted(list(ad.init.keys()))]))
		return self.astar(start, act_seq, hint_list)

	def solve(self, trace, hints, sketch):
		hint_seq = []
		for hint_dict in hints:
			hint_seq.extend(hint_dict["commands"])
			hint_seq.extend(hint_dict["half-commands"])
		act_seq = self.solve_helper(trace, hint_seq)
		print("SOLUTION")
		print(" : ".join([str(act) for act in act_seq]))
		self.update_sketch(sketch, act_seq)
		return sketch