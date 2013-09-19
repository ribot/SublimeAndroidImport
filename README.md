Sublime Android Import
======================

A Sublime Text 2 plugin which automatically deals with imports from the Android SDK. When the command is run it will parse the current file and create a list of the Android classes which have been used. It will then automatically add the necessary imports at the top of the file

Installation
------------
Currently the plugin is not stable enough to be in the package manager, so a manual installation is required. To install you need to copy all the files into a folder in your Sublime plugins directory.

Known Problems
--------------
- Unable to find classes within anonymous classes - [issue](https://github.com/musiKk/plyj/issues/8)
