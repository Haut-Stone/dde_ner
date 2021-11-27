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
        self.rel_train_data = json.load(open('../../tools/check_data/neo4j_use_relation.json'))
        self.data = []
        self.all_ins_for_every_sen = dict()
        self.ins_pair_list = []
        self.type_pair_list = []
        self.rel_predict_data = []

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
        # todo 暂时通过全连接的方式去构造关系，
        # 生成全部实体
        for sen_data in self.data:
            if sen_data['id'] not in self.all_ins_for_every_sen:
                self.all_ins_for_every_sen[sen_data['id']] = []
            pos_b = -1
            pos_e = -1
            for i in range(len(sen_data['labels'])):  # 查找所有的单词
                label = bytes.decode(sen_data['labels'][i])
                if label.split('-')[0] == 'S':
                    pos_b = i
                    pos_e = i+1
                    node = {
                        'name': ' '.join(sen_data['words'][pos_b:pos_e]),
                        'pos': [pos_b, pos_e],
                        'type': label.split('-')[-1],
                        'token': sen_data['words']
                    }
                    self.all_ins_for_every_sen[sen_data['id']].append(node)
                else:
                    if label.split('-')[0] == 'B':
                        pos_b = i
                    if label.split('-')[0] == 'E':
                        pos_e = i + 1
                        node = {
                            'name': ' '.join(sen_data['words'][pos_b:pos_e]),
                            'pos': [pos_b, pos_e],
                            'type': label.split('-')[-1],
                            'token': sen_data['words']
                        }
                        self.all_ins_for_every_sen[sen_data['id']].append(node)
            print(self.all_ins_for_every_sen[sen_data['id']])

        # 这里不是全连接，而是对于所有出现的（实体名对）（类型对）有没有出现过。
        # 首先先去针对原始训练数据构造组合
        for item in self.rel_train_data:
            name1 = item['h']['name']
            name2 = item['t']['name']
            type1 = item['h']['type'].split('_')[-1]
            type2 = item['t']['type'].split('_')[-1]
            self.ins_pair_list.append((name1, name2))
            print((name1, name2))
            if (type1, type2) not in self.type_pair_list:
                self.type_pair_list.append((type1, type2))
                print((type1, type2))

        txt = open('../../tools/out_data/关系预测数据.txt', 'w', encoding='utf-8')
        for key, values in self.all_ins_for_every_sen.items():
            for i in range(len(values)):  # i 是头节点
                for j in range(len(values)):  # j是尾节点
                    if (values[i]['name'], values[j]['name']) not in self.ins_pair_list:  # 不是存在的的实体名对不预测
                        print('a')
                        print(values[i]['type'], values[j]['type'])
                        if (values[i]['type'], values[j]['type']) not in self.type_pair_list:  # 不是存在的类型对不预测
                            print('b')
                            continue

                    if i == j:
                        continue
                    rel = {
                        'token': values[i]['token'],
                        'h': {
                            'name': values[i]['name'],
                            'pos': values[i]['pos'],
                            'type': values[i]['type']
                        },
                        't': {
                            'name': values[j]['name'],
                            'pos': values[j]['pos'],
                            'type': values[j]['type']
                        },
                        'relation': 'NA'
                    }
                    self.rel_predict_data.append(rel)
                    txt.write(str(rel))
                    txt.write('\n')
        txt.close()

    def pretty_print(self, line, preds, id_counter):
        words = line.strip().split()
        lengths = [max(len(w), len(p)) for w, p in zip(words, preds)]
        padded_words = [w + (l - len(w)) * ' ' for w, l in zip(words, lengths)]
        padded_preds = [p.decode() + (l - len(p)) * ' ' for p, l in zip(preds, lengths)]
        sen = {
            'id': id_counter,
            'sen': line,
            'words': words,
            'labels': preds,
            'padded_words': padded_words,
            'padded_preds': padded_preds
        }
        # print(words, preds)
        self.data.append(sen)
        print('words: {}'.format(' '.join(padded_words)))
        print('preds: {}'.format(' '.join(padded_preds)))

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
        id_counter = 0
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
                self.pretty_print(line, pred['tags'], id_counter=id_counter)
                id_counter += 1
                break
        self.gen_answer()


if __name__ == '__main__':
    a = ModelRunner()
    a.run()
