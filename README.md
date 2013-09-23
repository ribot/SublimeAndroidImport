Sublime Android Import
======================

A Sublime Text 2 plugin which automatically deals with imports from the Android SDK. When the command is run it will parse the current file and create a list of the Android classes which have been used. It will then automatically add the necessary imports at the top of the file

Installation
------------
### Package Control

The easiest way to install this is with [Package Control](http://wbond.net/sublime\_packages/package\_control).

1) Make sure you've restarted Sublime if you've just installed Package Control.
2) Bring up the Command Palette (`Cmd+Shift+P` on OS X, `Ctrl+Shift+P` on Linux & Windows).
3) Select `Package Control: Install Package` (it will take a few seconds to load).
4) Select `AndroidImport` when the list appears.

Package Control will automatically keep the plugin up to date with the latest version.

### More complex methods
#### OSX

    $ cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
    $ git clone git://github.com/ribot/SublimeAndroidImport.git AndroidImport

#### Linux (Ubuntu like distros)

    $ cd ~/.config/sublime-text-2/Packages/
    $ git clone git://github.com/ribot/SublimeAndroidImport.git AndroidImport

#### Windows 7:
Copy the directory to: `C:\Users\<username>\AppData\Roaming\Sublime Text 2\Packages`

#### Windows XP:
Copy the directory to: `C:\Documents and Settings\<username>\Application Data\Sublime Text 2\Packages`

Usage
-----
While looking at an Android java file press `Cmd+Shift+O` to import all Android classes. You can also choose _Import Android Classes_ in the _Tools_ menu or from the _Command Palette_.

Known Issues
------------
- Gets confused and therefore ignores the R class.
- Generally untested and may miss classes.
