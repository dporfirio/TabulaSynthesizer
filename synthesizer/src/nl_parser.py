import spacy
import nltk
import copy
import contractions
import string
from program import *
from entities import *
from wordnet_wrapper import *
nlp = spacy.load("en_core_web_sm")
# from snips_nlu import SnipsNLUEngine
# from snips_nlu.default_configs import CONFIG_EN


class NLParser:

	def __init__(self):
		self.action_data = ActionData.get_instance()
		self.entity_data = EntityData.get_instance()
		self.lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
		self.ww = WordnetWrapper()
		self.vnet3 = nltk.corpus.util.LazyCorpusLoader('verbnet3', nltk.corpus.reader.verbnet.VerbnetCorpusReader,r'(?!\.).*\.xml')

	def preprocess_text(self, text):
		# convert everything to lowercase
		text = text.lower()

		# remove contractions
		text = contractions.fix(text)

		# remove punctuation
		# col 1: split string
		a_list = nltk.tokenize.sent_tokenize(text)

		# col 2:
		b_list = [] 
		table = str.maketrans('', '', string.punctuation)
		for sent in a_list:
			words = sent.split()
			stripped = [w.translate(table) for w in words]
			processed_sent = " ".join(stripped)
			b_list.append(processed_sent.lower())

		return b_list

	def is_noun(self, tag):
		if tag == "NN" or tag == "NNS" or tag == "NNP" or tag == "NNPS":
			return True
		return False

	def is_pronoun(self, tag):
		if tag == "PRP" or tag == "PRP$":
			return True
		return False

	def is_verb(self, tag):
		if tag == "VB" or tag == "VBD" or tag == "VBN" or tag == "VBG" or tag == "VBP" or tag == "VBZ":
			return True
		return False

	def tag_sentences(self, sentence):
		sent_split = sentence.split()
		sentence = " ".join(sent_split)
		entities = self.entity_data.get_entities(sentence)
		doc = nlp(sentence)
		tags = [(str(token), token.tag_) for token in doc]
		nouns = [(i, tags[i][0], tags[i][1]) for i in range(len(tags)) \
				if self.is_noun(tags[i][1]) \
				and not any(ent[1].name == self.entity_data.stemmer.stem(tags[i][0]) for ent in entities)]
		pronouns = [(i, tags[i][0], tags[i][1]) for i in range(len(tags)) if self.is_pronoun(tags[i][1])]
		verbs = [(i, self.lemmatizer.lemmatize(tags[i][0], "v"), tags[i][1]) for i in range(len(tags)) if self.is_verb(tags[i][1])]
		return entities, nouns, pronouns, verbs

	def get_task_hints(self, verbs, entities, nouns, pronouns):
		'''
		Collect (1) commands, (2) half-commands [commands with missing entities], and (3) constraints [entities without a command]
		Collect unparameterized commands (ucoms) by looking at each verb
		TODO: make this a LOT more robust
		'''

		def remove_duplicate_entities(remaining_entities, entity):
			idxs = []
			for i, ent in enumerate(remaining_entities):
				if ent[1] == entity[1]:
					idxs.append(i)
			idxs.reverse()
			for idx in idxs:
				del remaining_entities[idx]

		def contains_more_entities(curr, best):
			if len(curr) > len(best):
				return True
			if len([c for c in curr if c != "HOLE"]) > len([b for b in best if b != "HOLE"]):
				return True
			return False

		def fit_entities_to_command(action_data, remaining_entities, curr_ordered_entities, best_ordered_entities):
			if len(curr_ordered_entities) > len(action_data["argtypes"]):
				return
			if len(remaining_entities) == 0 or len(curr_ordered_entities) == len(action_data["argtypes"]): #and len(curr_ordered_entities) > len(best_ordered_entities):
				# fill remaining entities with holes if necessary
				for i in range(len(curr_ordered_entities), len(action_data["argtypes"])):
					curr_ordered_entities.append("HOLE")
				if contains_more_entities(curr_ordered_entities, best_ordered_entities):
					best_ordered_entities.clear()
					best_ordered_entities.extend(curr_ordered_entities)
			for i, entity in enumerate(remaining_entities):
				action_data_argtype = action_data["argtypes"][len(curr_ordered_entities)]
				_curr_ordered_entities = copy.copy(curr_ordered_entities)
				val = "HOLE"
				if action_data_argtype in entity[1].categories:
					val = entity
				_curr_ordered_entities.append(val)
				_remaining_entities = copy.copy(remaining_entities)[:i]
				_remaining_entities.extend(remaining_entities[i + 1:])
				remove_duplicate_entities(_remaining_entities, entity)
				fit_entities_to_command(action_data, _remaining_entities, _curr_ordered_entities, best_ordered_entities)

		task_hints = {"commands": [], "half-commands": [], "constraints": copy.copy(entities)}
		for verb_data in verbs:
			candidate_action_names = []
			for cmd_name, cmd_data in self.action_data.action_primitives.items():
				verb_classes = self.vnet3.classids(verb_data[1])
				if any([cmd_verb in vc for vc in verb_classes for cmd_verb in cmd_data["verbnet"]]):
					candidate_action_names.append(cmd_name)
			best_action_name = None
			best_entities = []
			print(candidate_action_names)
			for action_name in candidate_action_names:
				curr_entities = []
				entities_copy = copy.copy(entities)
				required_args = self.action_data.action_primitives[action_name]["argnames"]
				missing_args = len(required_args) - len(entities_copy)
				for i in range(max(0,missing_args)):
					entities_copy.append((None, self.entity_data.get_null_entity()))
				print(action_name)
				print(entities_copy)
				fit_entities_to_command(self.action_data.action_primitives[action_name], entities_copy, [], curr_entities)
				if best_action_name is None or curr_entities.count("HOLE") < best_entities.count("HOLE"):
					best_action_name = action_name
					best_entities = curr_entities
			for ent in best_entities:
				to_remove = [unused_ent for unused_ent in task_hints["constraints"] if unused_ent[0] == ent[0]]
				task_hints["constraints"] = list(set(task_hints["constraints"]).difference(set(to_remove)))
			args = {}
			if best_action_name is None:
				continue
			print(best_action_name)
			print(best_entities)
			for i, argname in enumerate(self.action_data.action_primitives[best_action_name]["argnames"]):
				args[argname] = ParamFilled(best_entities[i][1]) if best_entities[i] != "HOLE" else ParamHole()
			command = Action(best_action_name, args)
			command_list = task_hints["commands"]
			if "HOLE" in best_entities:
				command_list = task_hints["half-commands"]
			command_list.append(command)
		print(task_hints)
		print(task_hints["half-commands"][0])
		exit()
		return task_hints

	def convert_speech_simple(self, sentence):
		original_sentence = sentence.split()
		contains_speech = False
		for i, word in enumerate(original_sentence):
			if word == "say" or word == "ask":
				contains_speech = True
				break
		sentence = original_sentence[:i+1]
		if contains_speech:
			sentence.append(self.entity_data.get_entity("content", "$speech").name)
		return " ".join(sentence), " ".join(original_sentence[i+1:])

	def parse(self, text):
		task_hints = []
		# TODO: call GPT-3 to convert commands to speech
		sentences = self.preprocess_text(text)
		for sentence in sentences:
			sentence, speech = self.convert_speech_simple(sentence)
			print(sentence)
			print(speech)
			entities, nouns, pronouns, verbs = self.tag_sentences(sentence)
			print(entities)
			task_hint = self.get_task_hints(verbs, entities, nouns, pronouns)
			for command in task_hint["commands"]:
				if "speech" in command.args:
					speech_ent = SpeechEntity("$speech", ["content"], speech)
					self.entity_data.add_new_entity(speech_ent)
					command.args["speech"] = ParamFilled(speech_ent)
			task_hints.append(task_hint)
		return task_hints
