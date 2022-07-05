from py2neo import Node, Graph
import random
import statistics

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

query = """
MATCH (microtopic:Microtopic)
RETURN microtopic.name AS name
"""

loop_index = int(input("Enter the number of iterations: "))
result_array = []
for i in range(0, loop_index):
    graph = Graph('http://localhost:7474/', password="975310")
    graph.delete_all()

    f = open("Microtopics.txt", "r+")
    nodes = f.readlines()

    for n in nodes:
        graph.create(Node("Microtopic", name=n.strip()))

    possibleCombinations = {}
    for index in range(0, len(nodes)):
        my_array = []
        for iterator in range(index + 1, len(nodes)):
            my_array.append(nodes[iterator].strip())
        possibleCombinations[nodes[index].strip()] = my_array
    print(possibleCombinations)

    f = open("Labels.csv", "r+")
    answers = f.readlines()
    answer_dic = {}
    for answer in answers:
        line_array = answer.split(",")
        answer_dic[line_array[0] + " " + line_array[1]] = int(line_array[2].strip())
    number_of_questions = 0

    keys = []
    for key in possibleCombinations.keys():
        keys.append(key)

    while possibleCombinations:
        index = random.randint(0, len(keys) - 1)
        s1 = keys[index]
        keys.pop(index)
        possible_array = possibleCombinations[s1]
        if possible_array:
            for s2 in possible_array:
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
        possibleCombinations.pop(s1)
    result_array.append(number_of_questions)
print(result_array)
print("Standard Deviation:", statistics.stdev(result_array))
print("Mean:", statistics.mean(result_array))
print("Max:", max(result_array))
print("Min:", min(result_array))


