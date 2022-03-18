import json
import sys
import os


def parse(filename=None):
	nl = traj = world = None
	testname = filename if filename is not None else "0.1/groceries.json"
	dir_path = os.path.dirname(os.path.realpath(__file__))
	dir_path = dir_path[:dir_path.index("TabulaSynthesizer")] + "TabulaSynthesizer/synthesizer/test_data/" + testname
	with open(dir_path, "r") as infile:
		data = json.load(infile)
		nl = data["nl"]
		traj = data["trajectories"]
		world = data["world"]
	return nl, traj, world
