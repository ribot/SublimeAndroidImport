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
android_class_list = dict()
for a_class in raw_class_list:
    # Splits the package list and gets the last part which is the class
    split_label = a_class['label'].split('.')
    class_name = split_label[-1]
    # Checks the first character is uppercase and discards if not, not a class
    # Also digards if it's the R class, for now
    if class_name[0].isupper() and class_name != 'R':
        if len(split_label) >=2 and split_label[0] == 'java' and split_label[1] == 'lang':
            pass
        else:
            if class_name not in android_class_list:
                android_class_list[class_name] = list()

            android_class_list[class_name].append(a_class['label'])

class AndroidImportCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        prev_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(plugin_path)

        # Get the current file contents as a string and parse the java into a tree
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))
        parser = plyj.Parser()
        tree = parser.parse_string(file_contents)

        # Start recursing through the tree looking for classes
        self.classes = set()
        for thing in tree.type_declarations:
            self.look_for_classes(thing)

        # Filter to just the android classes
        found_android_classes = list()
        for found_class in self.classes:
            if found_class in android_class_list:
                found_android_classes.append(android_class_list[found_class])

        # Look at all current imports
        current_imports = set()
        for an_import in tree.import_declarations:
            current_imports.add(an_import.name.value)

        # Get a set of imports which are still required
        required_imports = set()
        for packages in found_android_classes:
            if len(packages) == 1:
                package = packages[0]
                if package not in current_imports:
                    required_imports.add(package)
            # TODO: We need to ask the user which package they want to use
            else:
                print 'Multiple packages in ' + str(packages)

        # Create an import string to insert
        import_string = ''
        for package in required_imports:
            import_string += 'import ' + package + ';\n'

        # Find the last line of imports
        lines = file_contents.split('\n')
        got_to_imports = False
        insert_point = None
        for i, line in enumerate(lines):
            if line.startswith('import '):
                got_to_imports = True
            elif not line.startswith('import ') and got_to_imports:
                # Found last import line
                insert_point = self.view.text_point(i, 0)
                break
        if insert_point is None:
            self.view.insert(edit, self.view.text_point(1, 0), '\n')
            insert_point = self.view.text_point(2, 0)

        # Insert the new imports
        self.view.insert(edit, insert_point, import_string)

        # Send a status message to show completion
        number_of_imports = str(len(required_imports))
        sublime.status_message("Finished importing " + number_of_imports + " Android classes")

        os.chdir(prev_path)

    # Only enabled for java files - Check this by looking for "java" in the current syntax name
    def is_enabled(self):
        return "java" in self.view.syntax_name(0)

    # A recursive method for searching for classes in the java parse tree
    def look_for_classes(self, thing):
        # If the current thing is a "Type" then add it to the class list
        if type(thing) is model.Type:
            self.classes.add(thing.name.value)
        # If its a method invocation we may be calling a static method of a class
        elif type(thing) is model.MethodInvocation and type(thing.name) is model.Name:
            possible_class_name = thing.name.value.split('.')[0]
            if possible_class_name[0].isupper():
                self.classes.add(possible_class_name)
        # Find any other names which could be class names
        elif type(thing) is model.Name:
            possible_class_name = thing.value.split('.')[0]
            if possible_class_name[0].isupper():
                self.classes.add(possible_class_name)

        # Recuse through all lists and "SourceElements" in the attributes of the current thing
        attributes = filter(lambda a: not a.startswith('__') and not callable(getattr(thing,a)), dir(thing))
        for a in attributes:
            next_thing = getattr(thing, a)

            if isinstance(next_thing, model.SourceElement):
                self.look_for_classes(next_thing)
            elif hasattr(next_thing, '__iter__'):
                for other_thing in next_thing:
                    self.look_for_classes(other_thing)
