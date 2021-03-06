from collections import Counter

import numpy as np

import gensim.downloader as api

from sklearn.feature_extraction.text import CountVectorizer

from utils import preprocess_text
from text_transformers.base_text_transformer import BaseTextTransformer


class Index(BaseTextTransformer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def as_matrix(self, sequences, token_to_id, unk_ix, pad_ix, max_len=None):
        """ Convert a list of tokens into a matrix with padding """
        if isinstance(sequences[0], str):
            sequences = list(map(str.split, sequences))

        max_len = min(max(map(len, sequences)), max_len or float('inf'))

        matrix = np.full((len(sequences), max_len), np.int32(pad_ix))
        for i, seq in enumerate(sequences):
            row_ix = [token_to_id.get(word, unk_ix) for word in seq[:max_len]]
            if len(row_ix) > 0:
                matrix[i, -len(row_ix):] = row_ix

        return matrix

    def fit_transform(self, texts, pretrained=False):
        min_count = 3
        max_count = len(texts) * 0.7

        clean_texts = [preprocess_text(t) for t in texts]

        counter = Counter()

        for text in clean_texts:
            for token in text:
                counter[token] += 1

        self.unique_tokens = [t for t in counter.keys() if max_count >= counter[t] >= min_count]
        unk, pad = "UNK", "PAD"
        self.unique_tokens = [unk, pad] + self.unique_tokens

        self.token_to_id = {t: i for i, t in enumerate(self.unique_tokens)}

        unk_ix, pad_ix = map(self.token_to_id.get, [unk, pad])
        n_tokens = len(self.unique_tokens)

        matrix = self.as_matrix(clean_texts, self.token_to_id, unk_ix, pad_ix)

        def get_word_embedding(word, w2v):
            if word == pad:
                return np.ones(100)
            if word in w2v:
                return w2v.get_vector(word)
            else:
                return np.random.rand(100)

        if pretrained:
            model = api.load('glove-twitter-100')
            embs = np.array([get_word_embedding(token, model) for token in self.unique_tokens])
        else:
            embs = None

        return pad_ix, n_tokens, matrix, embs
