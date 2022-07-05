from py2neo import Node, Graph
from itertools import combinations
import random

graph = Graph('http://localhost:7474/', password="sayfriendandenter")
graph.delete_all()

f = open("Microtopics.txt", "r+")
nodes = f.readlines()

for n in nodes:
	graph.create(Node("Microtopic", name=n.strip()))

nodes = []

query = """
MATCH (microtopic:Microtopic)
RETURN microtopic.name AS name
"""

data = graph.run(query)

for d in data:
	nodes.append(d[0])
print(nodes)

possibleCombinations = list(combinations(nodes, 2))

check = """
		MATCH (a:Microtopic),(b:Microtopic)
		WHERE a.name = {s1} AND b.name = {s2} AND (a)-[*]->(b)
		RETURN a
		"""

create = """
		MATCH (a:Microtopic),(b:Microtopic)
		WHERE a.name = {s1} AND b.name = {s2}
		CREATE (a)-[r:PREREQUISITE_OF]->(b)
		"""
f = open("Labels.csv", "w+")


def write_label(string1, string2, positive):
	f.write(string1 + "," + string2 + "," + positive + "\n")
	f.write(string2 + "," + string1 + "," + "0" + "\n")


while possibleCombinations:
	index = random.randint(0, len(possibleCombinations) - 1)
	s1 = str(possibleCombinations[index][0])
	s2 = str(possibleCombinations[index][1])

	result1 = graph.evaluate(check, s1=s1, s2=s2)
	result2 = graph.evaluate(check, s1=s2, s2=s1)
	if not (result1 or result2):
		answer = input("Is " + s1 + " prerequisite of " + s2 + "?")
		if answer == "yes":
			graph.run(create, s1=s1, s2=s2)
			write_label(s1, s2, "1")
		else:
			answer = input("Is " + s2 + " prerequisite of " + s1 + "?")
			if answer == "yes":
				graph.run(create, s1=s2, s2=s1)
				write_label(s2, s1, "1")
			else:
				write_label(s1, s2, "0")
	else:
		if result1:
			write_label(s1, s2, "1")
		else:
			write_label(s2, s1, "1")

	possibleCombinations.pop(index)

