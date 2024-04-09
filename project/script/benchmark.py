import sys
import yaml
from tqdm import tqdm
from medicine import MedicineData

sys.path.append('./src')

from knowledge import KnowledgeBase

class Benchmark(object):

    def __init__(self, path:str) -> None:
        self.read_ground_truth(path)

    def read_ground_truth(self, path:str) -> None:
        with open(path) as f:
            ground_truth = f.read().splitlines()
        self.medicine = []
        for entry in ground_truth:
            entry = entry.split(',')[1:]
            entry = [name for name in entry if name != '']
            self.medicine.append(entry)

    def entity_link(self, base:KnowledgeBase, threshold:float, distance) -> None:
        for i, entry in tqdm(enumerate(self.medicine), 
                             desc='entry', 
                             leave=False, 
                             total=len(self.medicine)):
            for j, mention in enumerate(entry):
                node, strsim = base.entity_link(mention, distance)
                entry[j] = node['label'] if strsim > threshold else 'unknown'
            self.medicine[i] = entry

    def save_ground_truth(self, path:str) -> None:
        with open(path, mode='w') as f:
            for entry in self.medicine:
                f.write(','.join(entry) + '\n')

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    base = KnowledgeBase(config['url'], config['usr'], config['passwd'])
    benchmark = Benchmark(config['test'])
    benchmark.entity_link(base, 0.7, MedicineData.jaccard_distance)
    benchmark.save_ground_truth(config['save'])