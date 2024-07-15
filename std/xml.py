# to comply with the standards of java and mysql regex engine
import regex as re
from std import computed, Object, clip, splice, binary_search, toggleCase
import html

from std.sets import Range, Union

def add(arr, val):
    return [x + val for x in arr]

class XMLNode:
    is_XMLNodeCaret = False
    is_XMLNodeText = False
    is_XMLNodeBinaryTag = False
    is_XMLNodeSingleTag = False
    is_XMLNodeArray = False
    is_XMLNodeUnbalancedTag = False
    
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
        return self.physicalText

    __repr__ = __str__

    def append_left_tag(self, tag):
        caret = XMLNodeCaret()
        parent = self.parent
        node = XMLNodeBinaryTag(tag, caret, parent=parent)
        if isinstance(parent, XMLNodeArray):
            parent.args.append(node)
        else:
            node = XMLNodeArray([self, node], parent)
            if parent:
                parent.replace(self, node)
        return caret

    def append_text_node(self, text):
        parent = self.parent
        node = XMLNodeText(text, parent)
        if isinstance(parent, XMLNodeArray):
            assert not parent.args[-1].is_XMLNodeText
            parent.args.append(node)
            return node
        else:
            array = XMLNodeArray([self, node], parent)
            if parent:
                parent.replace(self, array)
            return array

    def append_single_tag(self, tag):
        parent = self.parent
        node = XMLNodeSingleTag(tag, parent)
        if isinstance(parent, XMLNodeArray):
            parent.args.append(node)
            return node
        else:
            array = XMLNodeArray([self, node], parent)
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
    

class XMLNodeCaret(XMLNode):
    is_XMLNodeCaret = True
    
    def append_left_tag(self, tag):
        caret = XMLNodeCaret()
        node = XMLNodeBinaryTag(tag, caret, parent=self.parent)
        if self.parent:
            self.parent.replace(self, node)
        return caret

    def append_text_node(self, text):
        node = XMLNodeText(text, self.parent)
        if self.parent:
            self.parent.replace(self, node)
        return node

    def append_single_tag(self, tag):
        node = XMLNodeSingleTag(tag, self.parent)
        if self.parent:
            self.parent.replace(self, node)
        return node

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

    
class XMLNodeText(XMLNode):
    is_XMLNodeText = True
    
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
    

class XMLNodeBinaryTag(XMLNode):
    is_XMLNodeBinaryTag = True
    
    def __init__(self, tagBegin, arg, tagEnd=None, parent=None):
        super().__init__(parent)
        self.tagBegin = tagBegin
        self.arg = arg
        self.tagEnd = tagEnd
        self.arg.parent = self

    def set_tagEnd(self, tagEnd):
        self.tagEnd = tagEnd
        if 'physicalText' in self.__dict__:
            del self.__dict__['physicalText']
        
    @property
    def tag(self):
        return self.tagBegin.tag
    
    @property
    def start(self):
        return self.tagBegin.start
    
    @property
    def stop(self):
        if self.is_unbalanced:
            if self.arg.is_XMLNodeCaret:
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
        
    @computed
    def style(self):
        _style = {}
        
        if self.text:
            if self.arg.is_XMLNodeArray:
                args = self.arg.args
                if self.tag in ("msub", "munder"):
                    if len(args) == 2:
                        args[1].modify_style('sub')
                            
                elif self.tag in ("msup", "mover"):
                    if len(args) == 2:
                        args[1].modify_style('sup')
                            
                elif self.tag in ("msubsup", "munderover"):
                    if len(args) == 3:
                        args[1].modify_style('sub')
                        args[2].modify_style('sup')
            
            _style[self.tag] = Range(0, len(self.text))
            for tag, set in self.arg.style.items():
                if tag in _style:
                    _style[tag] = _style[tag].union_without_merging(set)
                else:
                    _style[tag] = set
            
        return _style

    @property
    def is_unbalanced(self):
        return not self.tagEnd or isinstance(self.tagEnd, XMLNodeUnbalancedTag)
    
    def logical2physical(self, pos):
        return self.arg.logical2physical(pos) + self.tagBegin.length

    def physical2logical(self, pos):
        return clip(self.arg.physical2logical(pos - self.tagBegin.length), 0, len(self.text) - 1)
    
    def is_physically_valid(self, pos):
        if self.tagBegin.length <= pos < self.length - self.tagEnd.length:
            return self.arg.is_physically_valid(pos - self.tagBegin.length)
    
    def is_sibling(self, start, end):
        if self.tagBegin.length <= start < end <= self.length - self.tagEnd.length:
            start -= self.tagBegin.length
            end -= self.tagBegin.length
            return self.arg.is_sibling(start, end)

    def getPhysicalIndices(self, start, stop):
        start, stop = self.arg.getPhysicalIndices(start, stop)
        
        physicalText = str(self.arg)
        _stop = stop
        #ignore white spaces to the end;
        while _stop < len(physicalText) and physicalText[_stop].isspace():
            _stop += 1
        
        if _stop == len(physicalText):
            if not start:
                stop = _stop + self.tagEnd.length

        stop += self.tagBegin.length
        
        if start:
            start += self.tagBegin.length
            
        return start, stop

    def replace(self, old, node):
        assert self.arg is old, self
        self.arg = node
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
        if parent.is_XMLNodeArray:
            index = parent.args.index(self)
            count = 1
            
            if arg.is_XMLNodeArray:
                args = arg.args
                for arg in args:
                    arg.parent = parent
                
                if args[0].is_XMLNodeText:
                    args[0].start = tagBegin.start
                else:
                    args.insert(0, XMLNodeText(tagBegin.reduceToNodeText(), parent))
                    
                if index and parent.args[index - 1].is_XMLNodeText:
                    index -= 1
                    count += 1
                    args[0].start = parent.args[index].start
                    
            elif arg.is_XMLNodeCaret:
                arg = XMLNodeText(self.tagBegin.reduceToNodeText(), parent)
                if index + 1 < len(parent.args) and parent.args[index + 1].is_XMLNodeText:
                    count += 1
                    arg.stop = parent.args[index + 1].stop
                
                if index and parent.args[index - 1].is_XMLNodeText:
                    index -= 1
                    count += 1
                    arg.start = parent.args[index].start
                
                args = [arg]
            else:
                arg.parent = parent
                if arg.is_XMLNodeText:
                    if index + 1 > len(parent.args) and parent.args[index + 1].is_XMLNodeText:
                        count += 1
                        arg.stop = parent.args[index + 1].stop
                    
                    if index and parent.args[index - 1].is_XMLNodeText:
                        index -= 1
                        count += 1
                        arg.start = parent.args[index].start
                    else:
                        arg.start = tagBegin.start
                    args = [arg]
                else:
                    args = [XMLNodeText(self.tagBegin.reduceToNodeText(), parent), arg]
                    if index and parent.args[index - 1].is_XMLNodeText:
                        index -= 1
                        count += 1
                        args[0].start = parent.args[index].start
                    
            splice(parent.args, index, count, *args)
                    
        else:
            assert parent.is_XMLNodeBinaryTag
            if arg.is_XMLNodeArray:
                args = arg.args
                if args[0].is_XMLNodeText:
                    args[0].start = tagBegin.start
                else:
                    args.insert(0, XMLNodeText(tagBegin.reduceToNodeText(), arg))
            elif arg.is_XMLNodeText:
                arg.start = tagBegin.start
            elif arg.is_XMLNodeCaret:
                arg = XMLNodeText(tagBegin.reduceToNodeText())
            else:
                arg = XMLNodeArray([XMLNodeText(self.tagBegin.reduceToNodeText()), arg])
                
            arg.parent = parent
            parent.replace(self, arg)
    
    def append_tag(self, node):
        parent = self.parent
        if isinstance(parent, XMLNodeArray):
            node.parent = parent
            assert not node.is_XMLNodeCaret
            parent.args.append(node)
            return node
        else:
            array = XMLNodeArray([self, node], parent)
            if parent:
                parent.replace(self, array)
            return array
        
    
class XMLNodeSingleTag(XMLNode):
    is_XMLNodeSingleTag = True
    
    def __init__(self, arg, parent=None):
        super().__init__(parent)
        self.arg = arg

    @property
    def tag(self):
        return self.arg.tag
    
    @property
    def start(self):
        return self.arg.start
    
    @property
    def stop(self):
        return self.arg.stop
    
    @computed
    def physicalText(self):
        return str(self.arg)

    @computed
    def text(self):
        return self.arg.text

    @property
    def logicalLength(self):
        return 1

    @computed
    def texts(self):
        return [self.text]
    
    @computed
    def style(self):
        _style = {}
        _style[self.tag] = Range(0, len(self.text))
        return _style

    def logical2physical(self, pos):
        return self.arg.length - 2

    def physical2logical(self, pos):
        return 0
    
    def is_physically_valid(self, pos):
        ...
            
    def is_sibling(self, start, end):
        ...
            
    def getPhysicalIndices(self, start, stop):
        return 0, self.arg.length

    def enumerate(self):
        yield from self.ptr.enumerate()

    def has(self, cls):
        if isinstance(self, cls):
            return True
        return self.ptr.has(cls)
    
    
class XMLNodeArray(XMLNode):
    is_XMLNodeArray = True
    
    def __init__(self, args, parent=None):
        super().__init__(parent)
        self.args = args
        for ptr in args:
            ptr.parent = self

    def append_left_tag(self, tag):
        caret = XMLNodeCaret()
        self.args.append(XMLNodeBinaryTag(tag, caret, parent=self))
        return caret

    def append_text_node(self, text):
        node = XMLNodeText(text, parent=self)
        assert not self.args[-1].is_XMLNodeText
        self.args.append(node)
        return node
    
    def append_single_tag(self, tag):
        node = XMLNodeSingleTag(tag, parent=self)
        self.args.append(node)
        return node
    
    def append_tag(self, node):
        node.parent = self
        assert not node.is_XMLNodeCaret
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
        for i, tagEnd in enumerate(self.args):
            if tagEnd.is_XMLNodeUnbalancedTag:
                _self = tagEnd.binaryTag
                assert _self.tagEnd is tagEnd, "_self.tagEnd is tagEnd"
                while True:
                    parent = _self.parent
                    if parent.is_XMLNodeArray:
                        index = parent.args.index(_self)
                        for j in range(index + 1, i if parent is self else len(parent.args)):
                            parent.args[j].modify_style(tagEnd.tag)
                    _self = parent
                    if parent is self:
                        break
        
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
        assert not node.is_XMLNodeArray
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
                if self.args[index].is_XMLNodeText:
                    if self.args[_index].is_XMLNodeText:
                        return True
                    
                    if self.args[_index].is_XMLNodeBinaryTag or self.args[_index].is_XMLNodeSingleTag:
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
        
        
class XMLNodeUnbalancedTag(XMLNode):
    is_XMLNodeUnbalancedTag = True

    def __init__(self, tagEnd, binaryTag, parent=None):
        super().__init__(parent)
        self.tagEnd = tagEnd
        self.binaryTag = binaryTag
        binaryTag.tagEnd = self

    @property
    def tag(self):
        return self.tagEnd.tag
    
    @property
    def start(self):
        return self.tagEnd.start
    
    @property
    def stop(self):
        return self.tagEnd.stop
    
    @computed
    def physicalText(self):
        return str(self.tagEnd)

    @computed
    def text(self):
        return ''

    @property
    def logicalLength(self):
        return 0

    @computed
    def texts(self):
        return []
    
    @computed
    def zeros(self):
        return [0]
    
    
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

tagName = '([a-z][-:_a-z]*\d*)'
attrList = '''(?:\s+:?[a-z][-:_a-z]*=(?:"[^"]*"|'[^']*'))*\s*'''
tagBegin = f'<{tagName}{attrList}>'
tagRegex = fr'''{tagBegin}(?=[\s\S]*?<\/\1>)|</{tagName}>|<(img|mspace|br){attrList}/>|&(#[0-9]+|#x[0-9a-f]+|[^\t\n\f <&#;]{{1,32}});'''

# print("tagRegex =", tagRegex)

def compile(text):
    start = 0
    
    richTexts = []
    leftTagCount = {}
    for m in re.finditer(tagRegex, text, re.IGNORECASE):
#                             1-----------------)                                                                     2-----------------)   3-------------)                                                   4----------------------------------------)
        if prevText := text[start:m.start()]:
            richTexts.append(PlainText(text, start, m.start()))

        if m[1]:
            tag = m[1]
            richText = TagBegin(text, m.start(), m.end(), tag)
            if tag not in leftTagCount:
                leftTagCount[tag] = 0
            leftTagCount[tag] += 1
        elif m[2]:
            tag = m[2]
            if leftTagCount.get(tag):
                leftTagCount[tag] -= 1
                richText = TagEnd(text, m.start(), m.end(), tag)
            elif prevText:
                richText = richTexts.pop()
                richText.stop = m.end()
            else:
                richText = PlainText(text, m.start(), m.end())
        elif m[3]:
            richText = TagSingle(text, m.start(), m.end(), m[3])
        else:
            richText = HTMLEntity(text, m.start(), m.end(), m[4])
        
        richTexts.append(richText)
        
        start = m.end()
    
    if len(text) > start:
        richTexts.append(PlainText(text, start, len(text)))

    caret = XMLNodeCaret()

    leftTagCount = {}
    for text in richTexts:
        if text.is_TagBegin:
            caret = caret.append_left_tag(text)
            if text.tag not in leftTagCount:
                leftTagCount[text.tag] = []
            leftTagCount[text.tag].append(caret.parent)
#            assert caret.parent.tagBegin is text, "caret.parent.tagBegin is text"
            
        elif text.is_TagEnd:
            old = caret
            while True:
                if caret:
                    root = caret
                    caret = caret.parent
                    if isinstance(caret, XMLNodeBinaryTag) and caret.tag == text.tag:
#                         assert caret.tagEnd is None
                        caret.set_tagEnd(text)
                        while True:
                            _caret = leftTagCount[text.tag].pop()
                            if caret is _caret:
                                break
                            _caret.reduceToNodeText()
#                         index = leftTagCount[text.tag].index(caret)
#                         leftTagCount[text.tag].pop(index)
                        break
                elif leftTagCount[text.tag]:
                    parent = leftTagCount[text.tag].pop()
                    caret = XMLNodeUnbalancedTag(text, parent)
                    while parent.stop < root.stop:
                        parent = parent.parent
                        
                    caret = parent.append_tag(caret)
                    break
                else:
                    text = text.reduceToNodeText()
                    caret = old.append_text_node(text)
                    break
                
        elif text.is_TagSingle or text.is_HTMLEntity:
            caret = caret.append_single_tag(text)
        else:
#             assert text.is_PlainText
            caret = caret.append_text_node(text)
        
    for tag in leftTagCount:
        while leftTagCount[tag]:
            leftTagCount[tag].pop().reduceToNodeText()

    return caret.root


class XMLText:
    def __init__(self, src, start, stop):
        self.src = src
        self.start = start
        self.stop = stop
    
    def __str__(self):
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
        return PlainText(self.src, self.start, self.stop)


class TagBegin(XMLText):
    is_TagBegin = True
    
    def __init__(self, src, start, stop, tag):
        super().__init__(src, start, stop)
        self.tag = tag
        
    
class TagEnd(XMLText):
    is_TagEnd = True
    
    def __init__(self, src, start, stop, tag):
        super().__init__(src, start, stop)
        self.tag = tag


class TagSingle(XMLText):
    is_TagSingle = True
    
    def __init__(self, src, start, stop, tag):
        super().__init__(src, start, stop)
        self.tag = tag
        
        text = tag.lower()
        if tag == 'img':
            text = '★'
        elif tag == 'mspace':
            text = ' '
        elif tag == 'br':
            text = '\n'
        else:
            text = '?'
            
        self.text = text


class HTMLEntity(XMLText):
    is_HTMLEntity = True
    
    def __init__(self, src, start, stop, tag):
        super().__init__(src, start, stop)
        self.tag = 'entity-' + tag
        text = html.unescape(f'&{tag};')
        if len(text) != 1:
            text = '?'
        
        self.text = text
        
    
class PlainText(XMLText):
    is_PlainText = True
    
    def __init__(self, src, start, stop):
        super().__init__(src, start, stop)

    @property
    def text(self):
        return str(self)
    

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
    physicalText = "firstly,&nbsp;<div><b>this&nbsp;is&nbsp;<I>an&nbsp;<font color='red'><i>italic</i>&nbsp;<u>&lt;underline&gt;</u><mspace /></font>, simply put</b>,&nbsp;this&nbsp;is&nbsp;an&nbsp;italic&nbsp;text,&nbsp;</I>with&nbsp;something&emsp;<u>&lt;underlined&gt;</u>;</div>&ensp;<b>another&nbsp;bold&nbsp;text&nbsp;is&nbsp;followed.&nbsp;</b>At&nbsp;last,&nbsp;there&nbsp;a&nbsp;plain&nbsp;text."
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