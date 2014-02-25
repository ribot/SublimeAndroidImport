import sys, os, collections

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))

# We need to do this to make the tests work
try:
    import plyj, model
except ImportError:
    import plyj.parser as plyj
    import plyj.model as model

class AndroidParser(object):
    def parse(self, fileContents, androidClassList):
        self.classes = set()

        parser = plyj.Parser()
        tree = parser.parse_string(fileContents)

        # Look for all the android classes used by the file passed in
        self.lookForClasses(tree)
        foundAndroidClasses = self.filterAndroidClasses(self.classes, androidClassList)
        # Get a list of all current imports in this file
        currentImports = self.findImports(tree)
        return self.findMissingImports(foundAndroidClasses, androidClassList, currentImports)

    # A recursive method for searching for classes in the java parse tree
    # TODO: This should really return the classes, rather than using an instance variable
    def lookForClasses(self, thing):
        # Check if we need to add this thing to the class list
        shouldAddResults = self.checkAddToClassList(thing)
        if shouldAddResults.shouldAdd:
            parts = shouldAddResults.className.split(".")
            for part in parts:
                if part[0].isupper():
                    self.classes.add(part)
                    break

        # Recuse through all lists and "SourceElements" in the non-callable attributes of the current thing
        attributes = filter(lambda a: not a.startswith('__') and not callable(getattr(thing,a)), dir(thing))
        for a in attributes:
            nextThing = getattr(thing, a)
            if isinstance(nextThing, model.SourceElement):
                self.lookForClasses(nextThing)
            elif hasattr(nextThing, '__iter__'):
                for otherThing in nextThing:
                    self.lookForClasses(otherThing)

    # Checks if the thing describes a class and if so returns a turple with True and the name to add
    def checkAddToClassList(self, thing):
        # Get the return turple ready
        returnValues = collections.namedtuple('Check', ['shouldAdd', 'className'])

        # If the current thing is a "Type" then add it to the class list
        if type(thing) is model.Type and type(thing.name) is model.Name:
            return returnValues(True, thing.name.value)

        # If its a method invocation we may be calling a static method of a class
        elif type(thing) is model.MethodInvocation and type(thing.name) is model.Name:
            possible_class_name = thing.name.value.split('.')[0]
            if possible_class_name[0].isupper():
                return returnValues(True, possible_class_name)

        # Find any other names which could be class names
        elif type(thing) is model.Name:
            possible_class_name = thing.value.split('.')[0]
            if possible_class_name[0].isupper():
                return returnValues(True, possible_class_name)

        return returnValues(False, None)

    # Filters out the found class list to just the ones which are in the Android SDK
    def filterAndroidClasses(self, allClasses, androidClasses):
        foundAndroidClasses = list()

        for foundClass in allClasses:
            if foundClass in androidClasses:
                foundAndroidClasses.append(foundClass)

        return foundAndroidClasses

    # Gets the list of imports currently in the java file
    def findImports(self, tree):
        currentImports = set()

        for anImport in tree.import_declarations:
            currentImports.add(anImport.name.value.split(".")[-1])

        return currentImports

    # Returns a list of packages which have not been imported
    def findMissingImports(self, foundAndroidClasses, androidClassList, currentImports):
        imports = collections.namedtuple('Check', ['required', 'actionNeeded'])
        imports.required = set()
        imports.actionNeeded = list()

        for package in foundAndroidClasses:
            # Check each to see if it's already imported
            required = True
            if package in currentImports:
                required = False

            # If not then add it to the correct list
            if required is not False:
                requiredPackageList = androidClassList.get(package)
                if len(requiredPackageList) == 1:
                    packagePath = requiredPackageList[0]
                    splitLabel = packagePath.split('.')
                    # Dont bother importing java.lang classes
                    if len(splitLabel) >=2 and splitLabel[0] == 'java' and splitLabel[1] == 'lang':
                        pass
                    else:
                        imports.required.add(packagePath)
                else:
                    imports.actionNeeded.append(requiredPackageList)

        return imports
