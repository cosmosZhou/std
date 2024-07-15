import numpy
from math import sqrt


# https://www.inf.fh-flensburg.de/lang/algorithmen/pattern/sundayen.htm
# https://en.wikipedia.org/wiki/Boyer%E2%80%93Moore_string-search_algorithm
# https://www.jianshu.com/p/2594d312cefd
def sunday(haystack, needle):
    
    needelLength = len(needle)
    
    haystackLength = len(haystack)
    
    dic = {v:needelLength - k for k, v in enumerate(needle)}
    
    end = needelLength
    
    while end <= haystackLength:
        begin = end - needelLength
        if haystack[begin:end] == needle:
            return begin

        if end >= haystackLength:
            return -1

        offset = dic.get(haystack[end])
        if not offset:
            offset = needelLength + 1
        
        end += offset

    return -1
    

def repetition_penalty(string, max_length=16):
    repetition_penalty = numpy.zeros((len(string), max_length))
    for i in range(1, len(string)):
        for index in range(max_length):
            length = index + 1
            end = i + 1
            beg = end - length * 2
            if beg >= 0:
                mid = beg + length
                if string[beg:mid] == string[mid:end]:
                    repetition_penalty[i][index] = repetition_penalty[i - length][index] + 1
            else:
                break

    repetition_penalty = repetition_penalty.max(0)
    # at least four consecutive characters are considered as repetitive
    return sum(penalty ** 2 * (1 + numpy.tanh(index - max_length / 5)) / 2 for index, penalty in enumerate(repetition_penalty) if index >= 3) / sqrt(len(string))


if __name__ == '__main__':
    text = 'aaaaaaaaabbbbbbbbbbbccccccccc'
    penalty = repetition_penalty(text, 32)
    print(penalty)
