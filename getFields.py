import re

filename = "fichier.txt"
variables = {}
with open(filename, "r") as f:
    text = f.read()
    for match in re.findall(r"##(\w+):([\w\s+-]+)", text):
        variables[match[0]] = match[1]

print(variables)
