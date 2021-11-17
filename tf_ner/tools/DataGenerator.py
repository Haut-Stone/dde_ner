"""
用来将大家的标注数据变成模型可用的数据并生成检查用的数据检查表
todo 完成数据分割和数据清洗任务
"""
import sqlite3
import json
import csv


class DataGenerator:

    def __init__(self):
        self.conn = sqlite3.connect('C:\\Users\\sjh\\Desktop\\doccano\\doccano21@11@15.db')
        self.ins_json = dict()
        self.rel_json = dict()
        self.rel_map = dict()
        self.path_now = []
        self.paths = dict()
        self.instances = dict()
        self.labels = dict()
        self.new_rel_json = dict()
        self.new_ins_json = dict()
        self.error = []
        self.ins_set = set()
        self.ins_rows = []
        self.rel_rows = []

    def get_sql_data(self, project_id):
        """
        获得一个项目中的所有数据,并以句子为单位组合，将属于一个句子的实体与关系全部整合到以句子为键的一个字典项中
        这里得到的是最原始的数据，系统里实体和关系填成什么样子这里就是什么样子
        """
        i = self.conn.cursor()
        r = self.conn.cursor()
        instances = i.execute(  # 获取该项目所有用户的实体标记列表
            '''
            select al.text, start_offset, end_offset, ae.text, api_span.example_id, ae.project_id, ap.name, au.username
            from api_span join api_label al on al.id = api_span.label_id
            join api_example ae on ae.id = api_span.example_id
            join api_project ap on ae.project_id = ap.id
            join auth_user au on api_span.user_id = au.id
            where ae.project_id = ''' + str(project_id) + '''
            order by start_offset;
            '''
        )
        relations = r.execute(
            '''
            select ar.name, a1.start_offset, a1.end_offset, al.text, a2.start_offset, a2.end_offset, al2.text, ae.text,
                   ar.project_id, ap.name, a1.example_id, au.username
            from api_annotationrelations join api_relationtypes ar on api_annotationrelations.type_id = ar.id
            join api_span a1 on api_annotationrelations.annotation_id_1 = a1.id
            join api_span a2 on api_annotationrelations.annotation_id_2 = a2.id
            join api_label al on al.id = a1.label_id
            join api_example ae on ae.id = a1.example_id
            join api_label al2 on al2.id = a2.label_id
            join api_example ae2 on ae2.id = a2.example_id
            join api_project ap on api_annotationrelations.project_id = ap.id
            join auth_user au on api_annotationrelations.user_id = au.id
            where ar.project_id = ''' + str(project_id) + ''';
            '''
        )

        for ins in instances:
            pos = self._pos_calculator(ins[3], ins[1], ins[2])
            data = {
                'type': ins[0],
                'pos_begin': pos[0],
                'word': ins[3][ins[1]:ins[2]],
                'pos_end': pos[1],
                'sen': ins[3],
                'example_id': ins[4],
                'project_id': ins[5],
                'project_name': ins[6],
                'username': ins[7]
            }
            ins_data_show = {
                '实体类型': ins[0],
                '起始单词位置': pos[0],
                '结束单词位置': pos[1],
                '实体': ins[3][ins[1]:ins[2]],
                '句子': ins[3],
                '句子 id': ins[4],
                '项目 id': ins[5],
                '项目名称': ins[6],
                '标注用户名': ins[7]
            }
            self.ins_rows.append(ins_data_show)
            if data['example_id'] not in self.ins_json:
                self.ins_json[data['example_id']] = []
            self.ins_json[data['example_id']].append(data)
        for rel in relations:
            pos1 = self._pos_calculator(rel[7], rel[1], rel[2])
            pos2 = self._pos_calculator(rel[7], rel[4], rel[5])
            data = {
                'name': rel[0],
                'pos_begin_1': pos1[0],
                'pos_end_1': pos1[1],
                'type_1': rel[3],
                'pos_begin_2': pos2[0],
                'pos_end_2': pos2[1],
                'type_2': rel[6],
                'sen': rel[7],
                'project_id': rel[8],
                'project_name': rel[9],
                'example_id': rel[10],
                'username': rel[11]
            }
            rel_data_show = {
                '关系名称': rel[0],
                '实体 1 起始单词位置': pos1[0],
                '实体 1 结束单词位置': pos1[1],
                '实体 1': rel[7][rel[1]:rel[2]],
                '实体 1 类型': rel[3],
                '实体 2 起始单词位置': pos2[0],
                '实体 2 结束单词位置': pos2[1],
                '实体 2': rel[7][rel[4]:rel[5]],
                '实体 2 类型': rel[6],
                '句子': rel[7],
                '项目 id': rel[8],
                '项目名称': rel[9],
                '句子 id': rel[10],
                '标注用户名': rel[11]
            }
            self.rel_rows.append(rel_data_show)
            if data['example_id'] not in self.rel_json:
                self.rel_json[data['example_id']] = []
            self.rel_json[data['example_id']].append(data)

    @staticmethod
    def _pos_calculator(sen, ins_start, ins_end):
        """
        计算单词位置
        """
        pos_tag = [-1 for _ in range(len(sen))]  # 为所有字母标记-1
        tag = 0
        flag = True  # 用来记录遇到空格后是否再遇到单词，来处理句子中出现多于一个空格的情况：例如( t )  ( +1 to +12 )
        for j in range(len(sen)):
            if sen[j] == ' ' and flag:
                tag += 1
                flag = False
            else:
                pos_tag[j] = tag
                flag = True

        # 对实体词组前后空格进行修正，去掉标注时多勾画的前后空格
        for j in range(ins_start, ins_end):
            if sen[j] == ' ':
                ins_start += 1
            else:
                break
        for j in range(ins_end - 1, ins_start - 1, -1):
            if sen[j] == ' ':
                ins_end -= 1
            else:
                break
        return [pos_tag[ins_start], pos_tag[ins_end - 1] + 1]

    def make_map(self):
        """
        制造link关系的邻接图表，关系是有向图的形式保存的
        对某一句话中所有的link关系，拿出来构成一张图，用来生成新的实体
        """
        for key, values in self.rel_json.items():
            solo_map = dict()
            for rel in values:
                # 使用关系构造一张邻接表
                if rel['name'] == 'Link':
                    solo_map[(rel['pos_begin_1'], rel['pos_end_1'])] = []
                    solo_map[(rel['pos_begin_2'], rel['pos_end_2'])] = []
            for rel in values:
                if rel['name'] == 'Link':
                    solo_map[(rel['pos_begin_1'], rel['pos_end_1'])].append((rel['pos_begin_2'], rel['pos_end_2']))
            self.rel_map[key] = solo_map.copy()

    def _dfs(self, example_id, node):
        """
        带有路径记录的dfs
        """
        self.path_now.append(node)

        if not self.rel_map[example_id][node]:  # 如果是尾节点
            if example_id not in self.paths:
                self.paths[example_id] = []
            self.paths[example_id].append(self.path_now.copy())

        for node in self.rel_map[example_id][node]:
            self._dfs(example_id, node)
        self.path_now.pop()

    def ins_conn_label(self, example_id):
        """
        生成一个实体列表和一个标签列表，对所有实体用 O 来进行标记
        """
        self.instances[example_id] = self.ins_json[example_id][0]['sen'].split()
        self.labels[example_id] = ['O' for _ in range(len(self.instances[example_id]))]
        for ins in self.ins_json[example_id]:
            for i in range(ins['pos_begin'], ins['pos_end']):
                self.labels[example_id][i] = ins['type']

    @staticmethod
    def _entity_aggregation(inss, labs, seq):
        """
        对实体进行聚合操作,返回聚合后的实体标签列表，返回新实体长度，返回缩减后的实体位置标记。
        """
        temp_ins = []
        temp_lab = []
        save_len = 0
        for i in range(len(seq)):
            # 统计长度
            save_len += seq[i][1] - seq[i][0]
            if i == 0:
                temp_ins += inss[0:seq[i][1]]
                temp_lab += labs[0:seq[i][1]]
            elif i == len(seq) - 1:
                temp_ins += inss[seq[i][0]:len(inss)]
                temp_lab += labs[seq[i][0]:len(labs)]
            else:
                temp_ins += inss[seq[i][0]:seq[i][1]]
                temp_lab += labs[seq[i][0]:seq[i][1]]
        new_seq = (seq[0][0], seq[0][0]+save_len)
        cut_len = (seq[-1][1] - seq[0][0] - save_len)
        return temp_ins, temp_lab, new_seq, cut_len

    def gen_new_ins_example(self, example_id):
        """
        生成新的实例，这里是最关键的一个步骤，而且也是最容易出现错误的步骤
        思路如下：
        1.首先对原始的所有标签，直接标记BIES
        2.删除所有 Link 类型的标签，只保留普通类型（1）
        3.对于每一个 Link 类实体，每一个都生成一个新的例子，其余的 Link 类型实体直接抛弃（2）
        4，（1）（2）两部分数据就是实际再用的数据
        """
        instance = self.instances[example_id].copy()
        instance_label = self.labels[example_id].copy()

        # 不管是否是连接词，先将所有实体对实体内单词直接打上标签BIE的标签
        for data in self.ins_json[example_id]:
            count = data['pos_end'] - data['pos_begin']
            num = (data['pos_begin'], data['pos_end'])
            if count == 1:  # 单个的标签
                for i in range(num[0], num[1]):
                    instance_label[i] = 'S-' + data['type']
            else:
                for i in range(num[0], num[1]):
                    if i == num[0]:
                        instance_label[i] = 'B-' + data['type']
                    elif i == num[1] - 1:
                        instance_label[i] = 'E-' + data['type']
                    else:
                        instance_label[i] = 'I-' + data['type']
        ori_example_ins = instance.copy()
        ori_example_lab = instance_label.copy()

        # 清除包含了 Link_ 类型的实体，构造一个仅仅保留正常实体的条目
        for i in range(len(ori_example_lab)):
            if 'Link' in ori_example_lab[i]:
                ori_example_lab[i] = 'O'
        if example_id not in self.new_ins_json:
            self.new_ins_json[example_id] = []
        self.new_ins_json[example_id].append((ori_example_ins, ori_example_lab))

        # 处理 Link_ 类型的实体标签问题
        if example_id in self.paths:
            # print(example_id, self.paths[example_id])
            for path in self.paths[example_id]:  # 每个新例子仅聚合一个实体，别的直接放弃掉。todo 当然这不是最优解，所以还可以优化
                word = self._entity_aggregation(instance, instance_label, path)
                # print(word)
                if word[3] < 0:
                    raise Exception(example_id, "Link路径从后向前", self.rel_json[example_id][0]['username'], self.rel_json[example_id][0]['sen'])
                count = word[2][1] - word[2][0]
                num = word[2]  # 新的实体的开始与结束位置
                temp_ins = []
                ins_type = ''
                if count == 1:  # 单个的标签
                    for i in range(num[0], num[1]):
                        ins_type = word[1][i].split('_')[-1]
                        word[1][i] = 'S-' + word[1][i].split('_')[-1]
                        temp_ins.append(word[0][i])
                else:
                    for i in range(num[0], num[1]):
                        if i == num[0]:
                            ins_type = word[1][i].split('_')[-1]
                            word[1][i] = 'B-' + word[1][i].split('_')[-1]
                            temp_ins.append(word[0][i])
                        elif i == num[1] - 1:
                            word[1][i] = 'E-' + word[1][i].split('_')[-1]
                            temp_ins.append(word[0][i])
                        else:
                            word[1][i] = 'I-' + word[1][i].split('_')[-1]
                            temp_ins.append(word[0][i])

                # 将新的实体保存到实体列表中
                ins_data_show = {
                    '实体类型': ins_type,
                    '起始单词位置': '无',
                    '结束单词位置': '无',
                    '实体': ' '.join(temp_ins),
                    '句子': self.rel_json[example_id][0]['sen'],
                    '句子 id': example_id,
                    '项目 id': self.rel_json[example_id][0]['project_id'],
                    '项目名称': self.rel_json[example_id][0]['project_name'],
                    '标注用户名': self.rel_json[example_id][0]['username']
                }
                self.ins_rows.append(ins_data_show)

                # 将其他 Link 实体清除
                for i in range(len(word[1])):
                    if 'Link' in word[1][i]:
                        word[1][i] = 'O'
                if example_id not in self.new_ins_json:
                    self.new_ins_json[example_id] = []
                self.new_ins_json[example_id].append((word[0], word[1]))

    def gen_new_rel_example(self, example_id):
        """
        删除实体间多余的单词，构造一个新的 json 组，对于之前的所有的 json 组中的内容，所有的位置都要根据单词位置进行一个修改。
        """
        for rel in self.rel_json[example_id]:  # 遍历某个实例中的全部关系
            instances = self.instances[example_id]
            labels = self.labels[example_id]
            seq_a = []
            seq_b = []
            if rel['name'] != 'Link':  # 如果找到一个普通关系
                if rel['type_1'].split('_')[0] == 'Link' or rel['type_2'].split('_')[0] == 'Link':  # 如果有一个是聚合元素
                    for seq in self.paths[example_id]:  # 遍历所有聚合元素路径
                        if (rel['pos_begin_1'], rel['pos_end_1']) in seq:  # 如果在某个路径中
                            seq_a = seq
                            break
                        else:
                            seq_a = [(rel['pos_begin_1'], rel['pos_end_1'])]
                    for seq in self.paths[example_id]:
                        if (rel['pos_begin_2'], rel['pos_end_2']) in seq:
                            seq_b = seq
                            break
                        else:
                            seq_b = [(rel['pos_begin_2'], rel['pos_end_2'])]
                    switch_back = False
                    if seq_a[0][0] > seq_b[-1][0]:  # 如果b实体在a实体前, 则把前边的实体换到序列 a 上
                        seq_a, seq_b = seq_b, seq_a
                        switch_back = True
                    if len(seq_b) > 1:  # 如果b需要进行缩短
                        temp = self._entity_aggregation(instances, labels, seq_b)
                        if len(seq_a) > 1:
                            temp2 = self._entity_aggregation(temp[0], temp[1], seq_a)
                            new_rel = (temp2[0], temp2[1], temp2[2], (temp[2][0]-temp2[3], temp[2][1]-temp2[3]))  # join_A, join_B
                        else:
                            new_rel = (temp[0], temp[1], seq_a[0], temp[2])  # A, join_B
                    else:
                        temp = self._entity_aggregation(instances, labels, seq_a)
                        new_rel = (temp[0], temp[1], temp[2], (seq_b[0][0]-temp[3], seq_b[0][1]-temp[3]))  # join_A, B
                    if switch_back:
                        new_rel = (new_rel[0], new_rel[1], new_rel[3], new_rel[2])  # 如果前方交换过，这里需要将关系指向再换回来
                    data = {
                        'name': rel['name'],
                        'pos_begin_1': new_rel[2][0],
                        'pos_end_1': new_rel[2][1],
                        'type_1': rel['type_1'].replace('Link-', ''),
                        'pos_begin_2': new_rel[3][0],
                        'pos_end_2': new_rel[3][1],
                        'type_2': rel['type_2'].replace('Link-', ''),
                        'sen': ' '.join(new_rel[0]),
                        'project_id': rel['project_id'],
                        'project_name': rel['project_name'],
                        'example_id': rel['example_id']
                    }
                    # print(data)
                    if data['example_id'] not in self.new_rel_json:
                        self.new_rel_json[data['example_id']] = []
                    self.new_rel_json[data['example_id']].append(data)
                else:  # 如果 A B 则直接进行添加
                    if rel['example_id'] not in self.new_rel_json:
                        self.new_rel_json[rel['example_id']] = []
                    self.new_rel_json[rel['example_id']].append(rel)

    def write_out(self):
        """
        将实体与关系的检查数据写出到 csv，用来让地学院的人检查
        将数据写入到 txt 与 json 文件 (这个文件是在 neo4j 中检查时要用到的)
        """
        headers = ['实体类型', '实体', '句子', '起始单词位置', '结束单词位置', '句子 id', '项目 id', '项目名称', '标注用户名']
        with open('./check_data/ins.csv', 'a', newline='', encoding='utf-8') as f:
            f_csv = csv.DictWriter(f, headers)
            f_csv.writeheader()
            f_csv.writerows(self.ins_rows)
        headers = ['关系名称', '实体 1', '实体 1 类型', '实体 2', '实体 2 类型', '句子', '实体 1 起始单词位置', '实体 1 结束单词位置', '实体 2 起始单词位置',
                   '实体 2 结束单词位置', '句子 id', '项目名称', '项目 id', '标注用户名']
        with open('./check_data/rel.csv', 'a', newline='', encoding='utf-8') as f:
            f_csv = csv.DictWriter(f, headers)
            f_csv.writeheader()
            f_csv.writerows(self.rel_rows)

        ins_txt = open('./raw_data/words.txt', 'a', encoding='utf-8')
        ins_lab_txt = open('./raw_data/tags.txt', 'a', encoding='utf-8')
        rel_txt = open('./raw_data/relations.txt', 'a', encoding='utf-8')
        check_use_data = []
        for values in self.new_rel_json.values():
            for value in values:
                token = value['sen'].split()
                relation = {  # 实际程序用
                    "token": token,
                    "h": {
                        "name": ' '.join(token[value['pos_begin_1']:value['pos_end_1']]),
                        "pos": [value['pos_begin_1'], value['pos_end_1']]
                    },
                    "t": {
                        "name": ' '.join(token[value['pos_begin_2']:value['pos_end_2']]),
                        "pos": [value['pos_begin_2'], value['pos_end_2']]
                    },
                    "relation": value['name']
                }
                relation2 = {  # neo4j 用
                    'token': token,
                    'h': {
                        'name': ' '.join(token[value['pos_begin_1']:value['pos_end_1']]),
                        'pos': [value['pos_begin_1'], value['pos_end_1']],
                        'type': value['type_1']
                    },
                    't': {
                        'name': ' '.join(token[value['pos_begin_2']:value['pos_end_2']]),
                        'pos': [value['pos_begin_2'], value['pos_end_2']],
                        'type': value['type_2']
                    },
                    'relation': value['name'],
                    'project': value['project_name'],
                    'example': ' '.join(token)
                }
                check_use_data.append(relation2.copy())
                rel_txt.write(str(relation))
                rel_txt.write('\n')
        with open('./check_data/relation.json', 'a', encoding='utf-8') as f:
            json.dump(check_use_data, f)
            f.close()
        for values in self.new_ins_json.values():  # 写入实体与标签
            for value in values:
                ins_txt.write(' '.join(value[0]))
                ins_txt.write('\n')
                ins_lab_txt.write(' '.join(value[1]))
                ins_lab_txt.write('\n')
        ins_txt.close()
        ins_lab_txt.close()
        rel_txt.close()

    def error_out(self):
        """
        将错误信息保存为文件
        """
        headers = ['负责用户名', '错误原因', '句子']
        with open('./check_data/error.csv', 'a', encoding='utf-8', newline='') as f:
            f_csv = csv.DictWriter(f, headers)
            f_csv.writeheader()
            f_csv.writerows(self.error)

    def link_check(self):
        """
        对link关机进行初始检查，查找出所有不正确的link标注
        """
        for key, values in self.rel_json.items():
            for rel in values:
                if rel['name'] == 'Link' and not ('Link' in rel['type_1'] and 'Link' in rel['type_2']):
                    print(rel['type_1'], rel['type_2'])
                    foo = {'句子': rel['sen'], '负责用户名': rel['username'], '错误原因': 'link 中不能出现普通标签，必须使用Link_前缀类型'}
                    print(foo)
                    self.error.append(foo)

    def run(self, project_id):
        self.get_sql_data(project_id)
        self.make_map()
        self.link_check()
        for key, values in self.ins_json.items():  # 对每个例子中的实体进行处理
            for ins in values:
                try:
                    if ins['type'].split('_')[0] == 'Link':  # 如果这个实体是一个连接实体
                        head = True
                        for rel in self.rel_json[key]:  # 首先遍历入度，判断其是不是一个 link 中的头实体
                            if rel['pos_begin_2'] == ins['pos_begin'] and rel['pos_end_2'] == ins['pos_end'] and rel['name'] == 'Link':  # 如果入度不为0，则不是头节点
                                head = False
                                break
                        if head:  # 如果是头节点则寻找整个关系链
                            self._dfs(key, (ins['pos_begin'], ins['pos_end']))
                            self.path_now = []
                except Exception as e:
                    print(e, '未找到合法的 link 路径: ', ins['username'], ins['sen'])
                    self.error.append({'句子': ins['sen'], '负责用户名': ins['username'], '错误原因': '单个实体不要使用带有Link的标签！未找到合法的 link 路径'})
                    self.path_now = []
            self.ins_conn_label(key)
            # print(self.ins_json[key])
            try:
                self.gen_new_ins_example(key)
                if key in self.rel_json:
                    self.gen_new_rel_example(key)  # 对于该条目的所有关系生成新的实例
            except Exception as err:
                print(err)
                e = str(err)
                e = e.replace(' ', '$', 3)
                e = e.replace('\'', '$', 4)
                e = e.replace(',', '$', 3)
                e = e.replace(' ', '@')
                e = e.replace('\'', '@').replace('$', ' ', 10)
                e = e.split()
                if len(e) > 1:
                    e[3] = e[3].replace('@', ' ')
                    # print(e)
                    self.error.append({'句子': e[3], '负责用户名': e[2], '错误原因': e[1]})
                else:
                    temp = self.rel_json[int(e[0])][0]
                    print(temp)
                    self.error.append({'句子': temp['sen'], '负责用户名': temp['username'], '错误原因': 'link 实体中标签类型不一致'})
        self.error_out()
        self.write_out()


if __name__ == '__main__':
    projects = [32, 31, 30, 34]
    for project in projects:
        a = DataGenerator()
        a.run(project)  # 生成数据
