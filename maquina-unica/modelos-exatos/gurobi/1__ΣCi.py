import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("1||ΣCi")

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

# Função objetivo
model.setObjective(gp.quicksum(C[i] for i in tarefas if i != 0), GRB.MINIMIZE)

# Restrições
# s(1) e s(2): cada tarefa tem exatamente um predecessor e um sucessor
for i in tarefas:
    model.addConstr(gp.quicksum(X[i, j] for j in tarefas if j != i) == 1)

for j in tarefas:
    model.addConstr(gp.quicksum(X[i, j] for i in tarefas if i != j) == 1)

# s(3): restrição de precedência
for i in tarefas:
    for j in tarefas:
        if i != j and j != 0: # tarefa fictícia não pode ser sucessora
            model.addConstr(C[j] >= C[i] - M + (p[j] + M) * X[i, j])

# s(4): fixação da tarefa fictícia 0 como início do cronograma
model.addConstr(C[0] == 0)

# Otimização
model.optimize()

# Impressão dos resultados
if model.Status == GRB.OPTIMAL:
    print("\nTarefas e seus tempos de conclusão:\n")
    for i in tarefas:
        if i != 0:
            print(f"Tarefa {i}: {C[i].X:.2f}")
    print(f"\nTempo de fluxo total = {model.ObjVal:.2f}")

elif model.SolCount > 0:
    print("\nTarefas e seus tempos de conclusão:\n")
    for i in tarefas:
        if i != 0:
            print(f"Tarefa {i}: {C[i].X:.2f}")
    print("\nO modelo encontrou uma solução viável, mas não foi possível comprovar a otimalidade.")
    print(f"Tempo de fluxo total = {model.ObjVal:.2f}")

else:
    print("Nenhuma solução viável encontrada.")

# Referências
# ARENALES, Marcos Nereu et al. Pesquisa Operacional. Rio de Janeiro: Elsevier, 2007.