class NLData:

	def __init__(self, content, parser):
		self.content = content
		self.task_hints = None
		self.parser = parser

	def parse_content(self):
		self.task_hints = self.parser.parse(self.content)

	def get_task_hints(self):
		return self.task_hints