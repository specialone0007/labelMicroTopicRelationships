f = open("Microtopics.txt", "r+")
nodes = f.readlines()
for k in range(0, len(nodes)):
    nodes[k] = nodes[k].strip()

f = open("Labels.csv", "r+")
answers = f.readlines()
answer_dic = {}
for answer in answers:
    line_array = answer.split(",")
    answer_dic[line_array[0] + "," + line_array[1]] = int(line_array[2].strip())

f = open("Weights.txt", "r+")
weights_lines = f.readlines()
my_array = []
for line in weights_lines:
    for e in line.strip().split(" "):
        if e != "":
            my_array.append(float(e))

weights_dic = {}
for i in range(0, len(nodes)):
    for j in range(0, len(nodes)):
        weights_dic[nodes[i] + "," + nodes[j]] = my_array[j * 29 + i]

only_positive_weights = {}
for relation in weights_dic.keys():
    trial = relation.split(",")
    if trial[0] != trial[1]:
        if weights_dic[relation] > 0:
            only_positive_weights[relation] = weights_dic[relation]

only_positive_weights_sorted = sorted(only_positive_weights.items(), key=lambda x: x[1])
medium = len(only_positive_weights_sorted) // 2
prev_max = len(only_positive_weights_sorted) - 1
prev_min = 0
prev_medium = medium

guess_dic = {only_positive_weights_sorted[prev_max][0]: 1, only_positive_weights_sorted[prev_min][0]: 0,
             only_positive_weights_sorted[prev_min + 1][0]: 0, only_positive_weights_sorted[prev_max - 1][0]: 1}

total_iterations = 0

size = int(input("Please enter the step size: "))

for i in range(size):
    if medium == prev_max - 1:
        break
    prev_medium = medium
    answer_1 = answer_dic[only_positive_weights_sorted[medium - 1][0]]
    answer_2 = answer_dic[only_positive_weights_sorted[medium][0]]
    answer_3 = answer_dic[only_positive_weights_sorted[medium + 1][0]]

    guess_dic[only_positive_weights_sorted[medium - 1][0]] = answer_1
    guess_dic[only_positive_weights_sorted[medium][0]] = answer_2
    guess_dic[only_positive_weights_sorted[medium + 1][0]] = answer_3

    total = answer_1 + answer_2 + answer_3
    print("Step:", i + 1)
    print("Previous Min:", prev_min)
    print("Previous Max", prev_max)
    print("Medium:", medium)
    print("Medium Weight:", only_positive_weights_sorted[medium][1])
    print("Total prerequisites around medium:", total)
    print("******************************************")
    if total > 1:
        for k in range(medium + 2, prev_max):
            guess_dic[only_positive_weights_sorted[k][0]] = 1
        prev_max = medium
        medium = (prev_min + medium) // 2
    else:
        for k in range(prev_min + 2, medium - 1):
            guess_dic[only_positive_weights_sorted[k][0]] = 0
        prev_min = medium
        medium = (medium + prev_max) // 2
    total_iterations += 1

if total > 1:
    for k in range(prev_min + 2, prev_medium - 1):
        guess_dic[only_positive_weights_sorted[k][0]] = 0
else:
    for k in range(prev_medium + 1, prev_max - 1):
        guess_dic[only_positive_weights_sorted[k][0]] = 12

for e in answer_dic.keys():
    if e not in guess_dic.keys():
        guess_dic[e] = 0

correct_guess = 0
for e in answer_dic.keys():
    if answer_dic[e] == guess_dic[e]:
        correct_guess += 1
print("Accuracy Rate:", "{0:.3f}".format(correct_guess / len(answer_dic)), "Number of Questions:",
      total_iterations * 3)
