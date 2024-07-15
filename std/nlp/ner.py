from intervaltree import IntervalTree

class Entity2Label:
    def __init__(self, label_schema='BILOU', resolve_conflict=True):
        """
        entity to label transformer
        :param label_schema: label schema, only allow 'BILOU', 'BIO' and None.
                            When its value is none, label will be uppercase of entity type(for semi-markov CRF)
        :param resolve_conflict: whether resolve conflict which entity start or end is not in token starts and ends list
        """
        if label_schema not in {'BILOU', 'BIO', None}:
            raise Exception(label_schema)
        self.label_schema = label_schema
        self.resolve_conflict = resolve_conflict

    def sent_batch(self, sent_list):
        """
        transform entities and text in paragraph list to labels
        :param sent_list: paragraph list
        :return:
        """
        for item in sent_list:
            self.sent(item)
        return sent_list

    def sent(self, sent):
        """
        transform text, entities, token and pos tags into labels, labels will attach in data object
        For example:
            input: sent = {'text': 'Steve Jobs founded Apple.Inc.',
                'tokens': [{'end': 5, 'start': 0, 'text': 'Steve'},
                  {'end': 10, 'start': 6, 'text': 'Jobs'},
                  {'end': 18, 'start': 11, 'text': 'founded'},
                  {'end': 24, 'start': 19, 'text': 'Apple'},
                  {'end': 25, 'start': 24, 'text': '.'},
                  {'end': 28, 'start': 25, 'text': 'Inc'},
                  {'end': 29, 'start': 28, 'text': '.'}],
                  'entities': [{'end': 10, 'entity': 'Steve Jobs', 'start': 0, 'type': 'PER'},
                         {'end': 28, 'entity': 'Apple.Inc', 'start': 19, 'type': 'COMP'}]
                  }
            output: ['B-PER', 'L-PER', 'O', 'B-COMP', 'I-COMP', 'L-COMP', 'O']
        :param sent: sentence to be transformed, must be dict type, and has text, entities and tokens key.
        :return: new data dict with labels
        """
        if not isinstance(sent, dict):
            raise TypeError('sent must be in dict type')
        if 'text' not in sent:
            raise KeyError('must have text field')
        elif 'entities' not in sent:
            raise KeyError('muse have entities field')
        elif 'tokens' not in sent:
            raise KeyError('must have tokens field')

        text = sent['text']
        entities = sent['entities']
        tokens = sent['tokens']

        if self.resolve_conflict:
            tokens = split_conflict_spans(entities, tokens, text)

        token_spans = sorted([(t['start'], t['end']) for t in tokens])
        labels = ['O'] * len(token_spans)

        for entity in entities:
            start_index, end_index = get_index_span(token_spans,
                                                    entity['start'],
                                                    entity['end'],
                                                    is_sorted=True)
            entity_labels = self.single(entity, start_index, end_index)
            labels[start_index:end_index] = entity_labels

        sent['tokens'] = tokens
        sent['labels'] = labels

        return sent

    def single(self, entity, start_index, end_index, type_in_label=None, label_suffix=None):
        """
        transform single entity to labels
        :param entity: entity in dict. must have entity, start, end and type key
        :param start_index: entity first token index in token list
        :param end_index: entity last token index in token list
        :param type_in_label: entity type string in label schema, default is None, assigned with entity type
        :param label_suffix: suffix string in label
        :return: labels represent entity
        """
        if type_in_label is None:
            type_in_label = entity['type']

        if not type_in_label:
            raise ValueError('entity type is empty')

        start_label = join_label('B', type_in_label, label_suffix)
        inter_label = join_label('I', type_in_label, label_suffix)
        end_label = join_label('L', type_in_label, label_suffix)
        unique_label = join_label('U', type_in_label, label_suffix)
        if self.label_schema == 'BILOU':
            if end_index - start_index == 1:
                entity_labels = [unique_label]
            else:
                entity_labels = [start_label]
                if end_index - start_index > 2:
                    entity_labels.extend([inter_label] * (end_index - start_index - 2))
                entity_labels.append(end_label)
        elif self.label_schema == 'BIO':
            entity_labels = [start_label]
            if end_index - start_index > 1:
                entity_labels.extend([inter_label] * (end_index - start_index - 1))
        elif not self.label_schema:
            entity_labels = [entity['type'].upper()] * (end_index - start_index)
        else:
            raise Exception('label schema is not supported.')
        return entity_labels


class EntityRelation2Label(Entity2Label):
    """
    transform entities and relations into labels with NovelTag schema in papar
    Zheng, Suncong, et al. "Joint extraction of entities and relations based on a novel tagging scheme." arXiv preprint arXiv:1706.05075 (2017).
    """

    def __init__(self):
        super().__init__()

    def sent(self, sent):
        if not isinstance(sent, dict):
            raise TypeError('sent must be in dict type')
        if 'text' not in sent:
            raise KeyError('must have text field')
        elif 'entities' not in sent:
            raise KeyError('muse have entities field')
        elif 'tokens' not in sent:
            raise KeyError('must have tokens field')
        elif 'relations' not in sent:
            raise KeyError('must have relations field')

        for e in sent['entities']:
            if 'id' not in e:
                raise KeyError('must have id field in entity for building relation')

        text = sent['text']
        entities = sent['entities']
        id2entity = {e['id']: e for e in entities}
        if len(entities) > len(id2entity):
            raise ValueError('entity ids have duplication! ')

        tokens = sent['tokens']
        relations = sent['relations']

        if self.resolve_conflict:
            tokens = split_conflict_spans(entities, tokens, text)

        token_spans = sorted([(t['start'], t['end']) for t in tokens])
        labels = ['O'] * len(token_spans)
        for relation in relations:
            first_entity_id = relation['e1']
            second_entity_id = relation['e2']
            rel_type = relation['type']
            labels = self.assign_labels_with_entity(token_spans, id2entity[first_entity_id],
                                                    labels, rel_type, 1)
            labels = self.assign_labels_with_entity(token_spans, id2entity[second_entity_id],
                                                    labels, rel_type, 2)

    def assign_labels_with_entity(self, token_spans, entity, labels, rel_type, entity_idx):
        start_index, end_index = get_index_span(token_spans,
                                                entity['start'],
                                                entity['end'],
                                                is_sorted=True)
        entity_labels = self.single(entity, start_index, end_index, rel_type, entity_idx)
        labels[start_index:end_index] = entity_labels
        return labels


def get_index_span(spans, start, end, is_sorted=False):
    """
    get start and end of index position in spans by start and end value in spans
    start is first value of tuple item in spans,
    end is second value of tuple item in spans.
    start and end must occur in spans

    For example,
        input spans = [(1, 5), (5, 10), (10,25), (25, 100)], start = 5, end = 100
        output: (1, 4)

    :param spans: span list to do search, every item is a two elements tuple.
    :param start: start position to be searched in  span starts
    :param end: end position to be searched in span ends
    :param is_sorted: Whether spans have been sorted in ascend order, default is False.
                      When you confirm that, set it True to save time.
    :return: start and end index in spans
    """
    if not is_sorted:
        spans = sorted(spans)

    start_index = end_index = -1
    # indicators to check span duplicates
    last_start = last_end = -1
    for idx, (span_start, span_end) in enumerate(spans):
        if last_start == span_start:
            raise ValueError('spans has duplicated start {}'.format(span_start))
        if last_end == span_end:
            raise ValueError('spans has duplicated end {}'.format(span_end))

        if span_start == start:
            start_index = idx
        if span_end == end:
            end_index = idx + 1
            break

        last_start = span_start
        last_end = span_end

    if start_index == -1:
        raise ValueError('start not in span starts')
    if end_index == -1:
        raise ValueError('end not in span ends')
    return start_index, end_index


def join_label(label, entity_type, suffix=None):
    if suffix is None:
        final_label = label + '_' + entity_type
    else:
        final_label = label + '_' + entity_type + '_' + str(suffix)
    return final_label


def split_conflict_spans(entities, tokens, text):
    """
    resolve the conflict in tokens and entities
    :param entities: entity list
    :param tokens: token list, everyone is a dict which has text, start, end and pos tag (optional)
    :param text: original text
    :return: new tokens whose conflicts have been resolved.
    """
    if not tokens:
        return tokens
    first_token_start = tokens[0]['start']
    last_token_end = tokens[-1]['end']

    token_spans = [(t['start'], t['end']) for t in tokens]
    token_starts, token_ends = list(zip(*token_spans))
    split_indices = []

    # get conflict index in sentence,
    # conflict means entity start not in token starts or entity end not in token ends
    for e in entities:
        if e['start'] < first_token_start:
            cross_boundary_msg = 'entity start {} is less than first token start {}'
            raise ValueError(cross_boundary_msg.format(e['start'], first_token_start))
        elif e['end'] > last_token_end:
            cross_boundary_msg = 'entity end {} is larger than last token end {}'
            raise ValueError(cross_boundary_msg.format(e['end'], last_token_end))
        if e['start'] not in token_starts:
            split_indices.append(e['start'])
        if e['end'] not in token_ends:
            split_indices.append(e['end'])
    split_indices = sorted(set(split_indices))

    # split token cross conflict index into two tokens
    for split_index in split_indices:
        tree = IntervalTree.from_tuples(token_spans)
        interval = list(tree.at(split_index))
        if len(interval) != 1:
            raise Exception('interval count error')
        interval = interval[0]
        if interval.begin == split_index:
            raise Exception('split index start error')
        elif interval.end == split_index:
            raise Exception('split index end error')
        token_spans.extend([(interval.begin, split_index), (split_index, interval.end)])
        if (interval.begin, interval.end) in token_spans:
            token_spans.remove((interval.begin, interval.end))

    token_spans = sorted(token_spans, key=lambda s: s[0])
    new_tokens = [{'text': text[s:e], 'start': s, 'end': e} for (s, e) in token_spans]

    # resolve conflict in pos_tag such as token
    # conflict tokens
    # todo: pos tag conflict resolving with some rules
    if 'pos_tag' in tokens[0]:
        pos_tags = []
        token_starts, token_ends = list(zip(*token_spans))
        for token in tokens:
            pos_tag = token['pos_tag']
            start = token['start']
            end = token['end']
            pos_start = token_starts.index(start)
            pos_end = token_ends.index(end)
            if pos_start == pos_end:
                pos_tags.append(pos_tag)
            elif pos_end - pos_start > 0:
                pos_tags.extend([pos_tag] * (pos_end - pos_start + 1))
            else:
                raise ValueError('token end index is before token start index')
        pos_tag_count = len(pos_tags)
        new_token_count = len(new_tokens)
        msg = 'pos tag count and token text count are not equal, token {}, pos tag {}'
        if pos_tag_count != new_token_count:
            raise Exception(msg.format(new_token_count, pos_tag_count))
        else:
            for token, pos_tag in zip(new_tokens, pos_tags):
                token['pos_tag'] = pos_tag
    return new_tokens
