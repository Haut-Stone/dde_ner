from DataGenerator import DataGenerator
from DataDivider import DataDivider
import os

if __name__ == '__main__':
    # todo 累了今天先不写啦，明天完善下整体的全自动数据生成流程。
    projects = [32, 31, 30, 34]
    for project in projects:
        a = DataGenerator()
        a.run(project)  # 生成数据
    divider = DataDivider()
    divider.divide_ins_data()
