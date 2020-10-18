1.  INTRODUCTION

   NOTE: This program is provided as-is. No support is provided, no maintenance
   is granted.


The program 'tutorial_metadata' extracts tutorial metadata from _text_ files
found in a given file tree. Shell scripts, program source files, etc, are
searched to retrieve the relevant data: description of the tutorial and
associated keywords.

Note that 'tutorial_metada' is written in Python2.

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

See the online help for more information. As it stands, the program can handle
shell script comments, Java comments, C comments, Lua comments (single-line
comments), Haskell comments, simple OCaml comments.
