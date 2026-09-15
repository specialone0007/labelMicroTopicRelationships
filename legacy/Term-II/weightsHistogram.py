import csv
from math import sqrt
import statistics

def zify(some_dict):
    arr = some_dict.values()
    sum_sq = x_bar = 0
    for index, val in enumerate(arr):
        x_bar += val
        sum_sq += val * val
    n = 1 + index
    x_bar *= 1.0/n
    std = sqrt(1.0 / index * sum_sq - (float(n) / index) * x_bar * x_bar)
    return {index_k: (v - x_bar) / std for index_k, v in some_dict.items()}


f = open("Microtopics.txt", "r+")
nodes = f.readlines()
for k in range(0, len(nodes)):
    nodes[k] = nodes[k].strip()

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

csv_name = "weightsHistogram.csv"
with open(csv_name, mode='w') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["Weight"])
    for weight in only_positive_weights.values():
        csv_writer.writerow([str(int(weight))])




