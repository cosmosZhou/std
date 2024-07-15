# to comply with the standards of java and mysql regex engine
import regex as re
from functools import singledispatch

@singledispatch
def normalize(text):
    return normalize_n(text)


@normalize.register(list)
def _(text):
    return [normalize(word) for word in text]


def normalize_n(word):
    word = re.compile('\n').sub(r'\\n', word)
    word = word.strip()
    word = word.lower()
    return word


def normalize_d(word):
    word = re.compile('\n').sub(r'\\n', word)
    word = re.compile('\d').sub(r'\d', word)
    word = word.strip()
    word = word.lower()
    return word


def split(text, split_digits=False):
    if m := re.compile('^[^\S\n]+').search(text):
        leadingSpaces = m.group()
        text = text[len(leadingSpaces):]
    else:
        leadingSpaces = ''
        
    array = []
    
    for m in re.compile('(\n+[^\S\n]*)|([^\n]+)').finditer(text):
        if newlines := m.group(1):
            array.append(newlines)
            continue
        
        for _m in re.compile('(\S+)(\s*)').finditer(m.group(2)):
            spaces = _m.group(2)
            subarray = []
            
            for __m in re.compile('(\w+)|(\W+)').finditer(_m.group(1)):
                if word := __m.group(1):
                    for ___m in re.compile('(\d+)|(\D+)').finditer(word):
                        if digits := ___m.group(1):
                            if split_digits and len(digits) > 2:
                                if i := len(digits) & 1:
                                    subarray.append(digits[0])
                                for j in range(i, len(digits), 2):
                                    subarray.append(digits[j:j + 2])
                            else:
                                subarray.append(digits)
                        else:
                            alphas = ___m.group(2)
                            subarray.append(alphas)

                    continue
                
                puncts = __m.group(2)
                while puncts:
                    if len(puncts) == 1:
                        subarray.append(puncts)
                        break
                    i = 1
                    while puncts[i] == puncts[0]:
                        i += 1
                        if i >= len(puncts):
                            break
                    
                    puncts1, puncts = puncts[:i], puncts[i:]
                    subarray.append(puncts1)
            
            subarray[-1] += spaces
            array += subarray

#     assert ''.join(array) == text
    
    if leadingSpaces:
        if array:
            array = [leadingSpaces] + array
        else:
            array = [leadingSpaces]
     
    return array

