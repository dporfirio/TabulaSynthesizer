import copy


class World:

	'''
	Singleton Storage Class
	'''
	__instance = None

	@staticmethod
	def get_instance():
		if World.__instance is None:
			print("ERROR: world state not initialized.")
			exit()
		return World.__instance

	def __init__(self, world, program):
		self.init(world, program)
		World.__instance = self

	def init(self, world, program):
		self.world = world
		self.fill_world()
		self.program = program

	def get_program(self):
		return self.program

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