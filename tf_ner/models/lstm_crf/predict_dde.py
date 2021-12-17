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
        self.rel_train_data = json.load(open('../../tools/raw_data_send_to_nre/rel_marked_neo4j_can_use.json'))
        self.data = []
        self.all_ins_for_every_sen = dict()
        self.entity_end_type_dict = dict()
        self.entity_begin_type_dict = dict()
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

        # 保存给地学院看的数据和可以二次利用的json数据
        # todo 生成json这一部分还没有测试，下次记得测试
        out_path = '../../tools/out_data/ner_predict_result.xlsx'
        storage_json_path = '../../tools/out_data/ner_predict_result.json'
        storage_json = []
        wb = xlsxwriter.Workbook(out_path)
        ws = wb.add_worksheet('sheet1')
        pink = wb.add_format({'bold': True, 'color': 'EA6140'})
        counter = 1
        out_ins_seq = []
        out_lab_seq = []
        for sen_data in self.data:
            json_line = {
                'words': sen_data['words'],
                'labels': sen_data['labels']
            }
            storage_json.append(json_line)
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
        json.dump(storage_json, open(storage_json_path, 'w', encoding='utf-8'))

        # 保存关系模型要用的数据
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
            # print(self.all_ins_for_every_sen[sen_data['id']])

        # 这里不是全连接，而是对于所有出现的（实体名对）（类型对）有没有出现过。
        # 首先先去针对原始训练数据构造组合
        # todo 这里以后重点也是对两边的实体要进行一个大小写，单复数的归一化
        for item in self.rel_train_data:
            name1 = item['h']['name'].strip().lower()  # 去除大小写
            name2 = item['t']['name'].strip().lower()
            type1 = item['h']['type'].split('_')[-1]
            type2 = item['t']['type'].split('_')[-1]
            if name1 not in self.entity_begin_type_dict:  # 确定结尾实体
                self.entity_begin_type_dict[name1] = []
            if name2 not in self.entity_end_type_dict:  # 确定开始实体
                self.entity_end_type_dict[name2] = []

            self.entity_begin_type_dict[name1].append(type2)
            self.entity_end_type_dict[name2].append(type1)
            self.ins_pair_list.append((name1, name2))
            # print((name1, name2))
            if (type1, type2) not in self.type_pair_list:
                self.type_pair_list.append((type1, type2))
                # print((type1, type2))

        txt = open('../../tools/raw_data_send_to_nre/rel_smart_ins_pair_no_rel.txt', 'w', encoding='utf-8')
        # print('===================================')
        for key, values in self.all_ins_for_every_sen.items():
            for i in range(len(values)):  # i 是头节点
                for j in range(len(values)):  # j是尾节点
                    name1 = values[i]['name'].strip().lower()
                    name2 = values[j]['name'].strip().lower()
                    type1 = values[i]['type']
                    type2 = values[j]['type']

                    if i == j:
                        continue
                    if (values[i]['name'], values[j]['name']) in self.ins_pair_list:
                        # print('a')
                        pass
                    elif name1 in self.entity_begin_type_dict:  # 如果有a节点
                        # print('b')
                        temp = self.entity_begin_type_dict[name1]  # 那我看b的type是否符合条件
                        if type2 not in temp:  # 不符合跳过b节点，符合那就生成
                            continue
                    elif name2 in self.entity_end_type_dict:  # 如果你b在
                        # print('c')
                        temp = self.entity_end_type_dict[name2]
                        if type1 not in temp:  # 如果我a不属于你要找的头结点的类型，那我就跳过
                            continue
                    else:  # ab都不在，那没有判断依据跳过
                        # print('d')
                        continue
                    # print(values[i]['type'], values[j]['type'])
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
