1.  INTRODUCTION

   NOTE: This program is provided as-is. No support is provided, no maintenance
   is granted. If this program were to inspire you, fork it and be kind enough
   to reference the source of your inspiration.


The program 'tutorial_metadata' extracts tutorial metadata from _text_ files
found in a given file tree. Shell scripts, program source files, etc, are
searched to retrieve the relevant data: description of the tutorial and
associated keywords.

Note that 'tutorial_metada' is written in Python2.

This program has been written and tested on Mac OSX 10.10 ("Yosemite").

Due to the implementation of one of its functions, the program can run only on
Linux/Unix operating systems.


    1.2 Installation

Copy 'tutorial_metadata' in a directory listed in your PATH environment
variable.



2. DESCRIPTION

To execute the program, type:

   tutorial_metadata {-h | --help}

or:

   tutorial_metadata <directory name>

The text files under <directory name> are searched for comments starting the
files, comments which contain a tutorial's metadata. Note that one file tree is
expected to contain text files belonging to a single tutorial.

A comment starting with "tutorial" will initiate the collection of
the metadata. Following the "tutorial" line(s), comment lines starting with
"kwords" provide the keywords associated with the tutorial. (Neither the
"tutorial" nor the "kword" markers are case-sensitive.)

When all the text files in the file tree rooted at <directory name> have been
processed, the tutorial description and its associated keywords are displayed
on stdout, looking like:

  Tutorial: my tutorial's description
  KWords: kw1, kw2, kw3

See the online help (tutorial_metadata -h) for more information. As it stands,
the program can handle shell script comments, Java comments, C comments, Lua
comments (single-line comments), Haskell comments, simple OCaml comments.


    2.1 Example

Assuming we are at the root of the file tree containing the following files:

   README.txt:
      # Tutorial #1: Tutorial example
      # KWords: example

   install.sh:
      #!/usr/bin/env bash
      ## tutorial #1: tutorial example, installation script
      ## KWorks: installation

   dir1/source2.ext2:
      ... some content but no comments, // being the comment mark ...
      // Tutorial #2
      // KWords: x, y

   dir1/source3.ext2:
      // Tutorial #1: Tutorial example using language X
      // KWords: language X

   dir1/dir2/source3.ext:
      ## tutorial #1: Tutorial example showing ...
      ## kwords: library

(where the start of the content of the files is given after their names),

then:

   $ tutorial_metadata .
   Tutorial #1: Tutorial example
   Keywords: example, installation, language X, library
