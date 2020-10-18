#!/usr/bin/env Python
##
## From a list of ASCII files, retrieve the metadata of the tutorial
## implemented by the files; ensure that keywords are not duplicated; print on
## stdout the result.
##
## If these files contain no tutorial metadata, nothing is printed. If the
## files contain only keywords but no heading (see below), a warning is printed
## on stderr whilst the heading is printed on stdout.
##
## The program's status code after execution is 0 if no error was met,
## different from 0 otherwise.
##
## The lines describing the tutorials are at the head of the files. They
## comprise a heading like "Tutorial #1: some summary text". This heading is
## the first comment line of the file. The syntax of a heading is:
## 
##   Tutorial SPC+ <text w/o line-return characters>
##
## The comment lines to extract also contain keywords introduced by the
## "KWords" keyword. The lines collecting the keywords can be many, all
## starting with the "KWords" keyword. The syntax of a KWord line is:
## 
##   KWords SPC* : SPC* <list of keywords and expressions>
##
## The lines to extract are comments in their original files. The comment
## marks might be preceded or followed by white spaces.
##
## If a file in the list of files does not start with a comment, it is skipped.
## 
## Some comments start with "#"s, with "*"s or with "/*" (possibly preceded
## only by white spaces in both cases). There might one or more white space
## between the comment characters and the "Tutorial" or "KWords" text.
##
## Example (where "|" marks the position 0 in a line of a file):
##
##   File #1 contains:
##     |## Tutorial #1: summary tut.1
##     |# KWords: kw1, kw2
##
##   File #2 contains:
##     | /* Tutorial #1: summary tut.1 *
##     |  * KWords: kw1, kw3           *
##     |  * KWords: kw4                */
##
##   The output is to be:
##     |Tutorial #1: summary tut.1
##     |KWords: kw1, kw2, kw3, kw4
##
## If the headings are partially the same, i.e., they start with the same
## "Tutorial ..." prefix, then the shortest one is retained but a warning
## is displayed.
##
## If the headings don't start similarly, i.e., don't start with the same
## "Tutorial ..." prefix , the program exits with an error message only. This
## is so because one cannot always tell whether the heading which seems to be
## at variance is actually part of the majority, majority which would tell
## which version of the heading is the "true" heading if we could know that
## majority from the start.
##
## Where relevant, the error messages should include the file name and line
## number where the error is found.
##
## --
## (C) Christian Wagner
##


import os.path
import re
import subprocess
import sys

def split_on_commas(string):
    """Splits STRING on ',\s*', thus swallowing white-spaces after commas.
    
    Returns a comprehension expression, aka. generator expression, running
    over the list of terms so extracted, empty terms removed. It is also
    ensured that redundant whitespaces have been removed from the terms.

    """
    return (
        normalise_text(t) for t in re.split(",\s*", string) if t != ""
    )

def normalise_text(string):
    """Returns a copy of STRING rid of its redundant whitespaces.

    Leading and trailing whitespaces are removed, too.
    """
    return re.sub( "\s+", " ", string.strip() )

def tail_after(string, head):
    """Returns the tail of STRING starting with HEAD.

    The tail is the part of STRING starting just after HEAD. The tail is the
    empty string if HEAD is not the head of STRING.

    Throws a ValueError exception if HEAD is longer than STRING.
    """
    hl = len(head)
    sl = len(string)
    if sl < hl:
        raise ValueError("HEAD longer than STRING.")
    else:
        return string[hl:]

def values_of_set(s):
    """Returns the list of values of the set S."""
    return [elt for elt in s]

class Comment(object):
    """
    Object storing one comment line and its line number in the file being
    processed.
    """
    def __init__(self, lineNo, string):
        """
        Initialise a new Comment instance. STRING is its content and LINE NO.

        The STRING is not expected to contain the comment mark anymore.
        """
        self.__lineNo = lineNo
        self.__current = string
        self.__error = ""
        self.__warning = ""
        self.__heading = ""  # stores ultimately a tutorial's heading
        self.__keywords = "" # stores ultimately a tutorial's list of kwords

    def addError(self, message):
        """Adds MESSAGE as error message.

        The error message is prepended with "Line #:", where "#" is the
        comment's line number in the file being processed. Returns the same
        Comment object after modification.
        """
        return self.__updateWarningOrError("__error", message)

    def addWarning(self, message):
        """Adds MESSAGE as warning message.

        The warning message is prepended with "Line #:", where "#" is the
        comment's line number in the file being processed. Returns the same
        Comment instance after modification.
        """
        return self.__updateWarningOrError("__warning",  message)

    def __updateWarningOrError(self, fieldName, message):
        if fieldName == "__error":
            self.__error = message
        elif fieldName == "__warning":
            self.__warning = message
        else:
            raise ValueError("Unknown field name: '%s'" % fieldName)
        return self

    def error(self):
        """Returns the content of the error message, or "" if there's none."""
        return self.__error

    def warning(self):
        """\
        Returns the content of the warning message, or "" if there's none."""
        return self.__warning

    def current(self):
        """Returns the current comment line."""
        return self.__current

    def setCurrent(self, value):
        """\
        Updates this instance's current comment line and returns the instance."""
        self.__current = value
        return self

    def heading(self):
        """Returns the collected tutorial heading."""
        return self.__heading
    
    def setHeading(self, heading):
        """Stores HEADING, a string, in this instance and returns the instance.

        This method should be called towards the end of the processing of the
        current input file, when _all_ the headings from the file have been
        processed.

        """
        self.__heading = heading
        return self

    def keywords(self):
        """Returns the collected tutorial keywords."""
        return self.__keywords

    def setKeywords(self, keywords):
        """Stores KEYWORDS in this instance and returns the instance.

        KEYWORDS is to be a string of comma-separated keywords.

        This method should be called towards the end of the processing of the
        the current input file, when _all_ the keywords have been extracted
        from the file.

        """
        self.__keywords = keywords
        return self
    


is_comment = re.compile("^\s*(#+|/\*|//|--|\(\*|;+)\s*").match

def secondary_comment_matcher(initial_comment_mark):
    """Returns the matcher of secondary lines of a multi-line comment.

    Such multi-line comment starts with string INITIAL_COMMENT_MARK.

    The returned matcher can used like this:
       is_secondary_comment = secondary_comment_matcher("##")
       match = is_secondary_comment(input_line)
       if match != None:
         # process this inside-comment line

    For file format where there is only one type of comment character, the
    "secondary" mark is the comment character surrounded by whitespaces, e.g.,
    " ## " or ";; ".
    
    For file format where the multi-line comment is distinguishable from
    single line comment, it is often possible to use the comment mark for
    multi-line comment to mark single line comments. For example, one can
    write in Java:
      /*
       * 2nd line of comment
       */

    or:
      /* 1st comment */
      /* 2nd comment */

    In such a case, the secondary comment mark is defined as "/*" or "*",
    surrounded by whitespaces.

    Since we require a comment mark, comments like:
      /*
        2nd comment
      */
    will fail to be processed by this program as we cannot determine a
    secondary comment mark.

    With the required precaution, the program can handle Lisp comments, Lua
    comments, shell-like comments, TLA+ comments.

    """
    if (initial_comment_mark[0]  == '#'  or
        initial_comment_mark[0]  == ';'  or
        initial_comment_mark[:2] == "--" or
        initial_comment_mark[:2] == '//'):
        return re.compile(
            "^" + single_char_comment_mark_regex(initial_comment_mark)
        ).match
    elif initial_comment_mark[:2] == "/*":
        return re.compile("^\s*(/\*|\*+)\s*").match
    elif initial_comment_mark[:2] == "(*":
        return re.compile("^\s*(\(\*|\*+)\s*").match

def define_comment_border_regex(initial_comment_mark):
    """Returns the compiled regex identifying "right border" comment marks.

    This "right border" mark is determined by the initial, opening
    INITIAL_COMMENT_MARK.

    A "border" comment mark is a comment mark used in multi-line comments,
    for the sake of prettiness. They are terminating a comment line. Here are
    some, on the right end:
    
           ## ... some comment text ... #
        or
           (* ... some comment text ... **)

    Such marks are usually preceded by 0 or more white-space characters.

    The regex returned allows to capture a terminating "border". For example,
    if INITIAL_COMMENT_MARK is "#", then the regex returned is "\s*#+\s*$". If,
    the initial comment mark is "/*", the regex returned is "\s*\*+/?\s*$". As
    can be seen, this second example matches "borders" like "*/", "**",
    "**/ *".

    The compiled regex returned can be used in re.findall(), re.sub(), etc.

    """
    if (initial_comment_mark[0]  == '#'  or
        initial_comment_mark[0]  == ';'  or
        initial_comment_mark[:2] == "--" or
        initial_comment_mark[:2] == '//'):
        return re.compile(
            single_char_comment_mark_regex(initial_comment_mark) +"$")
    elif initial_comment_mark[:2] == "/*":
        return re.compile("\s*\*+/?\s*$")
    elif initial_comment_mark[:2] == "(*":
        return re.compile("\s*\*+\)?\s*$")

def single_char_comment_mark_regex(commentMark):
    return "\s*{}\s*".format(commentMark)


class ProcessLine(object):
    """
    Implements a stateful function which returns a Comment object at each call.

    Initialisation: ProcessLine(fp), where "fp" is a File object.
    """
    def __init__(self, fp):
        self.__file_pointer = fp
        self.__lineNo = 0
        self.__isSecondComment = None
        self.__borderCommentRE = None

    def __call__(self):
        """Reads a line from the currently opened file and returns a Comment
        object.

        The line read is checked to see whether it is a comment. If it is, the
        comment mark, and surrounding whitespaces, are removed and the text of
        the comment is added to the Comment object.

        If the line is not a comment, an empty string is added to the Comment
        object.
        
        In the other cases, an error message is logged in the Comment object.
        Failure can occur when a secondary comment mark, used in a multi-line
        comment section, is not found as expected. An example of a secondary
        comment mark would be "*" (or several "*") in comment where the first
        line starts with "/*" in a Java source file.
        """
        line = self.__file_pointer.readline().rstrip()
        self.__lineNo += 1
        if line == "":
            return self.__newComment("")
        else:
            return self.__getComment(line)

    def __newComment(self, commentText):
        return Comment(self.__lineNo, commentText)

    def __getFirstComment(self, line):
        """Returns the content of the first line of a multi-line comment.

        Returns a Comment instance containing the content of a non-empty line
        of a multi-line comment. This content will be clean of leading comment
        mark(s) and surrounding white spaces.

        If LINE is not a comment, a Comment instance, initialised with an empty
        string, is returned.

        If LINE contains the Unix shebang (#!/) or if the comment is empty,
        then LINE is discarded and the processing of the next comment line is
        called for, ultimately returning one of the Comment instane types
        described above.
        """
        comment_mark_match = is_comment(line)
        if comment_mark_match is None:
            return self.__newComment("")
        elif line[:3] == "#!/":
            return self.__call__()
        else:
            comment_mark = comment_mark_match.group(1)
            self.__borderCommentRE = define_comment_border_regex(comment_mark)
            text  = self.__commentText(line, comment_mark_match)
            if text == "":
                return self.__call__()
            else:
                self.__isSecondComment = secondary_comment_matcher(
                    comment_mark)    
                return self.__newComment(text)

            
    def __getComment(self, line):
        if self.__isSecondComment == None:
            return self.__getFirstComment(line)
        secondary_comment_mark_match = self.__isSecondComment(line)
        text = self.__commentText(line, secondary_comment_mark_match)
        # Load a new line from the opened file if the comment is empty:
        if text == "":
            return self.__call__()
        elif text != None:
            return self.__newComment(text)
        else:
            return self.__newComment("")

        
    def __commentText(self, line, comment_mark_match):
        """\
        Returns the content of a comment LINE, i.e., cleaned of comment marks.

        Returns a comment line without its comment mark, and surrounding
        whitespaces, and its "right border", if any, or returns None if
        COMMENT_MARK_MATCH is None.

        COMMENT_MARK_MATCH is a MatchObject instance.

        """
        if comment_mark_match != None:
            mark_and_whitespaces = comment_mark_match.group()
            comment_text = tail_after(line, mark_and_whitespaces)
            # The lookup for a "border" has to be done after the comment mark
            # has been extracted because some opening comment marks could be
            # mangled if the "border" extraction were to be applied first.
            comment_text = re.sub(self.__borderCommentRE, "", comment_text)
            return comment_text.strip()
        else:
            return None


is_heading = re.compile(r"^\s*Tutorial\s+",re.I).match

is_kwords = re.compile("^\s*KWords\s*:",re.I).match

def read_heading_prefix(s):
    '''Returns the heading prefix found in the string S, or None.'''
    prefix = is_heading(s)
    return prefix and prefix.group() or None

def read_kwords_prefix(s):
    '''Returns the prefix of the keywords found in the string S, or None.'''
    prefix = is_kwords(s)
    return prefix and prefix.group() or None


class ProcessComment(object):
    """
    Implements a stateful function handling the tutorial's comment section.
    """
    def __init__(self):
        self.__heading = ""
        self.__headingLC = ""  # heading in lower-case letters
        self.__keywordsSet = set([])
        # A heading must have been read for keywords to be acceptable:
        self.__keywordsAllowed = False


    def __call__(self, comment):
        """Processes the comment line stored in the COMMENT object.

        Processes the comment line stored in the COMMENT object, extracting
        tutorial heading or tutorial keywords, depending on the content of the
        comment line.

        The processing guarantees that a tutorial heading must have been
        observed before tutorial keywords can be processed. Otherwise, a
        warning is issued and the keywords are ignored.

        It also guarantees that the tutorial heading stored is the prefix of
        all headings observed, assuming that all headings have a common
        prefix. Otherwise, the processing flags an error. For example:

           # Tutorial 1: a
           # Tutorial 1: a b

        will lead to the stored tutorial heading to be "Tutorial 1: a".

        Finally, the processing guarantees that several lines of keywords can
        contribute to the list of keywords stored as long as these lines of
        keywords come immediately after the tutorial heading and are
        consecutive. For example:

           # Tutorial 1: a
           # KWords: k1, k2
           # KWords: k3

        will lead to the stored keywords list: k1, k2, k3.

        Otherwise, if the processing is successful, the COMMENT object is
        updated so that its current comment line is set to None. This value is
        the sign sent downstream to stress that some processing has been
        done.

        When the value of the current comment line in the returned COMMENT is
        different from None, the caller will assume that the processing of the
        comment section of the file currently processed is done since no
        metadata was extracted.

        If the processing highlighted a change of tutorial heading but the new
        heading is compatible with those seen so far, a warning is logged in
        COMMENT. Otherwise, an error is reported.

        If an error occurs during the processing, OBJECT's current comment line
        is left unchanged but an error message is logged in COMMENT.

        Finally, if COMMENT's current comment line is not a comment, this is
        interpreted as a signal that the keywords collected and the heading
        collected should be stored in COMMENT before sending it on.
        """
        currentCommentLine = comment.current()
        headingPrefix = read_heading_prefix(currentCommentLine)
        if headingPrefix != None:
            self.__keywordsAllowed = True
            return self.__updateHeading(
                self.__tutorialHeading(headingPrefix, currentCommentLine),
                comment)
                    
        kwordsPrefix = read_kwords_prefix(currentCommentLine)
        if kwordsPrefix != None:
            if not self.__keywordsAllowed:
                return comment.addWarning(
                    "%s: '%s'" %
                    ("Found keywords definition in file with no Tutorial line",
                     currentCommentLine))

            return self.__updateKeywords(
                self.__tutorialKeywords(kwordsPrefix, currentCommentLine),
                comment)
        
        ## Otherwise, the collection of a tutorial metadata is deemed finished.
        ## So, we update the Comment object which will carry the metadata
        ## downstream. Before that, we reset the __keywordsAllowed flag to
        ## ensure that only valid input files are processed.
        self.__keywordsAllowed = False
        comment.setHeading(self.__heading)
        return comment.setKeywords(self.__keywordsToString())

        
    def __tutorialHeading(self, headingPrefix, commentLine):
        """\
        Returns the normalised tutorial heading, prefixed with HEADING PREFIX.

        COMMENT LINE provides the text after HEADING PREFIX to the value
        returned..

        Note that HEADING PREFIX will be capitalized before being added to
        the result.

        """
        return "{} {}".format(
            normalise_text(headingPrefix).capitalize(),
            normalise_text(tail_after(commentLine, headingPrefix)))
    
    def __tutorialKeywords(self, keywordsPrefix, commentLine):
        return normalise_text(tail_after(commentLine, keywordsPrefix))
    
    def __keywordsToString(self):
        """Returns a string of comma-separated sorted keywords."""
        return ", ".join(sorted(values_of_set(self.__keywordsSet)))
    
    def __updateHeading(self, newHeading, comment):
        """Processes the NEW HEADING and returns COMMENT updated.

        Note that the most generic heading is the outcome of the processing
        and is kept as reference heading. A heading H1 is more generic than
        a heading H2 if H1 matches the start of H2.

        If NEW HEADING is not overlapping the start of the heading currently
        stored, an error is logged in COMMENT.

        COMMENT's "current" field is set to None if the processing was
        successful. Otherwise, COMMENT is left unchanged.

        """
        if self.__heading == "":
            self.__storeHeading(newHeading)
            return comment.setCurrent(None)
        # Comparisons done on the lower case versions of self.__heading and
        # newHeading.
        _newHeading = newHeading.lower()
        if self.__headingLC == _newHeading:
            return comment.setCurrent(None)
        elif self.__headingLC.find(_newHeading) == 0:
            self.__storeHeading(newHeading)
            comment.setCurrent(None)
            return comment.addWarning(
                "will use newly found, shorter heading '%s'" % newHeading)
        elif _newHeading.find(self.__headingLC) == 0:
            return comment.setCurrent(None)
        else:
            return comment.addError(
                "heading '%s' different from previous files' heading '%s'\n"
                % (newHeading, self.__heading))

        
    def __storeHeading(self, heading):
        self.__heading = normalise_text(heading)
        self.__headingLC = self.__heading.lower()
        
    def __updateKeywords(self, keywords, comment):
        """Stores keywords extracted from KEYWORDS, removing duplicates.

        Note that KEYWORDS is simply ignored if it is empty: no error is
        reported.

        Updates CURRENT's "current" field with None and returns COMMENT.
        """
        for kw in split_on_commas(keywords):
            self.__keywordsSet.add(kw)
        return comment.setCurrent(None)


# Enums are a Python 3.x feature:
NOT_DONE = 0
DONE = 1
WARNING = 2
ERROR = 3
    

def assess_processing_result(comment):
    """Assesses the state, as reported in the COMMENT object, of the processing
    of the comment. Returns a pair (code, object).

    The code is NOT_DONE if the processing is not finished; DONE if it is
    finished; WARNING if a warning has been raised during the processing; ERROR
    if an error has been raised.

    The 2nd term of the pair returned is:
    - the COMMENT object if the code is NOT_DONE or DONE
    - the string representing the warning or error message in the other cases
    
    """
    if comment.error() != "":
        return (ERROR, comment.error())
    
    warning = comment.warning()
    if warning != "":
        return (WARNING, warning)
    elif comment.current() == None:
        return (NOT_DONE, comment)
    else:
        return (DONE, comment)

def handle_error(message, fileName):
    """Prints the error MESSAGE on stderr, with the FILE NAME (of
    the file being processed) and a colon prepended to the message.
    """
    sys.stderr.write("{}:{}\n".format(fileName, message))

def handle_warning(message, fileName):
    """Prints the warning MESSAGE on stderr, with the FILE NAME (of the file
    being processed) and a colon prepended to the message.

    Printing warnings (nearly) as they are raised gives a chance to the user
    to interrupt the processing early and try to fix the issue.
    """
    sys.stderr.write("Warning:{}:{}\n".format(fileName, message))

def display_metadata(comment):
    """Prints on stdout the tutorial's heading and the tutorial's keywords,
    if any, logged in the COMMENT object.

    Raises a AssertionError if there is no heading but there are keywords.

    If the keywords are missing whilst there is a heading, a warning message is
    printed on stderr, but the heading is printed, too. This is because it
    might be the case that some files have a no tutorial keywords.
    """
    heading = comment.heading()
    keywords = comment.keywords()
    if heading != "" and keywords != "":
        print "{}\nKeywords: {}".format(heading, keywords)
    elif heading != "" and keywords == "":
        sys.stderr.write("Warning: failed to find any tutorial keywords.\n")
        print heading
    elif heading == "" and keywords != "":
        raise AssertionError("Found keywords but no tutorial heading.")
    else:
        return
    
def process(fileNames):
    """Processes the files named in FILE NAMES, an iterable, and prints out
    the tutorial's metadata at the end of the processing. In case of processing
    error, prints an error message refering to the file and the line of the
    error, and exits.

    See display_metadata() for a description of what the metadata consist in.

    The files named in FILE NAMES are all supposed to be readable.

    The program terminates with this function, returning 0 in case of succesful
    execution, an non-zero value otherwise.

    """
    result = None
    processComment = ProcessComment()
    for fn in fileNames:
        with open(fn, 'r') as fp:
            next_comment = ProcessLine(fp)
            while True:
                (processingCode, result) = assess_processing_result(
                    processComment(next_comment()))
                if processingCode == ERROR:
                    handle_error(result, fn)
                    sys.stderr.write("Processing aborted.\n")
                    exit(1)
                elif processingCode == WARNING:
                    handle_warning(result, fn)
                elif processingCode == DONE: break
    try:
        if result is None:
            sys.stderr.write("AssertionError: input file names list empty.\n")
            exit(1)
        else:
            display_metadata(result)
    except AssertionError as e:
        sys.stderr.write("AssertionError: {}.\n".format(e))
        exit(1)
    exit(0)    


def get_file_names(directoryPath):
    """Returns an iterator over existing file names, or None in case of error.

    If case of error, a message is also displayed on stderr.

    Note that the current implementation works only on Linux/Unix.
    """
    # Looks for ASCII files (file type includes  "text") in the tree rooted at
    # directoryPath. The Unix command "file" is used to determine the file
    # type.
    all_text_files = (
        "find %s -type f| xargs file| grep ' text'| awk -F: '{print $1}'"
        % directoryPath)
    

    try:
        names = subprocess.check_output(all_text_files, shell=True)
        # We filter out the names of Emacs backup files (*~) and Emacs
        # auto-saved files (#*#)
        if len(names) == 0:
            return None
        else:
            return (
                fn for fn in re.split('\n', names)
                if (fn != '' and fn[-1] != '~' and fn[-1] != '#'))
    except subprocess.CalledProcessError as e:
        sys.stderr.write("Failed to execute: {}\n".format(e.cmd))
        return None
    except:
        sys.stderr.write("Error: {}\n".format(sys.exc_info()[0]))
        return None

def command_line_syntax(programName):
    return "{} [ [-h|--help] | <directory name> ]".format(programName)

def report_command_line_error(msg):
    """
    Prints on stderr the error MSG followed by the program's call syntax.
    """
    sys.stderr.write(
        "Error:{}\nSyntax: {}\n".format(msg, command_line_syntax(sys.argv[0]))
    )

def display_manual():
    sys.stderr.write("{}\n".format(command_line_syntax(sys.argv[0])))
    sys.stderr.write(
"""
where
  -h|--help		leads to the display of the current page
  <direectory name>	is the name of the directory to browse

The program browses the file tree rooted at <directory name> for ASCII files
with an opening comment section containing tutorial metadata. At the end of the
execution, the metadata found, if any, are displayed on stdout.

The files contributing metadata should start with the said comment section.
Otherwise, they are skipped.

The metadata consist in:
1) a non-empty comment line starting with "Tutorial"
2) One or several consecutive comment lines starting with "KWords"

In case the "Tutorial" line is not always the same, the smallest version, i.e.,
the most generic version, is retained as long as it is included in all longer
versions.

All the versions have to fully include the smaller versions, otherwise the
program considers them part of different tutorial metadata, raises an error and
aborts. The program considers that the file tree can contain only one tutorial.

If a file contains keywords but no "Tutorial" line, a warning is displayed and
the file is skipped.

The output printed on stdout is comprised of, first, the "Tutorial" line,
followed by a "KWords" line listing, in alphabetical order, all the keywords
collected.

If the processing only led to collecting "Tutorial" lines, the resulting
"Tutorial" line (see above) is displayed but a warning reports, on stderr, the
lack of keywords.

The program's exit status code is 0 if the execution was successful,
non-zero otherwise.
"""
    )
    
def get_args():
    """Parses the command line.

    Returns the name of the directory to browse or prints the manual, depending
    on what the user requested. In the latter case, the program exits after
    having displayed the help pages.

    Returns None if the named directory does not exist. Otherwise, returns
    a string: the directory name or  null if the manual was requested.

    The command line syntax is: <program's name> [[-h|--help] | dirName]

    """
    args = sys.argv
    if "-h" in args or "--help" in args:
        display_manual()
        return ""
    elif len(args) < 2:
        report_command_line_error("Error: invalid command line")
        return None
    elif os.path.exists(args[1]):
        return args[1]
    else:
        report_command_line_error(
            "Error: non-existent directory: '{}'".format(args[1])
        )
        return None
    
if __name__ == '__main__':
    directoryName = get_args()
    if directoryName == None:
        exit(1)
    elif directoryName == "":
        exit(0)
    else:
        fileNames = get_file_names(directoryName)
        if fileNames != None:
            # Exit happens in process()
            process(fileNames)
