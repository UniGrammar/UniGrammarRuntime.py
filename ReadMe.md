UniGrammarRuntime.py [![Unlicensed work](https://raw.githubusercontent.com/unlicense/unlicense.org/master/static/favicon.png)](https://unlicense.org/)
===================
~~![GitLab Build Status](https://gitlab.com/UniGrammar/UniGrammarRuntime.py/badges/master/pipeline.svg)~~
~~![GitLab Coverage](https://gitlab.com/UniGrammar/UniGrammarRuntime.py/badges/master/coverage.svg)~~
[![Libraries.io Status](https://img.shields.io/librariesio/github/UniGrammar/UniGrammarRuntime.py.svg)](https://libraries.io/github/UniGrammar/UniGrammarRuntime.py)
[![Code style: antiflash](https://img.shields.io/badge/code%20style-antiflash-FFF.svg)](https://codeberg.org/KOLANICH-tools/antiflash.py)

**We have moved to https://codeberg.org/UniGrammar/UniGrammarRuntime.py, grab new versions there.**

Under the disguise of "better security" Micro$oft-owned GitHub has [discriminated users of 1FA passwords](https://github.blog/2023-03-09-raising-the-bar-for-software-security-github-2fa-begins-march-13/) while having commercial interest in success and wide adoption of [FIDO 1FA specifications](https://fidoalliance.org/specifications/download/) and [Windows Hello implementation](https://support.microsoft.com/en-us/windows/passkeys-in-windows-301c8944-5ea2-452b-9886-97e4d2ef4422) which [it promotes as a replacement for passwords](https://github.blog/2023-07-12-introducing-passwordless-authentication-on-github-com/). It will result in dire consequencies and is competely inacceptable, [read why](https://codeberg.org/KOLANICH/Fuck-GuanTEEnomo).

If you don't want to participate in harming yourself, it is recommended to follow the lead and migrate somewhere away of GitHub and Micro$oft. Here is [the list of alternatives and rationales to do it](https://github.com/orgs/community/discussions/49869). If they delete the discussion, there are certain well-known places where you can get a copy of it. [Read why you should also leave GitHub](https://codeberg.org/KOLANICH/Fuck-GuanTEEnomo).

---

Runtime for UniGrammar-generated wrappers for generated parsers. Generated parsers can be used without wrappers, but wrappers allow to use them uniformly, swapping implementation but keeping the interface.

This allows to
* get rid of hard dependencies on specific libraries, instead any supported parser library can be used, for which a parser is generated;
* benchmark and compare performance of various parsing libraries;
* use the most performant of the available libraries.


How-to use
-----------

* Generate or construct manually a `parser bundle`. A parser bundle is an object storing and giving out
    * pregenerated parsers for different backends (can be generated standalonely using `transpile`)
    * auxilary information (can be generated using `gen-aux`):
        * production names to capture groups mappings, for the parser generators not supporting capturing;
        * production names to booleans mappings, telling if the AST node is a collection, for the parser generators not capable to tell the difference between an iterable or a node in AST;
        * benchmark results
        * a wrapper, transforming backend-specific AST into backend-agnostic one
    Parser bundle can be constructed from a dir on storage or compiled directly into an object in memory. In any case it can be used by a backend.

* Construct a backend. A backend here is an object
    * storing underlying parser objects
    * providing necessary functions to be used by a wrapper to transform backend-specific AST into backend-agnostic one.

There are 2 ways to construct a backend:
    * You can import the backend manually: `from UniGrammarRuntime.backends.<backend name> import <backend class name>` and construct it: `b = <backend class name>("<your grammar name>", <your bundle>)`.
    * Or you can just call a method of the bundle, constructing the needed backend. Pass `None` to select the backend automatically based on benchmarking results.

* Now you can do low-level stuff using backend methods:
    * You can parse your grammar into its backend-native format using `b.parse("<your string to parse>")` method.
    * You can preprocess the AST generated by `parse` and observe the result, using `preprocessAST`.
    * You can check if preprocessed AST nodes represent a collection using `isList` and iterate over them using `iterateList`.
    * You can transform terminal nodes into `str`s using `getTextFromToken`.
    * You can merge subtrees into a single `str` using `mergeShit`.

This all can be useful if you
    * don't want to use a generated wrapper
    * are designing a new Template, so you need the generator to generate custom postprocessing, in order to do it you need to craft it manually first
    * are debugging
    * are just playing around

* Now we go a level higher. You can use a wrapper to get a prettied backend-agnostic postprocessed AST.
    * Import the generated wrapper module.
       * manually `import <wrapper module name>`
       * Via a backend:
    * Then it contains some classes. The class you usually need is aliased to `__MAIN_PARSER__`.
        * Construct the wrapper, initializing it with the backend: `w = <wrapper module name>.__MAIN_PARSER__(b)`
    * Parse what you need: `ast = w("<your string to parse>")`

Examples
--------

* https://codeberg.org/prebuilder/pyMetakitDefinitionString/src/branch/master/pyMetakitDefinitionString/__init__.py
* https://codeberg.org/KOLANICH-libs/FullingMotorModelDecoder.py/src/branch/master/FullingMotorModelDecoder/__init__.py
* https://codeberg.org/KOLANICH-libs/AptSourcesList.py/src/branch/master/AptSourcesList/__init__.py
