import json
import sys
import os


def parse():
	nl = traj = world = None
	testname = sys.argv[1]
	path = os.getcwd()
	path = path[:path.index("src")] + "test_data/" + testname
	with open(path, "r") as infile:
		data = json.load(infile)
		nl = data["nl"]
		traj = data["trajectories"]
		world = None
	return nl, traj, world
