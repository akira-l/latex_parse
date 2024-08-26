# Script for converting LaTeX to Markdown, using the regular expressions library (see https://docs.python.org/3/library/re.html).
# Created by Timon Idema on 15-07-2022.
#
# Script loads a tex file, carries out the following steps:
# 1: Replace all chapters and sections with Markdown equivalents, retaining labels.
# 2: Replace all equations with Markdown equivalents, retaining labels.
# Replace LaTeX directives like \emph{} with Markdown equivalents.
# Replace opening quotes (`) with straight ones ('), and non-breaking spaces (~) with html non-breaking spaces (&nbsp;).
# Finally, we export the tex file and clean up the resulting file.

# Some helpful regex patterns (NB: Requires regex package instead of re, see https://pypi.org/project/regex/):
# Pair of curly braces, with arbitrarily many subnested curly braces inside: {(?:[^}{]*(?R)?)*+}
# Matches e.g. \vec{\hat{x}}. Add encompassing parentheses to get the argument as return value: {((?:[^}{]*(?R)?)*+)}
# 'unrolled' version (better performance): {([^}{]*+(?:(?R)[^}{]*)*+)}
# Note that the ?R here stands for recursive. We can be more precise, by looking at the 'first match group' (etc.), indicated with ?1 etc. (?0 is everything), see https://www.rexegg.com/regex-recursion.html, https://codeigo.com/python/recursive-regex/, https://stackoverflow.com/questions/546433/regular-expression-to-match-balanced-parentheses
# With leader argument (common case), example \dv:
# \\dv(\[(\d)\])?({([^{}]*+(?:(?3)[^{}]*)*+)})({([^{}]*+(?:(?5)[^{}]*)*+)})?

# Hint: to test out regex expressions, use regex101.com; adding the option 'single line' is equivalent to the 're.DOTALL' flag, the default option 'multiline' is equivalent to the 're.MULTILINE' flag.


#import enum
#import re
import regex
import os

def FindSubstringInBraces(fullstring, startpos):
    # Find arguments contained between {}.
    # Starting position: element after opening { in fullstring.
    # Search until matching closing }, allowing for nesting.
    # Returns string in {}.
    returnstring = ""
    pos = startpos
    nestingdepthcounter = 0
    # While loop to search for closing "}".
    while ((pos<len(fullstring)) and ((fullstring[pos] != "}") or (nestingdepthcounter > 0))):
        character = fullstring[pos]
        returnstring += character
        if (character == "{"): nestingdepthcounter += 1
        elif (character == "}"): nestingdepthcounter -= 1
        pos += 1
    return returnstring

def FindMatchingEndif(fullstring, startpos):
    # Given a starting position (after an \ifxxx in LaTeX), find the matching \fi.
    # Starting position: element after \ifxxx in fullstring.
    # Search until matching closing \fi, allowing for nesting.
    # Also check for \else at top level.
    # Returns strings between startpos and \else, and \else and \fi.
    # If there is no else, the second string is empty.
    returnstring = ""
    returnstring1 = ""
    pos = startpos
    nestingdepthcounter = 0
    # While loop to search for closing "\fi".
    while ((pos<len(fullstring)-2) and ((fullstring[pos:pos+3] != "\\fi") or (nestingdepthcounter > 0))):
        if (nestingdepthcounter == 0) and (pos<len(fullstring)-5 and fullstring[pos:pos+5] == "\\else"):
            returnstring1 = returnstring
            returnstring = ""
            pos += 5    # Plus the one we add below, we get the five characters of "\else"
        else:
            character = fullstring[pos]
            returnstring += character
            if (fullstring[pos:pos+3] == "\\if"): nestingdepthcounter += 1
            elif (fullstring[pos:pos+3] == "\\fi"): nestingdepthcounter -= 1
            pos += 1
    if (returnstring1 != ""):
        return [returnstring1, returnstring]
    else:
        return [returnstring, ""]

def CommentReplace(matchobject):
    return "<!--" + matchobject.group(1) + "-->"

def LineCommentRemove(matchobject):
    # Remove a single-line comment, unless it starts with a keyword.
    if (matchobject.group(1) != None): return matchobject.group(0)
    else: return ""
    
def CommentRemove(matchobject):
    # Remove comment (but not the symbol before %).
    return matchobject.group(1)

def EqRefReplace(matchobject):
    return "(\\ref{" + matchobject.group(1) + "})"

def AccentsReplace(latexstring):
    # Replace accented letters with their HTML counterparts. Just a long list of substitutions.
    result = latexstring

    result = re.sub(r"\\\"\{a\}", "&auml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"\{e\}", "&euml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"\{i\}", "&iuml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"\{o\}", "&ouml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"\{u\}", "&uuml;", result, 0, re.MULTILINE)

    # Also without the parentheses...
    result = re.sub(r"\\\"a", "&auml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"e", "&euml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"i", "&iuml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"o", "&ouml;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\"u", "&uuml;", result, 0, re.MULTILINE)

    result = re.sub(r"\\\`\{a\}", "&agrave;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\`\{e\}", "&egrave;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\`\{i\}", "&igrave;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\`\{o\}", "&ograve;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\`\{u\}", "&ugrave;", result, 0, re.MULTILINE)

    result = re.sub(r"\\\'\{a\}", "&aacute;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\'\{e\}", "&eacute;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\'\{i\}", "&iacute;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\'\{o\}", "&oacute;", result, 0, re.MULTILINE)
    result = re.sub(r"\\\'\{u\}", "&uacute;", result, 0, re.MULTILINE)

    #The Å in Ångström. Note that $Acirc; actually gives an A with a circumflex.
    result = re.sub(r"\\r{A}", "Å", result, 0, re.MULTILINE)

    return result

def QuotesReplace(matchobject):
    if len(matchobject.group(0)) == 1: return "'"
    elif len(matchobject.group(0)) == 2: return "''"
    else: return matchobject.group(0)

def FixPrfRef(matchobject):
    return "{prf:ref}`" + matchobject.group(1) + "`"

def textttReplace(matchobject):
    # Replace \texttt{X} with `X`.
    result = "`" + matchobject.group(2) + "`"
    return result

def CenterToCentering(matchobject):
    return "\\centering\n" + matchobject.group(1) + "\n"

def CenterRemove(matchobject):
    return matchobject.group(1) + "\n"

def ChapterTitleReplace(matchobject):
    # If chapter is found, replace with section in markdown;
    # add any chapter label as markdown label.
    returnstring = ""
    if (matchobject.group(3) != None):
        # There's a label.
        returnstring = "(" + matchobject.group(4)+ ")=\n"
    returnstring += "# " + matchobject.group(2) + "\n"
    return returnstring

def AppendicesReplace(matchobject):
    # If a \begin{appendices} - \end{appendices} pair is found,
    # add "Appendix " to the title of every section inside the pair,
    # and remove the \begin{appendices} - \end{appendices}.
    def AddAppendixToSectionName(localmatchobject):
        return "\\section{Appendix: " + localmatchobject.group(1) + "}"
    returnstring = matchobject.group(1)
    regexpression = r"\\section{([^}]+)}"
    returnstring = re.sub(regexpression, AddAppendixToSectionName, returnstring, 0, re.MULTILINE)
    return returnstring

def SectionTitleReplace(matchobject):
    # If (sub)section is found, replace with subsection in markdown;
    # add any subsection label as markdown label.
    # Order: section --> level 2, subsection --> level 3, subsubsection --> level 4. (chapter is level 1).
    # NB: If 'short' title is given, use that (no LaTeX).
    returnstring = ""
    if (matchobject.group(5) != None):
        # There's a label.
        #print("There's a label.\n")
        returnstring = "(" + matchobject.group(6)+ ")=\n"
    if (matchobject.group(1) == "sub"): returnstring += "#"
    elif (matchobject.group(1) == "subsub"): returnstring += "##"
    if (matchobject.group(2) != None):
        # There's a short version. Use it.
        returnstring += "## " + matchobject.group(3) + "\n"
    else:
        returnstring += "## " + matchobject.group(4) + "\n"
    return returnstring

def StraightdReplace(matchobject):
    returnstring = "\\mathrm{d}"
    if (matchobject.group(1) != None):
        # Check for '\ddo' (from '\ddot{x}') -> do not replace.
        if (matchobject.group(1) == "o"): returnstring = "\\ddo"
        elif (matchobject.group(1) != " "): returnstring += matchobject.group(1)
    return returnstring

def UnitvecReplace(matchobject):
    return "\\bm{\\hat{" + matchobject.group(1) + "}}"

#def TwovecReplace(matchobject):
#    return "\\begin{pmatrix} " + matchobject.group(1) + "\\\\ " + matchobject.group(2) + " \\end{pmatrix}"

def ThreevecReplace(matchobject):
    return "\\begin{pmatrix} " + matchobject.group(1) + "\\\\ " + matchobject.group(2) + "\\\\ " + matchobject.group(3) + " \\end{pmatrix}"

def DiffReplace(matchobject):
    return r"\\frac{\\partial " + matchobject.group(1) + r"}{\\partial " + matchobject.group(2) + "}"

def InprodReplace(matchobject):
    return "\\langle" + matchobject.group(1) + r"\\,," + matchobject.group(2) + "\\rangle"

def EquationReplace(matchobject):
    # If an equation is found (in between \begin{equation} and \end{equation}), replace with equation in markdown.
    # Add markdown label if label given.
    returnstring = "\n$$\n" + matchobject.group(4).strip()
    #if (matchobject.group(5) != None): returnstring += matchobject.group(5)
    #if (matchobject.group(6) != None): returnstring += matchobject.group(6)
    returnstring += "\n$$"
    if (matchobject.group(2) != None):
        # There's a label. Add it.
        returnstring += " (" + matchobject.group(3) + ")\n"
    elif (matchobject.group(5) != None):
        # Endlabel. Still add it.
        returnstring += " (" + matchobject.group(6) + ")\n"
    else: returnstring += "\n"
    return returnstring

def EquationReplaceAdmonition(matchobject):
    # If an equation is found (in between \begin{equation} and \end{equation}), replace with math block in markdown.
    # Add markdown label if label given.
    returnstring = "\n```{math}\n"
    if (matchobject.group(2) != None):
        # There's a label. Add it.
        returnstring += ":label: " + matchobject.group(3) + "\n"
    returnstring += matchobject.group(4) + "\n```\n"
    return returnstring

def UnnumberedEquationReplace(matchobject):
    # Replace an unnumbered equation in \[ .. \] with an admonition.
    # Too many problems with JB if we replace with $$ .. $$.
    returnstring = "\n```{math}\n" + str.strip(matchobject.group(1)) + "\n```\n"
    return returnstring

def InlineEquationReplace(matchobject):
    # If an inline equation of the form \(equation\) is found, replace with $equation$.
    return "$" + matchobject.group(1) + "$"

def EqnArrayArgumentReplace(matchobject):
    return r"&" + matchobject.group(1)

def EqnArrayToAlign(matchobject):
    # Turn \begin{eqnarray} .. \end{eqnarray} in to \begin{align} .. \end{align} 
    returnstring = re.sub(r"eqnarray", r"align", matchobject.group(0), 0, re.MULTILINE)
    returnstring = re.sub(r"&\s*(=|<|>|\\leq|\\geq|\!=)\s*&", EqnArrayArgumentReplace, returnstring, 0, re.MULTILINE)
    return returnstring

def AlignReplace(matchobject):
    # If an align environment is found (in between \begin{align} and \end{align}), replace with align in markdown.
    # Check for presence of \begin{subequations} .. \end{subequations} around align.
    # Also check for difference between \begin{alignat}{d} and \begin{align}
    # Add markdown label if label given.
    # Note that dollarmath + align won't work with amsmath, so we build a math block.
    if (matchobject.group(1) != None):
        # Already done. Just return what we got in.
        return matchobject.group(0)
    returnstring = "\n```{math}\n"
    if (matchobject.group(2) != None):
        # Subequations. Check for label.
        if (matchobject.group(3) != None):
            # There's a label. Add it.
            returnstring += ":label: " + matchobject.group(4) + "\n"
    elif (matchobject.group(7) != None):
        # No subequations, but there's at least one label. Add it.
        returnstring += ":label: " + matchobject.group(8) + "\n"
        # Check for multiple labels. If present, split the object.
        labels = re.finditer(r"\\label{([^}]+)}\s?", matchobject.group(9), re.MULTILINE)
        labellist = []
        for labelid, label in enumerate(labels, start=1):
            # Extract relevant data of labels.
            labellist.append((labelid, label.start(), label.end(), label.group(1)))
        if (len(labellist) > 0):
            # Additional labels found. Loop over them, adding a separate math block to the returnstring for each of them.
            # Note that we strip off 3 characters (the \\\n) but need to re-add the \n.
            firstequation = matchobject.group(9)[:labellist[0][1]-2]
            if (matchobject.group(5) != None):
                # Alignat.
                returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + firstequation + "\n" + "\\end{alignat*}" + "\n```\n"
            else:
                returnstring += "\\begin{align*}\n" + firstequation + "\n" + "\\end{align*}" + "\n```\n"
            for (labelid, startpos, endpos, label) in labellist:
                # Additional labels found. Loop over them, adding a separate math block to the returnstring for each of them.
                # Except for the last one, cut the last two characters off (the \\\n but need to re-add the \n)
                if (labelid < len(labellist)):
                    equation = matchobject.group(9)[endpos:labellist[labelid][1]-3]
                else:
                    equation = matchobject.group(9)[endpos:]
                returnstring += "\n```{math}\n"
                returnstring += ":label: " + label + "\n"
                if (matchobject.group(4) != None):
                    # Alignat.
                    returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + equation + "\n" + "\\end{alignat*}" + "\n```\n"
                else:
                    returnstring += "\\begin{align*}\n" + equation + "\n" + "\\end{align*}" + "\n```\n"
            return returnstring
    elif (matchobject.group(10) != None):
        # Single label at the end.
        returnstring += ":label: " + matchobject.group(11) + "\n"

    # Strip labels and \nonumber comments from string
    # (not strictly needed but cleaner).
    strippedequations = re.sub(r"\\label{[^}]+}\s?|\\nonumber", "", matchobject.group(9), 0, re.MULTILINE)

    # Single-label case; complete the returnstring, stripping internal label info.
    if (matchobject.group(5) != None):
        # Alignat.
        returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + strippedequations + "\n" + "\\end{alignat*}" + "\n```\n"
    else: returnstring += "\\begin{align*}\n" + strippedequations.strip() + "\n" + "\\end{align*}" + "\n```\n"
    return returnstring

def AlignReplaceOld(matchobject):
    # If an align environment is found (in between \begin{align} and \end{align}), replace with align in markdown.
    # Check for presence of \begin{subequations} .. \end{subequations} around align.
    # Also check for difference between \begin{alignat}{d} and \begin{align}
    # Add markdown label if label given.
    # Note that dollarmath + align won't work with amsmath, so we build a math block.
    returnstring = "\n```{math}\n"
    if (matchobject.group(1) != None):
        # Subequations. Check for label.
        if (matchobject.group(2) != None):
            # There's a label. Add it.
            returnstring += ":label: " + matchobject.group(3) + "\n"
    elif (matchobject.group(7) != None):
        # No subequations, but there's at least one label. Add it.
        returnstring += ":label: " + matchobject.group(8) + "\n"
        # Check for multiple labels. If present, split the object.
        labels = re.finditer(r"\\label{([^}]+)}\s?", matchobject.group(9), re.MULTILINE)
        labellist = []
        for labelid, label in enumerate(labels, start=1):
            # Extract relevant data of labels.
            labellist.append((labelid, label.start(), label.end(), label.group(1)))
        if (len(labellist) > 0):
            # Additional labels found. Loop over them, adding a separate math block to the returnstring for each of them.
            firstequation = matchobject.group(9)[:labellist[0][1]]
            if (matchobject.group(4) != None):
                # Alignat.
                returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + firstequation + r"\\end{alignat*}" + "\n```\n"
            else:
                returnstring += "\\begin{align*}\n" + firstequation + "\\end{align*}" + "\n```\n"
            for (labelid, startpos, endpos, label) in labellist:
                # Additional labels found. Loop over them, adding a separate math block to the returnstring for each of them.
                if (labelid < len(labellist)):
                    equation = matchobject.group(9)[endpos:labellist[labelid][1]]
                else:
                    equation = matchobject.group(9)[endpos:]
                returnstring += "\n```{math}\n"
                returnstring += ":label: " + label + "\n"
                if (matchobject.group(4) != None):
                    # Alignat.
                    returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + equation + r"\\end{alignat*}" + "\n```\n"
                else:
                    returnstring += "\\begin{align*}\n" + equation + "\\end{align*}" + "\n```\n"
            return returnstring
    elif (matchobject.group(10) != None):
        # Single label at the end.
        returnstring += ":label: " + matchobject.group(11) + "\n"

    # Strip labels and \nonumber comments from string
    # (not strictly needed but cleaner).
    strippedequations = re.sub(r"\\label{[^}]+}\s?|\\nonumber", "", matchobject.group(9), 0, re.MULTILINE)

    # Single-label case; complete the returnstring, stripping internal label info.
    if (matchobject.group(4) != None):
        # Alignat.
        returnstring += "\\begin{alignat*}" + matchobject.group(6) + "\n" + strippedequations + r"\\end{alignat*}" + "\n```\n"
    else: returnstring += "\\begin{align*}\n" + strippedequations.strip() + r"\n\\end{align*}" + "\n```\n"
    return returnstring

def NewFigurePath(oldpath):
    # Add images folder & replace any .pdf with .svg.
    newpath = "images/" + re.sub(r"\.pdf", ".svg", oldpath)
    return newpath

def FigureReplace(matchobject):
    # If a figure environment is found (in between \begin{figure} and \end{figure}), replace with figure in markdown.
    # Note: replacing the figure with code will happen later (to avoid parsing code).
    # Add markdown label and caption if given.
    returnstring = "```{figure} " + NewFigurePath(matchobject.group(7)) + "\n"
    if (matchobject.group(11) != None):
        # There's a label. Add it.
        returnstring += ":name: " + matchobject.group(12) + "\n"
    if (matchobject.group(3) != None):
        # There's a specified width. Add it.
        returnstring += ":width: " + matchobject.group(4) + "\n"
    if (matchobject.group(8) != None):
        # There's a caption. Add it.
        returnstring += matchobject.group(10) + "\n"
    returnstring += "```\n"
    return returnstring

def IncludeGraphicsReplace(matchobject):
    # Replace a figure that's 'inline' (no figure environment, just \includegraphics, possibly with \centering). Sometimes occurs in problems. No caption or label.
    returnstring = "\n```{figure} " + NewFigurePath(matchobject.group(3)) + "\n" + "```\n"
    return returnstring

def TableReplace(matchobject):
    # If a table environment is found (in between \begin{table} and \end{table}), replace with table block. Alternatively, could use list-table, but then cannot control alignment.
    # Add label and caption if given.
    returnstring = "```{table} "
    footercaption = ""
    if (matchobject.group(6) != None):
        # There's a caption. Add it. First check if there is a [].
        if (matchobject.group(7) != None):
            # Short caption provided. Add the long one to the end.
            returnstring += matchobject.group(8) + "\n"
            footercaption = matchobject.group(9) + "\n"
        else:
            returnstring += matchobject.group(9) + "\n"
    else: returnstring += "\n"
    # Assume one header row.
    #returnstring += ":header-rows: 1\n"
    # Check for label.
    if (matchobject.group(10) != None):
        # There's a label. Add it.
        returnstring += ":name: " + matchobject.group(11) + "\n"
    # Get the makeup of the table (column layout).
    makeupstrings = str.split(matchobject.group(4), "|")
    if (makeupstrings[-1] == ""): makeupstrings = makeupstrings[0:-1]
    if (makeupstrings[0] == ""): makeupstrings = makeupstrings[1:]
    Ncolumns = len(makeupstrings)
    rowmakeup = "|"
    for columnmakeup in makeupstrings:
        for letter in columnmakeup:
            # Three options: l, c, r. Add column makeup accordingly.
            if (letter=="l"):
                rowmakeup += " :--- |"
            elif (letter=="c"):
                rowmakeup += " :--: |"
            elif (letter=="r"):
                rowmakeup += " ---: |"
            else:
                rowmakeup += " ---- |"
    
    # Split the rows.
    rows = str.splitlines(matchobject.group(5))
    
    # Check if the first row contains \hline. If not, take as header row, otherwise take second row as header row.
    rowindex = 0
    if ("\\hline" in rows[0]): rowindex = 1
    columns = str.split(rows[rowindex].strip(), "&")
    headerrow = "| "
    for entry in columns: headerrow += entry.rstrip("\\") + "|"
    returnstring += headerrow + "\n"
    
    # After the header row, add the makeup row.
    returnstring += rowmakeup + "\n"

    # Loop over remaining rows; for each, check if we have a \hline (skip), otherwise add row.
    rowindex += 1
    while rowindex < len(rows):
        # Strip leading and trailing whitespace.
        currentrow = rows[rowindex].strip()
        # First check if the row doesn't start with a % or contains a \hline (if so, skip).
        if ((len(currentrow)==0) or (currentrow[0:4] == "<!--") or ("\\hline" in currentrow)): rowindex += 1
        else:
            columns = str.split(currentrow, "&")
            row = "| "
            for entry in columns: row += entry.rstrip("\\") + "|"
            returnstring += row + "\n"
            rowindex += 1

    returnstring += "```\n" + footercaption
    return returnstring

def ParboxRemove(matchobject):
    # Replace \parbox[x]{dist}{text} with just the text.
    return matchobject.group(2)

def ProblemRefReplace(matchobject):
    # Replace problem~\ref{ch:X}.\ref{pb:Y} with "Exercise Y".
    return "{numref}`" + matchobject.group(3) + "`"

def ExampleRefReplace(matchobject):
    return "{prf:ref}`" + matchobject.group(7) + "`"

def RefReplace(matchobject):
    # Did not include (table). Needs number update for including.
    #print(matchobject.group(2))
    if (matchobject.group(2) == "fig" or matchobject.group(2) == "Fig" or matchobject.group(3) == "Table" or matchobject.group(3) == "table"):
        # Figure or table. Note that {numref} automatically includes "Fig. "
        returnstring = "{numref}`" + matchobject.group(18) + "`"    
    elif (matchobject.group(4) == "ch" or matchobject.group(4) == "Ch" or matchobject.group(7) == "sec" or matchobject.group(7) == "Sec" or matchobject.group(9) == "app" or matchobject.group(9) == "App"):
        # Chapter / section / appendix. Note that {numref} automatically includes "Section "
        #returnstring = matchobject.group(1)
        #if (matchobject.group(12) == "s"): returnstring += "s"
        #returnstring += matchobject.group(13) + "{numref}`" + matchobject.group(15) + "`"
        returnstring = "{numref}`" + matchobject.group(18) + "`"
    elif (matchobject.group(11) == "eq" or matchobject.group(11) == "Eq"):
        # Equation, preceded by a word.
        returnstring = matchobject.group(1)
        if (matchobject.group(15) == "s"): returnstring += "s"
        if (matchobject.group(16) != None): returnstring += matchobject.group(16)
        returnstring += "{eq}`" + matchobject.group(18) + "`"
    elif (matchobject.group(1) == "theorem" or matchobject.group(1) == "Theorem" or matchobject.group(13) == "prop" or matchobject.group(13) == "Prop" or matchobject.group(1) == "lemma" or matchobject.group(1) == "Lemma" or matchobject.group(1) == "corollary" or matchobject.group(1) == "Corollary" or matchobject.group(1) == "axiom" or matchobject.group(1) == "Axiom" or matchobject.group(1) == "def" or matchobject.group(1) == "Def"):
        # Object from the long list of sphinx:proof environments.
        returnstring = "{prf:ref}`" + matchobject.group(18) + "`"
    else:
        # Just a \ref. 
        # First, re-add any preceding s because it is likely from a word.
        if (matchobject.group(15) != None): returnstring = "s"
        else: returnstring = ""
        # Check first elements of argument on whether they start with 'ch:', 'sec:', 'app:', or 'fig:'; if so, match accordingly. If not, assume equation.
        #if (matchobject.group(14) != None): returnstring = matchobject.group(14)
        #else: returnstring = ""
        if (matchobject.group(16) != None): returnstring += matchobject.group(16)
        parts = matchobject.group(18).split(":")
        if (len(parts) == 1 or parts[0] == 'eq'):
            returnstring += "{eq}`" + matchobject.group(18) + "`"
        elif (parts[0] == 'fig'):
            returnstring += "{numref}`" + matchobject.group(18) + "`"
        elif ((parts[0] == 'table') or (parts[0] == 'tab')):
            returnstring +=  "{numref}`" + matchobject.group(18) + "`"
        elif (parts[0] == 'ch' or parts[0] == 'sec' or parts[0] == 'app'):
            returnstring += "{numref}`" + matchobject.group(18) + "`"
        elif (parts[0] == 'thm' or parts[0] == 'prop' or parts[0] == 'lemma' or parts[0] == 'cor' or parts[0] == 'axiom' or parts[0] == 'def'):
            returnstring += "{prf:ref}`" + matchobject.group(18) + "`"
        else: returnstring +=  "{eq}`" + matchobject.group(18) + "`"
    if (matchobject.group(17) == None and matchobject.group(19) == ")"):
        returnstring += ")"
    return returnstring

def TheoremReplace(matchobject):
    returnstring = "```{prf:" + matchobject.group(1) + "}"
    if (matchobject.group(3) != None): returnstring += " " + matchobject.group(4)
    returnstring += "\n"
    if (matchobject.group(5) != None): returnstring += ":label: " + matchobject.group(6) + "\n"
    returnstring += matchobject.group(7) + "```\n"
    return returnstring

def CitationReplace(matchobject):
    return matchobject.group(1) + "{cite}`" + matchobject.group(2) + "`"

def EnumerateReplace(matchobject):
    # Replace a \begin{enumerate}..\end{enumerate} with enumerated list.
    # Check (group 1) if \begin{enumerate} is followed by [(a)], if so, itemize with abcd... instead of 1, 2, 3 etc. Group 2 is the contents of the thing between brackets.
    # Other options might have to be added later.
    returnstring = matchobject.group(3)
    # Update: also strip any \label{..} as those don't work (yet) for itemized lists in JB.
    returnstring = re.sub(r" *\\item (\\label{[^}]+})?", "1. ", returnstring)
    return returnstring

def ItemizeItemReplace(matchobject):
    # Replace \item with "-", adding any object in [].
    if (matchobject.group(2) != None):
        return "- **" + matchobject.group(3) + "**"
    else: return "-"

def ItemizeReplace(matchobject):
    # Replace a \begin{itemize}..\end{itemize} with unnumbered list.
    # Choices: +, *, -, we will try -.
    # For now, no nesting.
    #returnstring = str.replace(matchobject.group(1), "\item", "-")
    #returnstring = re.sub(r" *\\item", "-", matchobject.group(2))
    returnstring = re.sub(r"( |\t)*\\item(\[([^\]]+)\])?", ItemizeItemReplace, matchobject.group(2))
    return returnstring

def HyperlinkReplace(matchobject):
    # Replace \href{link}{text} and \bookref{link}{text} with MarkDown hyperlink [text](link).
    return "[" + matchobject.group(3) + "](" + matchobject.group(2) + ")"

def FramedReplace(matchobject):
    # Replace \begin{framed}...\end{framed} with a 'note' box.
    return "```{note}\n" + matchobject.group(1) + "```\n"

def TcolorboxReplace(matchobject):
    # Replace \begin{tcolorbox}[..]..\end{tcolorbox} with a 'note' or titled box.
    #opening = "```{note}\n"
    returnstring = "```{note}\n"
    # First, check if the first argument contains a title.
    if (matchobject.group(1) != None):
        localregexpression = r",title=([^,]+)"
        titlematch = re.search(localregexpression, matchobject.group(1))
        if (titlematch != None):
            #opening = "```{admonition} " + titlematch.group(1) + "\n"
            returnstring = "```{admonition} " + titlematch.group(1) + "\n" + matchobject.group(2).strip() + "\n```\n"
        else:
            # No title, but there could be 'ams align', implying internal math.
            localregexpression = r"ams align"
            amsalignmatch = re.search(localregexpression, matchobject.group(1))
            if (amsalignmatch != None):
                # Math. Could make a note, but rather box the math.
                labelregexpression = r"\\label\{([^\}]+)\}"
                labelmatch = re.search(labelregexpression, matchobject.group(2))
                #NB: don't add 4 `s here, as that'll lead to an error when checking for nesting.
                #returnstring = "```{note}\n```{math}\n"
                returnstring = "```{math}\n"
                if (labelmatch != None):
                    returnstring + ":label: " + labelmatch.group(1) + "\n"
                    returnstring += "\\boxed{" + re.sub(labelregexpression, "", matchobject.group(2)).strip() + "}"
                else: returnstring += "\\boxed{" + matchobject.group(2).strip() + "}"
                #returnstring += "\n```\n```\n"
                returnstring += "\n```\n"
            else:
                returnstring += matchobject.group(2).strip() + "\n```\n"
    else: returnstring += matchobject.group(2).strip() + "\n```\n"
    return returnstring
    #return opening + matchobject.group(2).strip() + "\n```\n"

def InfoboxReplace(matchobject):
    # Replace an info box with an admonition.
    # The matchobject contains eight groups:
    # 1. The index item (optional)
    # 2. The name as in the index item (optional).
    # 3. The text of the left column.
    # 4. The name as in the text.
    # 5. The dates (optional).
    # 6. Some layout comments in the right column (optional - typically 'centering').
    # 7. Path of the portrait.
    # 8. Caption of the portrait (optional).
    returnstring = ""
    infoboxstring = ""

    # Add an index ref if one is given.
    if (matchobject.group(1) != None):
        lastname = str.split(matchobject.group(2), ",")[0]
        returnstring = "```{index} " + lastname + "\n```\n"

    # Extract the box title.
    boxtitle = matchobject.group(4)
    if (matchobject.group(5) != None): boxtitle += " " + matchobject.group(5)

    # Info box is simply the left column (for now).
    infoboxstring = matchobject.group(3) + "\n"

    # Figure.
    infoboxstring += "```{figure} " + NewFigurePath(matchobject.group(7)) + "\n" + "---\n" + "width: 300\n" + "---\n"
#    if (matchobject.group(8) != None):
#        # There's a label. Add it.
#        returnstring += ":name: " + matchobject.group(9) + "\n"
    if (matchobject.group(8) != None):
        # There's a caption. Add it.
        infoboxstring += matchobject.group(8) + "\n"
    infoboxstring += "```\n"

    """ Double as we'll go over admonition nesting again later.
    regexpression = r"`{3,}"    # Find three-or-more `
    admonitionmatches = re.findall(regexpression, infoboxstring, re.MULTILINE)
    # Find longest element, if there are any.
    if len(admonitionmatches) > 0:
        maxadmonitionlength = len(max(admonitionmatches))
        admonitionstring = "`" * (maxadmonitionlength + 1)
    else:
        admonitionstring = "```"
    """
    admonitionstring = "```"

    # Now add the admonition to the returnstring.
    returnstring += admonitionstring + "{admonition}"
    if (boxtitle != ""): returnstring += " " + boxtitle + "\n"
    else: returnstring += "\n"
#    if (problemlabel != ""):
#        returnstring += ":label: " + problemlabel + "\n"
    returnstring += ":class: dropdown\n"
    returnstring += infoboxstring.rstrip() + "\n" + admonitionstring + "\n\n"
    return returnstring

def IndexEntryReplace(matchobject):
    arguments = str.split(matchobject.group(2), "|")
    indexentry = re.sub(r"!", " ; ", arguments[0])
    return "\n\n```{index} " + indexentry + "\n```\n" + matchobject.group(1)

def CombineIndexEntries(matchobject):
    return "```{index} " + matchobject.group(1) + ", " + matchobject.group(2) + "\n```"

def LatexCommandsReplace(matchobject):
    if (matchobject.group(1) == 'emph' or matchobject.group(1) == 'textit'): return "*" + matchobject.group(2) + "*"
    if (matchobject.group(1) == 'textbf'): return "**" + matchobject.group(2) + "**"
    if matchobject.group(1) == 'index': return ""
    if matchobject.group(1) == 'mbox': return "\\text{" + matchobject.group(2) + "}"
    #if matchobject.group(1) == 'bvec': return "\\bm{" + matchobject.group(2) + "}"
    return matchobject.group(0)

def bfInTextReplace(matchobject):
    return "**" + matchobject.group(1).strip() + "**"

def itInTextReplace(matchobject):
    return "*" + matchobject.group(2).strip() + "*"

def TwovecReplace(latexstring):
    # Given a LaTeX string, replace \twovec{}{} with matrix form, allowing for nested braces. NB: Can be replaced by TwoArgumentMacroReplace.
    regexpression = r"\\twovec{"
    matches = re.finditer(regexpression, latexstring, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = footnoteid, start = match.start(), end = match.end(), match = match.group()))
        argument1 = FindSubstringInBraces(latexstring, match.end())
        argument2 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + 2)
        matchlist.append((matchid, match.start(), argument1, argument2))

    result = latexstring
    if (len(matchlist) > 0):
        # Replace inprod{.}{.} with \langle . \,, . \rangle in result string.
        #"\\langle" + matchobject.group(1) + "\,," + matchobject.group(2) + "\\rangle"
        for (matchid, startpos, argument1, argument2) in reversed(matchlist):
            endpos = startpos + 11 + len(argument1) + len(argument2)
            result = result[:startpos] + "\\begin{pmatrix} " + argument1 + "\\\\ " + argument2 + " \\end{pmatrix}" + result[endpos:]

    return result

def SourceRefReplace(latexstring, sourcesstring):
    # Replace all occurrences of source citations, of the form [\ref{source}], with a footnote containing the reference as found on a single line in the sourcesstring.
    result = latexstring
    regexpression = r"\[\\ref{([^}]+)}\]"
    matches = re.finditer(regexpression, result, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        matchlist.append((matchid, match.start(), match.group(1)))
    if (len(matchlist) > 0):
        for (matchid, startpos, argument) in reversed(matchlist):
            regexpression = r"\\item \\label{" + argument + r"} (.*)(\\fi)?"
            sourcematch = re.search(regexpression, sourcesstring, re.MULTILINE)
            if (sourcematch != None):
                endpos = startpos + 8 + len(argument)
                result = result[:startpos] + "\\footnote{" + sourcematch.group(1) + "}" + result[endpos:]
    return result

def TwoArgumentMacroReplace(latexstring, latexmacro, startstring, midstring, endstring):
    # Given a LaTeX string, a pattern of the form "\macro", find all occurrences of \macro{}{} (allowing for nested braces) and replace with startstring . midstring . endstring. Example: \inprod{}{} -> <. , .>.
    matches = re.finditer(latexmacro + r"{", latexstring, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        #print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchid, start = match.start(), end = match.end(), match = match.group()))
        argument1 = FindSubstringInBraces(latexstring, match.end())
        argument2 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + 2)
        matchlist.append((matchid, match.start(), argument1, argument2))

    result = latexstring
    if (len(matchlist) > 0):
        # Replace inprod{.}{.} with \langle . \,, . \rangle in result string.
        #"\\langle" + matchobject.group(1) + "\,," + matchobject.group(2) + "\\rangle"
        for (matchid, startpos, argument1, argument2) in reversed(matchlist):
            endpos = startpos + len(latexmacro) + 4 + len(argument1) + len(argument2) - 1
            result = result[:startpos] + startstring + argument1 + midstring + argument2 + endstring + result[endpos:]

    return result

def dvReplace(matchobject):
    # Replace \dv[n]{x}, \dv[n]{y}{x} with actual derivatives, to nth order. First order if no [n] argument given. # No third argument needed as ordinary derivative can only be with respect to one argument.
    result = "\\frac{\\mathrm{d}"
    if (matchobject.group(1) != None):
        # There's a power, i.e., n>1.
        result += "^" + matchobject.group(2) + " "
    if (matchobject.group(5) != None):
        # Two arguments.
        result += matchobject.group(4) + "}{\\mathrm{d}" + matchobject.group(6)
    else:
        # One argument.
        result += "}{\\mathrm{d}" + matchobject.group(4)
    if (matchobject.group(1) != None):
        result += "^" + matchobject.group(2)
    result += "}"
    return result

def pdvReplace(matchobject):
    # Replace \pdv[n]{f}{x} (and possibly further arguments) with actual partial derivatives, to nth order.
    # If no [n] argument given, assume first order if there are two arguments, and second order if there are three.
    result = "\\frac{\\partial"
    
    # First the power.
    if (matchobject.group(1) != None):
        # There's a power, i.e., n>1.
        result += "^" + matchobject.group(2) + " "
    elif (matchobject.group(7) != None):
        # There are three arguments; set power to two.
        result += "^2 "
    else:
        result += " "
    
    if (matchobject.group(5) != None):
        # At least two arguments.
        result += matchobject.group(4) + "}{\\partial " + matchobject.group(6)
        if (matchobject.group(7) != None):
            # Three arguments.
            result += " \\partial " + matchobject.group(8)
    else:
        # One argument.
        result += "}{\\partial " + matchobject.group(4)

    if ((matchobject.group(1) != None) and (matchobject.group(7) == None)):
        # There's a specified power. Add it.
        result += "^" + matchobject.group(2)
    result += "}"

    return result

def pdvReplaceOLD(latexstring):
    # Replace \pdv[n]{f}{x} (and possibly further arguments) with actual partial derivatives, to nth order.
    # First find all occurrences with an n argument.
    matches = re.finditer(r"\\pdv(\[(\d)\])?{", latexstring, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches):
        #print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchid, start = match.start(), end = match.end(), match = match.group()))
        argument1 = FindSubstringInBraces(latexstring, match.end())
        argument2 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + 2)
        totallength = match.end() - match.start() + len(argument1) + len(argument2) + 4
        if (match.group(1) != None): 
            #print(", order {number}\n".format(number = match.group(2)))
            if (latexstring[match.end() + len(argument1) + len(argument2) + 3] == "{"):
                argument3 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + len(argument2) + 4)
                #print([argument1, argument2, argument3])
                argument1 = "\\partial^2 " + argument1
                argument2 = "\\partial " + argument2 + " \\partial " + argument3
                totallength += len(argument3) + 2
            else:
                #print([argument1, argument2])
                argument1 = "\\partial^" + match.group(2) + " " + argument1
                argument2 = "\\partial " + argument2 + "^" + match.group(2)
        else:
            #print([argument1, argument2])
            argument1 = "\\partial " + argument1
            argument2 = "\\partial " + argument2
        matchlist.append((matchid, match.start(), totallength, argument1, argument2))
    
    result = latexstring
    if (len(matchlist) > 0):
        for (matchid, startpos, totallength, argument1, argument2) in reversed(matchlist):
            endpos = startpos + totallength - 1
            result = result[:startpos] + "\\frac{" + argument1 + "}{" + argument2 + "}" + result[endpos:]

    return result


def InprodReplace(latexstring):
    # Given a LaTeX string, replace \inprod{}{} with <. , .>, allowing for nested braces.
    #  NB: Can be replaced by TwoArgumentMacroReplace.
    regexpression = r"\\inprod{"
    matches = re.finditer(regexpression, latexstring, re.MULTILINE)
    inprodlist = []
    for inprodid, match in enumerate(matches, start=1):
        # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = footnoteid, start = match.start(), end = match.end(), match = match.group()))
        argument1 = FindSubstringInBraces(latexstring, match.end())
        argument2 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + 2)
        inprodlist.append((inprodid, match.start(), argument1, argument2))

    result = latexstring
    if (len(inprodlist) > 0):
        # Replace inprod{.}{.} with \langle . \,, . \rangle in result string.
        #"\\langle" + matchobject.group(1) + "\,," + matchobject.group(2) + "\\rangle"
        for (inprodid, startpos, argument1, argument2) in reversed(inprodlist):
            endpos = startpos + 11 + len(argument1) + len(argument2)
            result = result[:startpos] + r"\\langle" + argument1 + r" \\,, " + argument2 + r"\\rangle" + result[endpos:]

    return result

def ThreeArgumentMacroReplace(latexstring, regexpression, startstring, midstring1, midstring2, endstring):
    # Given a LaTeX string, a pattern of the form "\macro", find all occurrences of \macro{}{} (allowing for nested braces) and replace with startstring . midstring . endstring. Example: \inprod{}{} -> <. , .>.
    matches = re.finditer(regexpression + r"{", latexstring, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchid, start = match.start(), end = match.end(), match = match.group()))
        argument1 = FindSubstringInBraces(latexstring, match.end())
        argument2 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + 2)
        argument3 = FindSubstringInBraces(latexstring, match.end() + len(argument1) + len(argument2) + 4)
        matchlist.append((matchid, match.start(), argument1, argument2, argument3))

    result = latexstring
    if (len(matchlist) > 0):
        # Replace macro{.}{.}{.} with beginstring . midstring1 . midstring2 . endstring in result string.
        #"\\langle" + matchobject.group(1) + "\,," + matchobject.group(2) + "\\rangle"
        for (matchid, startpos, argument1, argument2, argument3) in reversed(matchlist):
            endpos = startpos + len(regexpression) + 6 + len(argument1) + len(argument2) + len(argument3) - 1
            result = result[:startpos] + startstring + argument1 + midstring1 + argument2 + midstring2 + argument3 + endstring + result[endpos:]

    return result

def EquationToAdmonition(matchobject):
    result = "```{math}\n"
    if matchobject.group(2) != None:
        result += ":label: " + matchobject.group(3) + "\n"
    result += matchobject.group(1) + "\n```\n"
    return result

def FormatFootnoteText(footnotetext):
    # Format the text in a footnote, such that, after the first line, every line indents, and admonitions are properly started on their own line.
    # First, make sure any stand-alone equations are in admonition form.
    regexpression = r"\$\$\n\s*(.*)\n\s*\$\$( \(([^\)]+)\))?"
    result = re.sub(regexpression, EquationToAdmonition, footnotetext, 0, re.MULTILINE)
    lines = str.split(result, "\n")
    result = lines[0] + "\n"
    if (len(lines) > 1):
        lines.pop(0)
        for line in lines:
            if (line != ""):
                result += "\t" + str.strip(line) + "\n"
    return result

def FigureCodeReplace(matchobject):
    # For each figure, check if there is a source file (python code to generate graphs etc.).
    # If so, replace the figure with the source file code + a rendering.
    # Retain caption and label.
    # NB: The figure source file should be in the folder images/(subfolder if present) (as this is the target in the MD file) and have the same name as the actual figure.
    sourcefilename = basepath + str.split(matchobject.group(1), ".")[0] + ".py"
    if (os.path.isfile(sourcefilename)):
        sourcefilelabel = str.split(str.split(matchobject.group(1), ".")[0], "/")[-1]
        result = "```{code-cell} ipython3\n:tags: [hide-input, remove-output]\n\n%config InlineBackend.figure_formats = ['svg']\n"
        with open(sourcefilename, 'r') as sourcefile:
            # Read file.
            result += sourcefile.read()
        result += "\n# Save graph to load in figure later (special Jupyter Book feature)\n"
        result += "glue(\"" + sourcefilelabel + "\", fig, display=False)\n```\n\n"
        result += "```{glue:figure} " + sourcefilelabel + "\n"
        if (matchobject.group(2) != None):
            # Figure label.
            result += ":name: " + matchobject.group(4) + "\n"
        if (matchobject.group(9) != None):
            # Figure caption.
            result += matchobject.group(9)
        result += "```\n"
    else:
        result = matchobject.group(0)
    return result

def ConvertFileContentToMarkdown(latexsource, sourceslist, isBaseFile):
    # Generate markdown from LaTeX through successive substitutions.
    # Input: read file (essentially a long string).
    # Second input: read content of file with sources (also a long string, only if given).
    # Third input: true if base file, false if problem (will be run again with basefile later, to get all refs and footnotes right).
    # Output: same string converted to MyST Markdown, can be written to a file.

    # Leave out as it gives unintended side-effects. 
    ## Step 0: Strip preamble and \end{document} (and anything after \end{document}).
    #regexpression = r"\\documentclass((.*?)\\begin{document}\s|\\end{document}(.*?))"
    #result = re.sub(regexpression, "", latexsource, 0, re.MULTILINE | re.DOTALL)

    result = latexsource

    # Prep step: LaTeX conditionals.
    # We only select A4paper parts from \ifAfourpaper ... \else .. \fi;
    # don't include solutions, and take the part that is not 'problemset'.
    # Flags for including parts (containsX): assume not.
    # For Aurele's book: take the \ifchoicecolor option.
    # First, find all instances of \ifxxx.
    regexpression = r"\\if(Afourpaper|includesolutions|problemset|choicecolor|online|contains\w+)?"
    matches = re.finditer(regexpression, result, re.MULTILINE)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        ## For each match, look for the matching closing "\fi". Could be on same line, but also further down. # Moved to below as it should be done per if.
        #arguments = FindMatchingEndif(result, match.end())
        #matchlist.append((matchid, match.start(), match.group(1), arguments[0], arguments[1]))
        matchlist.append((matchid, match.start(), match.end(), match.group(1)))
    # Note there is a bug: if there are nested conditionals, one of the arguments contains another if, but if that's already removed, we remove too much.    
    if (len(matchlist) > 0):
        #for (matchid, startpos, qualifier, argument1, argument2) in reversed(matchlist):
        for (matchid, startpos, qualifierend, qualifier) in reversed(matchlist):
            # Found a qualifier.
            # NEW: find the matching \fi and arguments.
            arguments = FindMatchingEndif(result, qualifierend)
            # First, get the length of the block:
            # 3 for '\if', length of the qualifier, length of the first argument (till \else or \fi),
            # 3 for '\fi', and if second argument not "", 5 for '\else' and second argument's length.
            #endpos = startpos + 6 + len(qualifier) + len(argument1)
            endpos = startpos + 6 + len(qualifier) + len(arguments[0])
            if (arguments[1] != ""): endpos += 5 + len(arguments[1])
            #if (argument2 != ""): endpos += 5 + len(argument2)
            # Now act depending on the code.
            if (qualifier == 'Afourpaper') or (qualifier == 'choicecolor') or (qualifier == 'online'):
                # Take the first part.
                result = result[:startpos] + arguments[0] + result[endpos:]
            elif (qualifier == 'includesolutions') or (qualifier == 'problemset'):
                # Take the last part.
                result = result[:startpos] + arguments[1] + result[endpos:]
            elif (qualifier == 'containsLagrangianmechanics') or (qualifier == 'containsCM'):
                # Take the first part (for physics1A book).
                result = result[:startpos] + arguments[0] + result[endpos:]
            else:
                # Take the last part (might need adaptation!)
                result = result[:startpos] + arguments[1] + result[endpos:]

    # Replace occurences of source citations (strictly of the form [\ref{}]) with a footnote, containing the info found in the sourceslist.
    if (sourceslist != ""):
        result = SourceRefReplace(result, sourceslist)

    """
    # Step 0: Replace LaTeX comments with MarkDown / HTML ones.
    # The leading "[^\\]" is to prevent \\% for actual % symbols to be caught.
    regexpression = r"[^\\]%([^\n]+)"
    result = re.sub(regexpression, CommentReplace, result)

    # Remove empty lines starting with a %.
    result = re.sub(r"^%$", "", result, 0, re.MULTILINE)
    """

    # Alternative: strip all comments, as in cleanlatex.
    # Remove lines with just a %.
    result = re.sub(r"%\n", "\n", result, 0, re.MULTILINE)
    
    # Comments that start at the start of a line.
    # Remove unless they start with a keyword (Problemtitle, Source, Figurewidth).
    regexpression = r"^%\s?(Problemtitle|Source|Figurewidth)?(.*)\n"
    result = re.sub(regexpression, LineCommentRemove, result, 0, re.MULTILINE | re.IGNORECASE)

    # Remove comments that start somewhere in a line.
    # Note we need to exclude linestarts and \% (for percent sign in eq.).
    # Just remove.
    regexpression = r"([^\n\\])(%.*)\s"
    result = re.sub(regexpression, CommentRemove, result, 0, re.MULTILINE)

    # Replace any \eqref{} with (\ref{}).
    result = re.sub(r"\\eqref{([^\}]+)}", EqRefReplace, result, 0, re.MULTILINE)

    # Remove any \hspace{} or \vspace{}.
    # UPDATE: just \vspace, \hspace is in info box. But do check for optional " \\"
    #result = re.sub(r"\\(h|v)space\{[^}]+}", "", result, 0, re.MULTILINE)
    result = re.sub(r"\\vspace{[^}]+}( *\\\\)?", "", result, 0, re.MULTILINE)

    # Remove \small and \normalsize (probably need more).
    regexpression = r"\\(small|normalsize)( )?"
    result = re.sub(regexpression, "", result, 0, re.MULTILINE)

    # Remove section counters.
    regexpression = r"\\setcounter{sectioncounter}{\\value{section}}"
    result = re.sub(regexpression, "", result, 0, re.MULTILINE)

    regexpression = r"\\setcounter{section}{\\value{sectioncounter}}"
    result = re.sub(regexpression, "", result, 0, re.MULTILINE)

    # Replace \[ ... \] with \begin{equation*} ... \end{equation*} as they give too much trouble.

    # Replace \ev{ with \braket{ (as used in physics2 package)
    regexpression = r"\\ev{"
    result = re.sub(regexpression, r"\\braket{", result, 0, re.MULTILINE)

    # Step 1: Chapters.
    regexpression = r"\\chapter\*?(\[[^\]]+\])?{([^}]+)}\s?(\\label{([^}]+)})?"
    result = re.sub(regexpression, ChapterTitleReplace, result, 0, re.MULTILINE)

    # Intermediate: for any \begin{appendices} - \end{appendices},
    # add "Appendix " to all section titles,
    # then remove \begin{appendices} - \end{appendices}.
    regexpression = r"\\begin{appendices}\s(.*?)\\end{appendices}\s"
    result = re.sub(regexpression, AppendicesReplace, result, 0, re.MULTILINE | re.DOTALL)
 
    # Also for subappendices.
    regexpression = r"\\begin{subappendices}\s(.*?)\\end{subappendices}\s"
    result = re.sub(regexpression, AppendicesReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step 2: Section headings.
    #regexpression = r"\\(sub|subsub)?section\*?(\[[^\]]+\])?{([^}]+)}\s?(\\label{([^}]+)})?"
    regexpression = r"\\(sub|subsub)?section\*?(\[([^\]]+)\])?{([^}]+)}\s?(\\label{([^}]+)})?"
    result = re.sub(regexpression, SectionTitleReplace, result, 0, re.MULTILINE)

    

    # Dutch (or French) accents. Replace with html.
    # Note that we need to do this early as accents have other roles.
    result = AccentsReplace(result)

    # Step X-1: Replace opening quotes with straight ones.
    # Note that we need to do this *before* the equations / figures as those have their own 'opening quotes' syntax.
    # Modification: only one or two, three or more are admonitions (might already be put in in exercises).
    # result = re.sub("`", "'", result, 0, re.MULTILINE)
    result = re.sub("`+", QuotesReplace, result, 0, re.MULTILINE)

    result = re.sub(r"\\textquotesingle ?", "'", result, 0, re.MULTILINE)

    # One thing that now has gone wrong, is {prf:ref}. Revert.
    regexpression = r"{prf:ref}'([^']+)'"
    result = re.sub(regexpression, FixPrfRef, result, 0, re.MULTILINE)

    # AFTER textquotes, put anything that is in \texttt{..} in a `...` block.
    regexpression = r"\\texttt({([^{}]*+(?:(?1)[^{}]*)*+)})"
    result = regex.sub(regexpression, textttReplace, result, 0, re.MULTILINE)

    # Replace \begin{center} ... \end{center} with \centering.
    # Needs to come before tables and figures.
    # Update: simply remove \begin{center} ... \end{center} as it doesn't fit with jupyter book style.
    regexpression = r"\\begin{center}\s(.*?)\s\\end{center}\s?"
    #result = re.sub(regexpression, CenterToCentering, result, 0, re.MULTILINE | re.DOTALL)
    result = re.sub(regexpression, CenterRemove, result, 0, re.MULTILINE | re.DOTALL)

    # Step 5b: Tables. Also include options to have whitespace before things folded in \begin-\end, and the option to account for a \resizebox command (used to compress a table to one A4 width). Caption becomes title; short caption (in []) taken if provided, in that case the long caption is printed under the table.
    #regexpression = r"\\begin{table(\*)?}(\[\w+\])?\s(\s*\\centering\s)?\s*\\begin{tabular}{([^}]*)}\s(.*?)\\end{tabular}\s*(\\caption{(.*?)})?\s*(\\label{([^}]+)})?\s?\\end{table(\*)?}"
    #regexpression = r"\\begin{table(\*)?}(\[\w+\])?\s(\s*\\centering\s|\\resizebox{\\textwidth}{!}{%?\s)?\s*\\begin{tabular}{([^}]*)}\s(.*?)\\end{tabular}}?\s*(\\caption{(.*?)})?\s*(\\label{([^}]+)})?\s?\\end{table(\*)?}"
    regexpression = r"\\begin{table(\*)?}(\[\w+\])?\s(\s*\\centering\s|\\resizebox{\\textwidth}{!}{%?\s)?\s*\\begin{tabular}{([^}]*)}\s(.*?)\\end{tabular}}?\s*(\\caption(\[([^\]]+)?\])?{(.*?)})?\s*(\\label{([^}]+)})?\s?\\end{table(\*)?}"
    result = re.sub(regexpression, TableReplace, result, 0, re.MULTILINE | re.DOTALL)

    # With tables: Remove any \parbox[x]{dist}{text}, just retaining the text.
    regexpression = r"\\parbox(\[\w+\])?\{[^}]+}{([^}]+)}"
    result = re.sub(regexpression, ParboxRemove, result, 0, re.MULTILINE)

    # Step X-2: Replace non-breaking tildes with &nbsp;
    # Also needs to come early, as markdown ~x~ means subscript - but after table, as we should have no new &.
    result = re.sub("~", "&nbsp;", result, 0, re.MULTILINE)

    # Replace \clearpage, \newpage, etc. with double line break.
    regexpression = r"(\\clearpage|\\cleardoublepage|\\newpage)"
    result = re.sub(regexpression, "\n\n", result, 0, re.MULTILINE)

    # Newlines
    # Replace \newline with end-of-line. Note that we cannot do the same with "\\" as that will also kill the "\\" in equations (e.g. matrix, align).
    #regexpression = r"(\\newline|\\\\)"
    regexpression = r"\\newline"
    result = re.sub(regexpression, "\n", result, 0, re.MULTILINE)

    # Remove \noindent.
    regexpression = r"(\\noindent\s?)"
    result = re.sub(regexpression, "", result, 0, re.MULTILINE)

    # Remove any \- indicating potential breaks in words.
    result = re.sub(r"\\-", "", result, 0, re.MULTILINE)

    # Step: TI layout for straight d's and diffs, bvec, unitvec.
    # Option 1 (preferred): changes to physics package in Latex.
    # Option 2 (without physics package)

    # Straight d's. Note that we exclude \ddo to not accidentally convert \ddot.
    # Update: now check for o in StraightdReplace.
    regexpression = r"\\dd(\w| )?"
    #regexpression = r"\\dd([a-n]|[p-z]| |\\|\^)"
    result = re.sub(regexpression, StraightdReplace, result, 0, re.MULTILINE)

    # bvec
    result = re.sub(r"\\bvec", r"\\bm", result, 0, re.MULTILINE)

    # unitvec
    regexpression = r"\\unitvec{([^}]+)}"
    result = re.sub(regexpression, UnitvecReplace, result, 0, re.MULTILINE)

    # twovec
    #result = TwovecReplace(result)
    #regexpression = r"\\twovec{([^}]*)}{([^}]*)}"
    #result = re.sub(regexpression, TwovecReplace, result, 0, re.MULTILINE)
    result = TwoArgumentMacroReplace(result, r"\\twovec", r"\begin{pmatrix} ", r" \\ ", r" \end{pmatrix}")

    # threevec
    #regexpression = r"\\threevec{([^}]*)}{([^}]*)}{([^}]*)}"
    #result = re.sub(regexpression, ThreevecReplace, result, 0, re.MULTILINE)
    result = ThreeArgumentMacroReplace(result, r"\\threevec", r"\begin{pmatrix} ", r" \\ ", r" \\ ", r" \end{pmatrix}")

    # spinor
    result = TwoArgumentMacroReplace(result, r"\\spinor", r"\begin{pmatrix} ", r" \\ ", r" \end{pmatrix}")

    # Tr (note that \Tr is in physics and as such would not need replacement.)
    result = re.sub(r"\\Tr", r"\\mathrm{Tr}", result, 0, re.MULTILINE)

    # diff
    #regexpression = r"\\diff{([^}]+)}{([^}]+)}"
    #result = re.sub(regexpression, DiffReplace, result, 0, re.MULTILINE)
    result = TwoArgumentMacroReplace(result, r"\\diff", r"\frac{\partial ", r"}{\partial ", r"}")

    # dv, one or two arguments.
    regexpression = r"\\dv(\[(\w)\])?({([^{}]*+(?:(?3)[^{}]*)*+)})({([^{}]*+(?:(?5)[^{}]*)*+)})?"
    result = regex.sub(regexpression, dvReplace, result, 0, re.MULTILINE)

    # dv (old)
    # result = TwoArgumentMacroReplace(result, r"\\dv", r"\frac{\mathrm{d} ", r"}{\mathrm{d} ", r"}")

    # pdv (old)
    #result = pdvReplace(result)

    # pdv, 1-3 arguments
    regexpression = r"\\pdv(\[(\w)\])?({([^{}]*+(?:(?3)[^{}]*)*+)})({([^{}]*+(?:(?5)[^{}]*)*+)})?({([^{}]*+(?:(?7)[^{}]*)*+)})?"
    result = regex.sub(regexpression, pdvReplace, result, 0, re.MULTILINE)

    # pdv. For now, do the [2] separate, leave higher order.
#    result = ThreeArgumentMacroReplace(result, r"\\pdv\[2\]", r"\frac{\partial^2 ", r"}{\partial ", r" \partial ", r"}")
#    result = TwoArgumentMacroReplace(result, r"\\pdv\[2\]", r"\frac{\partial^2 ", r"}{\partial ", r"^2}")
#    result = TwoArgumentMacroReplace(result, r"\\pdv", r"\frac{\partial ", r"}{\partial ", r"}")

    # Commutator
    result = TwoArgumentMacroReplace(result, r"\\commutator", r"\left[", r", ", r"\right]")

    # bookref (TI defined command for problems to be able to refer to book eq. and fig. numbers in solution manual).
    regexpression = r"\\bookref"
    result = re.sub(r"\\bookref", r"\\ref", result, 0, re.MULTILINE)

    # Order symbol
    result = re.sub(r"\\Order", r"\\mathcal{O}", result, 0, re.MULTILINE)

    # Script L Lagrangian
    result = re.sub(r"\\Lg", r"\\mathcal{L}", result, 0, re.MULTILINE)

    # inprod (revised using new TwoArgumentMacroReplace function)
    result = TwoArgumentMacroReplace(result, r"\\inprod", r"\langle ", r" \,, ", r" \rangle")

    # Step 3: Equations.
    # Arbitrary number of lines by 'dotall' flag:
    #regexpression = r"\\begin{equation(\*)?}\s?(\\label{([^}]+)})?\s?(.*?)\\end{equation(\*)?}"
    # Extension to also allow 'label' at end.
    # NB: always go for an admonition in a problem.
    regexpression = r"\\begin{equation(\*)?}\s?(\\label{([^}]+)})?\s?(.*?)(\\label{([^}]+)})?\s?\\end{equation(\*)?}"
    if (isBaseFile):
        result = re.sub(regexpression, EquationReplace, result, 0, re.MULTILINE | re.DOTALL)
    else:
        result = re.sub(regexpression, EquationReplaceAdmonition, result, 0, re.MULTILINE | re.DOTALL)

    # Unnumbered equations with '\[ .. \]' syntax: simply make $$.
    # Update: actually turn into a math admonition, as they are breaking things in jb conversion unless we add white lines (but then they break indentation).
    #result = re.sub(r"(\\\[|\\\])", r"$$", result, 0, re.MULTILINE)
    regexpression = r"\\\[(.*)\\\]"
    result = re.sub(regexpression, UnnumberedEquationReplace, result, 0, re.MULTILINE)

    # Inline equations. If in $equation$, fine. If in \(equation\), put in dollars.
    regexpression = r"\\\((.*?)\\\)"
    result = re.sub(regexpression, InlineEquationReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step 4A: Align environments with subequations numbering.
    # Label in markdown will be the label (if any) given to the whole group.
    # Retrieve other labels as well, making substitutions accordingly.
    # First, we find all subequations sets.
    regexpression = r"\\begin{subequations}(.*?)\\end{subequations}"
    matches = re.finditer(regexpression, result, re.MULTILINE | re.DOTALL)
    # Loop over matches, extracting labels. If there is just one label, we need do nothing (will be the group label). If there are multiple labels, we need to substitute the others in text with A/B/C etc.
    for match in matches:
        labels = re.findall(r"\\label{([^}]+)}" , match.group())
        #print(len(labels))
        if (len(labels) > 1):
            grouplabel = labels[0]
            #print(grouplabel)
            for labelid, label in enumerate(labels):
                if (labelid > 0):
                    # New string: label of the whole group + letter in alphabet. A is number 65, a is 97.
                    labelstring = "ref{" + grouplabel + "})" + chr(96 + labelid)
                    result = re.sub("ref{" + label + r"}\)", labelstring, result, 0, re.MULTILINE)
                    #print([label, labelstring])
                    labelstring = "ref{" + grouplabel + "}" + chr(96 + labelid)
                    result = re.sub(r"ref{" + label + r"}", labelstring, result, 0, re.MULTILINE)

    # Again find all subequation sets, now lifting out the content.
#    regexpression = r"\\begin{subequations}\s(\\label{([^}]+)})?\s?\\begin{align(at)?}({\d})?\s?(.*?)\\end{align(at)?}\s?\\end{subequations}"

 #   result = re.sub(regexpression, SubEqReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step 4: Align environments.
    #regexpression = r"\\begin{align(\*)?}\s(\\label{([^}]+)})?\s?(.*?)\\end{align(\*)?}"
    #result = re.sub(regexpression, AlignReplace, result, 0, re.MULTILINE | re.DOTALL)

    # 4.B: eqnarray for those too stubborn to let go of them.
    # Simply turn into align,
    # killing the second & on each line.
    regexpression = r"\\begin{eqnarray(\*)?}({\d})?\s(\\label{([^}]+)})?\s?(.*?)\s+(\\label{([^}]+)})?\s?\\end{eqnarray(\*)?}"
    result = re.sub(regexpression, EqnArrayToAlign, result, 0, re.MULTILINE | re.DOTALL)

    # Step 4: Align environments.
    # 4.1: regular align, possibly with subequations.
    #regexpression = r"(\\begin{subequations}\s)?(\\label{([^}]+)}\s)?\\begin{align(at)?(\*)?}({\d})?\s(\\label{([^}]+)})?\s?(.*?)\\end{align(at)?(\*)?}(\s)?(\\end{subequations})?"
    # Same, but with additional option for label at end.
    regexpression = r"(\\begin{subequations}\s)?(\\label{([^}]+)}\s)?\\begin{align(at)?(\*)?}({\d})?\s(\\label{([^}]+)})?\s?(.*?)\s+(\\label{([^}]+)})?\s?\\end{align(at)?(\*)?}(\s)?(\\end{subequations})?"
    # Same, but now wihtout a group for the stars (not needed), and with a group for chekcing for a leading ```{math} (due to earlier runthrough in problem or example).
    regexpression = r"(```{math}\n|:label: \w+\n)?(\\begin{subequations}\s)?(\\label{([^}]+)}\s)?\s*?\\begin{align(at)?\*?}({\d})?\s(\\label{([^}]+)})?\s?(.*?)\s+(\\label{([^}]+)})?\s?\\end{align(at)?(\*)?}(\s)?(\\end{subequations})?"
    result = re.sub(regexpression, AlignReplace, result, 0, re.MULTILINE | re.DOTALL)

    

    # Step 5: Figures.
    # TI Figure prior (shold be removed, left in to ease physics1A book production): strip "/figures/PNG" and "/figures/PDF"
    result = re.sub(r"/figures/PNG", "", result, 0, re.MULTILINE)
    result = re.sub(r"/figures/PDF", "", result, 0, re.MULTILINE)
    result = re.sub(r"/problemfigures/PDF", "", result, 0, re.MULTILINE)
    result = re.sub(r"/problemfigures/PNG", "", result, 0, re.MULTILINE)
    result = re.sub(r"mechanics/figures/", "mechanics/", result, 0, re.MULTILINE)
    result = re.sub(r"mechanics/problems/", "mechanics/", result, 0, re.MULTILINE)

    # And for QMbook
    result = re.sub(r"/figures/", "/", result, 0, re.MULTILINE)
    #result = re.sub(r"introduction/figures/", "introduction/", result, 0, re.MULTILINE)
    #result = re.sub(r"SE/figures/", "SE/", result, 0, re.MULTILINE)
    result = re.sub(r"SE/tunnelingexamples.pdf", "SE/tunnelingexamples.png", result, 0, re.MULTILINE)
    result = re.sub(r"SE/Hydrogen_fine_structure.png", "SE/Hydrogen_fine_structure.svg", result, 0, re.MULTILINE)

    # Caption limited by line breaks.
    #regexpression = r"\\begin{figure(\*)?}\s(\\centering\s)?\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\\caption{([^\n]+)})?\s?(\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    # Caption with dotall flag, can contain arbitrary number of line breaks:
    #regexpression = r"\\begin{figure(\*)?}\s(\\centering\s)?\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\\caption{((?s).*?)})?\s?(\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    # Ibid, but through dotall flag
    # (In regexpression101.com, put flag 'single line' for dotall, or \gms)
    #regexpression = r"\\begin{figure(\*)?}\s(\\centering\s)?\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\\caption{(.*?)})?\s?(\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    #regexpression = r"\\begin{figure(\*)?}(\[\w+\])?\s(\\centering\s)?\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\\caption{(.*?)})?\s?(\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    #regexpression = r"\\begin{figure(\*)?}(\[\w+\])?\s(\s*\\centering\s)?\s*\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\s*\\caption{(.*?)})?\s?(\s*\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    #regexpression = r"\\begin{figure(\*)?}(\[\w+\])?\s(\s*\\centering\s)?\s*\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\s*\\caption(\[[^\]]+\])?{(.*?)})?\s?(\s*\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    #regexpression = r"\\begin{figure(\*)?}(\[!?\w+!?\])?\s(\s*\\centering\s)?\s*\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\s*\\caption(\[[^\]]+\])?{(.*?)})?\s?(\s*\\label{([^}]+)})?\s?\\end{figure(\*)?}"
    regexpression = r"\\begin{figure(\*)?}(\[!?\w+!?\])?\s(%Figurewidth: (\d+)\s)?(\s*\\centering\s)?\s*\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(\s*\\caption(\[[^\]]+\])?{(.*?)})?\s?(\s*\\label{([^}]+)})?\s?\\end{figure(\*)?}"

    result = re.sub(regexpression, FigureReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Following is attempt to account for leading spaces / tabs, but makes regexpression greedy.
    #regexpression = r"\\begin{figure(\*)?}(\[\w+\])?\s(.*\\centering\s)?.*\\includegraphics(\[[^\]]+\])?{([^}]+)}\s(.*\\caption{(.*?)})?\s?(.*\\label{([^}]+)})?\s?\\end{figure(\*)?}"

    # Step 6: Theorems, Propositions, Lemmas, proofs, axioms.
    regexpression = r"\\begin{(theorem|proposition|lemma|corollary|axiom|definition|proof)(\*)?}(\[([^\]]+)\])?\s(\\label{([^}]+)}\s)?(.*?)\\end{(theorem|proposition|lemma|corollary|axiom|definition|proof)(\*)?}"
    result = re.sub(regexpression, TheoremReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Internal references and citations only for basefile (will include problems),
    # as otherwise refs in problems might break.
    if (isBaseFile):
        # Step 7A: Internal references to problems.
        # Specific structure: problem~\ref{ch:X}.\ref{pb:Y}
        # (allow for case and 'exercise' instead of 'probblem').
        # Replace with only a link to the exercise (will have 'exercise' by Sphinx setting).
        regexpression = r"(problem|exercise)(~| |&nbsp;)\\ref{[^}]+}\.\\ref{(pb:[^}]+)}"
        result = re.sub(regexpression, ProblemRefReplace, result, 0, re.MULTILINE | re.IGNORECASE)

        # Step 7: Internal references. #TO ADD TABLES
        #regexpression = r"((fig)(?:\.|ure)?|(ch)(\.|apter)?|(sub)?(sec)(\.|tion)?|(app)(\.|endix|ices)?|(eq)(\.|uation)?)?(s)?(~|&nbsp;| )([(])?\\ref{([^}]+)}([)])?"
        #regexpression = r"((fig)(?:\.|ure)?|(table)|(ch)(\.|apter)?|(sub)?(sec)(\.|tion)?|(app)(\.|endix|ices)?|(eq)(\.|uation)?)?(s)?(~|&nbsp;|-|\s)([(])?\\ref{([^}]+)}([)])?"
        regexpression = r"((fig)(?:\.|ure)?|(table)|(ch)(\.|apter)?|(sub)?(sec)(\.|tion)?|(app)(\.|endix|ices)?|(eq)(\.|uation)?|theorem|(prop)(?:\.|osition)?|lemma|corollary|axiom|(def)(?:\.|inition)?)?(s)?(~|&nbsp;|-|\s)([(])?\\ref{([^}]+)}([)])?"
        #result = re.sub(regexpression, RefReplace, result, 0, re.MULTILINE)
        result = re.sub(regexpression, RefReplace, result, 0, re.MULTILINE | re.IGNORECASE)

        # Step 8: Citations. Last two commented-out lines add a local bibliography at the bottom of the page. Unfortunately, it doesn't work well if the same source is cited in multiple documents.
        # Commented-out: add a separate references file.
        regexpression = r"(~|&nbsp;| )\\citep?{([^}]+)}"
        result = re.sub(regexpression, CitationReplace, result, 0, re.MULTILINE)
        matches = re.findall(r"{cite}", result)
        #if (len(matches) > 0):
        #    result += "## References\n```{bibliography}\n:style: unsrt\n:filter: docname in docnames\n```"

    # End of ifBaseFile.

    # Step 9: Enumerate environments - bugged, is greeedy.
    regexpression = r"\\begin{enumerate}(\[([^\]]+)\])?\s(.*?)\\end{enumerate}"
    result = re.sub(regexpression, EnumerateReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step 9b: Itemize environments.
    regexpression = r"\\begin{itemize}\s(.*?)\\end{itemize}"
    regexpression = r"\\begin{itemize}(\[[^\]]+\])?\s(.*?)\\end{itemize}"
    result = re.sub(regexpression, ItemizeReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Hyperlinks
    regexpression = r"\\(book)?href{(.*?)}{(.*?)}"
    result = re.sub(regexpression, HyperlinkReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Astronomical symbols (not widely used, but nice to have)
    result = re.sub(r"\\mercury", "&#x263F;", result, 0, re.MULTILINE)  # ☿
    result = re.sub(r"\\venus", "&#x2640;", result, 0, re.MULTILINE)    # ♀
    result = re.sub(r"\\earth", "&#x2641;", result, 0, re.MULTILINE)    # ⊕
    result = re.sub(r"\\mars", "&#x2642;", result, 0, re.MULTILINE)     # ♂
    result = re.sub(r"\\jupiter", "&#x2643;", result, 0, re.MULTILINE)  # ♃
    result = re.sub(r"\\saturn", "&#x2644;", result, 0, re.MULTILINE)   # ♄
    result = re.sub(r"\\uranus", "&#x26E2;", result, 0, re.MULTILINE)   # ⛢
    result = re.sub(r"\\neptune", "&#x2646;", result, 0, re.MULTILINE)  # ♆
    result = re.sub(r"\\pluto", "&#x2647;", result, 0, re.MULTILINE)    # ♇
    result = re.sub(r"\\sun", "&#x2609;", result, 0, re.MULTILINE)      # ☉ 
    result = re.sub(r"\\leftmoon", "&#x263E;", result, 0, re.MULTILINE)    # ☾ 

    # Step Y: Footnotes. Again, only run for basefile.
    if(isBaseFile):
        # First, we find anything that is either '\footnote' OR anything between top-level matched {}. That's a lot of hits!
        # All
        regexpression = r"\\footnote{"
        matches = re.finditer(regexpression, result, re.MULTILINE)
        footnoteslist = []
        for footnoteid, match in enumerate(matches, start=1):
            # print("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = footnoteid, start = match.start(), end = match.end(), match = match.group()))
            """
            footnotetext = ""
            pos = 0
            nestingdepthcounter = 0
            while (((result[match.end() + pos] != "}") or (nestingdepthcounter > 0)) and (pos < len(result) - match.end())):
                character = result[match.end() + pos]
                footnotetext += character
                if (character == "{"): nestingdepthcounter += 1
                elif (character == "}"): nestingdepthcounter -= 1
                pos += 1
            """
            footnotetext = FindSubstringInBraces(result, match.end())
            footnoteslist.append((footnoteid, match.start(), footnotetext))

        if (len(footnoteslist) > 0):
            # Remove footnotes from result string, add ref number.
            for (footnoteid, startpos, footnotetext) in reversed(footnoteslist):
                endpos = startpos + 11 + len(footnotetext)
                result = result[:startpos] + "<sup>[^" + str(footnoteid) + "]</sup>" + result[endpos:]
            # Add footnotes to the end of result string.
            result += "\n\n"
            for (footnoteid, startpos, footnotetext) in footnoteslist:
                result += "[^" + str(footnoteid) + "]: " + FormatFootnoteText(footnotetext) + "\n\n" 
    
    # End of footnotes isBaseFile

    # Framed boxes: turn into notes.
    regexpression = r"\\begin{framed}\s?(.*?)\\end{framed}\s?"
    result = re.sub(regexpression, FramedReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Color box from optics book, also turn into notes.
    regexpression = r"\\begin{tcolorbox}\s?\[(.*?)\]\s?(.*?)\\end{tcolorbox}\s?"
    result = re.sub(regexpression, TcolorboxReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step Q: People info boxes. Already partly processed as we've gone through the above steps.
    regexpression = r"\\begin{figure\*}\[?.?\]?\n\\fbox{\n\s?\\begin{minipage}\S*\s?\n(\\index{([^}]*)})?(\\textbf{([^}]*)}\s?(\(\d*-\d*\))?.*?)\n\\end{minipage}\n\\hspace{[^}]*}\n\s?\\begin{minipage}\S*\s?\n(.*?)\\includegraphics\[[^\]]*\]{([^}]*)}\n\\caption{(.*?)}\n\\end{minipage}\n}\n\\end{figure\*}"
    result = re.sub(regexpression, InfoboxReplace, result, 0, re.MULTILINE | re.DOTALL)

    # Step 5b: Figures that are not in a `figure` environment: just with an \includegraphics. Note that this should come after the people info boxes.
    regexpression = r"(\\centering)?\s?\\includegraphics(\[[^\]]+\])?{([^}]+)}\s?"
    result = re.sub(regexpression, IncludeGraphicsReplace, result, 0, re.MULTILINE)

    # Step X: Any commands of the form \code{xxx}. This might have to come earlier.
    # Simple code, does not account for nested arguments - replaced.
    #regexpression = r"\\(\w+){([^}]+)}"
    #result = re.sub(regexpression, LatexCommandsReplace, result, 0, re.MULTILINE)

    # Index entries. Note that we take everything from the last \n, as we need to place the index admonition there. We run this multiple times, as there may be multiple entries per block (not very elegant, but works for now).
    regexpression = r"\n(.*?)\\index{([^}]+)}"
    for i in range(5):
        result = re.sub(regexpression, IndexEntryReplace, result, 0, re.MULTILINE)

    # Combine any multiple index boxes.
    regexpression = r"```{index} (.+)\n```\n\n```{index} (.+)\n```"
    for i in range(4):
        result = re.sub(regexpression, CombineIndexEntries, result, 0, re.MULTILINE)

    # Code that can account for nested arguments.
    regexpression = r"\\(\w+){"
    matches = re.finditer(regexpression, result, re.MULTILINE)
    #matchcount = 0
    #for match in matches: matchcount += 1
    #print(matchcount)
    matchlist = []
    for matchid, match in enumerate(matches, start=1):
        # For each match, look for the matching closing "}".
        argument1 = FindSubstringInBraces(result, match.end())
        matchlist.append((matchid, match.start(), match.group(1), argument1))
    #print(len(matchlist))
    if (len(matchlist) > 0):
        for (matchid, startpos, latexcommand, argument1) in reversed(matchlist):
            # Found a command and the argument in braces (including subarguments.)
            # First, get the length of \code{xxx} : length of 'code' + length of 'xxx' + 3 (for the \, {, and }).
            endpos = startpos + 3 + len(latexcommand) + len(argument1)
            # Now act depending on the code.
            if (latexcommand == 'emph' or latexcommand == 'textit' or latexcommand == 'underline'):
                result = result[:startpos] + "*" + argument1 + "*" + result[endpos:]
            elif (latexcommand == 'textbf'):
                result = result[:startpos] + "**" + argument1 + "**" + result[endpos:]
#            elif latexcommand == 'index':
#                # Remove index (this will need updating later).
#                result = result[:startpos] + result[endpos:]
            elif latexcommand == 'mbox':
                result = result[:startpos] + "\\text{" + argument1 + "}" + result[endpos:]
# Remove 'ev' as (1) it's in the physics package and (2) it could be nested.
#            elif latexcommand == 'ev':
#                result = result[:startpos] + "\\langle " + argument1 + " \\rangle" + result[endpos:]

    # {\bf XYZ} --> **XYZ**
    regexpression = r"\{\\bf([^\}]+)\}"
    result = re.sub(regexpression, bfInTextReplace, result, 0, re.MULTILINE)

    # {\it XYZ} or {\em XYZ} --> *XYZ*
    regexpression = r"\{\\(it|em)([^\}]+)\}"
    result = re.sub(regexpression, itInTextReplace, result, 0, re.MULTILINE)

    # TI physics 1A specific (needs manual intervention otherwise)
    # Ampère in table (& gets replaced by |)
    result = re.sub(r"Amp\|egrave;re", "Amp&egrave;re", result)
    # Ceres symbol in eqs. & const.
    result = re.sub(r"Ceres \|  \|", "Ceres | &#x26B3; |", result, 0, re.MULTILINE)
    # defCV in entropy.md refers to a subequation.
    result = re.sub(r"{eq}`defCV`", "{eq}`defspecificheat`A", result)
    # Part {eq}`part:mechanics` should get part I as the parts have no labels.
    result = re.sub(r"{eq}`part:mechanics`", "I", result)

    # TI mathappendix specific
    # Width of polar coordinates figure - superseded by %Figurewidth: macro.
    # result = re.sub(r":name: fig:polarcoordinates\n", ":name: fig:polarcoordinates\n:width: 300px\n", result)

    # Admonitions may have become nested. Resolve by matching opening-closing pairs, adding levels as required. Note that we only need to do this once, i.e., when processing the whole file
    if(isBaseFile):
        # First, find all opening and closing admonitions.
        regexpression = r"```({[^}]*})?(.*)?\n"
        matches = re.finditer(regexpression, result, re.MULTILINE)
        # Make a list of admonitions (open/close), as they appear. Record id, startpos, type (0=open, 1=close), and indent level (all set at 0).
        matchlist = []
        for matchid, match in enumerate(matches): #enumerate(matches, start=0):
            if (match.group(1) != None): matchtype = 0
            else: matchtype = 1
            matchlist.append([matchid, match.start(), matchtype, 0])    # Square brackets for (mutable) list; round brackets give (immutable) tuple and an error when we need to change value of indent level below.
        # Now go through the list in reverse order. For every closing admonition, find the accompanying open one,
        # counting how many levels of subadmonitions they contain.
        # If they contain subadmonitions, add the required number of extra `, also store that number for the accompanying open admonition. Open admonitions only add ` (as many as recorded).
        if (len(matchlist) > 0):
            for (matchid, startpos, type, level) in reversed(matchlist):
                # Check open / closed.
                if (type == 0):
                    # Open. Read level.
                    if (level > 0):
                        # Need to add level number of ` - do so.
                        insertstring = "`" * level
                        result = result[:startpos] + insertstring + result[startpos:]
                else:
                    # Closed. Search back for accompanying open.
                    locallevel = 0
                    level = 0
                    pos = matchid-1
                    while ((pos > 0) and ((locallevel > 0) or (matchlist[pos][2] == 1))):
                        if (matchlist[pos][2] == 1):
                            # Previous admonition is a close. Increase level.
                            locallevel += 1
                            if (locallevel > level): level = locallevel
                        else:
                            # Previous admonition is an open. Decrease level.
                            locallevel -= 1
                        pos -= 1
                    # If the curent pair contains others, level is larger than one.
                    # Add extra ` for the current close, and store level for the open.
                    if level > 0:
                        insertstring = "`" * level
                        result = result[:startpos] + insertstring + result[startpos:]
                        matchlist[pos][3] = level
    # End isBaseFile for admonition nesting.

    # Cleanup. First, remove superfluous whitespace and empty lines.
    result = re.sub(r"^\s*\n", "\n", result, 0, re.MULTILINE)

    # Weird repeats of \n sometimes randomly appear. Clean up.
    #result = re.sub(r"\n{3,}", "\n\n", result, 0, re.MULTILINE)

    # In a problem file or example, remove all empty lines, and after the first 1. or -, give every line that doesn't start with a number or a - an indentation.
    if (not isBaseFile):
        result = re.sub(r"^\n", "", result, 0, re.MULTILINE)
        lines = str.split(result, "\n")
        result = ""
        enumerationstarted = False
        for line in lines:
            line = str.strip(line)
            if (line != ""):
                if (line[0:2] == "1." or line[0:2] == "- "):
                    enumerationstarted = True
                    result += line + "\n"
                else:
                    if (enumerationstarted):
                        result += "\t" + line + "\n"
                    else:
                        result += line + "\n"

    # Finally, we check figures, to see if any have a source file (and thus could be built from the source).
    # Note that we include options for indentation (to maintain!).
    #regexpression = r"`{3,}{figure}\s(.+?)\s(\:name\:\s(.+?)\s)?(\:width\:\s(.+?)\s)?(.*?\s)?`{3,}"
    regexpression = r"```{figure}\s(.+?)\s((\s+)?\:name\:\s(.+?)\s)?((\s+)?\:width\:\s(.+?)\s)?(\s+)?(.*?\s)?(\s+)?```"
    result = re.sub(regexpression, FigureCodeReplace, result, 0, re.MULTILINE | re.DOTALL)

    # If we have replaced any figure with code, we need a YAML frontmatter block.
    if (re.search(r"{code-cell} ipython3", result) != None):
        YAMLblock = "---\njupytext:\n    formats: md:myst\n"
        YAMLblock += "    text_representation:\n        extension: .md\n        format_name: myst\n"
        YAMLblock += "kernelspec:\n    display_name: Python 3 (ipykernel)\n    language: python\n"
        YAMLblock += "    name: python3\n"
        YAMLblock += "---\n"
        """
        with open("./YAMLblock.md", 'r') as YAMLfrontmatter:
            # Read file.
            YAMLblock = YAMLfrontmatter.read()
        """
        result = YAMLblock + result

    return result

def ProcessWorkedExample(examplestring, title, label, sourceslist):
    # Set up start.
    result = "```{prf:example} " + title + "\n"
    if (label != ""): result += ":label: " + label + "\n"
    result += ":class: example\n"

    # Split off a solution (if it's there). To simplify, first replace with an easy-to-recognize pattern.
    examplestring2 = re.sub(r"%Worked example solution\n\\(sub)?subsubsection\*{Solution}", "|||", examplestring, 0, re.MULTILINE)
    examplelist = str.split(examplestring2, "|||")

    # First the problem part
    result += ConvertFileContentToMarkdown(examplelist[0], sourceslist, False)

    # Check if there's a solution part.
    if (len(examplelist) > 1):
        result += "\n---\n" + "**Solution**\n" + ConvertFileContentToMarkdown(examplelist[1], sourceslist, False)

    return result + "\n```\n"

def ProcessProblemtitle(problemstring):
    # Check if the problem has a title. If so, extract it, and remove from the problem string.
    result = problemstring
    regexpression = r"%\s?Problemtitle{([^}]+)}|%\s?Problemtitle\s?:?\s?(.*)|^\\textbf{([^}]+)}"
    problemtitlematch = re.findall(regexpression, problemstring, re.MULTILINE)
    if (len(problemtitlematch) > 0 and problemtitlematch[0][0] != ""):
        # Title found as comment in LaTeX, type %Problemtitle{X}. Copy title and remove comment.
        problemtitle = problemtitlematch[0][0]
        result = re.sub(r"% ?Problemtitle{([^}]+)}", "", problemstring)
    elif (len(problemtitlematch) > 0 and problemtitlematch[0][1] != ""):
        # Title found as comment in LaTeX, type % Problemtitle X. Copy title and remove content.
        problemtitle = problemtitlematch[0][1]
        result = re.sub(r"%\s?Problemtitle\s?:?\s?(.*)", "", problemstring)
    elif (len(problemtitlematch) > 0 and len(problemtitlematch[0]) > 0 and problemtitlematch[0][2] != ""):
        # Problem title found as bold text at start of line. Copy title.
        problemtitle = problemtitlematch[0][2]
        # Could add something here to remove the title - leave for now.
    else: problemtitle = ""
    # Also remove any remaining lines that start with %.
    result = re.sub(r"%.*", "", result, re.MULTILINE)
    return (problemtitle, result.strip())

def ProblembreakReplace(matchobject):
    # First, look for equations, and make them math admonitions (dollarmath doesn't work here as we have indented lines).
    regexpression = r"\\begin{equation(\*)?}\s*(\\label{([^}]+)})?\s?(.*?)\\end{equation(\*)?}"
    result = re.sub(regexpression, EquationReplaceAdmonition, matchobject.group(1), 0, re.MULTILINE | re.DOTALL)
    # Next, indent all lines to not break the numbering.
    textlines = str.split(result,"\n")
    textblock = "\n"
    for line in textlines:
        textblock += "    " + line + "\n"
    return textblock + "\n"

def ProcessProblembreaks(problemstring):
    # Check if somewhere (or at multiple places) in the problem there is a \setcounter \end{enumerate} ... \begin{enumerate} \setcounter pattern. If so, remove it, and indent the text in between.
    # Also remove any "\newcounter{X}" line.
    regexpression = r"\\newcounter{[^}]+}\n"
    result = re.sub(regexpression, "", problemstring, 0, re.MULTILINE)
    regexpression = r"\\setcounter{[^}]+}{\\value{enumi+}}\s\\end{enumerate}\s(.*?)\\begin{enumerate}\[\(a\)\]\s\\setcounter{enumi+}{\\value{[^}]+}}"
    result = re.sub(regexpression, ProblembreakReplace, result, 0, re.MULTILINE | re.DOTALL)
    return result

def ProcessProblems(problemsource, sourceslist):
    # Given a string containing a problem set, convert it to a set of exercises in markdown/sphinx.
    # The string consists of a \begin{enumerate}[..] \item \item ... \end{enumerate},
    # with an item for each problem, each on a line, with one of two options: either an included file, or a single problem with no subproblems.

    # Remove any line that starts with %\item
    problemliststring = re.sub(r"%\\item(.*?)\n", "", problemsource, 0, re.MULTILINE)

    # First, list all \item positions, catching a potential following \label and a potential following \input, and get (last position) the \end{enumerate}.
    regexpression = r"(\\item|\\end{enumerate})\s?(\\label{([^}]*)})?\s?(\\input{([^}]*)})?"
    #matches = re.finditer(regexpression, problemsource, re.MULTILINE)
    matches = re.finditer(regexpression, problemliststring, re.MULTILINE)
    # Make a list of problems, as they appear. Record id, startpos, label (if present), source file (if present).
    matchlist = []
    for matchid, match in enumerate(matches):
        if (match.group(2) != None): problemlabel = match.group(3)
        else: problemlabel = ""
        if (match.group(4) != None): problempath = match.group(5)
        else: problempath = ""
        matchlist.append([matchid, match.start(), problemlabel, problempath]) 

    #print(len(matchlist))
    returnstring = ""
    if len(matchlist) > 0:
        for (matchid, startpos, problemlabel, problempath) in matchlist:
            if (matchid < len(matchlist)-1):
                if (problempath != ""):
                    #with open(basepath + problempath.rstrip(".tex") + ".tex",
                    with open(basepath + problempath.split(".")[0] + ".tex", 'r') as problemfile:
                        #print(problempath)
                        # Read file.
                        problemstring = problemfile.read()
                        # Remove solution if present.
                        regexpression = r"\\ifincludesolutions.*?\n\\fi"
                        problemstring = re.sub(regexpression, "", problemstring, re.MULTILINE | re.DOTALL)
                        # Check if the problem has a title. If so, extract it. Also remove any other lines that start with a %.
                        (problemtitle, problemstring) = ProcessProblemtitle(problemstring)
                        # Check if somewhere in the problem there is a break of the numbering. If so, adapt by indenting.
                        problemstring = ProcessProblembreaks(problemstring)
                        problemstring = ConvertFileContentToMarkdown(problemstring, sourceslist, False)

                        #problemstring = ConvertFileContentToMarkdown(problemstring)
                        #problemstring = ConvertFileContentToMarkdown(problemfile.read())
                else:
                    if (problemlabel != ""):
                        startpos += 9 + len(problemlabel)
                    problemstring = problemsource[startpos+5:matchlist[matchid + 1][1]]
                    # Check if the problem has a title.
                    (problemtitle, problemstring) = ProcessProblemtitle(problemstring)
                    problemstring = ConvertFileContentToMarkdown(problemstring, sourceslist, False)
                
                # LaTeX source converted to Markdown. Wrap in exercise admonition.
                # First we need to know the highest sub-admonition level,
                # to which we add one for the new admonition.
                """ NB: OVERRULED by admonition nesting resolution when running full file
                regexpression = r"`{3,}"    # Find three-or-more `
                admonitionmatches = re.findall(regexpression, problemstring, re.MULTILINE)
                # Find longest element, if there are any.
                if len(admonitionmatches) > 0:
                    maxadmonitionlength = len(max(admonitionmatches))
                    admonitionstring = "`" * (maxadmonitionlength + 1)
                else:
                    admonitionstring = "```"
                """
                admonitionstring = "```"

                # Now add the exercise to the returnstring.
                returnstring += admonitionstring + "{exercise}"
                if (problemtitle != ""): returnstring += " " + problemtitle + "\n"
                else: returnstring += "\n"
                if (problemlabel != ""):
                    returnstring += ":label: " + problemlabel + "\n"
                returnstring += ":class: dropdown\n"
                returnstring += problemstring.rstrip() + "\n" + admonitionstring + "\n\n"

    return returnstring

#def ReadAndConvertLatexFile(filename, sourcesfilename):
def ReadAndConvertLatexContent(content):
    # Main function. Open the file in readonly mode.
    # Generate markdown from LaTeX through successive substitutions.
    #if (sourcesfilename != ""):
    #    with open(sourcesfilename+".tex", 'r') as sourcesfile:
    #        sourceslist = sourcesfile.read()
    #else:
    #    sourceslist = ""
    sourceslist = "" 
    latexsource = content 

    #with open(filename+".tex", 'r') as file:
    if True: 
        #latexsource = file.read()
        result = ""
        # Check if the file has 'worked example' sections,
        # indicated by a pair or triplet (with solution) of comments.
        #regexpression = r"(%Worked example start\n\\(sub)?subsection{Worked example: ([^}]+)}\n)(.*)\n%Worked example end"
        regexpression = r"(%Worked example start\n\\(sub)?subsection{Worked example: ([^}]+)}\n(\\label{([^}]+)}\n)?)(.*?)\n%Worked example end"
        matches = re.finditer(regexpression, latexsource, re.MULTILINE | re.DOTALL)
        # Make a list of matches.
        # Record, id, startpos, title, label, startpos of actual text, endpos.
        matchlist = []
        for matchid, match in enumerate(matches):
            if match.group(4) != None:
                label = match.group(5)
            else:
                label = ""
            matchlist.append([matchid, match.start(), match.group(3), label, match.start() + len(match.group(1)), match.end()])
        if (len(matchlist) > 0):
            prevendpos = 0
            for (matchid, startpos, title, label, realstartpos, endpos) in matchlist:
                result += latexsource[prevendpos:startpos]
                result += ProcessWorkedExample(latexsource[realstartpos:endpos], title, label, sourceslist)
                prevendpos = endpos
            result += latexsource[prevendpos:]
            # Search for references to any of the labels of the problems; replace not with {numref} but with {prf:ref}.
            for (matchid, startpos, title, label, realstartpos, endpos) in matchlist:
                regexpression = r"((sub)?(sec)(\.|tion)?|example)?(s)?(~|&nbsp;|-|\s)\\ref{(" + label + r")}"
                result = re.sub(regexpression, ExampleRefReplace, result, 0, re.MULTILINE | re.IGNORECASE)
            latexsource = result
            result = ""
        #else:
        #    result = latexsource

        # Select problem sets from the file.
        regexpression = r"(\\(sub|subsub)?section\*?{Problems}\s?)(\\label{([^}]+)}\s?)?(\\begin{enumerate}.*?\\end{enumerate}\s|\\input{([^}]+)}\s)"
        matches = re.finditer(regexpression, latexsource, re.MULTILINE | re.DOTALL)
        # Make a list of problem sections, as they appear. Record id, startpos, startpos of actual problems, endpos.
        matchlist = []
        for matchid, match in enumerate(matches):
            if (match.group(6) != None): problemsourcefile = match.group(6)
            else: problemsourcefile = ""
            if (match.group(3) != None): problemsectionlabel = match.group(4)
            else: problemsectionlabel = ""
            if (match.group(2) == None): problemsectionlevel = 1
            elif (match.group(2) == "sub"): problemsectionlevel = 2
            else: problemsectionlevel = 3
            matchlist.append([matchid, match.start(), match.start() + len(match.group(1)), match.end(), problemsourcefile, problemsectionlevel, problemsectionlabel])
        if (len(matchlist) > 0):
            # There are problem sections. Add a style part to the Markdown to make subproblems labeled by a-z instead of numbers.
            # UPDATE: overruled by global setting --> leave this part out.
            #result = '`<style type="text/css">\n% Styling list items inside exercises.\n\t.exercise.admonition ol {\n\t\tlist-style-type: lower-alpha;\n\t}\n</style>`\n\n'
            filelength = len(latexsource)
            result = ""
            """ Add at end, with all problems, to process refs and footnotes in one go.
            if (matchlist[0][1] > 0):
                # Doesn't start with a problem set. Start with regular.
                result += ConvertFileContentToMarkdown(latexsource[:matchlist[0][1]], sourceslist)
            """
            for (matchid, startpos, realstartpos, endpos, problemsourcefile, problemsectionlevel, problemsectionlabel) in matchlist:
                # Add problem section. First add label and section title (right level).
                if (problemsectionlabel != ""):
                    result += "(" + problemsectionlabel + ")=\n"
                result += "#" * (problemsectionlevel + 1) + " Problems\n"
                # Add the problems - either from an external file, or from the detected part.
                if (problemsourcefile != ""):
                    # Different file. Load that file, then process.
                    # The weird stripping-and-adding ".tex" is to ensure that we have ".tex" at the end, as a LaTeX input also works without it.
                    #with open(basepath+problemsourcefile.rstrip(".tex") + ".tex" + 'r'):
                    with open(basepath+problemsourcefile.rstrip(".tex") + ".tex") as problemfile:
                        result += ProcessProblems(problemfile.read(), sourceslist)
                else:
                    result += ProcessProblems(latexsource[realstartpos:endpos], sourceslist)
                # Unless we've reached the end of the source file, add the next part (until the next problem section).
                if (endpos < filelength):
                    if (matchid < len(matchlist)-1):
                        result += ConvertFileContentToMarkdown(latexsource[endpos:matchlist[matchid+1][1]], sourceslist, False)
                    else:
                        result += ConvertFileContentToMarkdown(latexsource[endpos:], sourceslist, False)
            # Now run Convertscript on main text + problems,
            # To get refs and footnotes in problems right.
            result = ConvertFileContentToMarkdown(latexsource[:matchlist[0][1]] + result, sourceslist, True)
        else:
            # No matches, i.e., no problems sections. Just convert the whole file in one go.
            result = ConvertFileContentToMarkdown(latexsource, sourceslist, True)
    return result 

    #if result:
    #    print("Conversion successful!")
    #    with open(filename+".md", 'w') as file:
    #        # Write the converted file as markdown.
    #        file.write(result)
    #        file.truncate()

# Main function - only to be executed if file is called as script, with an argument that is the name of the LaTeX file to be converted.
if __name__ == "__main__":
    import sys
    import re
    # Read filename (first argument) and name of file with (image) sources (optional second argument). Note that the zeroth argument is the script name.
    filename = sys.argv[1]
    #basepath = "./"
    #basepath = "/Users/timonidema/Documents/Teaching/mathappendix/"
    #basepath = "/Users/timonidema/Documents/Teaching/physics lecture notes/"
    #basepath = "/Users/timonidema/Documents/Teaching/quantum mechanics lecture notes/"
    basepath = "/Users/timonidema/Documents/Textbooks/latextemplate/"
    if (len(sys.argv) > 2):
        sourcesfilename = sys.argv[2]
        ReadAndConvertLatexFile(basepath+filename, basepath+sourcesfilename)
    else:
        ReadAndConvertLatexFile(basepath+filename, "")

#    filename = "tensors"
#    filename = "mechanicsforces"
    #basepath = "./"
