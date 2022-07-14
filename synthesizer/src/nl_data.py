class NLData:

	def __init__(self, content, parser):
		self.content = Content(content)
		self.parser = parser

	def parse_content(self):
		self.content.add_intervals(self.parser.parse_from_raw_text(self.content.get_text()))

	def get_task_hints(self):
		return self.content.get_task_hints()


class Content:

	def __init__(self, text):
		self.text = text
		self.intervals = []

	def get_text(self):
		return self.text

	def add_intervals(self, intervals):
		self.intervals = intervals

	def get_task_hints(self):
		hints = []
		for interval in self.intervals:
			if interval.get_task_hint() is not None:
				hints.append(interval.get_task_hint())
		return hints


class Interval:

	def __init__(self, start, end, classification):
		self.start = start  # char position (not including spaces)
		self.end = end  # char position (not including spaces)
		self.classification = classification  # cmd, trigger, or conditional
		self.task_hint = None  # the actual action(s), organized as a task hint

	def set_task_hint(self, task_hint):
		self.task_hint = task_hint

	def get_task_hint(self):
		return self.task_hint

	def get_text_from_interval(self, text):
		i = 0
		substring = ""
		active = False
		for char in text:
			if i == self.start:
				active = True
			elif i == self.end:
				active = False
			if active:
				substring += char
			if char != " ":
				i += 1
		return substring

	def __str__(self):
		s = "INTERVAL: ({}, {})\n".format(self.start, self.end)
		s += "    {}\n".format(self.classification)
		for hint_tup in self.task_hint["commands"]:
			for hint in hint_tup:
				s += "      CMD: {}\n".format(hint)
		for hint_tup in self.task_hint["half-commands"]:
			for hint in hint_tup:
				s += "      CMD: {}\n".format(hint)
		for hint_tup in self.task_hint["constraints"]:
			for hint in hint_tup:
				s += "      CMD: {}\n".format(hint)
		return s
