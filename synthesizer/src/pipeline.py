import sys
import argparse
from nl_parser import *
from planner import *
from world import *
from recording import *
from program import *


class Pipeline:

	'''
	Pipeline refers to "Analysis Pipeline".
	This should be what happens when data is received.
	It does the following:
	  - stores raw input data (place inside of convenience classes)
	  - runs level 1 (sketch) analysis
	  - stores results of level 1 (sketch) analysis
	  - runs level 2 (synthesis) analysis
	  - stores results of level 2 (synthesis) analysis
	'''

	def __init__(self, world, local_load=False):

		# level 1 analysis
		self.nl_parser = NLParser()
		if local_load:
			self.nl_parser.entity_data.load_entities_from_file()
		else:
			self.nl_parser.entity_data.load_entities_from_file("non_object_entities")

		# level 1 data 
		self.task_hints = None  # contains commands, half commands, and constraints

		# level 2 analysis
		self.world_st = World(world, Program())
		self.planner = Planner()

		# level 2 data
		self.program = None

	def reload_world(self, world):
		self.world_st.init(world)

	def load_user_input(self, nl, traj):
		recording = Recording(nl, traj, self.planner, self.nl_parser)
		prog = self.world_st.get_program()
		#partial_program = []
		#unseen_wps = {}
		#for wp_label in self.raw_traj:
		#	existing_wp = prog.get_wp_from_label(wp_label)
		#	if existing_wp is not None:
		#		partial_program.append(existing_wp)
		#	elif wp_label in unseen_wps:
		#		partial_program.append(unseen_wps[wp_label])
		#	else:
		#		unseen_wps[wp_label] = Waypoint(wp_label)
		#		partial_program.append(unseen_wps[wp_label])
		recording.create_partial_program_from_user_sequence()
		recording.parse_raw_input()
		prog.add_recording(recording)

	def update_available_entities(self, new_avail_ents):
		print("Updating available entities.")
		self.nl_parser.entity_data.update_available_entities(new_avail_ents)


if __name__ == "__main__":
	import test_parser
	parser = argparse.ArgumentParser(description='The test interface for tabula.')
	parser.add_argument('-f', '--file', type=str, required=True)
	parser.add_argument('-o','--oracle', action='store_true', help='Replenish the oracle test cases with updated results', required=False)
	args = vars(parser.parse_args())
	nl, traj, world = test_parser.parse(args["file"])
	pipeline = Pipeline(world, True)
	for indiv_nl, indiv_traj in zip(nl, traj):
		pipeline.load_user_input(indiv_nl, indiv_traj)
	#print(pipeline.program)
	if args["oracle"]:
		pipeline.world_st.get_program().write_result("test_files/oracle/{}.txt".format(args["file"][args["file"].rindex("/"):]))
	else:
		pipeline.world_st.get_program().write_result("test_files/temp/{}.txt".format(args["file"][args["file"].rindex("/"):]))
