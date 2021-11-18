from nltk.corpus import wordnet as wn
import json
import csv

# print(wn.synset('apatite.n.01').lemma_names())
json_data = json.load(open('./check_data/ins_set_data.json', encoding='utf-8'))


def data_filter(name):
    name1 = name.replace('Apatite', 'apatite')
    name1 = name1.replace('Apa - tites', 'apatite')
    name1 = name1.replace('Apatites', 'apatite')
    name1 = name1.replace('apatites', 'apatite')
    name1 = name1.replace('apa - tites', 'apatite')
    name1 = name1.replace('MORs', 'MOR')
    name1 = name1.replace('PCD forma - tion', 'PCD formation')
    name1 = name1.replace('PCDs', 'PCD')
    name1 = name1.replace('REEs', 'REE')
    name1 = name1.replace('W skarns', 'W skarn')
    name1 = name1.replace('magmatic arcs', 'magmatic arc')
    name1 = name1.replace('porphy - ries', 'porphyry')
    name1 = name1.replace('porphyries', 'porphyry')
    name1 = name1.replace('High', 'high')
    name1 = name1.replace('Low', 'low')
    name1 = name1.replace('car - bonatites', 'carbonatites')
    name1 = name1.replace('carbon - atites', 'carbonatites')
    name1 = name1.replace('high - est', 'highest')
    name1 = name1.replace('oxy - gen', 'oxygen')
    name1 = name1.replace('por - phyry', 'porphyry')
    name1 = name1.replace('unmineral - ized', 'unmineralized')
    name1 = name1.replace('low - est', 'lowest')
    name1 = name1.replace('( 87Sr / 86 Sr ) i', '( 87Sr / 86Sr ) i')
    name1 = name1.replace('Cu - Mo - related', 'Cu - Mo related')
    name1 = name1.replace('Cu - Mo– related', 'Cu - Mo related')
    name1 = name1.replace('Cu - Mo–related', 'Cu - Mo related')
    name1 = name1.replace('Juras - sic', 'Jurassic')
    name1 = name1.replace('JURASSIC', 'Jurassic')
    name1 = name1.replace('Mio - cene', 'Miocene')
    name1 = name1.replace('mag - mas', 'magmas')
    name1 = name1.replace('basalts', 'basalt')
    name1 = name1.replace('diorites', 'diorite')
    name1 = name1.replace('intrusions', 'intrusion')
    name1 = name1.replace('l ow e r c r u s t', 'lower crust')
    name1 = name1.replace('magmas', 'magma')
    name1 = name1.replace('magmatic suites', 'magmatic suite')
    name1 = name1.replace('brec - cia', 'breccia')
    name1 = name1.replace('deposits', 'deposit')
    name1 = name1.replace('pre - vious', 'previous')
    name1 = name1.replace('J u r a s s i c', 'Jurassic')
    name1 = name1.replace('Carbonate', 'carbonate')
    name1 = name1.replace('Carbonatites', 'carbonatites')
    name1 = name1.replace('Porphyry', 'porphyry')
    name1 = name1.replace('Cal - cium', 'Calcium')
    name1 = name1.replace('Zir - con', 'zircon')
    name1 = name1.replace('contents', 'content')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    # name1 = name1.replace('', '')
    return name1


rows_ins = []
ins_set = set()

for data in json_data:
    name = data_filter(data['name'])
    types = data['type']
    ins_set.add((name, types))

ls = list(ins_set)
for data in ls:
    line = [data[0], data[1]]
    rows_ins.append(line)

headers = ['name', 'type']
with open('./check_data/instance.csv', 'w', encoding='utf-8', newline='') as f:
    f_csv = csv.writer(f)
    f_csv.writerow(headers)
    f_csv.writerows(rows_ins)
