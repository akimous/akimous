# Changelog

## 0.3.0 (2019-12-01)

* Select the name automatically when renaming files.
* Fix broken forward delete caused by realtime formatter.
* Remember opened folders in file tree.
* Prevent context menu going out of the viewport.

## 0.2.0 (2019-11-24)

* Close completion popup on saving.
* Workaround support for Makefile syntax highlighting. (use YAML)
* Fix an extra space being added after closing braces. `(1, 2).`
* Fix `=` being added as tail in dictionary completion for comments/strings.
* Fix find text input not correctly focused when hotkey `command + f` is pressed.
* Fix panel right does not automatically pop up when references are requested.
* Fix tab bar is not correctly initialized if the panel is hidden during start up.
* Fix `.a` not correctly formatted as `self.a` after an opening brace.
* Fix realtime formatter being triggered for non-python files.

## 0.1.2 (2019-11-15)

* Fix ugly panel scrollbars on Windows.
* Fix whitespace insertion when multiple cursors are present.

## 0.1.1 (2019-11-14)

* Fix initialization failure due to `ptyprocess` not supporting Windows.

## 0.1.0 (2019-11-13)

* Initial release