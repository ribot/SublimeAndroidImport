import sublime, sublime_plugin, plyj, model, json, os, collections

plugin_path = os.path.dirname(os.path.abspath(__file__))

class AndroidImportCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        self.classes = set()

        # Setup the plugin in the super class
        sublime_plugin.TextCommand.__init__(self, view)

        # Load the list of classes
        json_file = open(plugin_path + '/classes.json')
        raw_class_list = json.loads(json_file.read())
        # Go through the class list and create a dictorary of the classes and packages
        self.android_class_list = dict()
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
                    if class_name not in self.android_class_list:
                        self.android_class_list[class_name] = list()

                    self.android_class_list[class_name].append(a_class['label'])

    def run(self, edit):
        # Change directory to the plugin dir
        prev_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(plugin_path)

        # Get the current file contents as a string
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))
        # Parse the java into a tree
        parser = plyj.Parser()
        tree = parser.parse_string(file_contents)

        self.look_for_classes(tree) # Start recursing through the tree looking for classes
        found_android_classes = filter_android_classes()
        current_imports = find_imports(tree)
        required_imports = find_missing_imports(found_android_classes, current_imports)
        import_string = create_import_string(required_imports)
        insert_point = find_import_position(file_contents)
        self.view.insert(edit, insert_point, import_string)

        # Send a status message to show completion
        number_of_imports = str(len(required_imports))
        sublime.status_message("Finished importing " + number_of_imports + " Android classes")

        # Put the current dir back, just incase
        os.chdir(prev_path)

    # Only enabled for java files - Check this by looking for "java" in the current syntax name
    def is_enabled(self):
        return "java" in self.view.syntax_name(0)

    # Filters out the found class list to just the ones which are in the Android SDK
    def filter_android_classes(self):
        found_android_classes = list()

        for found_class in self.classes:
            if found_class in self.android_class_list:
                found_android_classes.append(self.android_class_list[found_class])

        return found_android_classes

    # Gets the list of imports currently in the java file
    def find_imports(self, tree):
        current_imports = set()

        for an_import in tree.import_declarations:
            current_imports.add(an_import.name.value)

        return current_imports

    # Returns a list of packages which have not been imported
    def find_missing_imports(self, found_android_classes, current_imports):
        required_imports = set()

        for packages in found_android_classes:
            if len(packages) == 1:
                package = packages[0]
                if package not in current_imports:
                    required_imports.add(package)
            # TODO: We need to ask the user which package they want to use
            else:
                print 'Multiple packages in ' + str(packages)

        return required_imports

    # Finds the position to add the imports. Will be at the end of the imports or one
    # line under the package decleration if there are no imports yet
    def find_import_position(self, file_contents):
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

        return insert_point

    # Returns the import string given the list of required imports
    def create_import_string(self, required_imports):
        import_string = ''
        for package in required_imports:
            import_string += 'import ' + package + ';\n'
        return import_string

    # A recursive method for searching for classes in the java parse tree
    def look_for_classes(self, thing):
        # Check if we need to add this thing to the class list
        results = self.check_add_to_class_list(thing)
        if results.should_add:
            self.classes.add(results.class_name)

        # Recuse through all lists and "SourceElements" in the non-callable attributes of the current thing
        attributes = filter(lambda a: not a.startswith('__') and not callable(getattr(thing,a)), dir(thing))
        for a in attributes:
            next_thing = getattr(thing, a)
            if isinstance(next_thing, model.SourceElement):
                self.look_for_classes(next_thing)
            elif hasattr(next_thing, '__iter__'):
                for other_thing in next_thing:
                    self.look_for_classes(other_thing)

    # Checks if the thing describes a class and if so returns a turple with True and the name to add
    def check_add_to_class_list(self, thing):
        # Get the return turple ready
        return_values = collections.namedtuple('Check', ['should_add', 'class_name'])
        should_add = False
        class_name = None

        # If the current thing is a "Type" then add it to the class list
        if type(thing) is model.Type:
            should_add = True
            class_name = thing.name.value
        # If its a method invocation we may be calling a static method of a class
        elif type(thing) is model.MethodInvocation and type(thing.name) is model.Name:
            possible_class_name = thing.name.value.split('.')[0]
            if possible_class_name[0].isupper():
                should_add = True
                class_name = possible_class_name
        # Find any other names which could be class names
        elif type(thing) is model.Name:
            possible_class_name = thing.value.split('.')[0]
            if possible_class_name[0].isupper():
                should_add = True
                class_name = possible_class_name
        
        return return_values(should_add, class_name)
