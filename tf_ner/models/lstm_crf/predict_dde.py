from pathlib import Path
import functools
import json
import tensorflow as tf
from main import model_fn
import os
import xlsxwriter

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


class ModelRunner:

    def __init__(self):
        self.lines = []
        self.DATADIR = '../../data/dde'
        self.PARAMS = './results_dde/params.json'
        self.MODELDIR = './results_dde/model'
        self.data = []

    def get_val_data(self):
        with open('../../data/dde/val.txt', 'r', encoding='utf-8') as f:
            while True:
                line = f.readline()
                if not line:
                    break
                self.lines.append(line)

    def gen_answer(self):

        # 保存给地学院看的数据
        out_path = '../../tools/out_data/answer.xlsx'
        wb = xlsxwriter.Workbook(out_path)
        ws = wb.add_worksheet('sheet1')
        pink = wb.add_format({'bold': True, 'color': 'EA6140'})

        counter = 1
        out_ins_seq = []
        out_lab_seq = []
        for sen_data in self.data:
            for i in range(len(sen_data['words'])):
                if str(sen_data['labels'][i], 'utf-8') != 'O':
                    out_ins_seq.append(pink)
                    out_lab_seq.append(pink)
                a = str(sen_data['padded_words'][i]) + ' '
                b = str(sen_data['padded_preds'][i]) + ' '
                out_ins_seq.append(a)
                out_lab_seq.append(b)
            ws.write_rich_string(counter, 0, *out_ins_seq)
            counter += 1
            ws.write_rich_string(counter, 0, *out_lab_seq)
            counter += 2
            out_ins_seq.clear()
            out_lab_seq.clear()
        wb.close()

        # 保存关系模型要用的数据

    def pretty_print(self, line, preds):
        words = line.strip().split()
        lengths = [max(len(w), len(p)) for w, p in zip(words, preds)]
        padded_words = [w + (l - len(w)) * ' ' for w, l in zip(words, lengths)]
        padded_preds = [p.decode() + (l - len(p)) * ' ' for p, l in zip(preds, lengths)]
        sen = {
            'sen': line,
            'words': words,
            'labels': preds,
            'padded_words': padded_words,
            'padded_preds': padded_preds
        }
        # print(words, preds)
        self.data.append(sen)
        # print('words: {}'.format(' '.join(padded_words)))
        # print('preds: {}'.format(' '.join(padded_preds)))

    @staticmethod
    def predict_input_fn(line):
        # Words
        words = [w.encode() for w in line.strip().split()]
        nwords = len(words)
        # Wrapping in Tensors
        words = tf.constant([words], dtype=tf.string)
        nwords = tf.constant([nwords], dtype=tf.int32)
        return (words, nwords), None

    def run(self):
        with Path(self.PARAMS).open() as f:
            params = json.load(f)
        params['words'] = str(Path(self.DATADIR, 'vocab.words.txt'))
        params['chars'] = str(Path(self.DATADIR, 'vocab.chars.txt'))
        params['tags'] = str(Path(self.DATADIR, 'vocab.tags.txt'))
        params['glove'] = str(Path(self.DATADIR, 'glove.npz'))
        estimator = tf.estimator.Estimator(model_fn, self.MODELDIR, params=params)
        self.get_val_data()
        for line in self.lines:
            predict_inpf = functools.partial(self.predict_input_fn, line)
            for pred in estimator.predict(predict_inpf):
                self.pretty_print(line, pred['tags'])
                break
        self.gen_answer()


if __name__ == '__main__':
    a = ModelRunner()
    a.run()
