import unittest, os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), "libs"))

import android_parser

class TestAndroidParser(unittest.TestCase):
    def setUp(self):
        print(android_parser)
        self.parser = android_parser.AndroidParser()

        classes_file = open('classes.txt')
        self.androidClassList = dict()
        for line in classes_file.readlines():
            line_parts = line.split('::')
            key = line_parts[0]
            line_parts.remove(key)

            self.androidClassList[key] = list()
            for package in line_parts:
                self.androidClassList[key].append(''.join(package.split()))

    def test_no_imports(self):
        imports = self.parser.parse('''
        class Foo {
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())

    def test_non_android_classes(self):
        imports = self.parser.parse('''
        class Foo {
            public NonAndroidClass notAndroid;
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class(self):
        imports = self.parser.parse('''
        class Foo {
            public Button button;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.widget.Button")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class_one_other(self):
        imports = self.parser.parse('''
        class Foo {
            public Button button;
            public NonAndroid nonAndroid;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.widget.Button")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class_already_imported(self):
        imports = self.parser.parse('''
        import android.widget.Button;

        class Foo {
            public Button button;
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class_already_imported_another_not(self):
        imports = self.parser.parse('''
        import android.widget.Button;

        class Foo {
            public Button button;
            public TextView textView;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.widget.TextView")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class_already_imported_another_not(self):
        imports = self.parser.parse('''
        import android.widget.Button;

        class Foo {
            public Button button;
            public TextView textView;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.widget.TextView")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_single_android_class_already_imported_another_not(self):
        imports = self.parser.parse('''
        import android.widget.Button;

        class Foo {
            public Button button;
            public TextView textView;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.widget.TextView")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_action_needed_lang(self):
        imports = self.parser.parse('''
        class Foo {
            public System system;
        }
        ''', self.androidClassList)

        expected_action_needed = list();
        expected_action_needed.append(['android.provider.Settings.System', 'java.lang.System'])

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, expected_action_needed)

    def test_action_needed_lang_imported(self):
        imports = self.parser.parse('''
        import java.lang.System;

        class Foo {
            public System system;
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())

    def test_action_needed_non_lang(self):
        imports = self.parser.parse('''
        class Foo {
            public Settings settings;
        }
        ''', self.androidClassList)

        expected_action_needed = list();
        expected_action_needed.append(['android.media.audiofx.BassBoost.Settings',
                                       'android.media.audiofx.EnvironmentalReverb.Settings',
                                       'android.media.audiofx.Equalizer.Settings',
                                       'android.media.audiofx.PresetReverb.Settings',
                                       'android.media.audiofx.Virtualizer.Settings',
                                       'android.provider.Contacts.Settings',
                                       'android.provider.ContactsContract.Settings',
                                       'android.provider.Settings'])

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, expected_action_needed)

    def test_action_needed_non_lang_imported(self):
        imports = self.parser.parse('''
        import android.provider.Settings;

        class Foo {
            public Settings settings;
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())

    def test_inner_class(self):
        imports = self.parser.parse('''
        class Foo {
            public AlertDialog.Builder builder;
        }
        ''', self.androidClassList)

        expected_imports = set()
        expected_imports.add("android.app.AlertDialog")

        self.assertEqual(imports.required, expected_imports)
        self.assertEqual(imports.actionNeeded, list())

    def test_inner_class_imported(self):
        imports = self.parser.parse('''
        import android.app.AlertDialog;

        class Foo {
            public AlertDialog.Builder builder;
        }
        ''', self.androidClassList)

        self.assertEqual(imports.required, set())
        self.assertEqual(imports.actionNeeded, list())
