from py2neo import Node, Graph
from itertools import combinations
import random
import statistics

loop_index = int(input("Enter the number of iterations: "))
result_array = []
for i in range(0, loop_index):
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
    f = open("Labels.csv", "r+")
    answers = f.readlines()
    answer_dic = {}
    for answer in answers:
        line_array = answer.split(",")
        answer_dic[line_array[0] + " " + line_array[1]] = int(line_array[2].strip())
    number_of_questions = 0

    while possibleCombinations:
        index = random.randint(0, len(possibleCombinations) - 1)
        s1 = str(possibleCombinations[index][0])
        s2 = str(possibleCombinations[index][1])

        result1 = graph.evaluate(check, s1=s1, s2=s2)
        result2 = graph.evaluate(check, s1=s2, s2=s1)
        if not (result1 or result2):
            answer = answer_dic[s1 + " " + s2]
            number_of_questions = number_of_questions + 1
            if answer == 1:
                graph.run(create, s1=s1, s2=s2)
            else:
                answer = answer_dic[s2 + " " + s1]
                number_of_questions = number_of_questions + 1
                if answer == 1:
                    graph.run(create, s1=s2, s2=s1)
        possibleCombinations.pop(index)

    result_array.append(number_of_questions)
print(result_array)
print("Standard Deviation:", statistics.stdev(result_array))
print("Mean:", statistics.mean(result_array))
print("Max:", max(result_array))
print("Min:", min(result_array))
