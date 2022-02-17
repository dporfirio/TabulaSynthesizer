class Planner:

	def __init__(self):
		pass

	def plan(self, sketch, hints):
		# collapse program into transition system

		# get a SORTED list of ALL traces with holes (avoid multiple repeats of loops)
		# we can trim prefixes before the first hole by enumerating all possible preconditions

		# best_solution = None
		# bad solutions = []
		# n = 1

		# while there is no solution:

			# find solution for n traces (avoiding previous bad solutions), prioritizing the traces that have the MOST holes

			# evaluate solution on ALL (non-n) traces

			# if there is a solution, set best solution break!

			# otherwise, add the bad solution to the list of bad solutions, n += 1

		return sketch