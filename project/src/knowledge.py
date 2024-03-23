import sys
import yaml
import numpy as np
from py2neo import Graph
from py2neo import Node
from py2neo import Subgraph
from py2neo import NodeMatcher
from py2neo import Relationship

class KnowledgeBase(object):

    def __init__(self, url:str, usr:str, passwd:str) -> None:
        self.graph = Graph(url, auth=(usr, passwd))

    def create_subgraph(self, subgraph:Subgraph) -> None:
        transaction = self.graph.begin()
        transaction.create(subgraph)
        self.graph.commit(transaction)

    def entity_link(self, mention:str, distance) -> tuple[Node, float]:
        matcher = NodeMatcher(self.graph)
        nodes   = matcher.match('Medicine').all()
        if len(nodes) == 0:
            return None, float('-inf')
        measure = lambda n: distance(n, mention)
        strsim  = [measure(node['label']) for node in nodes]
        index   = np.argmax(strsim)
        return nodes[index], strsim[index]

    def clear_node(self, type:str) -> None:
        cypher = f'MATCH (n:{type}) DETACH DELETE n'
        self.graph.run(cypher)

if __name__ == '__main__':
    with open(sys.argv[1]) as stream:
        config = yaml.load(stream, yaml.Loader)
    base = KnowledgeBase(config['url'], config['usr'], config['passwd'])
    base.graph.run(r'MATCH (n:Medicine{label: $m}) RETURN n.indication', m='代文')