import sublime, sublime_plugin, json, sys, os, collections, zipfile

plugin_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(plugin_path)

import plyj, model

class AndroidImportCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        # Setup the plugin in the super class
        sublime_plugin.TextCommand.__init__(self, view)

        try:
            plugin_path = sublime.packages_path() + '/AndroidImport'
            classes_file = open(plugin_path + '/classes.txt')
        except IOError:
            try:
                plugin_path = sublime.installed_packages_path() + '/AndroidImport'
                classes_file = open(plugin_path + '/classes.txt')
            except IOError:
                try:
                    plugin_path = sublime.packages_path() + '/AndroidImport.sublime-package'
                    with zipfile.ZipFile(plugin_path) as package_zip:
                        classes_file = package_zip.open('classes.txt')
                except IOError:
                    try:
                        plugin_path = sublime.installed_packages_path() + '/AndroidImport.sublime-package'
                        with zipfile.ZipFile(plugin_path) as package_zip2:
                            print(package_zip2)
                            classes_file = package_zip2.open('classes.txt')
                    except IOError:
                        sublime.error_message("Couldn't load AndroidImport plugin. Maybe try reinstalling...")
                        return

        self.android_class_list = dict()
        for line in classes_file.readlines():
            line_parts = line.decode("utf-8").split('::')
            key = line_parts[0]
            line_parts.remove(key)

            self.android_class_list[key] = list()
            for package in line_parts:
                self.android_class_list[key].append(''.join(package.split()))

    def run(self, edit):
        self.classes = set()
        self.edit = edit

        # Change directory to the plugin dir
        if not plugin_path.endswith('.sublime-package'):
            prev_path = os.path.dirname(os.path.abspath(__file__))
            os.chdir(plugin_path)

        # Get the current file contents as a string
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))
        # Parse the java into a tree
        parser = plyj.Parser()
        tree = parser.parse_string(file_contents)

        self.look_for_classes(tree) # Start recursing through the tree looking for classes
        found_android_classes = self.filter_android_classes()
        current_imports = self.find_imports(tree)
        imports = self.find_missing_imports(found_android_classes, current_imports)
        import_string = self.create_import_string(imports.required)
        insert_point = self.find_import_position(file_contents)
        self.view.insert(edit, insert_point, import_string)

        # Check if we have any required user input
        if len(imports.action_needed) > 0:
            # TODO: Do some user input
            self.action_needed_imports = imports.action_needed
            self.ask_user_to_pick_package()

        # Send a status message to show completion
        number_of_imports = str(len(imports.required))
        sublime.status_message("Finished importing " + number_of_imports + " Android classes")

        # Put the current dir back, just incase
        if not plugin_path.endswith('.sublime-package'):
            os.chdir(prev_path)

    def ask_user_to_pick_package(self):
        if len(self.action_needed_imports) > 0:
            self.package_choices = self.action_needed_imports.pop()
            sublime.active_window().show_quick_panel(self.package_choices, self.user_picked_package)

    def user_picked_package(self, index):
        if index >= 0:
            picked_package = self.package_choices[index]
            split_label = picked_package.split('.')
            # Dont bother importing java.lang classes
            if len(split_label) >=2 and split_label[0] == 'java' and split_label[1] == 'lang':
                pass
            else:
                self.view.run_command('android_insert', {'picked_package': picked_package})
        # Recurse again to pick the next one
        self.ask_user_to_pick_package()

    # Only enabled for java files - Check this by looking for "java" in the current syntax name
    def is_enabled(self):
        return "java" in self.view.scope_name(0)

    # Filters out the found class list to just the ones which are in the Android SDK
    def filter_android_classes(self):
        found_android_classes = list()

        for found_class in self.classes:
            if found_class in self.android_class_list:
                found_android_classes.append(found_class)

        return found_android_classes

    # Gets the list of imports currently in the java file
    def find_imports(self, tree):
        current_imports = set()

        for an_import in tree.import_declarations:
            current_imports.add(an_import.name.value.split(".")[-1])

        return current_imports

    # Returns a list of packages which have not been imported
    def find_missing_imports(self, found_android_classes, current_imports):
        imports = collections.namedtuple('Check', ['required', 'action_needed'])
        imports.required = set()
        imports.action_needed = list()

        for package in found_android_classes:
            # Check each to see if it's already imported
            required = True
            if package in current_imports:
                required = False

            # If not then add it to the correct list
            if required is not False:
                required_package_list = self.android_class_list.get(package)
                if len(required_package_list) == 1:
                    package_path = required_package_list[0]
                    split_label = package_path.split('.')
                    # Dont bother importing java.lang classes
                    if len(split_label) >=2 and split_label[0] == 'java' and split_label[1] == 'lang':
                        pass
                    else:
                        imports.required.add(package_path)
                else:
                    imports.action_needed.append(required_package_list)

        return imports

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
            self.view.insert(self.edit, self.view.text_point(1, 0), '\n')
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
            parts = results.class_name.split(".")
            for part in parts:
                if part[0].isupper():
                    self.classes.add(part)
                    break

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
        if type(thing) is model.Type and type(thing.name) is model.Name:
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

class AndroidInsertCommand(AndroidImportCommand):
    def run(self, edit, picked_package):
        import_string = self.create_import_string([picked_package])
        file_contents = self.view.substr(sublime.Region(0, self.view.size()))
        insert_point = self.find_import_position(file_contents)
        self.view.insert(edit, insert_point, import_string)
