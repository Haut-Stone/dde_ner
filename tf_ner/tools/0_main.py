from DataGenerator import DataGenerator
from DataDivider import DataDivider
from tf_ner.data.dde.build_vocab import build_vocab
from tf_ner.data.dde.build_glove import build_glove

import os

if __name__ == '__main__':

    # 先删除之前的数据文件
    os.remove('./raw_data/tags.txt')
    os.remove('./raw_data/words.txt')
    os.remove('./raw_data/relations.txt')
    os.remove('./check_data/neo4j_use_relation.json')
    os.remove('./check_data/error.csv')
    os.remove('./check_data/all_ins.csv')
    os.remove('./check_data/all_rel.csv')

    # 对与需要生成的项目列表，生成数据
    projects = [32, 31, 30, 34]
    for project in projects:
        a = DataGenerator('C:\\Users\\sjh\\Desktop\\doccano\\doccano21@11@15.db')
        a.run(project)

    # 生成过后将所有的数据进行数据集划分
    DataDivider().divide_ins_data(5)  # 4:1划分

    # 进行词向量的生成
    # build_vocab()
    # build_glove()

    # 模型训练
    # train_dde

    # 结果分析
    # result_statistics
