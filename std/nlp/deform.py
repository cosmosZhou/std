import regex as re
import random
from random import randrange
from math import ceil
from std.nlp.segment import sbd


ASCII_DIGITS = '0123456789'
MULTIBYTE_DIGITS = '０１２３４５６７８９'
CJK_UNIFIED_IDEOGRAPH = '一二三四五六七八九十'
CIRCLED_NUMBER = '⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿'
NEGATIVE_CIRCLED = '⓿❶❷❸❹❺❻❼❽❾❿⓫⓬⓭⓮⓯⓰⓱⓲⓳⓴'
DOUBLE_CIRCLED = '⓵⓶⓷⓸⓹⓺⓻⓼⓽⓾'
DINGBAT_CIRCLED_SANS_SERIF = '➀➁➂➃➄➅➆➇➈➉'
DINGBAT_NEGATIVE_CIRCLED_SANS_SERIF = '➊➋➌➍➎➏➐➑➒➓'
# CIRCLED_NUMBER_ON_BLACK_SQUARE = '㉈㉉㉊㉋㉌㉍㉎㉏'
orderedListRegex = f'[{ASCII_DIGITS}{MULTIBYTE_DIGITS}{CJK_UNIFIED_IDEOGRAPH}{CIRCLED_NUMBER}{NEGATIVE_CIRCLED}{DOUBLE_CIRCLED}{DINGBAT_CIRCLED_SANS_SERIF}{DINGBAT_NEGATIVE_CIRCLED_SANS_SERIF}]+'
leadingDigitRegex = re.compile(f'({orderedListRegex}|\({orderedListRegex}\) ?|\[{orderedListRegex}\] ?|（{orderedListRegex}）|【{orderedListRegex}】)[,，、]?[^\n]+')

punctuation_regex = r'[-\s*:,;.\'"~#`，：；。、“”‘’/\\]'
start_punctuation_regex = re.compile(f'^{punctuation_regex}+')
stop_punctuation_regex = re.compile(f'{punctuation_regex}+$')


def start_stop_dict(texts):
    dict = {}
    for i in range(1, len(texts)):
        start = start_punctuation_regex.search(texts[i])
        if start:
            start = start.group(0)
        else:
            start = ''

        stop = stop_punctuation_regex.search(texts[i])
        if stop:
            stop = stop.group(0)
        else:
            stop = ''

        punct = f"{start}\n{stop}"
        if punct not in dict:
            dict[punct] = []
        dict[punct].append(i)

    return dict


def shuffle(texts, textIndices):
    textIndices = filter(lambda i: len(texts[i]) > 1, textIndices)
    orderedTexts = [texts[i] for i in textIndices]
    if hit := shuffle_loop(orderedTexts):
        for i, s in zip(textIndices, orderedTexts):
            texts[i] = s
    return hit


def shuffled_list(array):
    random.shuffle(array)
    return array


def shuffle_loop(texts):
    count = ceil(len(texts) / 5)

    hit = 0
    dict = {}
    punct = {}

    for i in shuffled_list([*range(1, len(texts))]):
        if i not in dict:
            dict[i] = start_stop_dict(texts[i])
            punct[i] = dict[i].keys()

        for j in shuffled_list([*range(0, i)]):
            if j not in dict:
                dict[j] = start_stop_dict(texts[j])
                punct[j] = dict[j].keys()

            if common := punct[i] & punct[j]:
                common = [*common]
                p = common[randrange(0, len(common))]
                indices_i = dict[i][p]
                indices_j = dict[j][p]
                _i = indices_i[randrange(0, len(indices_i))]
                _j = indices_j[randrange(0, len(indices_j))]

                texts[i][_i], texts[j][_j] = texts[j][_j], texts[i][_i]
                hit += 1
                if hit >= count:
                    return hit
    return hit


def ordinal(text):
    try:
        return ASCII_DIGITS.index(text)
    except ValueError:
        ...

    try:
        return MULTIBYTE_DIGITS.index(text)
    except ValueError:
        ...

    try:
        return CJK_UNIFIED_IDEOGRAPH.index(text) + 1
    except ValueError:
        ...

    try:
        return CIRCLED_NUMBER.index(text)
    except ValueError:
        ...

    try:
        return NEGATIVE_CIRCLED.index(text)
    except ValueError:
        ...

    try:
        return DOUBLE_CIRCLED.index(text) + 1
    except ValueError:
        ...
    
    try:
        return DINGBAT_CIRCLED_SANS_SERIF.index(text) + 1
    except ValueError:
        ...

    try:
        return DINGBAT_NEGATIVE_CIRCLED_SANS_SERIF.index(text) + 1
    except ValueError:
        ...

    return 0


def deform(text, duplicate=True):
    assert text, 'text is empty'
    
    texts = sbd(text)
    
    text_trimmed = re.sub('\s+', '', text)
    assert re.sub('\s+', '', ''.join(texts)) == text_trimmed, f"differences detected:\n{''.join(texts)}\n{text}"
    results = []
    orderedTextIndices = []
    unorderedTextIndices = []
    k = prev_index = 0
    for line in texts:
        blocks = re.split('([:,：，]+\s*)', line)
        if not blocks[-1]:
            blocks.pop()
        result = []
        for i in range(0, len(blocks), 2):
            result.append(''.join(blocks[i: i + 2]))
        results.append(result)

        if match := leadingDigitRegex.match(line):
            index = ordinal(match.group(1))
            if index == prev_index + 1:
                prev_index = index
                orderedTextIndices.append(k)
            else:
                prev_index = 0
                unorderedTextIndices.append(k)
        else:
            if prev_index:
                continuation = False
                if len(results) > 1:
                    if results[-2][-1].endswith('\n'):
                        if re.match(" +", line):
                            continuation = True
                    else:
                        continuation = True

                if continuation:
                    results.pop()
                    results[-1] += result
                else:
                    prev_index = 0
                continue
            unorderedTextIndices.append(k)
        k += 1
    
    assert re.sub('\s+', '', ''.join(''.join(result) for result in results)) == text_trimmed

    if not shuffle(results, orderedTextIndices):
        shuffle(results, unorderedTextIndices)

    if duplicate:
        i = randrange(0, len(results))
        j = randrange(0, len(results[i]))
        duplicate = results[i][j]

        i = randrange(0, len(results))
        j = randrange(0, len(results[i]))
        results[i].insert(j, duplicate)

    return ''.join(''.join(result) for result in results)


if __name__ == '__main__':
    answers = [
        "As a language model, I can assist a patent examiner in several ways:\n\n1. Research and Organization: I can help by quickly searching through vast amounts of patent data to find relevant information based on specific keywords or phrases. This can save the examiner time and effort in locating pertinent prior art when reviewing applications.\n\n2. Language Support: Since I'm proficient in multiple languages, I can translate foreign patent documents or provide language assistance in understanding complex technical terms or phrases used in patent applications.\n\n3. Consistency Checks: I can proofread and check for grammatical, spelling, and formatting errors in patent documents, ensuring that the application meets the required standards.\n\n4. Idea Generation: I can generate ideas for potential improvements or alternative embodiments based on the given patent document, which can help the examiner in evaluating the novelty and non-obviousness of the invention.\n\n5. Trend Analysis: By analyzing patterns in patent filings over time, I can provide insights into emerging technologies or areas of research interest, helping the examiner stay updated on the latest developments in their field.\n\nOverall, my capabilities as a language model can significantly enhance the efficiency and effectiveness of a patent examiner's daily\ntasks.\nFrom:\n[1]\n[2]\n[3]\n[4]\n[5]", 
        'Hmm, that is a tricky situation!  There are several possibilities which I will lay out below, and you can choose which one to try based on your particular situation and preferred method of repair.  The most likely cause of this problem is either that the upper or lower sash is stuck due to rust or some other form of structural damage, or that the window sash stops are incorrectly aligned and preventing the window from opening fully.  Another possible cause is that the tracks or guides that the window sashes run in are damaged.  Finally it is also possible that the upper or lower sashes are physically blocked by something, but this is much less likely.  Here are the different repair options: \n1.  You can try lubricating the sash stops or tracks with a lubricant product like WD-40 to see if this helps loosen the sash.  You can also carefully insert a razor blade or knife tip into the crack between the sash and the stop to test for looseness or damage of the sash or stop.  You can install new stops if the existing stops are damaged. \n 2.  Alternatively you could try realigning the sashes if they are not properly aligned.  First clear the sashes of any dust or debris using a blow dryer or compressed air can.  Then carefully pry the sash up at the bottom using a putty knife or other strong but thin object.  You will need to realign the tracks by forcing the sash up at the top and bottom until it is locked back into place. \n 3.  Finally you could try removing a small portion of the window trim around the sash in order to access the window sash from behind, and see if you can dislodge the stuck sash from that angle.  This will require some careful digging around with a putty knife or paint scraper to pry up the wood around the stuck sash, then you should be able to pry up the sash from behind to release it. \nHope this helps!  Good luck with your repair project !', 
        'Good question.  Here are three possible answers: \n1.  I think some people think their hair is pretty, and that its length reflects the vanity of their character, or some other abstract human value.  This would be a more aesthetic answer.\n2.  I think many people think they are supposed to have long hair.  Many religions say you should have long hair, so this reflects their cultural influence.  This would be a more sociological answer.\n3.  I think that people were required to wear their hair long in the past, and the same traditions continue to be applied now, regardless of people’s aesthetic preferences or social ideals.  This would be a more historical answer.', 
        'Here are some additional patents that deal with the compaction density of electrode sheets:\n\n1. CN107706549A - High-Capacity Positive Electrode Material for Lithium Ion Batteries and Preparation Method Thereof: This patent describes a positive electrode material for lithium-ion batteries with high compaction density, which can improve the energy density of the battery [5].\n\n2. US20190273099A1 - Electrode Plate for Secondary Battery and Manufacturing Method Therefor: This patent relates to an electrode plate for secondary batteries, wherein the electrode mixture layer has a high compaction density, which contributes to improved battery capacity and cycle life [6].\n\n3. JP2018190799A - Positive Electrode Active Material for Non-Aqueous Electrolyte Secondary Battery: This patent describes a positive electrode active material for non-aqueous electrolyte secondary batteries, which has a high compaction density and can improve the energy density of the battery [7].\n\n4. KR1019930096971B1 - Positive Electrode Active Material for Lithium Secondary Battery and Preparation Method Thereof: This patent deals with a positive electrode active material for lithium secondary batteries, which has a high compaction density and can enhance the capacity and cycle characteristics of the battery [8].\n\nThese patents highlight the importance of electrode sheet compaction density in improving the performance of various types of batteries, including lithium-ion, sodium-ion, and non-aqueous electrolyte secondary batteries.\nFrom:\n[1]\n[2]\n[3]\n[4]', 
        '當然，以下是具體的流程：\n\n1. 首先，你需要找一位經驗豐富的治療師與你合作。你可以在網上搜索你所在地區的治療師，並根據治療師所提供的參考選擇一位。\n\n2. 你將與治療師安排第一次預約，通常第一次預約持續大約60分鐘。\n\n3. 在第一次預約中，你將闡述你為何求助於治療，希望透過治療獲得什麼，以及你對治療的任何顧慮。\n\n4. 如果治療師認為你們會有良好的配合，治療師將給你一份填寫的入院表格。入院表格與第一次預約內容相似，但會更加詳細。\n\n5. 一旦治療師收到你完成的入院表格，治療師將決定是否接受你作為客戶。如果治療師接受你作為客戶，你將安排下一個預約。', 
        'Sure, here are some valuable things to consider before making a major move:  \n\n-   Consider your employment status, and plan for any necessary professional certifications or licensing requirements.  Make sure you have the appropriate support and resources available in your new location to retain or pursue your desired career.\n-   Conduct proper research into the expected living costs and standard of living in your new potential community.  There are many resources available online for estimating average costs of housing, utilities, and other daily expenses, which will help you prepare a comprehensive cost analysis and financial planning for your new home.\n-   Consider the local educational opportunities and school systems available in your potential new location.  Evaluate the quality, reputation, and curricula of local schools in relation to your desired living situation and family lifestyle.\n-   Explore potential issues related to local crime, violence, and safety in your potential new location.  Be sure to consider any special safety considerations for family members with medical conditions or physical disabilities.\n-   Conduct thorough research into local cultural norms, customs, and social conditions in your new potential location.  Take note of any important regional or cultural differences that you wish to respect and incorporate into your new home and local community.', 
        "Sure, here are ten interesting topics for me:\n1. The nature and meaning of love and relationships\n2. The history and evolution of art from different cultures and time periods\n3. The neuroscience behind memory formation and retrieval processes in the brain\n4. Exploring alternative approaches such as meditation or mindfulness practices on mental health well-being\n5. Investigating potential benefits among sustainable living strategies implemented by a community toward urban agriculture projects\n6. Discussions around environmental impact due to rapidly growing technological advancements i.e., artificial intelligence(AI) & virtual reality (VR); looking at ethical concerns within this frame\n7. Mapping out various forms of renewable energy sources like solar panels/battery storage systems etc.; examining their efficiency relative differences between these resources towards power generation modelled scenarios", 
        "Here are several ideas for things you could do indoors or outdoors when it's raining:\n\n1. Read a book in front of your fireplace, cuddle up with your favorite book and let the rain pour down your face while losing yourself in an excellent story.\n2. Have tea by candles - In nature on a mug of hot coffee and glowing flames outside is what everyone should experience at least once before they die!\n3. Pickle vegetables – You can pickle various greens such as sweet potato, red cabbage, kale etc all year long to enjoy whenever winter rolls around next.\n4. Get cooking noodles - A good bowl full of pasta will make all the difference during these depressive days also just sprinkle few lemon zest drops over top especially if fried along with fresh veggies like broccoli would add multiple flavours which might turn u in favour this way there won’t need to go restaurants frequently . \n5. Organize clean house party-Clean those small jobs put aside now take help from other family members organize one where everyone heads towards their part making them feel bonded together again after months apart thus killing two birds get happy ending.", 
        "To address this problem, several steps can be taken as follows:\n1. Identify the root cause of delays and work closely with stakeholders affected by these issues (e.g., product managers or management). This will help in determining if there are any underlying bottlenecks that need to be addressed.\n2. Work together from a systems perspective – identify areas where risks might occur; anticipate what could go wrong during implementation based upon available data/evidence points for consideration around new policies within lessons learned scenarios so providers' efforts can extend beyond documentation-based solutions towards true wellness and resilience methodologies such as narrative / design thinking modalities ?\n3. Prioritize tasks which require further resources like budget allocation ,people assignmentand trainingto accelerate delivery .\n4. Implement metrics(scores )for projects teams throughput measure against certain criterialike no effectiveness flag feedbacks daily number finished recordsings evaluated impact etc ;\n5. Through enablement initiatives encourage individuals throughout your organization including decision makersto become more familiarizedwith", 
        "Sure! Here's an algorithm that can help you in generating questions based on any given passage:\n\n1. Read the passage carefully and take notes as needed 2. Identify key points mentioned in the passage such as names or important events 3. Think about possible ways to approach these points with more specific details 4. Generate multiple-choice questions relating each point and its prompt detail/prompt", 
        "As an AI language model, I don't have personal preferences or abilities as humans but here is some advice on how teachers can help their students learn:\n1. Set clear and achievable goals for each student by providing regular feedback about progress towards these goals so they know where they need to improve. 2. Encourage active learning strategies like asking questions, participating in group discussions; provide opportunities through activities such as hands-on experiments during class time sessions facilitate effective teaching of information learned until it stays long term retained into memory .3. Make sure all lessons include practical applications and relatable examples relevant to everyday life situations while keeping in mind kids’ attention span levels available resources at schools sufficient practice sessions also play significant role enhancing retention ability improving academic performance gradually.4. Test your students regularly with quizzes/tests regarding previously taught topics ensuring them stay focused engages learner maintaining high level motivation specially when initial grades start appearing important than ever due strong foundation secured focus will never erase unexpectedly even if studying later meaning cognitive absorption goes positive step forward success prediction based not least full comprehension done carefully hence stopping psychology fear raise triggered efficiency decreasing off chance miscalculations mistakes discouragement actions lose sight capacity essential competencies besides gradual improvement ceilings set high expect side focal point should remain succeed rather fail helps avoid waste repetition redo scenarios thinking skillfully behind perform beats persevere tireless dedicate strive innovative education techniques growth among public inspires patriotism and responsibility society come together eventually energizing lives vivid truly integral mission accomplished assure future prosperity further allow feel safety whenever trust inner self brings outside environment supportive relationship results stimulates curiosity fundamental component promoting better habits listening advisably understand children regardless age educator instructions interactive game which tackles problems holistically filling gap occurrences make budding individuals contribute concerning evolve approach duties given accentuate cultural attitudes norms standard accomplishments typically fairly natural operate under same principle bring more chances greatest amount appreciation encouraged exciting locations could spark joy joy blending conceivable portrayed visionaries trigger marvels prevail robust sense obligation toward one’s own stability useful belongingness dare across vast continental lines university networking grow intentional expressions acknowledge opportunity preservation value human relationships empower thriving communities inclusivity promote participation everyone help enjoying maximized enthusiasm timely embodied manifest increased commitment teamwork motivation elevated intellectual satisfaction basic synergy able occur cascading throughout inhabitants possibly revolutionize major parts worldwide positively saddled character.", 
        "1. February\n2. March\n3. April\n4. May\n5. June"
    ]
    for text in answers:
        print(text)
        print(deform(text))

    