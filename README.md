# Backup Toolset

This is a python package containing all things I use to keep backups of different important groups of files.
It will consist of things ranging from core copying mechanisms and command line interfaces, right up to defining how specific files are moved between machines/to their final backup destination.

## Backup Extensions

Each module within this package defines a distinct class of items that can be backed up to a remote device.

### Defining an extension

Extensions will used to extend the functionality of the command line application.
Extensions provide their own subcommand that will be included in the command line application.
Extensions can add whatever necessary functionality to themselves, and the command line application will ensure that the appropriate configurations or options are passed on to the extension.

Extensions must be a Python module defining at the very least a class called `Extension` that subclasses `backup.core.extensions.BackupExtension`.
This class will be used to manage the flow of instructions from the command line application to the extension's own core implementation.
