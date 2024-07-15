# to comply with the standards of java and mysql regex engine
import regex as re
from std import computed, Object, clip, splice, binary_search, toggleCase
from std.sets import Range, Union


def add(arr, val):
    return [x + val for x in arr]


class LaTexNode:
    is_LaTexCaret = False
    is_LaTexWord = False
    is_LaTexBinary = False
    is_LaTexArgs = False
    
    def __init__(self, parent=None):
        self.parent = parent

    @property
    def root(self):
        while self.parent:
            self = self.parent
        return self

    def has_recursive_error(self):
        try:
            str(self.root)
        except Exception as e:
            return True
        
    def replace(self, *_):
        ...

    @computed
    def physicalText(self):
        caret = self
        s = ''
        while caret is not None:
            s += str(caret)
            caret = caret.parent
#         s += '\n'
        return s
    
    def __str__(self):
        return self.text

    __repr__ = __str__

    def append_left_tag(self, tag):
        caret = LaTexCaret()
        parent = self.parent
        node = LaTexBinary(tag, caret, parent=parent)
        if isinstance(parent, LaTexArgs):
            parent.args.append(node)
        else:
            node = LaTexArgs([self, node], parent)
            if parent:
                parent.replace(self, node)
        return caret

    def append_text_node(self, text):
        parent = self.parent
        node = LaTexWord(text, parent)
        if isinstance(parent, LaTexArgs):
            assert not parent.args[-1].is_LaTexWord
            parent.args.append(node)
            return node
        else:
            array = LaTexArgs([self, node], parent)
            if parent:
                parent.replace(self, array)
            return array

    def enumerate(self):
        assert False, type(self)
        
    def has(self, cls):
        return False
    
    def __repr__(self):
        return str(self)
    
    @property
    def zeros(self):
        return []
    
    @computed
    def style(self):
        return {}

    def modify_style(self, tag):
        if self.text:
            set = Range(0, len(self.text))
            _style = self.style
            if tag in _style:
                _style[tag] = _style[tag].union_without_merging(set)
            else:
                _style[tag] = set
    
    @property
    def length(self):
        return self.stop - self.start
    
    def sanctity_check(self):
        ...
        
    @computed
    def style_traits(self):
        style_traits = [''] * len(self.text)
        for i, s in enumerate(self.style_input):
            s = [*s]
            s.sort()
            s = '.'.join(s)
            style_traits[i] = s
        return style_traits
    
    @computed
    def style_input(self):
        style_input = [set() for _ in range(len(self.text))]
        for tag, s in self.style.items():
            if s.is_Range:
                for i in range(s.start, s.stop):
                    style_input[i].add(tag)
            elif s.is_Union:
                for s in s.args:
                    for i in range(s.start, s.stop):
                        style_input[i].add(tag)
        return style_input
    
    def append_binary(self, cls):
        parent = self.parent
        if cls.input_precedence > parent.stack_precedence:
            new = LaTexCaret()
            parent.replace(self, cls(self, new))
            return new
        else:
            return self.parent.append_binary(cls)

    def append_left_parenthesis(self, scaled=True):
        self.parent.replace(self, LaTexParenthesis(self, scaled=scaled))
        return self

    def append_left_ceil(self, scaled=True):
        print(self.parent)
        self.parent.replace(self, LaTexCeil(self, scaled=scaled))
        return self

class LaTexCaret(LaTexNode):
    is_LaTexCaret = True
    
    def append_left_tag(self, tag):
        caret = LaTexCaret()
        node = LaTexBinary(tag, caret, parent=self.parent)
        if self.parent:
            self.parent.replace(self, node)
        return caret

    def append_word(self, text):
        node = LaTexWord(text, self.parent)
        if self.parent:
            self.parent.replace(self, node)
        return node

    def append_spaces(self, text):
        return self

    @property
    def text(self):
        return ""
    
    @computed
    def physicalText(self):
        return ""
    
    @property
    def logicalLength(self):
        return 0
    
    @property
    def texts(self):
        return []
    
    def enumerate(self):
        yield

    def has(self, cls):
        return isinstance(self, cls)
    
    @property
    def length(self):
        return 0

    
class LaTexWord(LaTexNode):
    is_LaTexWord = True
    
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.arg = text

    @property
    def start(self):
        return self.arg.start
    
    @property
    def stop(self):
        return self.arg.stop

    @start.setter
    def start(self, start):
        self.arg.start = start

    @stop.setter
    def stop(self, stop):
        self.arg.stop = stop
    
    @computed
    def text(self):
        return self.arg.text
    
    @computed
    def physicalText(self):
        return str(self.arg)
    
    @property
    def logicalLength(self):
        return self.arg.length

    @computed
    def texts(self):
        return [self.text]
    
    def logical2physical(self, pos):
        return pos

    def physical2logical(self, pos):
        return pos
    
    def is_physically_valid(self, pos):
        return 0 <= pos < self.length

    def is_sibling(self, start, end):
        return 0 <= start < end <= self.length
        
    def getPhysicalIndices(self, start, stop):
        return start, stop
        
    def enumerate(self):
        yield (self.lexeme, False)

    def has(self, cls):
        return isinstance(self, cls)

    def append_text_node(self, text):
        assert self.stop == text.start, "this.stop == text.start"
        self.stop = text.stop
        return self
    
    def append_spaces(self, text):
        parent = self.parent
        newNode = LaTexPhrase([self, LaTexWord(text)])
        parent.replace(self, newNode)
        return newNode


class LaTexUnary(LaTexNode):
    is_LaTexUnary = True
    def __init__(self, arg, parent=None):
        super().__init__(parent)
        args = arg,
        self.args = args
        arg.parent = self

    @property
    def arg(self):
        return self.args[0]

    @arg.setter
    def arg(self, arg):
        self.args = arg,

    def replace(self, old, new):
        assert old is self.arg
        self.arg = new

        if new.parent:
            assert new.parent is self
        else:
            new.parent = self


class LaTexParenthesis(LaTexUnary):
    def __init__(self, arg, parent=None, scaled=True):
        super().__init__(arg, parent)
        self.scaled = scaled

    @property
    def text(self):
        text = self.arg.text
        lparamthesis = '('
        rparamthesis = ')'
        if self.scaled:
            lparamthesis = r'\left' + lparamthesis
            rparamthesis = r'\right' + rparamthesis
        return f"{lparamthesis}{text}{rparamthesis}"
    

class LaTexBracket(LaTexUnary):
    def __init__(self, arg, parent=None, scaled=True):
        super().__init__(arg, parent)
        self.scaled = scaled

    @property
    def text(self):
        text = self.arg.text
        lbracket = '['
        rbracket = ']'
        if self.scaled:
            lbracket = r'\left' + lbracket
            rbracket = r'\right' + rbracket
        return f"{lbracket}{text}{rbracket}"


class LaTexFloor(LaTexUnary):
    def __init__(self, arg, parent=None, scaled=True):
        super().__init__(arg, parent)
        self.scaled = scaled

    @property
    def text(self):
        text = self.arg.text
        lfloor = f'\lfloor'
        rfloor = f'\rfloor'
        if self.scaled:
            lfloor = r'\left' + lfloor
            rfloor = r'\right' + rfloor
        return f"{lfloor}{text}{rfloor}"


class LaTexCeil(LaTexUnary):
    def __init__(self, arg, parent=None, scaled=True):
        super().__init__(arg, parent)
        self.scaled = scaled

    @property
    def text(self):
        text = self.arg.text
        lceil = f'\lceil'
        rceil = f'\rceil'
        if self.scaled:
            lceil = r'\left' + lceil
            rceil = r'\right' + rceil
        return f"{lceil}{text}{rceil}"


class LaTexBinary(LaTexNode):
    is_LaTexBinary = True
    
    def __init__(self, lhs, rhs, parent=None):
        super().__init__(parent)
        args = lhs, rhs
        self.args = args
        for arg in args:
            arg.parent = self

    @property
    def lhs(self):
        return self.args[0]
    
    @lhs.setter
    def lhs(self, lhs):
        self.args = lhs, self.rhs
        
    @property
    def rhs(self):
        return self.args[1]
    
    @rhs.setter
    def rhs(self, rhs):
        self.args = self.lhs, rhs

    @property
    def start(self):
        return self.tagBegin.start
    
    @property
    def stop(self):
        if self.is_unbalanced:
            if self.arg.is_LaTexCaret:
                return self.tagBegin.stop
            return self.arg.stop
        return self.tagEnd.stop
    
    @computed
    def physicalText(self):
        s = str(self.tagBegin) + str(self.arg)
        if self.is_unbalanced:
            return s
        return s + str(self.tagEnd)

    @computed
    def text(self):
        return self.arg.text

    @property
    def logicalLength(self):
        return self.arg.logicalLength

    @computed
    def texts(self):
        return self.arg.texts
    
    @computed
    def zeros(self):
        return self.arg.zeros if self.text else [0]
        
    def replace(self, old, node):
        if old is self.lhs:
            self.lhs = node
        elif old is self.rhs:
            self.rhs = node
        else:
            raise
        if node.parent:
            assert node.parent is self
        else:
            node.parent = self

    def enumerate(self):
        yield from self.ptr.enumerate()

    def has(self, cls):
        if isinstance(self, cls):
            return True
        return self.ptr.has(cls)

    def reduceToNodeText(self):
        arg, tagBegin, tagEnd, parent = self.arg, self.tagBegin, self.tagEnd, self.parent
        assert tagEnd is None, "tagEnd == null"
        if parent.is_LaTexArgs:
            index = parent.args.index(self)
            count = 1
            
            if arg.is_LaTexArgs:
                args = arg.args
                for arg in args:
                    arg.parent = parent
                
                if args[0].is_LaTexWord:
                    args[0].start = tagBegin.start
                else:
                    args.insert(0, LaTexWord(tagBegin.reduceToNodeText(), parent))
                    
                if index and parent.args[index - 1].is_LaTexWord:
                    index -= 1
                    count += 1
                    args[0].start = parent.args[index].start
                    
            elif arg.is_LaTexCaret:
                arg = LaTexWord(self.tagBegin.reduceToNodeText(), parent)
                if index + 1 < len(parent.args) and parent.args[index + 1].is_LaTexWord:
                    count += 1
                    arg.stop = parent.args[index + 1].stop
                
                if index and parent.args[index - 1].is_LaTexWord:
                    index -= 1
                    count += 1
                    arg.start = parent.args[index].start
                
                args = [arg]
            else:
                arg.parent = parent
                if arg.is_LaTexWord:
                    if index + 1 > len(parent.args) and parent.args[index + 1].is_LaTexWord:
                        count += 1
                        arg.stop = parent.args[index + 1].stop
                    
                    if index and parent.args[index - 1].is_LaTexWord:
                        index -= 1
                        count += 1
                        arg.start = parent.args[index].start
                    else:
                        arg.start = tagBegin.start
                    args = [arg]
                else:
                    args = [LaTexWord(self.tagBegin.reduceToNodeText(), parent), arg]
                    if index and parent.args[index - 1].is_LaTexWord:
                        index -= 1
                        count += 1
                        args[0].start = parent.args[index].start
                    
            splice(parent.args, index, count, *args)
                    
        else:
            assert parent.is_LaTexBinary
            if arg.is_LaTexArgs:
                args = arg.args
                if args[0].is_LaTexWord:
                    args[0].start = tagBegin.start
                else:
                    args.insert(0, LaTexWord(tagBegin.reduceToNodeText(), arg))
            elif arg.is_LaTexWord:
                arg.start = tagBegin.start
            elif arg.is_LaTexCaret:
                arg = LaTexWord(tagBegin.reduceToNodeText())
            else:
                arg = LaTexArgs([LaTexWord(self.tagBegin.reduceToNodeText()), arg])
                
            arg.parent = parent
            parent.replace(self, arg)
    
    def append_tag(self, node):
        parent = self.parent
        if isinstance(parent, LaTexArgs):
            node.parent = parent
            assert not node.is_LaTexCaret
            parent.args.append(node)
            return node
        else:
            array = LaTexArgs([self, node], parent)
            if parent:
                parent.replace(self, array)
            return array
        
    
class LaTexIn(LaTexBinary):
    input_precedence = 5
    stack_precedence = 5

    @property
    def text(self):
        lhs, rhs = self.args
        return fr'{lhs} \in {rhs}'


class LaTexArgs(LaTexNode):
    is_LaTexArgs = True
    
    def __init__(self, args, parent=None):
        super().__init__(parent)
        self.args = args
        for ptr in args:
            ptr.parent = self

    def append_left_tag(self, tag):
        caret = LaTexCaret()
        self.args.append(LaTexBinary(tag, caret, parent=self))
        return caret

    def append_text_node(self, text):
        node = LaTexWord(text, parent=self)
        assert not self.args[-1].is_LaTexWord
        self.args.append(node)
        return node
    
    def append_tag(self, node):
        node.parent = self
        assert not node.is_LaTexCaret
        self.args.append(node)
        return node
    
    @computed
    def physicalText(self):
        return ''.join(str(nd) for nd in self.args)

    @property
    def start(self):
        return self.args[0].start
    
    @property
    def stop(self):
        return self.args[-1].stop

    @computed
    def text(self):
        return ''.join(nd.text for nd in self.args)
    
    @property
    def logicalLength(self):
        return sum(el.logicalLength for el in self.args)

    @computed
    def texts(self):
        return [text for nd in self.args for text in nd.texts]
    
    @computed
    def zeros(self):
        zeros = []
        length = 0
        for arg in self.args:
            zeros += [zero + length for zero in arg.zeros]
            length += len(arg.text)
        return zeros

    @computed
    def style(self):
        _style = {}
        length = 0
        for arg in self.args:
            for tag, set in arg.style.items():
                set += length
                if tag in _style:
                    _style[tag] = _style[tag].union_without_merging(set)
                else:
                    _style[tag] = set
            
            length += len(arg.text)
        
        return _style

    def replace(self, old, node):
        i = self.args.index(old)
        self.args[i] = node
        assert self.__class__ is not node.__class__
        if node.parent:
            assert node.parent is self
        else:
            node.parent = self

    def enumerate(self):
        for node in self.args:
            yield from node.enumerate()

    def has(self, cls):
        if isinstance(self, cls):
            return True
        for e in self.args:
            if e.has(cls):
                return True
        return False

    def interval(self, className):
        if text := self.text:
            zeros = self.zeros
            if not zeros or zeros[0]:
                zeros.insert(0, 0)
            
            if not zeros or zeros[-1] < len(text):
                zeros.append(len(text))
                
            interval = map(lambda i: Object(offsetStart=zeros[i - 1], offsetStop=zeros[i], className=className), range(1, len(zeros)))
            interval = [*interval]
        else:
            interval = []

        return detect_style(interval, self.style)
    
    @computed
    def logicalOffset(self):
        logicalOffset = []
        start = 0
        for arg in self.args:
            stop = start + arg.logicalLength
            logicalOffset.append((start, stop))
            start = stop
        
        return logicalOffset
    
    @computed
    def physicalOffset(self):
        physicalOffset = []
        start = 0
        for arg in self.args:
            stop = start + arg.length
            physicalOffset.append((start, stop))
            start = stop
            
        return physicalOffset
    
    @computed
    def offsets(self):
        offsets = []
        offset = 0
        for arg in self.args:
            offsets.append(offset)
            offset += arg.length - arg.logicalLength
        
        return offsets
        
    def logical2physical(self, pos):
        logicalOffset, offsets = self.logicalOffset, self.offsets
        assert logicalOffset, logicalOffset
        index = binary_search(logicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)

        prev_start = logicalOffset[index][0]
        return self.args[index].logical2physical(pos - prev_start) + prev_start + offsets[index]
    
    def physical2logical(self, pos):
        physicalOffset, offsets = self.physicalOffset, self.offsets
        assert physicalOffset, physicalOffset
        index = binary_search(physicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)

        prev_start = physicalOffset[index][0]
        return self.args[index].physical2logical(pos - prev_start) + prev_start - offsets[index]
    
    def is_physically_valid(self, pos):
        physicalOffset, offsets = self.physicalOffset, self.offsets
        assert physicalOffset, physicalOffset
        index = binary_search(physicalOffset, pos, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
        if index < len(physicalOffset):
            prev_start = physicalOffset[index][0]
            pos -= prev_start
            if pos >= 0:
                return self.args[index].is_physically_valid(pos)
        
    def is_sibling(self, start, end):
        if start < end:
            physicalOffset, offsets = self.physicalOffset, self.offsets
            assert physicalOffset, physicalOffset
            index = binary_search(physicalOffset, start, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
            _index = binary_search(physicalOffset, end - 1, lambda args, hit: -1 if hit >= args[1] else 1 if hit < args[0] else 0)
            if _index == index < len(physicalOffset):
                prev_start = physicalOffset[index][0]
                start -= prev_start
                end -= prev_start
                if start >= 0:
                    return self.args[index].is_sibling(start, end)
                
            if index < _index < len(physicalOffset):
                if self.args[index].is_LaTexWord:
                    if self.args[_index].is_LaTexWord:
                        return True
                    
                    if self.args[_index].is_LaTexBinary:
                        prev_start = physicalOffset[_index][0]
                        end -= prev_start
                        if end == self.args[_index].length:
                            return True

    def cmp(self, args, hit):
        return -1 if hit >= args[1] else 1 if hit < args[0] else 0
        
    def getPhysicalIndices(self, start, stop):
        logicalOffset, offsets = self.logicalOffset, self.offsets
        index = binary_search(logicalOffset, start, self.cmp)
        _index = binary_search(logicalOffset, stop - 1, self.cmp)
        
        if index == _index:
            prev_start = logicalOffset[index][0]
            return add(self.args[index].getPhysicalIndices(start - prev_start, stop - prev_start), prev_start + offsets[index])
        else:
            [prev_start, prev_stop] = logicalOffset[index]
            _prev_start = logicalOffset[_index][0]
            start = add(self.args[index].getPhysicalIndices(start - prev_start, prev_stop - prev_start), prev_start + offsets[index])[0]
            stop = add(self.args[_index].getPhysicalIndices(0, stop - _prev_start), _prev_start + offsets[_index])[1]
            return [start, stop]

    def sanctity_check(self):
        src = str(self)
        for args in self.interval(''):
            offsetStart, offsetStop, className = args.offsetStart, args.offsetStop, args.className
            physicalStart = self.logical2physical(offsetStart)
            physicalStop = physicalStart + offsetStop - offsetStart
            if not re.search('img|mspace|br|entity-(#[0-9]+|#x[0-9a-f]+|[^\t\n\f <&#;]{1,32})', className, re.IGNORECASE):
                if src[physicalStart:physicalStop] != self.text[offsetStart:offsetStop]:
                    print(f'{src[physicalStart:physicalStop]} != {self.text[offsetStart:offsetStop]}')
                    physicalStart = self.logical2physical(offsetStart)
                    physicalStop = physicalStart + offsetStop - offsetStart
                    print(physicalStart, physicalStop)
    

class LaTexPhrase(LaTexArgs):
    
    def append_operator(self, token):
        match token.text:
            case r'\in':
                return self.append_binary(LaTexIn)
            case _:
                raise Exception(f"unexpected token {token}")

        
class LaTexDocument(LaTexArgs):
    input_precedence = 0
    stack_precedence = 0


def style_type(ptr, style):
    offsetStart = ptr.offsetStart
    offsetStop = ptr.offsetStop
    this_set = Range(offsetStart, offsetStop)
    
    style_intersected = {}
    for tag in style:
        set = style[tag]
        if isinstance(set, dict):
            set = Union(**set) if 'args' in set else Range(**set)
        
        intersection = set & this_set
        
        if not intersection:
            continue
        
        style_intersected[tag] = intersection

    if not style_intersected:
        return
    
    indicator = [Object(className=ptr.className) for i in range(offsetStop - offsetStart)]
    
    def processRangeObject(set, tag):
        start = set.start
        stop = set.stop
        for i in range(start, stop):
            if indicator[i].className:
                indicator[i].className += ' ' + tag
            else:
                indicator[i].className = tag
    
    for tag in style_intersected:
        set = style_intersected[tag]
        set = set.__add__(-offsetStart)
            
        args = [set] if set.is_Range else set.args
        for i, s in enumerate(args):
            if i and args[i - 1].stop == s.start:
                tag = toggleCase(tag)
            processRangeObject(s, tag)

    interval = []
    i = 0
    while i < len(indicator):
        j = i + 1
        while j < len(indicator):
            if indicator[j].className != indicator[i].className:
                break
            j += 1
        
        className = indicator[i].className
        if not className:
            className = ptr.className
            
        interval.append(Object(offsetStart=i + offsetStart, offsetStop=j + offsetStart, className=className))
        i = j
        
    return interval
    
    
def detect_style(interval, style):
    i = 0
    while i < len(interval):
        ptr = interval[i]
        
        stype = style_type(ptr, style)
        if isinstance(stype, list):
            interval = interval[:i] + stype + interval[i + 1:]
            i += len(stype) - 1
        elif stype:
            ptr.className += f" {style}"
        
        i += 1
            
    return interval

tagRegex = f'([\\\\](?:\w+| ))|(\w+)|(\s+)|(\W)'

# print("tagRegex =", tagRegex)

def compile(text):
    start = 0
    
    richTexts = []
    for m in re.finditer(tagRegex, text, re.IGNORECASE):
        if start <= len(text) < m.start():
            richTexts.append(TagSpaces(text, start, m.start()))

        if m[1]:
            richText = TagBackSlash(text, m.start(), m.end())
        elif m[2]:
            richText = TagWord(text, m.start(), m.end())
        elif m[3]:
            richText = TagSpaces(text, m.start(), m.end())
        else:
            richText = TagOperator(text, m.start(), m.end())
        
        richTexts.append(richText)
        
        start = m.end()
    
    if len(text) > start:
        richTexts.append(TagSpaces(text, start, len(text)))

    caret = LaTexCaret()
    root = LaTexDocument([caret])

    size = len(richTexts)
    i = 0
    while i < size:
        token = richTexts[i]
        match token:
            case TagWord():
                caret = caret.append_word(token)
            case TagSpaces():
                caret = caret.append_spaces(token)
            case TagOperator():
                caret = caret.append_operator(token)
            case TagBackSlash():
                match token.text:
                    case r'\left':
                        i += 1
                        match richTexts[i].text:
                            case '(':
                                caret = caret.append_left_parenthesis(True)
                            case '[':
                                caret = caret.append_left_bracket(True)
                            case '\lfloor':
                                caret = caret.append_left_floor(True)
                            case '\lceil':
                                caret = caret.append_left_ceil(True)
                    case r'\right':
                        match richTexts[i].text:
                            case ')':
                                caret = caret.append_right_parenthesis(True)
                            case ']':
                                caret = caret.append_right_bracket(True)
                            case r'\rfloor':
                                caret = caret.append_right_floor(True)
                            case r'\rceil':
                                caret = caret.append_right_ceil(True)
                        
                    case _:
                        caret = caret.append_operator(token)
        i += 1

    return root


class PlainString:
    def __init__(self, src, start, stop):
        self.src = src
        self.start = start
        self.stop = stop
    
    def __str__(self):
        return self.text
    
    @property
    def text(self):
        return self.src[self.start:self.stop]
    
    __repr__ = __str__
    
    is_PlainText = False
    is_TagEnd = False
    is_TagBegin = False
    is_TagSingle = False
    is_HTMLEntity = False
    
    @property
    def length(self):
        return self.stop - self.start
    
    def reduceToNodeText(self):
        return TagSpaces(self.src, self.start, self.stop)


class TagBackSlash(PlainString):
    ...


class TagWord(PlainString):
    ...


class TagOperator(PlainString):
    ...


class TagSpaces(PlainString):
    ...
    

def cmp_range(a, b):
    if a.stop <= b.start:
        return -1
            
    if a.start >= b.stop:
        return 1
    
    return 0
    
    
def is_alphanum(ch):
    return re.compile('[\p{Letter}\d]').match(ch)


def convertToOriginal(arr):
    s = ""
    for i in range(len(arr) - 1):
        s += arr[i]

        if is_alphanum(arr[i][-1]) and is_alphanum(arr[i + 1][0]):
            s += " "

    s += arr[-1]
    return s

def is_punct(ch):
    return re.compile('\p{Punctuation}').match(ch)

def convertToOriginalWithOffsets(arr):
    s = ""
    start = 0
    offsets = []
    for i in range(len(arr) - 1):
        stop = start + len(arr[i])
        offsets.append((start, stop))
        s += arr[i]

        if (is_alphanum(arr[i][-1]) or is_punct(arr[i][-1])) and is_alphanum(arr[i + 1][0]):
            s += " "
            stop += 1
            
        start = stop

    stop = start + len(arr[-1])
    offsets.append((start, stop))
    s += arr[-1]
    
    return s, offsets


def test():
    physicalText = "x \\in \\left(\\left\\lceil{x}\\right\\rceil - 1, \\left\\lceil{x}\\right\\rceil\\right]"
    richText = compile(physicalText)
    # print(richText)
    richText.sanctity_check()
    print("physical text =", richText.physicalText)
    print(" logical text =", richText.text)
    print(" style_traits =", richText.style_traits)
    
    # for tag, set in richText.style.items():
    #     if set.is_Range:
    #         print(tag, ":", richText.text[slice(*set.args)])
    #     else:
    #         print(tag, ":", '\t'.join(map(lambda arg: richText.text[slice(*arg.args)], set.args)))
            
    start, stop = 20, 39
    print("the logical text is :")
    print(richText.text[start:stop])
    print("its style trait is :")
    print(richText.style_traits[start:stop])
    
    start, stop = richText.getPhysicalIndices(start, stop)
    print("its original physical text is:")
    print(physicalText[start:stop])
    print()
    

if __name__ == '__main__':
    test()
