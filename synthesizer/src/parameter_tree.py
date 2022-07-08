import yaml


class ParameterTree:

	def __init__(self):
		file = open("parameter_tree.yaml", "r")
		self.tree = yaml.load(file, yaml.FullLoader)


if __name__ == "__main__":
	pt = ParameterTree()
	print(pt.tree)