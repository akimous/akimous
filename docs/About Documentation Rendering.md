## Goals

* Beautifully render docstrings

* Find parameter names.

## Thoughts

* Even if Sphinx domains are injected, there will possibly be some uncovered directives and roles.
* I want it to render even if some domains and directives are not defined.
* It must be parsed, or we cannot get good line breaks.
* It must be parsed, or documents other than devdocs prepared ones will break.



## Possible Approaches

* Preprocess reST and feed into docutils.
  * Bad support for advanced features.
  * Crappy HTML generation
  * Still need to translate to reST if the source is Numpy or Google style
* Use Sphinx
  * No usable API
* Use third party library
  * Bad support
* Display raw string
  * How to deal with word wrapping problem?