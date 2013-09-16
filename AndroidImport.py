import sublime, sublime_plugin

import parser as plyj
import model

class AndroidImportCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		if "java" in self.view.syntax_name(0):
			file_contents = self.view.substr(sublime.Region(0, self.view.size()))

			parser = plyj.Parser()
			tree = parser.parse_string(file_contents)

			self.classes = set()
			for thing in tree.type_declarations:
				self.look_for_classes(thing)

			print(self.classes)
		else:
			print('Not a java file')

	def look_for_classes(self, thing):
		if type(thing) is model.Type:
			self.classes.add(thing.name.value)

		attributes = filter(lambda a: not a.startswith('__') and not callable(getattr(thing,a)), dir(thing))
		for a in attributes:
			next_thing = getattr(thing, a)

			if isinstance(next_thing, model.SourceElement):
				self.look_for_classes(next_thing)
			elif hasattr(next_thing, '__iter__'):
				for other_thing in next_thing:
					self.look_for_classes(other_thing)

	def is_enabled(self):
		return "java" in self.view.syntax_name(0)
