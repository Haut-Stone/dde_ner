"""Build an np.array from some glove file and some vocab file

You need to download `glove.840B.300d.txt` from
https://nlp.stanford.edu/projects/glove/ and you need to have built
your vocabulary first (Maybe using `build_vocab.py`)
"""

__author__ = "Guillaume Genthial"

from pathlib import Path
import numpy as np
import csv

not_find = []


def build_glove():
    # Load vocab
    with Path('vocab.words.txt').open(encoding='utf-8') as f:
        word_to_idx = {line.strip(): idx for idx, line in enumerate(f)}
    size_vocab = len(word_to_idx)

    # Array of zeros
    embeddings = np.zeros((size_vocab, 300))  # 默认给全0矩阵

    # Get relevant glove vectors
    # todo 这里其实是可以去显示的
    found = 0
    print('Reading GloVe file (may take a while)')
    with Path('../../tools/raw_data/glove.840B.300d.txt').open(encoding='utf-8') as f:  # 这个文件可以从readme中看到，需要单独下载
        for line_idx, line in enumerate(f):
            if line_idx % 100000 == 0:
                print('- At line {}'.format(line_idx))
            line = line.strip().split()
            if len(line) != 300 + 1:
                continue
            word = line[0]
            embedding = line[1:]
            if word in word_to_idx:
                found += 1
                word_idx = word_to_idx[word]
                embeddings[word_idx] = embedding

    # for key, value in word_to_idx.items():
    #     if np.count_nonzero(embeddings[value]) == 0:
    #         not_find.append({'单词': key})
    #         print(key, '@@@')

    # headers = ['单词']
    # with open('./can_not_find_embedding.csv', 'w', encoding='utf-8', newline='') as f:
    #     f_csv = csv.DictWriter(f, headers)
    #     f_csv.writeheader()
    #     f_csv.writerows(not_find)
    print('- done. Found {} vectors for {} words'.format(found, size_vocab))

    # Save np.array to file
    np.savez_compressed('glove.npz', embeddings=embeddings)


if __name__ == '__main__':
    build_glove()
