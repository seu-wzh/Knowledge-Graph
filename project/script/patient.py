import os
import sys
import yaml
import time
import random
import numpy as np
import pandas as pd
from tqdm import tqdm
from py2neo import Node
from py2neo import Relationship
from py2neo import Subgraph
from py2neo import NodeMatcher
from medicine import MedicineData

sys.path.append('./src')

from knowledge import KnowledgeBase

class PatientData(object):

    def __init__(self, path:str) -> None:
        self.data = pd.read_excel(path)

    def load_medicine_dict(self, path:str) -> None:
        with open(path) as f:
            self.medicine = f.read().splitlines()

    def extract_medicine(self, refine_nbr:int) -> None:
        try:
            count = 0
            correct = 0
            for i, row in enumerate(random.sample(range(len(self.data)), len(self.data))):
                diagnosis = self.data['出院带药'][row]
                if pd.isna(diagnosis):
                    continue;
                medicine_list = []
                for medicine in self.medicine:
                    if diagnosis.find(medicine) != -1:
                        medicine_list.append(medicine)
                count += 1
                if len(medicine_list) < refine_nbr:
                    print('[INFO] accuracy rate til now {}%'.format(correct / count * 100))
                    print('[INFO] tuple in record: {}'.format(i))
                    print('[INFO] <row {}> diagnosis: {}'.format(row, diagnosis))
                    print('[INFO] medicine_list: {}'.format(medicine_list))
                    new_medicine = input('[INFO] enter new medicine: ').split(',')
                    if '' in new_medicine:
                        new_medicine.remove('')
                    if len(new_medicine) == 0:
                        correct += 1
                    self.medicine.extend(new_medicine)
                    os.system('clear')
                else:
                    correct += 1
        except KeyboardInterrupt:
            print('start to quit script')

    def recognize_medicine(self):
        medicine_category = []
        for diagnosis in tqdm(self.data['出院带药'], desc='entry', leave=False):
            if pd.isna(diagnosis):
                medicine_category.append(pd.NA)
                continue
            medicine_list = []
            for medicine in self.medicine:
                if diagnosis.find(medicine) != -1:
                    medicine_list.append(medicine)
            medicine_category.append(','.join(medicine_list) if len(medicine_list) != 0 else pd.NA)
        self.data.insert(self.data.shape[1], '带药列表', medicine_category)

    def save_data_as(self, path:str) -> None:
        self.data.to_excel(path)

    def save_dict_as(self, path:str) -> None:
        with open(path, 'w') as f:
            for medicine in self.medicine:
                f.write(f'{medicine}\n')
    
    def medicine_link(self, base:KnowledgeBase, medicine:list, distance, threshold:float):
        nodes = []
        for mention in medicine:
            node, strsim = base.entity_link(mention, distance)
            if strsim >= threshold:
                nodes.append(node)
        return nodes

    def extract_patient_node(self, base:KnowledgeBase, distance, threshold:float) -> None:
        checknull = lambda x: None if pd.isna(x) else x
        def admission_diagnosis(entry):
            admdiag = checknull(entry)
            if admdiag is None: return None
            if '酸中毒' in admdiag: return '糖尿病酮症酸中毒'
            if '糖尿病酮症' in admdiag: return '糖尿病酮症'
            if '1型糖尿病' in admdiag: return '1型糖尿病'
            if '2型糖尿病' in admdiag: return '2型糖尿病'
            return '糖尿病'
        # ---------------------------------------------------------------------------- #
        nodes = []
        relations = []
        for index, entry in tqdm(self.data.iterrows(), leave=False, total=self.data.shape[0]):
            node = Node('Patient', 
                        id=entry['id'], 
                        性别=['男', '女'][entry['性别（男1女2） '] - 1], 
                        入院诊断=admission_diagnosis(entry['入院诊断 数值 ']), 
                        出院诊断=entry['出院诊断（先联）'], 
                        入院体重=checknull(entry['入院体重指数 数值 ']), 
                        收缩压=checknull(entry['入院收缩压']), 
                        舒张压=checknull(entry['入院舒张压']), 
                        腰围=checknull(entry['入院腰围 数值 ']), 
                        导出年龄=entry['导出年龄'], 
                        发病年龄=entry['发病年龄'], 
                        空腹胰岛素=checknull(entry['胰岛素-空腹 数值']), 
                        餐后30胰岛素=checknull(entry['胰岛素-餐后30 数值']), 
                        餐后60胰岛素=checknull(entry['胰岛素-餐后60 数值']), 
                        餐后120胰岛素=checknull(entry['胰岛素-餐后120 数值']), 
                        空腹C肽=checknull(entry['C-肽-空腹 数值']), 
                        餐后30C肽=checknull(entry['C-肽-餐后30 数值']), 
                        餐后60C肽=checknull(entry['C-肽-餐后30 数值']), 
                        餐后120C肽=checknull(entry['C-肽-餐后120 数值']), 
                        糖化血红蛋白=checknull(entry['糖化血红蛋白 数值']), 
                        谷丙转氨酶=checknull(entry['谷丙转氨酶 数值']), 
                        谷草转氨酶=checknull(entry['谷草转氨酶 数值']), 
                        碱性磷酸酶=checknull(entry['碱性磷酸酶 数值']), 
                        谷酰转肽酶=checknull(entry['谷酰转肽酶 数值']), 
                        总胆红素=checknull(entry['总胆红素 数值']), 
                        直接胆红素=checknull(entry['直接胆红素 数值']), 
                        总胆汁酸=checknull(entry['总胆汁酸 数值']), 
                        尿素氮=checknull(entry['尿素氮 数值']), 
                        肌酐=checknull(entry['肌酐 数值']), 
                        尿酸=checknull(entry['尿酸 数值']), 
                        甘油三酯=checknull(entry['甘油三酯 数值']), 
                        胆固醇=checknull(entry['胆固醇 数值']), 
                        H胆固醇=checknull(entry['H-胆固醇 数值']), 
                        L胆固醇=checknull(entry['L-胆固醇 数值']), 
                        载脂蛋白A=checknull(entry['载脂蛋白AⅠ 数值']), 
                        脂蛋白a=checknull(entry['脂蛋白(a) 数值']), 
                        载脂蛋白B=checknull(entry['载脂蛋白B 数值']), 
                        尿微量白蛋白=checknull(entry['尿微量白蛋白 数值']), 
                        促甲状腺激素=checknull(entry['促甲状腺激素 数值']), 
                        游离三碘甲状腺原氨酸=checknull(entry['游离三碘甲状腺原氨酸 数值']), 
                        游离甲状腺素=checknull(entry['游离甲状腺素 数值']), 
                        甲状腺球蛋白抗体=checknull(entry['甲状腺球蛋白抗体 数值']), 
                        抗甲状腺过氧化酶抗体=checknull(entry['抗甲状腺过氧化酶抗体 数值']), 
                        促甲状腺素受体抗体=checknull(entry['促甲状腺素受体抗体 数值']), 
                        孕酮=checknull(entry['孕酮 数值']), 
                        雌二醇=checknull(entry['雌二醇 数值']), 
                        泌乳素=checknull(entry['泌乳素 数值']), 
                        总睾酮=checknull(entry['总睾酮 数值']), 
                        硫酸去氢表雄酮=checknull(entry['硫酸去氢表雄酮 数值']), 
                        性激素结合蛋白=checknull(entry['性激素结合蛋白 数值']), 
                        血清骨钙素=checknull(entry['血清骨钙素测定 数值']), 
                        血清胶原羟末端肽=checknull(entry['血清I型胶原羟末端肽β特殊序列测定 数值']), 
                        血清胶原氨基末端肽=checknull(entry['血清总I型胶原氨基末端肽测定 数值']), 
                        羟基维生素D=checknull(entry['25-羟基维生素D 数值']), 
                        葡萄糖=checknull(entry['葡萄糖 数值']), 
                        葡萄糖餐后0_5=checknull(entry['葡萄糖(餐后0.5h) 数值']), 
                        葡萄糖餐后1=checknull(entry['葡萄糖(餐后1h) 数值']), 
                        葡萄糖餐后2=checknull(entry['葡萄糖(餐后2h) 数值']), 
                        尿微量白蛋白_肌酐=checknull(entry['尿微量白蛋白/肌酐 数值']), 
                        eGFR_MDRD=checknull(entry['eGFR(MDRD) 数值']), 
                        甲胎蛋白=checknull(entry['甲胎蛋白 数值']), 
                        癌胚抗原=checknull(entry['癌胚抗原 数值']), 
                        糖类抗原125=checknull(entry['糖类抗原125 数值']), 
                        糖类抗原15_3=checknull(entry['糖类抗原15-3 数值']), 
                        糖类抗原19_9=checknull(entry['糖类抗原19-9 数值']), 
                        糖类抗原72_4=checknull(entry['糖类抗原72-4 数值']), 
                        糖类抗原242=checknull(entry['糖类抗原242 数值']), 
                        非小细胞肺癌相关抗原21_1=checknull(entry['非小细胞肺癌相关抗原21-1 数值']), 
                        神经元特异性烯醇化酶=checknull(entry['神经元特异性烯醇化酶 数值']), 
                        游离前列腺特异性抗原=checknull(entry['游离前列腺特异性抗原 数值']), 
                        总前列腺特异性抗原=checknull(entry['总前列腺特异性抗原 数值']), 
                        铁蛋白=checknull(entry['铁蛋白 数值']), 
                        抗谷氨酸脱羧酶抗体=checknull(entry['抗谷氨酸脱羧酶抗体(GAD-Ab) 数值']), 
                        胰岛细胞抗体=checknull(entry['胰岛细胞抗体 数值']), 
                        抗胰岛素抗体=checknull(entry['抗胰岛素抗体(IAA) 数值']), 
                        妊娠=bool(entry['妊娠']), 
                        癌症=bool(entry['癌症']), 
                        感染=bool(entry['感染']), 
                        糖尿病酮症=bool(entry['糖尿病酮症']), 
                        糖尿病视网膜病变=bool(entry['糖尿病视网膜病变']), 
                        糖尿病肾病=bool(entry['糖尿病肾病']), 
                        糖尿病周围神经病变=bool(entry['糖尿病周围神经病变']), 
                        下肢动脉病变=bool(entry['下肢动脉病变']), 
                        颈动脉病变=bool(entry['颈动脉病变']), 
                        脑血管病=bool(entry['脑血管病']), 
                        冠心病=bool(entry['冠心病']), 
                        高血压病=bool(entry['高血压病']))
            nodes.append(node)
            medicine = [] if pd.isna(entry['带药列表']) else entry['带药列表'].split(',')
            medicine = self.medicine_link(base, medicine, distance, threshold)
            for medicine_node in medicine:
                relations.append(Relationship(node, 'use', medicine_node))
        base.create_subgraph(Subgraph(nodes, relations))

    def data_cleaning(self) -> None:
        def funct(value):
            if type(value) == str:
                try:
                    if value[0] in ['<', '>']:
                        return float(value[1:])
                    return float(value)
                except:
                    return float('nan')
            return value
        for column in self.data.columns[8:76]:
            df = self.data[column]
            if df.isna().any():
                df = df.apply(funct)
                self.data[column] = df.fillna(df.median())

    def vectorize(self) -> np.ndarray:
        return self.data.iloc[:, 8:76].to_numpy()

    def extract_used_medicine(self, base:KnowledgeBase, distance, threshold:float) -> None:
        matcher = NodeMatcher(base.graph)
        relations = []
        for index, entry in tqdm(self.data.iterrows(), leave=False, total=self.data.shape[0]):
            node = matcher.match('Patient', id=entry['id']).first()
            medicine = [] if pd.isna(entry['带药列表']) else entry['带药列表'].split(',')
            medicine = self.medicine_link(base, medicine, distance, threshold)
            for medicine_node in medicine:
                relations.append(Relationship(node, 'use', medicine_node))
        base.create_subgraph(Subgraph(relationships=relations))

    def modify_node_properties(self, base:KnowledgeBase, funct) -> None:
        matcher = NodeMatcher(base.graph)
        for index, entry in tqdm(self.data.iterrows(), leave=False, total=self.data.shape[0]):
            node = matcher.match('Patient', id=entry['id']).first()
            funct(base, node, entry)

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    random.seed(int(time.time()))
    base = KnowledgeBase(config['url'], config['usr'], config['passwd'])
    data = PatientData(config['data_copy'])

    # base.clear_node('Patient')

    # data.extract_patient_node(base, MedicineData.jaccard_distance, 0.7)
    # data.extract_used_medicine(base, MedicineData.jaccard_distance, 0.7)

    # data.load_medicine_dict(config['dict'])
    # data.extract_medicine(config['refine'])
    # data.recognize_medicine()
    # data.save_data_as(config['data_copy'])
    # data.save_dict_as(config['dict_copy'])

    data.data_cleaning()
    np.save(config['vector'], data.vectorize())