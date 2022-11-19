import re
from collections import namedtuple

import coreferee, spacy  # don't remove coreferee
import inflect
import lemminflect
from spacy import Vocab

from helpers import html_replaced_with_spaces

nlp = spacy.load('en_core_web_trf')
nlp.add_pipe('coreferee')

inflector = inflect.engine()

# https://github.com/msg-systems/coreferee/issues/19#issuecomment-911522340

html = (open("aliceInWonderland/4560944924381563385_11-h-2.htm.xhtml", "r", encoding='utf-8')).read()
html = '''<pre>
     <i>Alice’s Right Foot, Esq.,
       Hearthrug,
         near the Fender,</i>
           (<i>with Alice’s love</i>).
</pre>
<p class="noindent">
Oh dear, what nonsense I’m talking!”
</p>
<p>
Just then her head struck against the roof of the hall: in fact she was now
more than nine feet high, and she at once took up the little golden key and
hurried off to the garden door.
</p>
<p>
Poor Alice! It was as much as she could do, lying down on one side, to look
through into the garden with one eye; but to get through was more hopeless than
ever: she sat down and began to cry again.
</p>'''

text = html_replaced_with_spaces(html)

# t = [f"{i} {txt}" for i, txt in enumerate(text.split(' '))]
# print(' '.join(t))

doc = nlp(text)

# for token in doc:
#     print(token.i, token.text)

p = inflect.engine()

CorrectOrderTuple = namedtuple('CorrectOrderTuple', ['i', 'old', 'new'])


class WordUpdater:
    updates = []

    def add(self, token, to):
        info = CorrectOrderTuple(token.idx, token.text, to)
        self.updates.append(info)


    @staticmethod
    def do_update(info: CorrectOrderTuple):
        global html

        to = info.new

        if info.old[0].isupper():
            to = to[0].upper() + to[1:]

        html = html[0: info.i] + to + html[info.i + len(info.old):]

    def update(self):
        self.updates.sort(key=lambda x: x.i)
        while self.updates:
            el = self.updates.pop()
            self.do_update(el)


word_updater = WordUpdater()


def update_token(token):
    prev_token = doc[token.i - 1]
    try:
        following_token = doc[token.i + 1]
    except IndexError:
        return
    # print(list(token.children),3333)
    print(prev_token, token, following_token, 222, following_token.lemma_, following_token.tag_)

    to_change = ' '.join([prev_token.text, token.text, following_token.text])

    if token.text.lower() in ['i', 'it', 'yourself', 'myself', 'we', 'they']:
        return

    if following_token.tag_[0:2] == 'VB' and following_token.lemma_ in ['has', 'be']:

        current_form = following_token.text
        plural_form = inflector.plural(current_form, 4)

        if plural_form == 'bes':
            plural_form = 'be'  # ffs
        elif plural_form == 'beens':
            plural_form = 'been'

        if plural_form != current_form:
            word_updater.add(following_token, plural_form)


    token_tag = token.tag_

    if token_tag[0:3] == 'PRP':  # personal pronoun
        if token.tag_ == 'PRP':  # personal pronoun
            suggested_updated = inflector.plural(token.text)
            if str(suggested_updated).lower() == 'their':
                suggested_updated = 'them'
            word_updater.add(token, suggested_updated)
        elif token.tag_ == 'PRP$':  # possessive pronoun
            word_updater.add(token, inflector.plural(token.text))



    # token.morph: Case=Nom|Gender=Fem|Number=Sing|Person=3|PronType=Prs
    # print(token.tag_, token.text, 222, token.morph)
    # print(token.morph, token._.inflect(following_token.tag_, ))
    # tag = Penn Treebank tag,


def do_coref():
    coref_chains = doc._.coref_chains
    # coref_chains.print()

    character = 'Alice'
    found_character_tokens = []
    for chain in coref_chains:
        found_character = False
        for token_info in chain:
            token = doc[token_info.root_index]
            if token.text == character:
                found_character = True
                break
        if found_character:
            for token_info in chain:
                token = doc[token_info.root_index]
                found_character_tokens.append(token)
        # else:
        #     print([doc[el.root_index].text for el in  chain])


    for token in found_character_tokens:
        if token.text == character:
            continue
        update_token(token)

    word_updater.update()

do_coref()


def do_all():
    coref_chains = doc._.coref_chains
    # coref_chains.print()

    found_character_tokens = []

    for token in doc:
        outcome = update_token(token)

    for token in found_character_tokens:
        update_token(token)

    word_updater.update()


# do_all()

print(html)



