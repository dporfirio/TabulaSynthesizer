import sys
import argparse
from simple_sketcher import *
from nl_parser import *
from planner import *
from program import *


class Pipeline:

	'''
	Pipeline refers to "Analysis Pipeline".
	It does the following:
	  - stores raw input data (place inside of convenience classes)
	  - runs level 1 (sketch) analysis
	  - stores results of level 1 (sketch) analysis
	  - runs level 2 (synthesis) analysis
	  - stores results of level 2 (synthesis) analysis
	'''

	def __init__(self, world, local_load=False):

		# raw input data
		self.raw_nl = None
		self.raw_traj = None

		# level 1 analysis
		self.nl_parser = NLParser()
		if local_load:
			self.nl_parser.entity_data.load_entities_from_file()
		else:
			self.nl_parser.entity_data.load_entities_from_file("non_object_entities")
		self.traj_parser = SimpleSketcher()

		# level 1 data 
		self.task_hints = None  # contains commands, half commands, and constraints
		self.sketch_data = None

		# level 2 analysis
		self.world_st = WorldState(world)
		self.planner = Planner()

		# level 2 data
		self.program = None

	def reload_world(self, world):
		self.world_st.init(world)

	def load_user_input(self, nl, traj):
		self.raw_nl = nl
		self.raw_traj = traj

	def sketch(self):
		self.sketch_data = self.traj_parser.sketch(self.raw_traj)

	def parse_nl(self):
		'''
		Return a ranked list of hints
		'''
		self.task_hints = self.nl_parser.parse(self.raw_nl)

	def plan(self):
		self.program = self.planner.plan(self.sketch_data, self.task_hints)

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
		pipeline.sketch()
		pipeline.parse_nl()
		pipeline.plan()
	#print(pipeline.program)
	if args["oracle"]:
		pipeline.program.write_result("test_files/oracle/{}.txt".format(args["file"][args["file"].rindex("/"):]))
	else:
		pipeline.program.write_result("test_files/temp/{}.txt".format(args["file"][args["file"].rindex("/"):]))
