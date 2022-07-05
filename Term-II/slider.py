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

only_positive_weights_sorted = sorted(only_positive_weights.items(), key=lambda x: x[1])

only_positive_weights_sorted_normalized = []

increment = 1 / len(only_positive_weights_sorted)
normalized_weight = 0
for weight in only_positive_weights_sorted:
    weight_list = list(weight)
    weight_list[1] = normalized_weight
    normalized_weight += increment
    only_positive_weights_sorted_normalized.append(tuple(weight_list))

prerequisites_nodes = {}
for node in nodes:
    prerequisites_nodes[node] = []

for weight in only_positive_weights_sorted_normalized:
    microtopics = weight[0].split(",")
    microtopic_1 = microtopics[0]
    microtopic_2 = microtopics[1]
    prerequisites_nodes[microtopic_2].append({"name": microtopic_1, "weight": weight[1]})

frontendjson = []

for node in nodes:
    frontendjson.append(
        {"name": node,
         "weight": 0,
         "prerequisites": {"nodes": prerequisites_nodes[node],
                           "and_edges": [],
                           "or_edges": []
                           }
         }
    )
