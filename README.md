# VS Code Extension: Python MRO

A Visual Studio Code Extension to show the inferred Method Resolution Order (MRO) list of a Python class/object via Hover or CodeLens by leveraging the functionality of the [Python MRO Language Server](https://github.com/mosckital/python-mro-language-server).

**MRO** is the order in which Python looks for a method in a hierarchy of classes. Python uses *C3 Linearisation* [(wiki page)](https://en.wikipedia.org/wiki/C3_linearization) as the underlying algorithm.

![Continuous Integration Status](https://github.com/mosckital/vscode_python_mro/workflows/Continuous%20Integration/badge.svg)
[![GitHub license](https://img.shields.io/github/license/mosckital/vscode_python_mro.svg)](https://github.com/mosckital/vscode_python_mro/blob/master/LICENSE)

## Features

This extension takes the advantage of *Hover* and *CodeLens* to conveniently show the inferred MRO list in VS Code. Moreover, the extension listens to the documentation changes so can take the unsaved changes into account during the MRO inference.

### Showing the MRO list via Hover

Ultimately, the extension aims to provide useful MRO information when user hovers over an entity in the editor. For example, the extension aims to show the MRO list when hovering over a class instance, or to show the order list of the parent classes which actually implements the method under hover.

Currently, this extension is able to show the MRO list when user hovers over the declared class name in its declaration section.

### Showing the MRO list via CodeLens

Ultimately, the extension aims to provide the MRO list for each user-declared class by a CodeLens at the start of the declaration section. The user can view the MRO list in a side panel by clicking the CodeLens, which works like the GitLens.

Currently, the MRO list will show in a pop-up message window at the right-bottom corner of the editor, but this will be upgraded to the mentioned side panel in a next release very soon.

## Requirements - Python MRO Language Server

Please use the following command to install the [`Python MRO Language Server`](https://github.com/mosckital/python-mro-language-server) via Pip in your machine to properly use this extension:

```shell
python3 -m pip install python-mro-language-server
```

## Usage

This extension will automatically launch when a Python file is open. It will also automatically launch a *Python MRO Language Server* during its launch process.

## Extension Settings

Currently there is no setting option available to the user. But they will become available in the next releases.

## Release Notes

Please refer to the [CHANGELOG](./CHANGELOG.md).