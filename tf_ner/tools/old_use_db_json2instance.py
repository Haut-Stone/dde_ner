"""
最初的老数据用
"""
import json

json_data = json.load(open('old_data_save/第一次完整可靠可用的少量数据/db_instances.json', encoding='utf-8'))
txt_words_file = open('old_data_save/第一次完整可靠可用的少量数据/db_words.txt', 'w', encoding='utf-8')
txt_tags_file = open('old_data_save/第一次完整可靠可用的少量数据/db_tags.txt', 'w', encoding='utf-8')

res = []
instance = []
instance_label = []
ori_sen = ''
id_now = -1
ins_set = set()


def pos_calculator(sen, ins_start, ins_end):
    """
    计算单词位置
    """
    pos_tag = [-1 for _ in range(len(sen))]
    tag = 0
    flag = True  # 用来记录遇到空格后是否再遇到单词，来处理句子中出现多于一个空格的情况：例如( t )  ( +1 to +12 )
    for i in range(len(sen)):
        if sen[i] == ' ' and flag:
            tag += 1
            flag = False
        else:
            pos_tag[i] = tag
            flag = True

    # 对实体词组前后空格进行修正，去掉标注时多勾画的前后空格
    for i in range(ins_start, ins_end):
        if sen[i] == ' ':
            ins_start += 1
        else:
            break
    for i in range(ins_end-1, ins_start-1, -1):
        if sen[i] == ' ':
            ins_end -= 1
        else:
            break
    print(pos_tag[ins_start])
    return [pos_tag[ins_start], pos_tag[ins_end-1]+1]


for data in json_data:
    if id_now != data['example_id']:  # 如果句子发生变化，则对老句子存储，新句子重置
        if id_now != -1:
            res.append({'ins': ' '.join(instance), 'label': ' '.join(instance_label)})
            txt_words_file.write(' '.join(instance))
            txt_words_file.write('\n')
            txt_tags_file.write(' '.join(instance_label))
            txt_tags_file.write('\n')

        ori_sen = data['text:1']
        instance = data['text:1'].split()
        instance_label = ['O' for _ in range(len(instance))]
        id_now = data['example_id']

    num = pos_calculator(ori_sen, data['start_offset'], data['end_offset'])
    count = num[1] - num[0]

    temp = ''  # 统计各种单词都出现了多少
    if count == 1:  # 单个的标签
        for i in range(num[0], num[1]):
            instance_label[i] = 'S-' + data['text']
            temp = instance[i]
    else:
        for i in range(num[0], num[1]):
            if i == num[0]:
                instance_label[i] = 'B-' + data['text']
                temp = instance[i]
            elif i == num[1]-1:
                instance_label[i] = 'E-' + data['text']
                temp = temp + ' ' + instance[i]
            else:
                instance_label[i] = 'I-' + data['text']
                temp = temp + ' ' + instance[i]
    ins_set.add((temp, data['text']))

res_list = []
ins_list = list(ins_set)
for data in ins_list:
    ins = {
        'name': data[0],
        'type': data[1],
    }
    res_list.append(ins)

with open('check_data/ins_set_data.json', 'w', encoding='utf-8') as f:
    json.dump(res_list, f)
with open('check_data/useful_data.json', 'w', encoding='utf-8') as f:
    json.dump(res, f)

txt_tags_file.close()
txt_words_file.close()


