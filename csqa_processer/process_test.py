import json
import os

coref = ['that', 'his', 'her', 'its', 'those', 'his/her']
import spacy
from spacy.tokens import Doc
from spacy.errors import user_warning, Errors, Warnings

nlp = spacy.load('en_core_web_sm')
options = {
    "collapse_punct": False,
    "collapse_phrases": True,
}

def filter_spans(spans):
    # Filter a sequence of spans so they don't contain overlaps
    get_sort_key = lambda span: (span.end - span.start, span.start)
    sorted_spans = sorted(spans, key=get_sort_key, reverse=True)
    result = []
    seen_tokens = set()
    for span in sorted_spans:
        if span.start not in seen_tokens and span.end - 1 not in seen_tokens:
            result.append(span)
            seen_tokens.update(range(span.start, span.end))
    return result

def get_doc_settings(doc):
    return {
        "lang": doc.lang_,
        "direction": doc.vocab.writing_system.get("direction", "ltr"),
    }

def parse_deps(orig_doc, options={}):
    """Generate dependency parse in {'words': [], 'arcs': []} format.
    doc (Doc): Document do parse.
    RETURNS (dict): Generated dependency parse keyed by words and arcs.
    """
    doc = Doc(orig_doc.vocab).from_bytes(orig_doc.to_bytes(exclude=["user_data"]))
    if not doc.is_parsed:
        user_warning(Warnings.W005)
    if options.get("collapse_phrases", False):
        np_chunks = filter_spans(list(doc.noun_chunks))
        with doc.retokenize() as retokenizer:
            for np in np_chunks:
                attrs = {
                    "tag": np.root.tag_,
                    "lemma": np.root.lemma_,
                    "ent_type": np.root.ent_type_,
                }
                retokenizer.merge(np, attrs=attrs)
    if options.get("collapse_punct", True):
        spans = []
        for word in doc[:-1]:
            if word.is_punct or not word.nbor(1).is_punct:
                continue
            start = word.i
            end = word.i + 1
            while end < len(doc) and doc[end].is_punct:
                end += 1
            span = doc[start:end]
            spans.append((span, word.tag_, word.lemma_, word.ent_type_))

        spans = filter_spans(spans)

        with doc.retokenize() as retokenizer:
            for span, tag, lemma, ent_type in spans:
                attrs = {"tag": tag, "lemma": lemma, "ent_type": ent_type}
                retokenizer.merge(span, attrs=attrs)
    if options.get("fine_grained"):
        words = [{"text": w.text, "tag": w.tag_} for w in doc]
    else:
        words = [{"text": w.text, "tag": w.pos_} for w in doc]
    arcs = []
    for word in doc:
        if word.i < word.head.i:
            arcs.append(
                {"start": word.i, "end": word.head.i, "label": word.dep_, "dir": "left"}
            )
        elif word.i > word.head.i:
            arcs.append(
                {
                    "start": word.head.i,
                    "end": word.i,
                    "label": word.dep_,
                    "dir": "right",
                }
            )
    return {"words": words, "arcs": arcs, "settings": get_doc_settings(orig_doc)}

def process_to_cqr(in_dir, dict_file, out_dir):
    entity_dict = json.loads(open(dict_file, 'r', encoding='utf-8').read())
    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            process_one(content,entity_dict)


def is_complete(turn):
    qid = turn['ques_type_id']
    if qid == 2:
        sec_sub_type = turn['sec_ques_sub_type']
        if sec_sub_type == 2 or sec_sub_type == 3:
            return False
    elif qid == 3:
        return False
    elif qid == 4:
        is_inc = turn['is_inc']
        if is_inc == 1:
            return False
    elif qid == 5:
        bool_ques_type = turn['bool_ques_type']
        if bool_ques_type in [2, 3, 5, 6]:
            return False
    elif qid == 6:
        return False
    elif qid == 7 or qid == 8:
        is_incomplete = turn['is_incomplete']
        if is_incomplete == 1:
            return False

    return True


def process_one(json_str, entity_dict):
    turns = json.loads(json_str)
    questions = []
    responses = []

    for turn in turns:
        speaker = turn['speaker']
        entities = None
        if 'entities_in_utterance' in turn:
            entities = turn['entities_in_utterance']
        elif 'entities' in turn:
            entities = turn['entities']

        utterance = turn['utterance']
        types = None
        if 'type_list' in turn:
            types = turn['type_list']

        entity_list = find_entity(utterance, entities, types, entity_dict)
        turn['entities'] = entity_list

        if speaker == 'USER':
            qid = turn['ques_type_id']
            if qid == 2:
                qtype = turn['question-type']
                sec_sub_type = turn['sec_ques_sub_type']
                if sec_sub_type == 2 or sec_sub_type == 3:
                    # that XXX, those XXX
                    continue
            elif qid == 4:
                is_inc = turn['is_inc']
                if is_inc == 1:
                    continue
            elif qid == 5:
                bool_ques_type = turn['bool_ques_type']
                if bool_ques_type in [2, 3, 5, 6]:
                    continue
            elif qid == 6:
                inc_ques_type = turn['inc_ques_type']
            elif qid == 7:
                # and how about XXX, what about XXX
                # replace such entity in the last question
                is_incomplete = turn['is_incomplete']
                if is_incomplete == 1:
                    pass
                    # last_entities = last_question['entities']
                    # last_ent_cnt = 0
                    # last_entity = None
                    # for ent in last_entities:
                    #     if ent['type'] == 'Entity':
                    #         last_ent_cnt += 1
                    #         last_entity = ent
                    #
                    # if len(entity_list) == 1 and last_ent_cnt == 1:
                    #     rewrite_query = last_question['utterance'].replace(last_entity['span'], entity_list[0]['span'])
                    #     turn['rewrite_query'] = rewrite_query
            elif qid == 8:
                is_incomplete = turn['is_incomplete']
                if is_incomplete == 1:
                    continue

            questions.append(turn)
        else:
            responses.append(turn)


def find_entity(utterance, entities, types, id_name_dict):
    u = str(utterance).lower()
    entity_list = list()
    if entities is not None:
        for entity_id in entities:
            entity = id_name_dict[entity_id]
            idx = u.find(entity.lower())
            if idx < 0:
                print(utterance+'\t'+entity_id)
            length = len(entity)
            span = str(utterance[idx:idx+length])
            entity_dict = dict()
            entity_dict['index'] = idx
            entity_dict['length'] = length
            entity_dict['span'] = span
            entity_dict['type'] = 'Entity'
            entity_list.append(entity_dict)

    if types is not None:
        for entity_id in types:
            entity = id_name_dict[entity_id]
            idx = u.find(entity.lower())
            if idx < 0:
                print(utterance+'\t'+entity_id)
            length = len(entity)
            span = str(utterance[idx:idx+length])
            entity_dict = dict()
            entity_dict['index'] = idx
            entity_dict['length'] = length
            entity_dict['span'] = span
            entity_dict['type'] = 'Type'
            entity_list.append(entity_dict)

    return entity_list


def get_miss_matched(in_dir, dict_file, out_file):
    miss_matched = dict()
    entity_dict = json.loads(open(dict_file, 'r', encoding='utf-8').read())
    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            turns = json.loads(content)
            for turn in turns:
                entities = None
                if 'entities_in_utterance' in turn:
                    entities = turn['entities_in_utterance']
                elif 'entities' in turn:
                    entities = turn['entities']

                utterance = turn['utterance']
                types = None
                if 'type_list' in turn:
                    types = turn['type_list']
                u = str(utterance).lower()

                if entities is None and types is None and utterance != 'Yes':
                    print(sub_dir+'\t'+file+'\t'+utterance)
                if entities is not None:
                    for entity_id in entities:
                        entity = entity_dict[entity_id]
                        idx = u.find(entity.lower())
                        if idx < 0:
                            key = entity_id+"-"+entity
                            if key not in miss_matched:
                                miss_matched[key] = set()
                            miss_matched[key].add(utterance)

                if types is not None:
                    for entity_id in types:
                        entity = entity_dict[entity_id]
                        idx = u.find(entity.lower())
                        if idx < 0:
                            key = entity_id + "-" + entity
                            if key not in miss_matched:
                                miss_matched[key] = set()
                            miss_matched[key].add(utterance)

    file = open(out_file, 'w', encoding='utf-8')
    for k,v in miss_matched.items():
        for line in v:
            file.write(k+'\t'+line+'\n')

    file.close()


def get_question_by_type(in_dir, out_dir):
    qtype = dict()
    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            turns = json.loads(content)
            for turn in turns:
                speaker = turn['speaker']
                utterance = turn['utterance']
                if speaker == 'USER':
                    qid = turn['ques_type_id']
                    key = ''
                    if qid == 1:
                        key = str(qid)
                    elif qid == 2:
                        sec_ques_type = turn['sec_ques_type']
                        sec_ques_sub_type = turn['sec_ques_sub_type']
                        key = str(qid)+'-'+str(sec_ques_type)+'-'+str(sec_ques_sub_type)
                    elif qid == 3:
                        key = str(qid)
                    elif qid == 4:
                        set_op_choice = turn['set_op_choice']
                        is_inc = turn['is_inc']
                        key = str(qid) + '-' + str(set_op_choice) + '-' + str(is_inc)
                    elif qid == 5:
                        bool_ques_type = turn['bool_ques_type']
                        key = str(qid)+'-'+str(bool_ques_type)
                    elif qid == 6:
                        inc_ques_type = turn['inc_ques_type']
                        key = str(qid) +'-'+str(inc_ques_type)
                    elif qid == 7:
                        count_ques_sub_type = turn['count_ques_sub_type']
                        is_incomplete = turn['is_incomplete']
                        key = str(qid) + '-' + str(count_ques_sub_type) + '-' + str(is_incomplete)
                    elif qid == 8:
                        count_ques_sub_type = turn['count_ques_sub_type']
                        is_incomplete = turn['is_incomplete']
                        key = str(qid) + '-' + str(count_ques_sub_type) + '-' + str(is_incomplete)

                    if key not in qtype:
                        qtype[key] = set()

                    qtype[key].add(utterance+'\t'+sub_dir+'-'+file)

    for k,v in qtype.items():
        file = open(os.path.join(out_dir, k), 'w', encoding='utf-8')
        for line in v:
            file.write(line+'\n')
        file.close()

def merge(in_dir, out_file):
    all_json = dict()
    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            turns = json.loads(content)
            all_json[sub_dir+'-'+file] = turns

    json.dump(all_json, open(out_file, 'w', encoding='utf-8'))


def extract_contextual(in_dir, out_dir):
    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            turns = json.loads(content)
            context_turns = set()
            for i in range(len(turns)):
                turn = turns[i]
                speaker = turn['speaker']

                if speaker == 'USER':
                    if is_complete(turn):
                        continue
                    else:
                        context_turns.add(i)
                        j = i-1
                        while j >= 0:
                            s = turns[j]['speaker']
                            if s == 'USER':
                                if is_complete(turns[j]):
                                    context_turns.add(j)
                                    break
                                else:
                                    context_turns.add(j)
                                    j -= 1
                            else:
                                context_turns.add(j)
                                j -= 1

            # select the continues turns as contextual conversations
            context_turns = list(context_turns)
            context_turns.sort()

            if len(context_turns) == 0:
                continue

            start = 0
            for i in range(1, len(context_turns)):
                if context_turns[i]-context_turns[i-1] > 1:
                    # a new conversation
                    one_session = []
                    for j in range(start, i):
                        turn = turns[context_turns[j]]
                        turn['folder'] = sub_dir
                        turn['file'] = file
                        turn['index'] = context_turns[j]
                        one_session.append(turn)

                    js = json.dumps(one_session, sort_keys=True, indent=2)
                    writer = open(os.path.join(out_dir, sub_dir+'-'+os.path.splitext(file)[0]+'-'+str(context_turns[start])+'.json'), 'w', encoding='utf-8')
                    writer.write(js)
                    writer.close()

                    start = i

            one_session = []
            for j in range(start, len(context_turns)):
                turn = turns[context_turns[j]]
                turn['folder'] = sub_dir
                turn['file'] = file
                turn['index'] = context_turns[j]
                one_session.append(turn)

            js = json.dumps(one_session, sort_keys=True, indent=2)
            writer = open(os.path.join(out_dir, sub_dir + '-' + os.path.splitext(file)[0] + '-' + str(context_turns[start]) + '.json'), 'w',
                          encoding='utf-8')
            writer.write(js)
            writer.close()


def find_all_possible_types(in_dir, dict_file, out_file):
    types = set()
    #entity_dict = json.loads(open(dict_file, 'r', encoding='utf-8').read())
    verbs = set()
    for line in open(dict_file, 'r', encoding='utf-8'):
        verbs.add(line.strip())

    for sub_dir in os.listdir(in_dir):
        print(sub_dir)
        for file in os.listdir(os.path.join(in_dir, sub_dir)):
            content = open(os.path.join(in_dir, sub_dir, file), 'r', encoding='utf-8').read()
            turns = json.loads(content)
            for turn in turns:
                speaker = turn['speaker']

                if speaker == 'USER':
                    utterance = str(turn['utterance']).strip().lower()

                    tokens = utterance.split(' ')
                    valid = False
                    type = []
                    if tokens[0] in ('which', 'what'):

                        for i in range(1, 6):
                            if i >= len(tokens):
                                break

                            if tokens[i] in ('is', 'are', 'have', 'has', 'had', 'were', 'was', 'do', 'does', 'did',
                                             'starred', 'took', 'works', 'produced', 'can', 'should', 'could', 'shall',
                                             'published', 'as', 'demonstrates', 'depicts', 'live', 'depict',
                                             'sponsored',
                                             'represent', 'appointed', 'represents', 'belong', 'belongs'
                                             'encodes', 'encode', 'drafted', 'flows', 'emerged'):
                                valid = True
                                break

                            if tokens[i] in verbs:
                                valid = True
                                break

                            type.append(tokens[i])

                    if len(type) > 0:
                        candidate_type = ' '.join(type)
                        if not valid:
                            print(candidate_type + '\t' + sub_dir+'\t'+file)
                        types.add(' '.join(type))

    writer = open(out_file, 'w', encoding='utf-8')
    for type in types:
        writer.write(type+'\n')

    writer.close()


def process(in_dir, id_name_file, out_dir):
    from nltk.parse.stanford import StanfordDependencyParser

    # path_to_jar = 'D:/Work/KBQA/ContextualLU/CSQA/stanford-parser-full-2018-10-17/stanford-parser.jar'
    # path_to_models_jar = 'D:/Work/KBQA/ContextualLU/CSQA/stanford-english-corenlp-2018-10-05-models.jar'
    #
    # dependency_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
    id_name_dict = json.loads(open(id_name_file, 'r', encoding='utf-8').read())
    for file in os.listdir(in_dir):
        content = open(os.path.join(in_dir,file), 'r', encoding='utf-8').read()
        turns = json.loads(content)

        for turn in turns:
            speaker = turn['speaker']
            utterance = turn['utterance']

            entities_in_utterance = None
            if 'entities_in_utterance' in turn:
                entities_in_utterance = turn['entities_in_utterance']

            u = str(utterance).lower()
            entity_list = list()
            if entities_in_utterance is not None:
                for entity_id in entities_in_utterance:
                    entity = id_name_dict[entity_id]
                    idx = u.find(entity.lower())
                    if idx < 0:
                        # coref question
                        # print(utterance + '\t' + entity_id)
                        continue
                    length = len(entity)
                    span = str(utterance[idx:idx + length])
                    entity_dict = dict()
                    entity_dict['index'] = idx
                    entity_dict['length'] = length
                    entity_dict['span'] = span
                    entity_dict['type'] = 'Entity'
                    entity_list.append(entity_dict)

            turn['entity_list'] = entity_list

            if speaker != 'USER':
                continue

            if is_complete(turn):
                continue

            qid = turn['ques_type_id']

            mention = detect_coref_mention(utterance)
            if mention != '':
                #print(mention)
                turn['coref_mention'] = mention

        js = json.dumps(turns, sort_keys=True, indent=2)
        writer = open(os.path.join(out_dir, file), 'w',
                      encoding='utf-8')
        writer.write(js)
        writer.close()


def detect_coref_mention(utterance):
    doc = nlp(utterance)
    try:
        res = parse_deps(doc, options)
    except:
        print(utterance)
        return ''

    words = res['words']
    mentions = set()
    mention = ''
    dep1 = dict()
    dep2 = dict()
    for arc in res['arcs']:
        start = arc['start']
        end = arc['end']
        dir = arc['dir']
        label = arc['label']
        if dir == 'right':
            if start not in dep1:
                dep1[start] = set()
            dep1[start].add((label, end))

            if end not in dep2:
                dep2[end] = set()
            dep2[end].add((label, start))

        else:
            if end not in dep1:
                dep1[end] = set()
            dep1[end].add((label, start))

            if start not in dep2:
                dep2[start] = set()
            dep2[start].add((label, end))

    for i in range(len(words)):
        word = words[i]
        if str(word['text']).startswith('that') or str(word['text']).startswith('those'):
            if word['text'] in ('that', 'those'):
                if i+1 < len(words):
                    if words[i+1]['tag'] != 'PUNCT':
                        mentions.add(i)
                        mentions.add(i+1)
                        get_fathers(i+1, dep1, mentions, words)
            else:
                mentions.add(i)
                if i in dep2:
                    for (label, child) in dep2[i]:
                        if label == 'det':
                            mentions.add(child)
                            # find more
                            get_fathers(child, dep1, mentions, words)

            get_fathers(i, dep1, mentions, words)
            if len(mentions) == 0:
                continue

            mentions = list(mentions)
            mentions.sort()
            mention_words = []
            for mid in mentions:
                mention_words.append(words[mid]['text'])

            mention = ' '.join(mention_words)
            if valid_mention(mention):
                break
            else:
                mentions = set()
                mention = ''

    return mention


def valid_mention(mention):
    arr = str(mention).split(' ')
    if arr[0] != 'that' and arr[0] != 'those':
        return False

    real_mention = ' '.join(arr[1:])

    if 'that ' in real_mention or 'those ' in real_mention:
        return False

    if arr[1] in ('is', 'are', 'was', 'were', 'has', 'have', 'had'):
        return False
    return True


def get_fathers(node, tree, fathers, words):
    if node not in tree:
        return

    for (label, father) in tree[node]:
        if label in ('prep', 'pobj', 'det'):
            if words[father]['text'] == 'as':
                continue
            fathers.add(father)
            get_fathers(father, tree, fathers, words)


if __name__ == "__main__":
    get_question_by_type('./CSQA_v9/test', './out_dir/qtype_test')
    #process_to_cqr('D:/Work/KBQA/ContextualLU/CSQA/CSQA_v9/train', 'D:/Work/KBQA/ContextualLU/CSQA/wikidata_proc_json-20190627T021029Z-002/items_wikidata_n.json', '')
    #get_miss_matched('D:/Work/KBQA/ContextualLU/CSQA/CSQA_v9/train', 'D:/Work/KBQA/ContextualLU/CSQA/wikidata_proc_json-20190627T021029Z-002/items_wikidata_n.json', 'D:\Work\KBQA\ContextualLU\CSQA\out_dir\missmatch.tsv')
    #merge('D:/Work/KBQA/ContextualLU/CSQA/CSQA_v9/train', 'D:/Work/KBQA/ContextualLU/CSQA/out_dir/train_all.json')
    extract_contextual('./CSQA_v9/test', './out_dir/context_test')
    #find_all_possible_types('D:/Work/KBQA/ContextualLU/CSQA/CSQA_v9/train', 'D:/Work/KBQA/ContextualLU/CSQA/verb.txt', 'D:\Work\KBQA\ContextualLU\CSQA\out_dir/type.tsv')
    process('./out_dir/context_test', './items_wikidata_n.json', './out_dir/processed_test')
    #mention = detect_coref_mention('Which fictional characters plays a role in greater number of books or applications than that fictional character ?')
    #print(mention)
    # from nltk.parse.stanford import StanfordDependencyParser
    #
    # path_to_jar = 'D:/Work/KBQA/ContextualLU/CSQA/stanford-parser-full-2018-10-17/stanford-parser.jar'
    # path_to_models_jar = 'D:/Work/KBQA/ContextualLU/CSQA/stanford-english-corenlp-2018-10-05-models.jar'
    #
    # dependency_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)
    # result = dependency_parser.parse('Who wrote the script for those works of art ?')
    # print(result.)
    # dep = result.__next__()
    # triples = list(dep.triples())
    # print(len(triples))

    # import spacy
    #
    # nlp = spacy.load('en_core_web_sm')
    # doc = nlp('Which administrative territories are those french\'s administrative divisions present in ?')
    # options = {
    #     "collapse_punct": False,
    #     "collapse_phrases": True,
    # }
    # res = spacy.displacy.parse_deps(doc, options)
    # print(res)
    # words = res['words']
    # for word in words:
    #     if str(word['text']).startswith('that') or str(word['text']).startswith('those'):
    #         print(word['text'])
