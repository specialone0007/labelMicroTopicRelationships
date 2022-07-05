import csv
f = open("Microtopics.txt", "r+")
nodes = f.readlines()
for k in range(0, len(nodes)):
    nodes[k] = nodes[k].strip()

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

weights_dic = {}
for i in range(0, len(nodes)):
    for j in range(0, len(nodes)):
        weights_dic[nodes[i] + " " + nodes[j]] = my_array[j * 29 + i]

only_positive_weights = {}
for relation in weights_dic.keys():
    if weights_dic[relation] > 0:
        only_positive_weights[relation] = weights_dic[relation]

upper_limit = int(input("Enter an upper limit for weights: "))
lower_limit = int(input("Enter an lower limit for weights: "))
print("Number of positive edges:", len(only_positive_weights))


choice = int(input("Vary Upper(1) or Lower(0) Limit(): "))
csv_data = []
csv_name = str(lower_limit) + "-" + str(upper_limit) + "_"

if choice == 1:
    csv_name += "vary_upper.csv"
    for upper in range(upper_limit, lower_limit, -100):
        result_dic = {}
        number_of_questions = 0
        for relation in only_positive_weights:
            if only_positive_weights[relation] > upper:
                result_dic[relation] = 1
            elif only_positive_weights[relation] < lower_limit:
                result_dic[relation] = 0
            else:
                result_dic[relation] = answer_dic[relation]
                number_of_questions += 1
        for e in answer_dic.keys():
            if e not in result_dic.keys():
                result_dic[e] = 0
        correct_guess = 0
        for e in answer_dic.keys():
            if answer_dic[e] == result_dic[e]:
                correct_guess += 1
        print("For thresholds:", lower_limit, "-", upper, "-->", "Accuracy Rate: ", "{0:.3f}".
              format(correct_guess / len(answer_dic)), "Number of Questions: ", number_of_questions)

        empty_array = [str(lower_limit), str(upper), str(correct_guess / len(answer_dic)), str(number_of_questions)]
        csv_data.append(empty_array)
if choice == 0:
    csv_name += "vary_lower.csv"
    for lower in range(lower_limit, upper_limit, 100):
        result_dic = {}
        number_of_questions = 0
        for relation in only_positive_weights:
            if only_positive_weights[relation] > upper_limit:
                result_dic[relation] = 1
            elif only_positive_weights[relation] < lower:
                result_dic[relation] = 0
            else:
                result_dic[relation] = answer_dic[relation]
                number_of_questions += 1
        for e in answer_dic.keys():
            if e not in result_dic.keys():
                result_dic[e] = 0
        correct_guess = 0
        for e in answer_dic.keys():
            if answer_dic[e] == result_dic[e]:
                correct_guess += 1
        print("For thresholds:", lower, "-", upper_limit, "-->", "Accuracy Rate: ", "{0:.3f}".
              format(correct_guess / len(answer_dic)), "Number of Questions: ", number_of_questions)

        empty_array = [str(lower), str(upper_limit), str(correct_guess / len(answer_dic)), str(number_of_questions)]
        csv_data.append(empty_array)

with open(csv_name, mode='w') as csv_file:
    csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(["Lower Threshold", "Upper Threshold", "Accuracy Rate", "Number of Questions"])
    for i in range(0, len(csv_data)):
        csv_writer.writerow(csv_data[i])
