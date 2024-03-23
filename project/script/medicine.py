import re
import sys
import yaml
import Levenshtein
import numpy as np
import pandas as pd
from py2neo import Graph
from py2neo import Node
from py2neo import Relationship
from py2neo import Subgraph
from py2neo import NodeMatcher
from py2neo import RelationshipMatcher

sys.path.append('./src')

from knowledge import KnowledgeBase

class MedicineData(object):

    def __init__(self) -> None:
        self.pattern = re.compile('^(.*)[(（](.*)[)）]$')

    def extract_from_table(self, table:pd.DataFrame, base:KnowledgeBase) -> None:
        nodes = []
        relations = []
        for mention, specs in zip(table['药 品 名 称'], table['规   格']):
            if pd.isna(specs):
                continue
            label, alias = self.pattern.search(mention).groups()
            label = Node('Medicine', label=label)
            alias = Node('Medicine', label=alias)
            relation = Relationship(label, 'sameAs', alias)
            nodes.append(label)
            nodes.append(alias)
            relations.append(relation)
        base.create_subgraph(Subgraph(nodes, relations))

    @staticmethod
    def edit_distance(a:str, b:str) -> int:
        return -Levenshtein.distance(a, b)

    @staticmethod
    def editi_distance(a:str, b:str) -> float:
        return -(1 - Levenshtein.ratio(a, b)) * (len(a) + len(b))

    @staticmethod
    def jaccard_distance(a:str, b:str) -> float:
        a = set(a)
        b = set(b)
        return len(a & b) / len(a | b)

    def extract_from_alias(self, alias_map:list, base:KnowledgeBase, threshold:float, distance) -> None:
        relations = []
        matcher = RelationshipMatcher(base.graph)
        for label, alias in alias_map:
            nodeA, strsim = base.entity_link(label, distance)
            if strsim < threshold:
                nodeA = Node('Medicine', label=label)
                base.graph.create(nodeA)
            nodeB, strsim = base.entity_link(alias, distance)
            if strsim < threshold:
                nodeB = Node('Medicine', label=alias)
                base.graph.create(nodeB)
            if not matcher.match((nodeA, nodeB), 'sameAs').exists() and\
               not matcher.match((nodeB, nodeA), 'sameAs').exists():
                relations.append(Relationship(nodeA, 'sameAs', nodeB))
        base.create_subgraph(Subgraph(relationships=relations))

    def extract_from_text(self, text:list, base:KnowledgeBase, threshold:float, distance) -> None:
        nodes = []
        for mention in text:
            strsim = base.entity_link(mention, distance)[1]
            if strsim < threshold:
                nodes.append(Node('Medicine', label=mention))
        base.create_subgraph(Subgraph(nodes=nodes))

    def __import_indication__(self, base:KnowledgeBase, label:str, indication:str) -> None:
        cypher = r'MATCH (n:Medicine{label: $m}) RETURN n.indication IS NOT NULL'
        if base.graph.run(cypher, m=label).evaluate():
            return
        cypher = r'MATCH (n:Medicine {label: $m}) SET n.indication = $i'
        base.graph.run(cypher, m=label, i=indication)
        cypher = r'MATCH (:Medicine {label: $m})-[:sameAs]-(n:Medicine) RETURN n.label'
        cursor = base.graph.run(cypher, m=label)
        for label in cursor:
            self.__import_indication__(base, label[0], indication)

    def import_indication(self, table:pd.DataFrame, base:KnowledgeBase) -> None:
        for label, indication in zip(table['medicine'], table['indication']):
            self.__import_indication__(base, label, indication)

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    with open(config['dict']) as f:
        text = f.read().splitlines()
    with open(config['alias']) as f:
        alias = f.read().splitlines()
        alias = [tuple(a.split(',')) for a in alias]

    base = KnowledgeBase(config['url'], config['usr'], config['passwd'])

    medicine = MedicineData()

    # base.clear_node('Medicine')

    # medicine.extract_from_table(pd.read_excel(config['table']), base)

    # distance = MedicineData.jaccard_distance
    # medicine.extract_from_alias(alias, base, 1, distance)
    # medicine.extract_from_text(text, base, 0.7, distance)

    # medicine.import_indication(pd.read_excel(config['indication']), base)