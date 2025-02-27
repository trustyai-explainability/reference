import random
import numpy as np
import json

PUNCTUATION = ".!?"
LETTERS = list("abcdefghijklmnopqrstuvwxyz")
WORD_START_FREQ = [.1154,.043,.052,.032,.028,.04,.016,.042,.073,.0051,.0086,.024,.038,.023,.076,.043,.0022,.028,.067,.16,.012,.0082,.055,.00045,.0076,.00045]
WORD_LEN_FREQ = [0.031500223549973574, 0.1717270251595334, 0.21533959273259357, 0.15851725399341543, 0.10974271430313375, 0.08657480795024995, 0.07316180953542249, 0.05690362963866195, 0.04064544974190139, 0.027435678575783436, 0.01524204365321302, 0.009145226191927812, 0.004064544974190139]
WORD_LENS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


# === WORD GENERATION MARKOV MODEL =================================================================
def proc_bigrams():
    with open("bigrams.json", "r") as f:
        bigrams = json.load(f)
    return bigrams


bigrams = proc_bigrams()

def specific_bigram_freq(start_letter):
    # given a specific start letter, get the probability of subsequent letters
    specific_bigrams = [(bg, f) for bg,f in bigrams if bg[0] == start_letter]
    specific_bigrams, freqs = zip(*specific_bigrams)
    freqs = np.array(freqs)/sum(freqs)
    return specific_bigrams, freqs


def gen_word(letter_bounds=(2, 8)):
    """Generates english-y words according to a bi-gram Markov chain """
    start_letter = np.random.choice(LETTERS, size=1, p=WORD_START_FREQ)[0]
    word = start_letter

    word_len = np.random.choice(WORD_LENS, size=1, p=WORD_LEN_FREQ)[0]
    for _ in range(word_len):
        specific_bigrams, freqs = specific_bigram_freq(word[-1])
        new_letters = np.random.choice(specific_bigrams, size=1, p=freqs)[0]
        word += new_letters[-1]
    return word


# === PARAGRAPH GENERATION =========================================================================
def gen_paragraph(max_len, sentence_bounds=(4,8), word_bounds=(5,15), letter_bounds=(3,8)):
    out = ""
    n_sent = random.randint(*sentence_bounds)
    since_last_break = 0;

    for _ in range(n_sent ):
        n_words = random.randint(*word_bounds)
        for word_idx in range(n_words):

            if max_len and len(out) > max_len:
                return out.strip(), True

            word = gen_word(letter_bounds)
            if word_idx==0: # capitalize first word
                word = word[0].upper() + word[1:]
            out += word

            if word_idx < n_words-1:
                if (len(out) - since_last_break) < 80:
                    out += " "
                else:
                    out += " \n"
                    since_last_break = len(out)
        out += random.choice(PUNCTUATION)
        out += " "
    return out.strip(), false