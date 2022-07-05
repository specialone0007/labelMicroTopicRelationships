from py2neo import Node, Graph
import random

f = open("Labels.csv", "r+")
answers = f.readlines()
answer_dic = {}
for answer in answers:
    line_array = answer.split(",")
    answer_dic[line_array[0] + " " + line_array[1]] = int(line_array[2].strip())

f = open("Weights.txt", "r+")
weights_lines = f.readlines()
my_array = []
for line in weights_lines:
    for e in line.strip().split(" "):
        if e != "":
            my_array.append(float(e))

f = open("Microtopics.txt", "r+")
nodes = f.readlines()
for k in range(0, len(nodes)):
    nodes[k] = nodes[k].strip()
weights_dic = {}
for i in range(0, len(nodes)):
    for j in range(0, len(nodes)):
        weights_dic[nodes[i] + " " + nodes[j]] = my_array[j * 29 + i]

threshold = int(input("Enter a threshold: "))

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

graph = Graph('http://localhost:7474/', password="975310")
graph.delete_all()

for n in nodes:
    graph.create(Node("Microtopic", name=n.strip()))

possibleCombinations = {}
for index in range(0, len(nodes)):
    my_array = []
    for iterator in range(index + 1, len(nodes)):
        my_array.append(nodes[iterator])
    possibleCombinations[nodes[index]] = my_array

number_of_questions = 0

keys = []
for key in possibleCombinations.keys():
    keys.append(key)

result_dic = {}
print(possibleCombinations.keys())
while possibleCombinations:
    index = random.randint(0, len(keys) - 1)
    s1 = keys[index]
    keys.pop(index)
    possible_array = possibleCombinations[s1]
    if possible_array:
        for s2 in possible_array:
            result1 = graph.evaluate(check, s1=s1, s2=s2)
            result2 = graph.evaluate(check, s1=s2, s2=s1)
            if result1:
                result_dic[s1 + " " + s2] = 1
            elif result2:
                result_dic[s2 + " " + s1] = 1
            if not (result1 or result2):
                weight = int(weights_dic[s1 + " " + s2])
                if weight >= threshold:
                    graph.run(create, s1=s1, s2=s2)
                    result_dic[s1 + " " + s2] = 1
                elif (-weight) >= threshold:
                    graph.run(create, s1=s2, s2=s1)
                    result_dic[s2 + " " + s1] = 1
                else:  # weight != 0:
                    if weight >= 0:
                        answer = answer_dic[s1 + " " + s2]
                        number_of_questions = number_of_questions + 1
                        if answer == 1:
                            graph.run(create, s1=s1, s2=s2)
                            result_dic[s1 + " " + s2] = 1
                    elif weight <= 0:
                        answer = answer_dic[s2 + " " + s1]
                        number_of_questions = number_of_questions + 1
                        if answer == 1:
                            graph.run(create, s1=s2, s2=s1)
                            result_dic[s2 + " " + s1] = 1
                    else:
                        answer = answer_dic[s1 + " " + s2]
                        number_of_questions = number_of_questions + 1
                        if answer == 1:
                            graph.run(create, s1=s1, s2=s2)
                            result_dic[s1 + " " + s2] = 1
                        else:
                            answer = answer_dic[s2 + " " + s1]
                            number_of_questions = number_of_questions + 1
                            if answer == 1:
                                graph.run(create, s1=s2, s2=s1)
                                result_dic[s2 + " " + s1] = 1
    possibleCombinations.pop(s1)
for e in answer_dic.keys():
    if e not in result_dic.keys():
        result_dic[e] = 0
correct_guess = 0
for e in answer_dic.keys():
    if answer_dic[e] == result_dic[e]:
        correct_guess += 1
    else:
        print("Wrong Guess:", e, result_dic[e])
print("Accuracy Rate: ", correct_guess / len(answer_dic))
print("Number of Questions: ", number_of_questions)
