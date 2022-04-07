import copy
import math
import itertools
import time
from program import *


class Planner:

	def __init__(self):
		self.world_st = WorldState.get_instance()

	def contains_double_loop(self, trace):
		idx = -1
		if len(trace) < 2:
			return False, idx
		# test to see if the same loop exists twice
		contains = False
		for i in range(1,math.floor((len(trace)+1)/2)):
			test_loop = trace[len(trace) - i:]
			test_loop.reverse()
			candidate_loop = trace[len(trace) - i*2:len(trace) - i]
			candidate_loop.reverse()
			if test_loop == candidate_loop:
				contains = True
				idx = i
				break
		return contains, idx

	def get_traces(self, curr_wp, holey_traces, curr_trace):
		# analyze curr trace to see if it is a complete trace
		if len(curr_wp.if_execs) == 0:
			if curr_trace not in holey_traces:
				holey_traces.append(curr_trace)
			return
		print("does this trace contain a double loop? {}".format(curr_trace))
		contains, i = self.contains_double_loop(curr_trace)
		if contains:
			print("yes")
			#curr_trace = curr_trace[:i+1]
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
		#print(new_act)
		if new_act[0][-1].name == "moveTo":
			curr_move_to = new_act[0][-1]
			i = 0
		else:
			curr_move_to = None
			act_history = copy.copy(act_history)
			act_history.reverse()
			for i, act in enumerate(act_history):
				if act.name == "moveTo":
					curr_move_to = act
					break
		if curr_move_to is None:
			###print("ERROR: must have a moveTo action in sequence of actions")
			exit()

		# see if there is a previous "moveTo", determine expected action
		other_move_to = None
		for j in range(i+1, len(act_history)):
			act = act_history[j]
			if act.equals(curr_move_to):
				other_move_to = act
				break

		if other_move_to is None:
			print("{} is not repeat".format(act_history[0]))
			return False
		print("{} IS a repeat action".format(new_act))
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
			###print("warning: must have a moveTo action in sequence of actions")
			return Exception
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
		#print("\nGETTING NEIGHBORS to {} (len {})".format(str([str(curr) for curr in current[0]]), len(current[0])))
		neighbors = []
		#print(len(current[0]))
		#for act in current[0]:
		#	print(act)
		#print()
		curr_args = {}
		action_history = list(current[0])
		most_recent_action = action_history[-1]
		for i, arg in enumerate(current[1]):
			curr_args[arg] = current[2][i]
		#print("CURR ARGS")
		#print(curr_args)
		ap = ActionData.get_instance().action_primitives
		ed = EntityData.get_instance().entities
		for act_name, act_data in ap.items():
			avail_args = []
			for argtype in act_data["argtypes"]:
				avail_args.append(ed[argtype])
			arg_combos = list(itertools.product(*avail_args))
			for arg_combo in arg_combos:
				args = {}
				item_args = {}
				for i, ent in enumerate(arg_combo):
					argname = act_data["argnames"][i]
					argval = ent
					args[argname] = ParamFilled(argval)
					if act_name != "moveTo" and "content" not in argval.categories and "narrative" not in argval.categories:
						item_args[argval] = False

				# candidate action
				act = Action(act_name, args)

				# vet unparameterized speech
				if act_name == "say":
					if type(args["speech"].label) != SpeechEntity:
						continue

				# if we are in a loop and the solution is not already inside of the loop
				'''
				if act_name == "moveTo":
					i = len(action_history) - 1
					temp_act_hist = []
					while i >= 0:
						temp_act_hist.append(action_history[i])
						if action_history[i].equals(act):
							break
						i -= 1
					if i >= 0:
						print(act)
						print(temp_act_hist)
						#time.sleep(1)
						#exit()
					if i >= 0:
						i -= 1
						j = 0
						is_same = True
						while j < len(temp_act_hist) and i >= 0:
							if not action_history[i].equals(temp_act_hist[j]):
								is_same = False
								break
							i -= 1
							j += 1
						if i < 0:
							is_same = False
						if is_same:
							#print("continuing")
							#if len(temp_act_hist) > 1:
							#	exit()
							#exit()
							continue
				'''

				# Vet the NON-moveto action and, NON-content, NON-narrative arguments.
				# if the robot is manipulating something that it is not
				# NEAR or does not POSSESS, then the action-to-be is invalid
				# start with what the robot possesses
				if curr_args["carryingItem"] in [ent.name for ent in item_args]:
					argval = [ent for ent in item_args if ent.name == curr_args["carryingItem"]][0]
					item_args[argval] = True
				#print()
				#print(act_name)
				#print(item_args)
				# now do what the robot is near
				act_hist_rev = copy.copy(action_history)
				act_hist_rev.reverse()
				try:
					loc, _, _ = self.find_previous_moveto(act_hist_rev)
					#print("we're good")
					#print(loc.args["destination"])
					regstr = loc.args["destination"].label.name
					#print("got it")
				except:
					#print("NOOO")
					regstr = "home base"
				#time.sleep(0.05)
				for argval, b in item_args.items():
					if not b:
						item_args[argval] = argval.name == regstr # self.world_st.is_entity_within_region(argval.name, regstr)
				
				# penalties:
				# - there is a penalty to CREATE
				# - there is a penalty if creation is NEEDLESS (there is already one in the world)
				creation_penalty = sum([1 for key, val in item_args.items() if not val])
				duplication_penalty = sum([1 for key, val in item_args.items() if ((not val) and key.name in self.world_st.world["regions"])])
				#print(item_args)
				#print(self.world_st.world)
				#if duplication_penalty > 0:
				#	print(self.world_st.world)
				#	exit()
				#if creation_penalty > 0:
				#	print(list(item_args.keys())[0])
				#	groc = list(item_args.keys())[0]
				#	print(groc.name in self.world_st.world)
				#	print(groc.name)
				#	print(type(groc.name))
				#	print(self.world_st.world.keys())
				#	print("CREATE")
				#	exit()
				penalty = creation_penalty + duplication_penalty
				#if not all(list(item_args.values())):
				#	continue

				#print("args are GOOD! {}".format(act))
				all_preconds_sat = True
				updated_args = {}
				for cond_name, cond_val in curr_args.items():
					post = act.postcondition._or[0]
					pre = act.precondition._or[0]
					if cond_name in pre and pre[cond_name] != cond_val:
						all_preconds_sat = False
					else:
						if cond_name in post:
							updated_args[cond_name] = post[cond_name]
						elif cond_name in pre:
							updated_args[cond_name] = pre[cond_name]
						else:
							updated_args[cond_name] = curr_args[cond_name]
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
					neighbors.append(((updated_act_hist, current[1], updated_argvals), penalty))
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

	def trace_satisfied_hints_helper(self, curr_act_idx, curr_hint_idx, act_history, hint_list, detached_tracker, sat_counter, scores):
		# recursive helper method
		# base case
		if curr_act_idx == len(act_history):
			scores.append(sum(sat_counter))
			if curr_hint_idx == len(hint_list) and all(list(detached_tracker.values())):
				return True
			#print("curr hint idx: {} out of {}".format(curr_hint_idx, len(hint_list)))
			return False

		# recursive case
		curr_act = act_history[curr_act_idx]
		result = False
		# -- see if current hint matches
		if curr_hint_idx < len(hint_list):
			#print("curr hint: {}".format(hint_list[curr_hint_idx]))
			#print("curr act: {}".format(curr_act))
			curr_hint_tuple = hint_list[curr_hint_idx]
			for curr_hint in curr_hint_tuple:
				if curr_hint.is_superset(curr_act):
					new_sat_counter = copy.copy(sat_counter)
					new_sat_counter[0] += 1
					sat = self.trace_satisfied_hints_helper(curr_act_idx + 1, curr_hint_idx + 1, act_history, hint_list, detached_tracker, new_sat_counter, scores)
					result = result or sat
		args = list(curr_act.args.values())
		args = [argval.label for argval in args]
		#print(args)
		for entity, val in detached_tracker.items():
			if not val:
				if any([(entity == arg or ("location" in entity.categories and self.world_st.is_entity_within_region(arg.name, entity.name))) for arg in args]):# entity in args:
					detached_tracker_copy = copy.copy(detached_tracker)
					detached_tracker_copy[entity] = True
					new_sat_counter = copy.copy(sat_counter)
					new_sat_counter[1] += 1
					#if len(act_history) > 4 and act_history[2].name == "grab" and act_history[3].args["destination"].label.name == "cabinets" and entity.name == "kitchen" and "cabinets" in [arg.name for arg in args]:
					#	print(entity)
					#	print(args)
					#	print(new_sat_counter)
						#exit()
					sat = self.trace_satisfied_hints_helper(curr_act_idx + 1, curr_hint_idx, act_history, hint_list, detached_tracker_copy, new_sat_counter, scores)
					result = result or sat
		sat = self.trace_satisfied_hints_helper(curr_act_idx + 1, curr_hint_idx, act_history, hint_list, detached_tracker, sat_counter, scores)
		result = result or sat
		return result

	def trace_satisfies_hints(self, act_history, hint_list, detached_entities):
		# recursively determine if the list of hints and detached entities are SEPARATELY
		# present in the act_history.
		detached_tracker = {}
		for ent in detached_entities:
			detached_tracker[ent] = False
		sat_counter = [0,0]
		scores = []
		to_return = self.trace_satisfied_hints_helper(0, 0, act_history, hint_list, detached_tracker, sat_counter, scores)
		#time.sleep(2)
		return to_return, max(scores)

	def goal_satisfied(self, curr, act_seq, hint_list, detached_entities):
		# 1) is the sequence of actions present in the curr?
		# 2) is the hint_list present in the curr?
		# 3) are all incomplete hints in the sequence? Each must be separately present. 
		act_history = curr[0]
		act_seq_idx = 0
		act_seq_idxs = []
		#hint_list_idx = 0
		detached_ents_included = 0
		for i, act in enumerate(act_history):
			if act_seq_idx < len(act_seq) and act_seq[act_seq_idx].is_superset(act):
				act_seq_idxs.append(i)
				act_seq_idx += 1
			#if hint_list_idx < len(hint_list) and hint_list[hint_list_idx].is_superset(act):
			#	hint_list_idx += 1
		#if act_seq_idx == len(act_seq) and hint_list_idx == len(hint_list):
		hint_sat, _ = self.trace_satisfies_hints(act_history, hint_list, detached_entities)
		###print("{} -- {}".format(hint_sat, act_seq_idx == len(act_seq)))
		if act_seq_idx == len(act_seq) and hint_sat:
			return True, act_seq_idxs
		return False, act_seq_idxs

	def heuristic(self, curr, act_seq, hint_list, detached_entities):
		# how far are we from including the act_seq, hint_list, and incomplete_hint_seq in curr?
		act_history = curr[0]
		act_seq_idx = 0
		hint_list_idx = 0
		empty_wp_penalty = 0
		seen_wp_list = [] # DO NOT double-penalize empty waypoints
		for i, act in enumerate(act_history):
			if act_seq_idx < len(act_seq) and act_seq[act_seq_idx].is_superset(act):
				act_seq_idx += 1
			#if hint_list_idx < len(hint_list) and hint_list[hint_list_idx].is_superset(act):
			#	hint_list_idx += 1
			if i < len(act_history) - 1 and act.name == "moveTo" and act_history[i+1].name == "moveTo":
				if act.args["destination"].label not in seen_wp_list:
					empty_wp_penalty += 0.1
					seen_wp_list.append(act.args["destination"].label)
		_, hint_score = self.trace_satisfies_hints(act_history, hint_list, detached_entities)
		#print((len(hint_list) + len(detached_entities)) - hint_score)
		#print(len(act_seq) - act_seq_idx)
		#print(empty_wp_penalty)
		val = (len(act_seq) - act_seq_idx) + ((len(hint_list) + len(detached_entities)) - hint_score) + empty_wp_penalty
		act_str = " : ".join([str(item) for item in curr[0]])
		return val

	def solutions_contain_neighbor(self, neighbor, solutions):
		'''
		The purpose of this method is to make sure that any additional available solutions
		are not duplicates of the first solution found. I.e., if the solution below exists,

		           X - Y - Z - X - Y - Z

		then the following additional solution should be prevented:

		           X - Y - Z - X - Y - Z - X
		'''
		result = False
		for solution in solutions:
			temp_result = True
			n_act_seq = neighbor[0]
			act_seq = solution[0]
			if len(n_act_seq) < len(act_seq):
				continue
			for i, n_act in enumerate(n_act_seq):
				#print(n_act)
				#print(act_seq[i])
				if i >= len(act_seq):
					break
				if not n_act.equals(act_seq[i]):
					temp_result = False
					break
			result = (result or temp_result)
		#if result:
		#	print("LSKADJFS")
		#	exit()
		return result

	def astar(self, start, act_seq, hint_list, detached_entities, solutions):
		open_set = [start]
		came_from = {}
		g_score = {}  # if an element is not here, the val is inf
		g_score[start] = 0
		f_score = {}  # if an element is not here, the val is inf
		f_score[start] = self.heuristic(start, act_seq, hint_list, detached_entities)
		while len(open_set) > 0:
			#time.sleep(0.1)
			#if len(solutions) > 0:
			#	time.sleep(1)
			current = open_set[0]
			print()
			print("~~~~~~~~~~~~~~~")
			print("~~~~~~~~~~~~~~~")
			#print("neighbors to:")
			for act in current[0]:
				print(act)
			goal_sat, trace_idxs = self.goal_satisfied(current, act_seq, hint_list, detached_entities)
			if goal_sat:
				print("obtained solution {}".format(len(solutions)))
				solutions.append((self.reconstruct_path(came_from, current), trace_idxs))
				if len(solutions) > 2:
					return #self.reconstruct_path(came_from, current), trace_idxs
			open_set.remove(current)
			# adhere to the length cap
			# SIMPLE: length cap = len(act_seq)*3 with a minimum of 10
			if len(current[0]) > max(10, len(act_seq) * 3):
				neighbors = []
			else:
				print("~~~~~~~~~~~~~~~")
				print(current[1])
				print(current[2])
				print("~~~~~~~~~~~~~~~")
				neighbors = self.get_current_neighbors(current)
				print()
				#exit()
			#time.sleep(1)
			print("neighbors:")
			for neighbor_data in neighbors:
				# vet the neighbor.
				# if there is already a solution that includes neighbor
				# discard the neighbor
				neighbor = neighbor_data[0]
				if self.solutions_contain_neighbor(neighbor, solutions):
					continue
				obj_penalty = neighbor_data[1]
			#	print(neighbor[0][-1])
				tentative_g_score = g_score[current] + (0 if self.is_repeat_action(list(current[0]), neighbor) else (1 + obj_penalty))
				if tentative_score < g_score[neighbor] if neighbor in g_score else 100000:
					came_from[neighbor] = current
					g_score[neighbor] = tentative_g_score
					f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, act_seq, hint_list, detached_entities)
					print(  "{} - {} - {}".format(neighbor[0][-1], g_score[neighbor], f_score[neighbor]))
					if neighbor not in open_set:
						open_set.append(neighbor)
						open_set.sort(key=lambda x: f_score[x])
			#	print(f_score[neighbor])
			#print()
		return #None

	def update_existing_wps(self, sketch, act_seq, wp_idxs, trace):
		'''
		For each wp in the trace:
			- if not yet confirmed:
				- change if necessary
				- confirm
			- elif confirmed
				- if not necessary to change, do nothing
				- else, make a new waypoint, insert it in trace as necessary
		'''
		confirmed = {}
		for wp_dict in trace:
			confirmed[wp_dict["waypoint"]] = False
		
		prev_wp = None
		for i, wp_dict in enumerate(trace):
			wp = wp_dict["waypoint"]
			wp_idx = wp_idxs[i]
			change_name = act_seq[wp_idx].args["destination"].label.name
			if not confirmed[wp]:
				sketch.change_wp_label(wp, change_name)
				confirmed[wp] = True
			else:
				if change_name != wp.label:
					nxt_wp = trace[i+1]["waypoint"].label if len(trace)> i+1 else None
					sketch.insert_new_waypoint(prev_wp.label, change_name, nxt_wp)
			prev_wp = wp


	def update_sketch(self, sketch, act_seq, wp_idxs, trace):
		self.update_existing_wps(sketch, act_seq, wp_idxs, trace)
		curr_acts = []
		wp = None
		prev_move_label = None
		for i, act in enumerate(act_seq):
			if act.name == "moveTo":
				if wp is None:
					if act.args["destination"].label.name in sketch.waypoints:
						wp = sketch.waypoints[act.args["destination"].label.name]
					else:
						# look to the future...
						end_wp_label = None
						for j in range(i+1, len(act_seq)):
							nxt_act = act_seq[j]
							if nxt_act.name == "moveTo":
								end_wp_label = nxt_act.args["destination"].label.name
								break
						wp = sketch.insert_new_waypoint(prev_move_label, act.args["destination"].label.name, end_wp_label)
					prev_move_label = wp.label
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

	def solve_helper(self, trace, hint_list, detached_entities):
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
		solutions = []
		self.astar(start, act_seq, hint_list, detached_entities, solutions)
		return solutions

	def solve(self, trace, hints, sketch):
		for item in trace:
			print(item["waypoint"])
		#exit()
		hint_seq = []
		for hint_dict in hints:
			hint_seq.extend(hint_dict["commands"])
			hint_seq.extend(hint_dict["half-commands"])

		# TODO: add incomplete hints! An unattached entity (incomplete hint)
		# MUST be included in the solution. SEPARATELY.
		detached_entities = []
		for hint_dict in hints:
			if len(hint_dict["constraints"]) > 0:
				detached_entities.append(hint_dict["constraints"][0][1])
		solutions = self.solve_helper(trace, hint_seq, detached_entities)
		###print(sketch)
		for i, solution in enumerate(solutions):
			act_seq = solution[0]
			###print("SOLUTION")
			###print(" : ".join([str(act) for act in act_seq]))
			sketch.overwrite(act_seq)
		sketch.overwrite(solutions[0][0])
		#self.update_sketch(sketch, act_seq, wp_idxs, trace)
		return sketch