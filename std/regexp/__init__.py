
# a legal open bracket is represented by
openBracket = "(?<![\\\\])\\[";

# a non-open-bracket char is represented by :
nonOpenBracket = "(?:(?<=[\\\\])\\[|[^\\[])";

# a non-bracket char is represented by :
nonBracket = "(?:[^\\[\\]]|(?<=[\\\\])\\[|(?<=[\\\\])\\])";

# a legal Close bracket is represented by
CloseBracket = "(?<![\\\\])\\]";

# a non-Close-bracket char is represented by :
nonCloseBracket = "(?:(?<=[\\\\])\\]|[^\\]])";

# any symbol to be matched outside the paired brackets:
# firstly, a legal open bracket is detected and, before the legal open bracket there are no brackets;
# .(?={nonBracket}*{openBracket})

# secondly, no legal Close brackt is detected: //all not
# .(?={nonCloseBracket}*$)
# put together:
outsidePairedBrackets = f"(?={nonBracket}*{openBracket}|{nonCloseBracket}*$)";

# symbol inside the paired brackets:
insidePairedBrackets = f"(?={nonOpenBracket}*{CloseBracket})";

leftParenthesisForCapture = f"(?<![\\\\])\\((?!(?:\\?<=|\\?<!|\\?=|\\?!|\\?:)){outsidePairedBrackets}";

def not_any(regex):
    return f"(?!(?:{regex}))\S+"

def need_escape(s):
    return s in "()[]{}"

def recursive_construct(parentheses, depth):
    mid = len(parentheses) // 2
    start = parentheses[0:mid]
    end = parentheses[mid:]

    if need_escape(start):
        start = "\\" + start
        end = "\\" + end

    not_parentheses = '\\[\\]' if parentheses == '[]' else parentheses
    if depth == 1:
        return f"{start}[^{not_parentheses}]*{end}";

    return f"{start}[^{not_parentheses}]*(?:" + recursive_construct(parentheses, depth - 1) + f"[^{not_parentheses}]*)*{end}"

def balancedGroups(parentheses, depth, multiple='*'):
    regex = recursive_construct(parentheses, depth)
    if multiple:
        return f"((?:{regex}){multiple})"
    else:
        return f"({regex})"

def balancedBraces(depth):
    multiple = ''
    if isinstance(depth, str):
        back = depth[-1]
        if back == '.':
            depth = len(depth)
        else:
            multiple = back
            depth = len(depth) - 1

        depth = 1 << depth - 1

    return balancedGroups("{}", depth, multiple)

def balancedParentheses(depth, multiple=''):
    return balancedGroups("()", depth, multiple)

def balancedBrackets(depth, multiple=''):
    return balancedGroups("[]", depth, multiple)

def recursive_construct_extended(parentheses, depth, lookBehindForBackslash=True):
    assert parentheses != '[]'
    mid = len(parentheses) // 2
    start = parentheses[:mid]
    end = parentheses[mid:]
    
    need_escape = need_escape(start)
    if need_escape:
        start = "\\" + start
        end = "\\" + end

    if need_escape:
        global insidePairedBrackets, outsidePairedBrackets
        nonParenthesesChars = [f"[^{parentheses}]"]
        if lookBehindForBackslash:
            nonParenthesesChars.append(f"(?<=[\\\\])[{parentheses}]")

        nonParenthesesChars.append(f"[{parentheses}]{insidePairedBrackets}")

        nonParenthesesChars = '|'.join(nonParenthesesChars)
        nonParenthesesChars = f"(?:{nonParenthesesChars})*"

        start = f"{start}{outsidePairedBrackets}"
        end = f"{end}{outsidePairedBrackets}"

        if lookBehindForBackslash:
            start = f"(?<![\\\\]){start}"
            end = f"(?<![\\\\]){end}"
    else:
        nonParenthesesChars = f"[^{parentheses}]*"
     
    return f"{start}{nonParenthesesChars}{end}" if depth == 1 else f"{start}{nonParenthesesChars}(?:" + recursive_construct_extended(parentheses, depth - 1, lookBehindForBackslash) + f"{nonParenthesesChars})*{end}"

def balancedGroupsExtended(parentheses, depth, multiple='*', lookBehindForBackslash=True):
    regex = recursive_construct_extended(parentheses, depth, lookBehindForBackslash)
    if multiple:
        return f"((?:{regex}){multiple})";
    else:
        return f"({regex})"

def balancedParenthesesExtended(depth, multiple=''):
    return balancedGroupsExtended("()", depth, multiple, True)

def balancedBracesExtended(depth, multiple=''):
    return balancedGroupsExtended("{}", depth, multiple, False)

def balancedBracketsExtended(depth, multiple=''):
    return balancedGroupsExtended("{}", depth, multiple, False)

import regex as re
def remove_capture(regex):
    global leftParenthesisForCapture
    # (?<=), (?<!), (?=), (?!), (?:)
    return re.sub(leftParenthesisForCapture, "(?:", regex)

from . import balanced
