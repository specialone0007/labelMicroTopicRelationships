import operator

f = open("Microtopics.txt", "r+")
lines = f.readlines()

in_degree = {}
possibleCombinations = []

for i in range(0, len(lines)):
    in_degree[lines[i].strip()] = 0
    for k in range(i + 1, len(lines)):
        possibleCombinations.append(lines[i].strip() + "," + lines[k].strip())

f = open("Relationships.txt", "r+")

writer = open("Labels.csv", "w+")
lines = f.readlines()
current_topic = ""

for line in lines:
    fixed_line = line.replace("*", "").strip()
    if "*" in line:
        current_topic = fixed_line
    else:
        in_degree[current_topic] += 1
        to_be_written1 = fixed_line + "," + current_topic
        to_be_written2 = current_topic + "," + fixed_line
        writer.write(to_be_written1 + ",1\n")
        writer.write(to_be_written2 + ",0\n")

        if to_be_written1 in possibleCombinations:
            possibleCombinations.remove(to_be_written1)
        if to_be_written2 in possibleCombinations:
            possibleCombinations.remove(to_be_written2)

while possibleCombinations:
    to_be_written = possibleCombinations[0]
    possibleCombinations.remove(to_be_written)
    writer.write(to_be_written + ",0\n")
    my_array = to_be_written.split(",")
    writer.write(my_array[1] + "," + my_array[0] + ",0\n")

sorted_in_degree = sorted(in_degree.items(), key=operator.itemgetter(1), reverse=True)
print("In-degree Sorted: ")
writer = open("advanced_to_basic.txt", "+w")
for element in sorted_in_degree:
    row = str(element).replace("(", "").replace(")", "").replace("'", "").split(",")
    print(element)
    writer.write(row[0] + "\n")

