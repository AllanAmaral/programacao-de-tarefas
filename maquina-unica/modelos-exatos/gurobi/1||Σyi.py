import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("1||Σyi")

model.setParam("TimeLimit", 600) # limite de execução (segundos)

# Dados
df = pd.read_csv("arquivo.csv", sep=";")

tarefas = df["tarefa"].to_list()
p = df.set_index("tarefa")["pi"].to_dict()
d = df.set_index("tarefa")["di"].to_dict()

M = 600 # parâmetro Big-M

# Variáveis
C = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ci")
X = model.addVars(tarefas, tarefas, vtype=GRB.BINARY, name="Xij")
T = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ti")
y = model.addVars(tarefas, vtype=GRB.BINARY, name="yi")

# Função objetivo
model.setObjective(gp.quicksum(y[i] for i in tarefas if i != 0), GRB.MINIMIZE)

# Restrições
# (1) e (2): cada tarefa tem exatamente um predecessor e um sucessor
for i in tarefas:
    model.addConstr(gp.quicksum(X[i, j] for j in tarefas if j != i) == 1)

for j in tarefas:
    model.addConstr(gp.quicksum(X[i, j] for i in tarefas if i != j) == 1)

# (3): restrição de precedência
for i in tarefas:
    for j in tarefas:
        if i != j and j != 0: # tarefa fictícia não pode ser sucessora
            model.addConstr(C[j] >= C[i] - M + (p[j] + M) * X[i, j])

# (4): fixação da tarefa fictícia 0 como início do cronograma
model.addConstr(C[0] == 0)

# definição do atraso e ativação da variável binária de atraso
for i in tarefas:
    if i != 0:
        model.addConstr(T[i] >= C[i] - d[i])

for i in tarefas:
    if i != 0:
        model.addConstr(T[i] <= M * y[i])

# Otimização
model.optimize()

# Impressão dos resultados
if model.Status == GRB.OPTIMAL:
    print("\nTarefas que atrasaram:\n")
    for i in tarefas:
        if i != 0:
            if T[i].X > 0:
                print(f"Tarefa {i}")
    print(f"\nNúmero de tarefas atrasadas = {model.ObjVal}")

elif model.SolCount > 0:
    print("\nTarefas que atrasaram:\n")
    for i in tarefas:
        if i != 0:
            if T[i].X > 0:
                print(f"Tarefa {i}")
    print("\nO modelo encontrou uma solução viável, mas não foi possível comprovar a otimalidade.")
    print(f"Número de tarefas atrasadas = {model.ObjVal}")

else:
    print("Nenhuma solução viável encontrada.")

# Referências
# ARENALES, Marcos Nereu et al. Pesquisa Operacional. Rio de Janeiro: Elsevier, 2007.
