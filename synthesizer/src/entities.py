import json
import os
from wordnet_wrapper import *
from nltk.stem.snowball import SnowballStemmer


class EntityData:

	'''
	Singleton Storage Class
	'''
	__instance = None

	@staticmethod
	def get_instance():
		if EntityData.__instance is None:
			EntityData()
		return EntityData.__instance

	def __init__(self):
		if EntityData.__instance is not None:
			raise Exception("EntityData is a singleton!")
		else:
			EntityData.__instance = self
		self.stemmer=SnowballStemmer("english")
		self.entities = {}    # mapping entities to objects
		self.obj2category = {}  # mapping objects to entities

	def load_entities_from_file(self, filename="entities"):
		# access the cmd json file
		ent_file = None
		dir_path = os.path.dirname(os.path.realpath(__file__))
		with open("{}/{}.json".format(dir_path, filename),"r") as infile:
			ent_file = json.load(infile)

		if ent_file is None:
			print("ERROR: could not file cmd_components file")
			exit()

		self.init(ent_file)

	def update_available_entities(self, ent_file):
		self.entities = {}
		self.obj2category = {}
		self.load_entities_from_file("non_object_entities")
		self.init(ent_file)

	def init(self, ent_file):
		# initialize the entities dict
		entities = {}
		for obj, obj_dict in ent_file.items():
			for category in obj_dict["categories"]:
				if category not in entities:
					entities[category] = []
				entities[category].append(obj)

		# now assemble the eneities objects
		established_entities = {}
		for category, obj_list in entities.items():
			self.entities[category] = []
			for obj in obj_list:
				if obj not in established_entities:
					self.obj2category[obj] = []
					established_entities[obj] = Entity(obj, self.obj2category[obj], self.stemmer)
				self.obj2category[obj].append(category)
				self.entities[category].append(established_entities[obj])

		# must add an extra
		#if "robot" in self.entities:
		#	print("ERROR: duplicate robot entity")
		#	exit()
		self.entities["robot"] = [Entity("robot", ["robot"]), Entity("you", ["robot"])]

	def get_entity_dict(self):
		return self.entities

	def get_entity(self, category, name):
		if category not in self.entities:
			print("ERROR: cannot find queried entity category")
			exit()

		ent_objs = self.entities[category]
		ent_list = [entity for entity in ent_objs if entity.name == name]
		if len(ent_list) == 0:
			print("ERROR: cannot find entity object within category")
			exit()

		return ent_list[0]

	def get_null_entity(self):
		return self.get_entity("null", "null")

	def add_new_entity(self, entity):
		categories = entity.categories
		for cat in categories:
			if cat not in self.entities:
				self.entities[cat] = []
			if any([True for other in self.entities[cat] if entity.equals(other)]):
				continue
			self.entities[cat].append(entity)
		self.obj2category[entity] = categories
		print(self.entities)
		print(entity)
		print(type(entity))
		#exit()

	def get_entities(self, text):
		nonstandard_arr = text.split()
		standard_arr = []
		for word in nonstandard_arr:
			standard_arr.append(self.stemmer.stem(word))
		text = " ".join(standard_arr)
		text = " {} ".format(text)

		def determine_entity_location(sentence, entity):

			sentence = "{} ".format(sentence.strip())

			# print("determining location of: {}".format(entity))
			idx = 0
			while " " in sentence:
				if sentence.index(entity) == 0:
					break
				idx += 1
				# print(sentence)
				sentence = sentence[sentence.index(" ") + 1:]

			return idx

		entities = []
		# TODO: this looks like we can only return one location of an entity, even if there are multiple
		for entity_class, entity_list in self.entities.items():
			for entity in entity_list:
				if " {} ".format(entity.standard_name) in text:
					print("ADDING")
					entities.append((determine_entity_location(text, "{} ".format(entity.standard_name)), entity, entity_class))

		# discard entities that are subsets of other entities
		# e.g. if we have entities "kitchen" and "kitchen cabinets" and they overlap, discard kitchen
		to_discard = []
		for i, e1 in enumerate(entities):
			if i in to_discard:
				continue
			e1_end = e1[0] + len(e1[1].standard_name)
			for j, e2 in enumerate(entities):
				if i == j or j in to_discard:
					continue
				e2_end = e2[0] + len(e2[1].standard_name)
				if e2[0] >= e1[0] and e2_end <= e1_end and not (e2[0] == e1[0] and e2_end == e1_end):  # is e2 inside of 1?
					to_discard.append(j)
		to_discard.sort(reverse=True)
		for j in to_discard:
			del entities[j]

		return entities


class Entity:

	def __init__(self, name, categories, stemmer=SnowballStemmer("english")):
		self.wordnet = WordnetWrapper()
		self.name = name
		#self.synonyms, self.antonyms = self.wordnet.get_synonyms_antonyms(self.name)
		#self.synsets = self.wordnet.get_synsets_by_word(self.name)
		self.categories = categories
		self.categories.sort()

		# compute the standardized version of the entity
		# (stemmed and lower-cased)
		standard_name = self.name.lower()
		self.standard_name = stemmer.stem(standard_name)
		self.stemmer = stemmer

	def equals(self, other):
		if other.name != self.name:
			return False
		if other.categories != self.categories:
			return False
		return True

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def duplicate(self):
		return Entity(self.name, self.categories, self.stemmer)


class SpeechEntity(Entity):

	def __init__(self, name, categories, speech):
		super().__init__(name, categories)
		self.speech = speech

	def equals(self, other):
		if other.name != self.name:
			return False
		if other.categories != self.categories:
			return False
		if type(other) != SpeechEntity:
			return False
		if other.speech != self.speech:
			return False
		return True

	def __str__(self):
		return "speech: {}".format(self.speech)