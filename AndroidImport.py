import sublime, sublime_plugin, plyj, model, json, os

class AndroidClass():
    def __init__(self, name, package):
        self.name = name
        self.package = package

# Load the list of classes
plugin_path = os.path.dirname(os.path.abspath(__file__))
json_file = open(plugin_path + '/classes.json')
raw_class_list = json.loads(json_file.read())
# Go through the class list and create a dictorary of the classes and packages
class_list = dict()
for a_class in raw_class_list:
    split_label = a_class['label'].split('.')
    class_name = split_label[-1]
    if class_name[0].isupper():
        class_list[class_name] = a_class['label']

class AndroidImportCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get the current file contents as a string and parse the java into a tree
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))
        parser = plyj.Parser()
        tree = parser.parse_string(file_contents)

        # Start recursing through the tree looking for classes
        self.classes = set()
        for thing in tree.type_declarations:
            self.look_for_classes(thing)

        # Print out the classes
        print(self.classes)

        # Send a status message to show completion
        sublime.status_message("Finished importing Android classes")

    # Only enabled for java files - Check this by looking for "java" in the current syntax name
    def is_enabled(self):
        return "java" in self.view.syntax_name(0)

    # A recursive method for searching for classes in the java parse tree
    def look_for_classes(self, thing):
        # If the current thing is a "Type" then add it to the class list
        if type(thing) is model.Type:
            self.classes.add(thing.name.value)

        # Recuse through all lists and "SourceElements" in the attributes of the current thing
        attributes = filter(lambda a: not a.startswith('__') and not callable(getattr(thing,a)), dir(thing))
        for a in attributes:
            next_thing = getattr(thing, a)

            if isinstance(next_thing, model.SourceElement):
                self.look_for_classes(next_thing)
            elif hasattr(next_thing, '__iter__'):
                for other_thing in next_thing:
                    self.look_for_classes(other_thing)
