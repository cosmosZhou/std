# std

a standard library for algorithms:  
pip install std.algorithm  

## multi-language segmenter 

```
from std.nlp.segment.cn import split  
split('结婚的和尚未结婚的确实在理念上将存在分歧。')  #['结婚', '的', '和', '尚未', '结婚', '的', '确实', '在', '理念上', '将', '存在', '分歧', '。']  

from std.nlp.segment.jp import split  
split('の出力と前記第3のゲート回路34-oの出力とを入力するアンドゲート回路35を備え、') #['の', '出力', 'と', '前記', '第', '3', 'の', 'ゲート', '回路', '34', '-', 'o', 'の', '出力', 'と', 'を', '入力', 'する', 'アンド', 'ゲート', '回路', '35', 'を', '備え', '、']  

from std.nlp.segment.en import split   
split('who are you?') #['who ', 'are ', 'you', '?']  
```


## rich text preprocessing

```
from std.xml import construct_rich_text
physicalText = "firstly,&nbsp;<div><b>this&nbsp;is&nbsp;<I>an&nbsp;<font color='red'><i>italic</i>&nbsp;<u>&lt;underline&gt;</u><mspace /></font>, simply put</b>,&nbsp;this&nbsp;is&nbsp;an&nbsp;italic&nbsp;text,&nbsp;</I>with&nbsp;something&emsp;<u>&lt;underlined&gt;</u>;</div>&ensp;<b>another&nbsp;bold&nbsp;text&nbsp;is&nbsp;followed.&nbsp;</b>At&nbsp;last,&nbsp;there&nbsp;a&nbsp;plain&nbsp;text."
richText = construct_rich_text(physicalText)
# print(richText)
richText.sanctity_check()
print("physical text =", richText.physicalText)
print(" logical text =", richText.text)
print(" style_traits =", richText.style_traits)

start, stop = 20, 39
print("the logical text is :")
print(richText.text[start:stop])
print("its style trait is :")
print(richText.style_traits[start:stop])

start, stop = richText.getPhysicalIndices(start, stop)
print("its original physical text is:")
print(physicalText[start:stop])
print()
```

## balanced parenthese/brachets/braces matching
```
from std.regexp import balanced
for pairedGroup in balanced.finditer("()", '((1 + 2) * (3 * 4)) + (7 + 8) * [8 + 8]'):
    print(pairedGroup)

for pairedGroup in balanced.findall("[]", '[[1 + 2] * [3 * 4]] + (7 + 8) * [8 + 8]'):
    print(pairedGroup)

print(balanced.search("{}", '{{1 + 2} * {3 * 4}} + {7 + 8} * [8 + 8]'))

outputs:
<regex.Match object; span=(0, 19), match='((1 + 2) * (3 * 4))'>
<regex.Match object; span=(22, 29), match='(7 + 8)'>
[[1 + 2] * [3 * 4]]
[8 + 8]
<regex.Match object; span=(0, 19), match='{{1 + 2} * {3 * 4}}'>
```

### supported paired groups:
()[]{}<>  
（）【】｛｝《》  
‘’“”「」『』  