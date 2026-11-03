"""Small RDF triple example, separate from vector search."""
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF

EX = Namespace('https://example.org/semantic-search/')
def example_graph():
    graph=Graph(); graph.bind('ex',EX)
    graph.add((EX.Prateek,EX.studiesAt,EX.SRM))
    graph.add((EX.SRM,RDF.type,EX.University))
    return graph

if __name__=='__main__':
    print(example_graph().serialize(format='turtle'))
