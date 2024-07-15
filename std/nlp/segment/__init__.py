import regex as re

dot_lookbehind = [
    r'\b([a-z]+|[A-Z][a-z]*)\s+\d+',
    r'\b[a-z]+',
    r'(\b[a-z]+| +[A-Z]+\.) +[A-Z][a-z]+', # The famous person is Martin Luther K.jr, JPR. Hendrikson
    r'\b[A-Z]?[a-z]+\s+[A-Z]+', # Washington DC
    r'\w+ +([A-Z]\.)+[A-Z]', # U.S.A.
]
dot_lookbehind = '|'.join(dot_lookbehind)

dot_lookahead = [
    r'[A-Z][a-z]*(?: +\w+\b|,)',
    r'''[“‘"'\d]''',
]
dot_lookahead = '|'.join(dot_lookahead)

def sbd(text):
    m = re.match('[;!?；！？…。\s]+', text)
    if m:
        leadingDelimiters = m.group()
        text = text[len(leadingDelimiters):]
    else:
        leadingDelimiters = ''
    
    regex = r"[^;!?；！？…。\r\n]+[;!?；！？…。\s]*"
    texts = []
    for m in re.finditer(regex, text):
        line = m.group()
        # if the current sentence is correct, skipping processing!
        if not re.match('[’”]', line) or not texts:
            # sentence boundary detected!
            start = 0
            # consider the following case: 1. firstly...  2. secondly... 3. thirdly...
            # the best answer is answer 1. Answer 2 is not correct.
            for englishSentenceMatch in re.finditer(fr'''(?<={dot_lookbehind})[.．]\s+(?={dot_lookahead})''', line):
                end = englishSentenceMatch.end()
                texts.append(line[start:end])
                start = end
            
            texts.append(line[start:] if start else line)
            continue
        
        if re.match('.[,)\]}，）】》、的]', line):
            # for the following '的 ' case, this sentence should belong to be previous one:
            # ”的文字，以及选项“是”和“否”。
            if line[1:3] == '的确':
                # for the following special case:
                # ”的确， GPS和其它基于卫星的定位系统为了商业、公共安全和国家安全的用 途而快速地发展。
                texts[-1] += line[0]
                # sentence boundary detected! insert end of line here
                texts.append(line[1:].lstrip())
            else:
                # for the following comma case:
                # ”,IEEE Jounalon Selected Areas in Communications,Vol.31,No.2,Feburary2013所述。
                texts[-1] += line
            continue
        
        m = re.match(r'.[;.!?:；。！？：…\r\n]+', line)
        boundaryIndex = m.end() if m else 1
        # considering the following complex case:
        # ”!!!然后可以通过家长控制功能禁止观看。
        # sentence boundary detected! insert end of line here
        texts[-1] += line[:boundaryIndex]
        if boundaryIndex < len(line):
            texts.append(line[boundaryIndex:].lstrip())

    if leadingDelimiters:
        if texts:
            texts[0] = leadingDelimiters + texts[0]
        else:
            texts.append(leadingDelimiters)
    # assert ''.join(texts) == leadingDelimiters + text
    return texts

if __name__ == '__main__':
    text = [
        "    The famous people is Martin Luther K.jr, JPR. Hendrikson. They are from U.S.A.", 
        "    Martin Luther K. Jr. delivered one of his powerful speeches in Washington D.C. I want to go there.",          #bad case
        "Martin Luther K. Jr. delivered one of his powerful speeches in Washington DC. I want to go there.",          #bad case
        "The famous people is Martin Luther K.jr. I want to visit him.",
        "Martin Luther K.jr. JPR. Hendrikson J.P.R. Hendrikson. U.S.A.",
        "My Father lived in U.S.A. He is a great man",
        "My Father lived in USA. He is a great man",
        "The new technology became broadly available in 2023. This innovation marked a turning point for many industries worldwide.",  #Sentence ends with word and digit.The next sentence starts with Word.
        "U.S.S.R. is a country. It is a big country. It is a powerful country. It is a country that no longer exists.", #Sentence ends with word.The next sentence starts with Word.
        "Many companies seek to establish headquarters in the UK. Each location offers unique advantages and challenges.", #Sentence ends with WORD.The next sentence starts with word.
        "There are some steps you can take to protect yourself from the flu. 1. make sure to wash your hands regularly. 2. avoid close contact with people who are sick. 3. get a flu shot every year.", #Sentence ends with word.The next sentence starts with digit.
        "P.R.C. is a country is a powerful country. It is a country that still exists.", #Sentence ends with word.The next sentence starts with word.
        "The global pandemic drastically changed the way we interact and communicate with each other in 2020. 2021 brought new challenges and some hope as vaccines became widely available.", #Sentence ends with digit.The next sentence starts with digit.
        "The pandemic broke out in December 2020. Many people died from this disease. The world was not prepared for this crisis at that moment.", #Sentence ends with digit.The next sentence starts with Word.
        "China is a happy country. 'I am very proud of my country,' said the president of China. ", #Sentence ends with word.The next sentence starts with Chinese single quotation.
        'China is a happy country. "I am very proud of my country," said the president of China. ', #Sentence ends with word.The next sentence starts with Chinese double quotation.
        "China is a happy country. ‘I am very proud of my country,’ said the president of China. ", #Sentence ends with word.The next sentence starts with English single quotation.
        'China is a happy country. “I am very proud of my country,” said the president of China. ', #Sentence ends with word.The next sentence starts with English double quotation.
        '    The number of foreign people learning Chinese increased significantly in 2023. "Chinese language may become the most popular language in the future." said the specialist', #Sentence ends with word and digit.The next sentence starts with English double quotation.
        "    The number of foreign people learning Chinese increased significantly in 2023. 'Chinese language may become the most popular language in the future.' said the specialist", #Sentence ends with word and digit.The next sentence starts with English single quotation.
        'The number of foreign people learning Chinese increased significantly in 2023. “Chinese language may become the most popular language in the future.” said the specialist', #Sentence ends with word and digit.The next sentence starts with Chinese double quotation.
        "The number of foreign people learning Chinese increased significantly in 2023. ‘Chinese language may become the most popular language in the future.’ said the specialist", #Sentence ends with word and digit.The next sentence starts with Chinese single quotation.
        'The British Museum is a great place in the UK. "If you have the chance to visit the UK, you must go to the British Museum." a British person would say.', #Sentence ends with WORD.The next sentence starts with English double quotation.
        "The British Museum is a great place in the UK. 'If you have the chance to visit the UK, you must go to the British Museum.' a British person would say.", #Sentence ends with WORD.The next sentence starts with English single quotation.
        'The British Museum is a great place in the UK. “If you have the chance to visit the UK, you must go to the British Museum.” a British person would say.', #Sentence ends with WORD.The next sentence starts with Chinese double quotation.
        "The British Museum is a great place in the UK. ‘If you have the chance to visit the UK, you must go to the British Museum.’ a British person would say.", #Sentence ends with WORD.The next sentence starts with Chinese single quotation.
        "\nOne of the eight wonders of the world, the Great Wall, is in China. 'I must go and see it one day,' said a foreigner.", #Sentence ends with Word.The next sentence starts with English single quotation.
        'One of the eight wonders of the world, the Great Wall, is in China. "I must go and see it one day," said a foreigner.', #Sentence ends with Word.The next sentence starts with English double quotation.
        'One of the eight wonders of the world, the Great Wall, is in China. “I must go and see it one day,” said a foreigner.', #Sentence ends with Word.The next sentence starts with Chinese double quotation.
        "\n\nOne of the eight wonders of the world, the Great Wall, is in China. ‘I must go and see it one day,’ said a foreigner.", #Sentence ends with Word.The next sentence starts with Chinese single quotation.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in  America. Next, we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with Word.The next sentence starts with word.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in america. Next, we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with word.The next sentence starts with word.
        "The journey took us across various states, all the way to the bustling city where our adventures reached their peak in America. Next we planned to visit the historic monuments and experience the rich culture firsthand.",   #Sentence ends with Word.The next sentence starts with word(without comma).
        '我觉得你说得对ai在某些地方确实能替代人类\n但是ai不可能完全能够替代人类',
        '我已经把五笔输入法给下载好了。要不要来看看',
        '明天又要下大雨了。又要下一周的雨'
    ]

    for text in text:
        for t in sbd(text):
            print(t)
