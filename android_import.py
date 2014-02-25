import sublime, sublime_plugin, json, sys, os, collections, zipfile

pluginPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))

import android_parser

class AndroidImportCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        # Setup the plugin in the super class
        sublime_plugin.TextCommand.__init__(self, view)

        try:
            pluginPath = sublime.packages_path() + '/AndroidImport'
            classes_file = open(pluginPath + '/classes.txt')
        except IOError:
            try:
                pluginPath = sublime.installed_packages_path() + '/AndroidImport'
                classes_file = open(pluginPath + '/classes.txt')
            except IOError:
                try:
                    pluginPath = sublime.packages_path() + '/AndroidImport.sublime-package'
                    with zipfile.ZipFile(pluginPath) as package_zip:
                        classes_file = package_zip.open('classes.txt')
                except IOError:
                    try:
                        pluginPath = sublime.installed_packages_path() + '/AndroidImport.sublime-package'
                        with zipfile.ZipFile(pluginPath) as package_zip2:
                            classes_file = package_zip2.open('classes.txt')
                    except IOError:
                        sublime.error_message("Couldn't load AndroidImport plugin. Maybe try reinstalling...")
                        return

        self.androidClassList = dict()
        for line in classes_file.readlines():
            line_parts = line.split('::')
            key = line_parts[0]
            line_parts.remove(key)

            self.androidClassList[key] = list()
            for package in line_parts:
                self.androidClassList[key].append(''.join(package.split()))

    def run(self, edit):
        self.edit = edit

        # Change directory to the plugin dir
        if not pluginPath.endswith('.sublime-package'):
            prevPath = os.path.dirname(os.path.abspath(__file__))
            os.chdir(pluginPath)

        # Get the current file contents as a string
        fileContents = self.view.substr(sublime.Region(0, self.view.size()))
        # Parse the java into a tree
        androidParser = android_parser.AndroidParser()
        imports = androidParser.parse(fileContents, self.androidClassList)

        importString = self.createImportString(imports.required)
        insertPoint = self.findImportPosition(fileContents)
        self.view.insert(edit, insertPoint, importString)

        # Check if we have any required user input
        if len(imports.actionNeeded) > 0:
            # TODO: Do some user input
            self.actionNeeded_imports = imports.actionNeeded
            self.askUserToPickPackage()

        # Send a status message to show completion
        numberOfImports = str(len(imports.required))
        sublime.status_message("Finished importing " + numberOfImports + " Android classes")

        # Put the current dir back, just incase
        if not pluginPath.endswith('.sublime-package'):
            os.chdir(prevPath)

    def askUserToPickPackage(self):
        if len(self.actionNeeded_imports) > 0:
            self.packageChoices = self.actionNeeded_imports.pop()
            sublime.active_window().show_quick_panel(self.packageChoices, self.userPickedPackage)

    def userPickedPackage(self, index):
        if index >= 0:
            pickedPackage = self.packageChoices[index]
            splitLabel = pickedPackage.split('.')
            # Dont bother importing java.lang classes
            if len(splitLabel) >=2 and splitLabel[0] == 'java' and splitLabel[1] == 'lang':
                pass
            else:
                self.view.run_command('android_insert', {'pickedPackage': pickedPackage})
        # Recurse again to pick the next one
        self.askUserToPickPackage()

    # Only enabled for java files - Check this by looking for "java" in the current syntax name
    def is_enabled(self):
        return "java" in self.view.scope_name(0)

    # Finds the position to add the imports. Will be at the end of the imports or one
    # line under the package decleration if there are no imports yet
    def findImportPosition(self, fileContents):
        lines = fileContents.split('\n')
        gotToImports = False
        insertPoint = None
        for i, line in enumerate(lines):
            if line.startswith('import '):
                gotToImports = True
            elif not line.startswith('import ') and gotToImports:
                # Found last import line
                insertPoint = self.view.text_point(i, 0)
                break

        if insertPoint is None:
            self.view.insert(self.edit, self.view.text_point(1, 0), '\n')
            insertPoint = self.view.text_point(2, 0)

        return insertPoint

    # Returns the import string given the list of required imports
    def createImportString(self, required_imports):
        importString = ''
        for package in required_imports:
            importString += 'import ' + package + ';\n'
        return importString

class AndroidInsertCommand(AndroidImportCommand):
    def run(self, edit, picked_package):
        importString = self.createImportString([picked_package])
        fileContents = self.view.substr(sublime.Region(0, self.view.size()))
        insertPoint = self.findImportPosition(fileContents)
        self.view.insert(edit, insertPoint, importString)
