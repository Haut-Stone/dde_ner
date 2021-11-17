
class DataDivider:

    def __init__(self):
        pass

    @staticmethod
    def divide_ins_data():
        """
        按比例划分训练集与测试集, 划分实体与关系数据集
        """
        words_file = open('./raw_data/words.txt', 'r', encoding='utf-8')
        tags_file = open('./raw_data/tags.txt', 'r', encoding='utf-8')
        train_words_file = open('../data/dde/train.words.txt', 'w', encoding='utf-8')
        train_tags_file = open('../data/dde/train.tags.txt', 'w', encoding='utf-8')
        test_a_words_file = open('../data/dde/testa.words.txt', 'w', encoding='utf-8')
        test_a_tags_file = open('../data/dde/testa.tags.txt', 'w', encoding='utf-8')

        ins_data_line_count = 0
        can_not_use = 0
        counter = 0
        for i in range(ins_data_line_count):
            words_line = words_file.readline()
            tags_line = tags_file.readline()
            words = words_line.strip().split()
            tags = tags_line.strip().split()
            print(i + 1, len(words), len(tags))
            if len(words) != len(tags):
                can_not_use += 1
                print('用不了：', i + 1)
            else:
                counter = (counter + 1) % 5  # 4:1 划分
                if counter != 0:
                    train_words_file.write(words_line)
                    train_tags_file.write(tags_line)
                else:
                    test_a_words_file.write(words_line)
                    test_a_tags_file.write(tags_line)

        words_file.close()
        tags_file.close()
        test_a_tags_file.close()
        test_a_words_file.close()
        train_words_file.close()
        train_tags_file.close()
