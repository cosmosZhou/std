import numpy, std
from math import sqrt


# https://www.inf.fh-flensburg.de/lang/algorithmen/pattern/sundayen.htm
# https://en.wikipedia.org/wiki/Boyer%E2%80%93Moore_string-search_algorithm
# https://www.jianshu.com/p/2594d312cefd
def sunday(haystack, needle, haystackLength=None):
    
    needelLength = len(needle)
    
    if haystackLength:
        haystackLength = min(len(haystack), haystackLength)
    else:
        haystackLength = len(haystack)
    
    # If the needle contains duplicate characters, the dictionary will only store the last occurrence of each character. When a duplicate key is encountered, the previous value for that key is overwritten.
    dic = {v: needelLength - k for k, v in enumerate(needle)}
    
    end = needelLength
    
    while end <= haystackLength:
        begin = end - needelLength
        if haystack[begin: end] == needle:
            return begin

        if end >= haystackLength:
            return -1

        offset = dic.get(haystack[end])
        if not offset:
            offset = needelLength + 1
        
        end += offset

    return -1


def match_repetition(s, ignores):
    return all(ch in ignores for ch in s)


def length_coefficient(length):
    # in the range of [0, 1]
    return (1 + numpy.tanh(0.4 * length - 6)) / 2

def repetition_penalty(string, max_length=64, ignores=()):
    min_length = 3
    coefficient = [length_coefficient(length) for length in range(0, max_length)]
    repetition_penalty = numpy.zeros((len(string), max_length))
    lookaheads = 5
    for i in range(1, len(string)):
        for index in range(min_length, max_length):
            length = index + 1
            end = i + 1
            beg = end - length
            if beg >= 0:
                s = string[beg: end]
                if ignores and match_repetition(s, ignores):
                    continue
                find = string[end : end + length * lookaheads].find(s)
                if find >= 0:
                    end += find + length
                    assert string[end - length: end] == s
                    repetition_penalty[end - 1][index] = (repetition_penalty[i][index] + 1 - (find / (length * lookaheads)) ** 2) * (1 + coefficient[index] / sqrt(max_length))
            else:
                break

    penalty = repetition_penalty.max(0)
    # at least four consecutive characters are considered as repetitive
    args = [penalty ** 2 * coefficient[index] for index, penalty in enumerate(penalty) if index >= min_length]
    penalty = sum(args) / sqrt(len(string))
    penalty = int(penalty)
    result = {"score" : -penalty}
    if penalty >= 1:
        index = std.argmax(args) + min_length
        # length = index + 1
        end = repetition_penalty[:, index].argmax()
        # end = end + 1
        error = string[end - index: end + 1]
        result['error'] = error
        count = string.count(error)
        result['count'] = count
        assert count > 1
    return result


if __name__ == '__main__':
    text = 'aaaaaaaaabbbbbbbbbbbccccccccc'
    penalty = repetition_penalty(text, 32)
    print(penalty)
