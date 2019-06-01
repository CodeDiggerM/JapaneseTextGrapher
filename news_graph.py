# coding:utf-8

from collections import Counter
from graph_show import GraphShow
from textrank import TextRank
import io
from pyknp import Juman, KNP
import re
import nltk
from word import Word

class NewsMining():
    """News Mining"""
    MOST_FREQUENTLY = 5
    FREQUENCY_COLOR = "yellow"
    KEYWORD_COLOR = "red"
    NER_COLOR = "green"
    SVO_COLOR = "blue"
    DEFAULT_COLOR = "rgba(51,255,153,0.2)"
    def __init__(self,
                 knppath="/home/sasano/usr/bin/knp",
                 juman="/home/sasano/usr/bin/juman",
                 ):
        self.textranker = TextRank(span=10)
        self.ners = ['人名', '組織名', '地名']
        self.condi_for_event = ['名詞', '動詞', '形容詞']
        self.ner_dict = {
            '人名': '人名',  # People, including fictional
            '組織名': '組織名',  # Companies, agencies, institutions, etc.
            '地名': '地名',  # Countries, cities, states.
        }
        # dependency markers for subjects
        self.SUBJECTS = {"nsubj",
                         "nsubjpass",
                         "csubj",
                         "csubjpass",
                         "agent",
                         "expl"}
        self.NUM_KEYWORD = 10
        # dependency markers for objects
        self.OBJECTS = {"dobj", "dative", "attr", "oprd"}
        self.stop_word = self.load_stopwords("stopword")

        self.graph_shower = GraphShow()
        self.knp = KNP(command=knppath,
                       jumancommand=juman,
                       option='-tab -anaphora')


    def load_stopwords(self, path):
        file_handle = io.open(path, mode="r", encoding="utf8")
        result = {}

        for v in file_handle.readlines():
            v = v.strip()
            if v not in result and len(v) > 0:
                try:
                    result[v.decode("utf8")] = True
                except:
                    result[v] = True

        return result

    def select_normalization_representative_notation(self, fstring):
        """ 正規化代表表記を抽出します
        """
        begin = fstring.find('正規化代表表記:')
        end = fstring.find('/', begin + 1)
        return fstring[begin + len('正規化代表表記:'): end]

    def select_dependency_structure(self, line):
        """係り受け構造を抽出します
        """
        # 解析
        result = self.knp.parse(line)

        # 文節リスト
        bnst_list = result.bnst_list()
        tuples = []
        sov = []
        for bnst in bnst_list:
            nodes = []
            node = bnst
            while node and not bnst.children:
                nodes += [node]
                node = node.parent
            sub = ""
            verb = ""
            obj = ""
            for node in nodes:
                if node.mrph_list():
                    genki = node.mrph_list()[0].genkei
                    hinsi = node.mrph_list()[0].hinsi
                    if genki not in self.stop_word:
                        if u"名詞" in hinsi and len(sub) == 0:
                            sub = genki
                        elif u"動詞" in hinsi:
                            verb = genki
                        elif u"名詞" in hinsi and len(obj) == 0:
                            obj = genki
                        if len(sub) > 0 and len(verb) > 0 and len(obj) > 0:
                            break
            if (len(sub) > 0 or len(obj) > 0) and len(verb) > 0:
                sov += [(sub, verb, obj)]
            if bnst.parent_id != -1 and bnst.mrph_list()[0].genkei not in self.stop_word:
                # (from, to)
                genki = bnst.mrph_list()[0].genkei
                hinsi = bnst.mrph_list()[0].hinsi
                bunrui = bnst.mrph_list()[0].bunrui


                genki_p = bnst.parent.mrph_list()[0].genkei
                hinsi_p = bnst.parent.mrph_list()[0].hinsi
                bunrui_p = bnst.parent.mrph_list()[0].bunrui

                tuples.append([Word(genki,
                                    hinsi,
                                    bunrui),
                               Word(genki_p,
                                    hinsi_p,
                                    bunrui_p)])
        return tuples, sov

    def clean_spaces(self, s):
        s = s.replace('\r', '')
        s = s.replace('\t', '')
        s = s.replace(' ', '')
        return s

    def remove_chars(self, text, cahr_set):
        table = {ord(char): None for char in cahr_set}
        return text.translate(table)

    def remove_noisy(self, content):
        """Remove brackets"""
        p1 = re.compile(r'（[^）]*）')
        p2 = re.compile(r'\([^\)]*\)')
        text = p2.sub('', p1.sub('', content))
        text = self.remove_chars(text, "1234567890")
        return self.remove_chars(text, u"1234567890")

    def collect_ners(self, ents):
        """Collect token only with PERSON, ORG, GPE"""
        collected_ners = []
        for token in ents:
            if token.label_ in self.ners:
                collected_ners.append(token.text + '/' + token.label_)
        return collected_ners

    def conll_syntax(self, sent):
        """Convert one sentence to conll format."""

        tuples = list()
        for word in sent:
            if word.head is word:
                head_idx = 0
            else:
                head_idx = word.head.i + 1
            tuples.append([word.i + 1,  # Current word index, begin with 1
                           word.text,  # Word
                           word.lemma_,  # Lemma
                           word.pos_,  # Coarse-grained tag
                           word.tag_,  # Fine-grained tag
                           '_',
                           head_idx,  # Head of current  Index
                           word.dep_,  # Relation
                           '_', '_'])
        return tuples

    def syntax_parse(self, sent):
        """Convert one sentence to conll format."""
        tuples = list()
        for word in sent:
            if word.head is word:
                head_idx = 0
            else:
                head_idx = word.head.i + 1
            tuples.append([word.i + 1,  # Current word index, begin with 1
                           word.text,  # Word
                           word.pos_,  # Coarse-grained tag
                           word.head,
                           head_idx,  # Head of current  Index
                           word.dep_,  # Relation
                           ])
        return tuples

    def build_parse_chile_dict(self, sent, tuples):
        child_dict_list = list()
        for word in sent:
            child_dict = dict()
            for arc in tuples:
                if arc[3] == word:
                    if arc[-1] in child_dict:
                        child_dict[arc[-1]].append(arc)
                    else:
                        child_dict[arc[-1]] = []
                        child_dict[arc[-1]].append(arc)
            child_dict_list.append([word, word.pos_, word.i, child_dict])
        return child_dict_list

    def complete_VOB(self, verb, child_dict_list):
        '''Find VOB by SBV'''
        for child in child_dict_list:
            word = child[0]
            # child_dict: {'dobj': [[7, 'startup', 'NOUN', buying, 5, 'dobj']], 'prep': [[8, 'for', 'ADP', buying, 5, 'prep']]}
            child_dict = child[3]
            if word == verb:
                for object_type in self.OBJECTS:  # object_type: 'dobj'
                    if object_type not in child_dict:
                        continue
                    # [7, 'startup', 'NOUN', buying, 5, 'dobj']
                    vob = child_dict[object_type][0]
                    obj = vob[1]  # 'startup'
                    return obj
        return ''

    def extract_triples(self, sent):
        svo = []
        tuples = self.syntax_parse(sent)
        child_dict_list = self.build_parse_chile_dict(sent, tuples)
        for tuple in tuples:
            rel = tuple[-1]
            if rel in self.SUBJECTS:
                sub_wd = tuple[1]
                verb_wd = tuple[3]
                obj = self.complete_VOB(verb_wd, child_dict_list)
                subj = sub_wd
                verb = verb_wd.text
                if not obj:
                    svo.append([subj, verb])
                else:
                    svo.append([subj, verb+' '+obj])
        return svo

    def extract_keywords(self, words_postags):
        return self.textranker.extract_keywords(words_postags, self.NUM_KEYWORD)

    def collect_coexist(self, ner_sents, ners):
        """Construct NER co-occurrence matrices"""
        co_list = []
        for words in ner_sents:
            co_ners = set(ners).intersection(set(words))
            co_info = self.combination(list(co_ners))
            co_list += co_info
        if not co_list:
            return []
        return {i[0]: i[1] for i in Counter(co_list).most_common()}

    def combination(self, a):
        '''list all combination'''
        combines = []
        if len(a) == 0:
            return []
        for i in a:
            for j in a:
                if i == j:
                    continue
                combines.append('@'.join([i, j]))
        return combines

    @staticmethod
    def is_eniglish(word):
        try:
            word.encode('utf8').decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    @staticmethod
    def is_number(word):
        try:
            float(word)
            return True
        except ValueError:
            pass

        try:
            import unicodedata
            unicodedata.numeric(word)
            return True
        except (TypeError, ValueError):
            pass
        return False


    def main(self, content):
        '''Main function'''
        if not content:
            return []

        words_postags = []  # token and its POS tag
        ner_sents = []      # store sentences which contain NER entity
        ners = []           # store all NER entity from whole article
        triples = []        # store subject verb object
        events = []         # store events
        collected_ners = []
        # 01 remove linebreaks and brackets
        content = self.remove_noisy(content)
        content = self.clean_spaces(content)
        sents = nltk.RegexpTokenizer(u'[^　！？。.]*[！？。.\n]').tokenize(content)
        print(sents)
        def check_and_fill(word,
                           words_postags,
                           collected_ners):
            if self.is_eniglish(word.word):
                word.word = word.word.lower()
            if word.word not in self.stop_word and not self.is_number(word.word):
                words_postags += [word]
                if word.bunrui in self.ners:
                    collected_ners += [word]

        for sent in sents:
            if len(sent) <= 1:
                continue
            word_pairs, sov = self.select_dependency_structure(sent)
            for word_pair in word_pairs:
                check_and_fill(word_pair[0],
                               words_postags,
                               collected_ners)
                check_and_fill(word_pair[1],
                               words_postags,
                               collected_ners)

            if collected_ners:
                triples += sov
                ners += collected_ners
                ner_sents.append([word.word + '/' + word.bunrui for word in words_postags])

        # 03 get keywords
        keywords = [i[0] for i in self.extract_keywords(words_postags)]
        for keyword in keywords:
            name = keyword
            cate = 'キーワード'
            color = self.KEYWORD_COLOR
            events.append([[name, self.DEFAULT_COLOR], [cate, color]])

        # 04 add triples to event only the word in keyword
        for t in triples:
            if (t[0] in keywords or t[1] in keywords) and len(t[0]) > 1 and len(t[1]) > 1:
                events.append([[t[0], self.DEFAULT_COLOR], [t[1], self.DEFAULT_COLOR]])
                if len(t[2]) > 0:
                    events.append([[t[1]],self.DEFAULT_COLOR],[[t[2], self.DEFAULT_COLOR]])

        # 05 get word frequency and add to events
        word_dict = [i[0] for i in Counter([word.word for word in words_postags if word.hinsi in self.condi_for_event
                                        ]).most_common(self.MOST_FREQUENTLY)]
        for wd in word_dict:
            name = wd
            cate = '頻出単語'
            color = self.FREQUENCY_COLOR

            events.append([[name, self.DEFAULT_COLOR], [cate, color]])

        # 06 get NER from whole article
        ner_dict = {word[0].word + '/' + word[0].bunrui: word[0] for word in Counter(ners).most_common(self.MOST_FREQUENTLY)}
        for ner in ner_dict:
            name = ner_dict[ner].word # Jessica Miller
            cate = ner_dict[ner].bunrui  # PERSON
            events.append([name, cate, self.NER_COLOR])

        # 07 get all NER entity co-occurrence information
        # here ner_dict is from above 06
        co_dict = self.collect_coexist(ner_sents, list(ner_dict.keys()))
        co_events = [[[i.split('@')[0].split('/')[0], self.DEFAULT_COLOR],
                      [i.split('@')[1].split('/')[0], self.DEFAULT_COLOR]] for i in co_dict]
        events += co_events

        # 08 show event graph
        self.graph_shower.create_page(events)
