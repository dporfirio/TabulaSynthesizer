import json
from wordnet_wrapper import *
from nltk.stem.snowball import SnowballStemmer


class EntityDB:

	def __init__(self, stemmer=SnowballStemmer("english")):
		self.entities = {}    # mapping entities to objects
		self.obj2entity = {}  # mapping objects to entities
		self.stemmer = stemmer

		# initialize the entities dict
		entities = {}

		# access the cmd json file
		ent_file = None
		with open("entities.json","r") as infile:
			ent_file = json.load(infile)

		if ent_file is None:
			print("ERROR: could not file cmd_components file")
			exit()

		for obj, obj_dict in ent_file.items():
			for category in obj_dict["categories"]:
				if category not in entities:
					entities[category] = []
				entities[category].append(obj)

		# now assemble the eneities objects
		established_entities = {}
		for entity, obj_list in entities.items():
			self.entities[entity] = []
			for obj in obj_list:
				if obj not in established_entities:
					self.obj2entity[obj] = []
					established_entities[obj] = Entity(obj, self.obj2entity[obj], stemmer)
				self.obj2entity[obj].append(entity)
				self.entities[entity].append(established_entities[obj])

		# must add an extra
		if "robot" in self.entities:
			print("ERROR: duplicate robot entity")
			exit()
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

		return (None, ent_list[0], name)

	def get_entities(self, text):
		print(text)
		nonstandard_arr = text.split()
		print(nonstandard_arr)
		standard_arr = []
		for word in nonstandard_arr:
			standard_arr.append(self.stemmer.stem(word))
			print(self.stemmer.stem(word))
		text = " ".join(standard_arr)
		print(text)
		text = " {} ".format(text)
		print(text)

		# print("getting entities for {}".format(text))

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
		self.synonyms, self.antonyms = self.wordnet.get_synonyms_antonyms(self.name)
		self.synsets = self.wordnet.get_synsets_by_word(self.name)
		self.categories = categories
		self.categories.sort()

		# compute the standardized version of the entity
		# (stemmed and lower-cased)
		standard_name = self.name.lower()
		self.standard_name = stemmer.stem(standard_name)
		self.stemmer = stemmer

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.name

	def duplicate(self):
		return Entity(self.name, self.categories, self.stemmer)
