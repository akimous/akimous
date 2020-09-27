# Changelog

## 0.8.6 (2020-09-27)

* Bump dependency versions.
* Fix failing UI tests caused by performance variation.

## 0.8.5 (2020-05-24)

* Bump dependency versions.

## 0.8.4 (2020-05-04)

* Fix broken sourcemap (Svelte 3.22).
* Bump dependency versions.

## 0.8.3 (2020-04-21)

* Hide horizontal scrollbar of completion popup on Windows.
* Bump dependency versions.

## 0.8.2 (2020-04-07)

* Upgrade XGBoost model format.
* Fix broken `user-select` in Safari.

## 0.8.1 (2020-04-06)

* Continue to start even if git is unavailable.
* Bump dependency versions.
* Revert to fuzzywuzzy.

## 0.8.0 (2020-03-24)

* Use rapidfuzz instead of fuzzywuzzy.

## 0.7.3 (2020-02-09)

* Update dependency versions.

## 0.7.2 (2020-01-29)

* Don't add `()` to completions if there's already one.
* Memorize editor cursor position.

## 0.7.1 (2020-01-19)

* Allow console to work in non-UNIX OS.
* Workaround Jedi not completing `in`.
* Fix text input in find panel not accepting whitespaces.
* Fix formatter adding redundant spaces before colons.

## 0.7.0 (2020-01-05)

* Implement "Open File" (quick search)

## 0.6.0 (2019-12-29)

* Reduce startup time and idle memory consumption.
* Implement context menu for file tabs and code editors.
* Implement hotkeys for finding assignments and usages.
* Don't run linter/formatter on non-Python files.
* Add "Fold All" function.
* Fix file created in file tree going into wrong places.
* Fix incorrect file tree node neighbor calculation.
* Fix file tree misbehavior when renaming folder.
* Allow renaming upper case to lower case on case-insensitive file system.
* Fix incorrect keyboard shortcut number for context menu.

## 0.5.1 (2019-12-22)

* Fix console not correctly initialized if a run is triggered when panel right is hidden.
* Fix broken completion provider (`t=T` not providing `TokenMap` as completion).
* Fix file tree git status not updated if going from changed to clean.
* Fix "Save All" not working.
* Fix tab color not correctly updated on save.
* Fix "go to line" not properly focused.
* Implement missing menu commands (save file, save all, undo, select all, assignments, usages).

## 0.5.0 (2019-12-15)

* Automatically detect indentation unit and size.
* Automatically dismiss "file changed" notification on file close.
* Fix backspace does not refresh completion in ExtraPrediction.
* Fix completion window not closed on character deletion.
* Fix `async def` not handled in CompletionProvider.
* Fix incorrectly adding tails for strings and comments.
* Fix single character variable name not being completed.
* Fix pasting text not triggering realtime formatter.
* Fix broken prompt when not saving file.
* Fix broken focus for findInDirectory.

## 0.4.0 (2019-12-08)

* Avoid reference panel to open duplicated editors.
* Warm up editor lazily to improve start up time when a lot of files are open.
* Preload Jedi modules to speed up first completion.
* Implement "Close" and "Close All" in file menu.
* Allow keyboard input (y/n) in prompts (e.g. closing an unsaved file).
* Implement basic git integration (show file and branch status).

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