from nltk.corpus import wordnet


class WordnetWrapper:
    class __WordnetWrapper:

        def __init__(self):
            pass

        def get_synonyms_antonyms(self, word):
            synonyms = []
            antonyms = []
            for syn in wordnet.synsets(word):
                for l in syn.lemmas():
                    synonyms.append(l.name())
                    if l.antonyms():
                        antonyms.append(l.antonyms()[0].name())

            return list(set(synonyms)), list(set(antonyms))

        def get_synsets_by_name(self, synset_names):
            to_return = []

            for syn_name in synset_names:
                syn = wordnet.synset(syn_name)
                to_return.append(syn)

            return to_return

        def get_synsets_by_word(self, word):
            synsets = wordnet.synsets(word)
            return synsets

        def get_similarity(self, word1, word2_synset, POS, average=False):
            word1_synsets = wordnet.synsets(word1)

            max_score = 0
            for word1_synset in word1_synsets:
                if word1_synset._pos != POS or word2_synset._pos != POS:
                    continue
                score = word1_synset.wup_similarity(word2_synset)
                if score is None:
                    continue
                # else:
                #    print("SCORE between {} and {}: {}".format(word1_synset,word2_synset,score))
                if not average:
                    if score > max_score:
                        max_score = score
                else:
                    max_score += score

            if average:
                max_score = (max_score / (len(word1_synsets) * 1.0)) if len(word1_synsets) > 0 else 0

            return max_score

        def __str__(self):
            return repr(self) + self.val

    instance = None

    def __init__(self):
        if not WordnetWrapper.instance:
            WordnetWrapper.instance = WordnetWrapper.__WordnetWrapper()

    def __getattr__(self, name):
        return getattr(self.instance, name)
