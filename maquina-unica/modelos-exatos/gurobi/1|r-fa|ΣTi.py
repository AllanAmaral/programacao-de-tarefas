import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("1|r-fa|ΣTi")

model.setParam("TimeLimit", 600) # limite de execução (segundos)

# Dados
df = pd.read_csv("arquivo.csv", sep=";")

tarefas = df["tarefa"].to_list()
p = df.set_index("tarefa")["pi"].to_dict()
d = df.set_index("tarefa")["di"].to_dict()

n = len(tarefas)

w = ... # duração da manutenção
u = ... # início mínimo da manutenção
v = ... # término máximo da manutenção

M = ... # parâmetro Big-M

# Variáveis
T = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ti")
s = model.addVars(tarefas + [n + 1], vtype=GRB.CONTINUOUS, lb=0, name="si")
C = model.addVars(tarefas + [n + 1], vtype=GRB.CONTINUOUS, lb=0, name="Ci")
y = model.addVars(tarefas, vtype=GRB.BINARY, name="yi")
z = model.addVars([(i, j) for i in tarefas + [n + 1] for j in tarefas + [n + 1] if i < j], vtype=GRB.BINARY, name="zij")

# Função objetivo (20)
model.setObjective(gp.quicksum(T[i] for i in tarefas), GRB.MINIMIZE)

# Restrições
# (21): impõe o máximo de uma tarefa retomável
model.addConstr(gp.quicksum(y[i] for i in tarefas) <= 1)

for i in tarefas:
    # (22) e (23): calculam o tempo de conclusão das tarefas
    model.addConstr(s[i] + p[i] <= C[i] + M * y[i])
    model.addConstr(s[i] + p[i] + w <= C[i] + M * (1 - y[i]))

# (24): define o tempo de conclusão da manutenção
model.addConstr(s[n + 1] + w == C[n + 1])

for i in tarefas:
    # (25): define o atraso de cada tarefa
    model.addConstr(C[i] - d[i] <= T[i]) 

for i in tarefas:
    for j in tarefas:
        if i < j:
            # (26) e (27): asseguram que duas tarefas não sejam processadas simultaneamente
            model.addConstr(C[i] <= s[j] + M * (1 - z[i, j]))
            model.addConstr(C[j] <= s[i] + M * z[i, j])

for i in tarefas:
    # (28) e (29): garantem que não haja sobreposição entre tarefas e período de indisponibilidade
    model.addConstr(C[i] <= s[n + 1] + M * (1 - z[i, n + 1] + y[i]))
    model.addConstr(C[n + 1] <= s[i] + M * (z[i, n + 1] + y[i]))

    # (30) e (31): definem a precedência entre início e término da manutenção e da tarefa retomável
    model.addConstr(s[i] <= s[n + 1] + M * (1 - y[i]))
    model.addConstr(C[i] >= C[n + 1] - M * (1 - y[i]))

# (32) e (33): estabelecem o intervalo da manutenção
model.addConstr(s[n + 1] >= u)
model.addConstr(C[n + 1] <= v)

# Otimização
model.optimize()

# Impressão dos resultados
if model.Status == GRB.OPTIMAL:
    print("\nTarefas e seus atrasos:\n")
    for i in tarefas:
            print(f"Tarefa {i}: {T[i].X:.2f}")
        
    print(f"\nSoma dos atrasos = {model.ObjVal:.2f}")
    print(f"\nPeríodo de manutenção: {s[n + 1].X:.2f} até {C[n + 1].X:.2f}")

elif model.SolCount > 0:
    print("\nTarefas e seus atrasos:\n")
    for i in tarefas:
            print(f"Tarefa {i}: {T[i].X:.2f}")
        
    print("\nO modelo encontrou uma solução viável, mas não foi possível comprovar a otimalidade.")
    print(f"Soma dos atrasos = {model.ObjVal:.2f}")
    print(f"\nPeríodo de manutenção: {s[n + 1].X:.2f} até {C[n + 1].X:.2f}")
    
else:
    print("Nenhuma solução viável encontrada.")

# Referências
# CHEN, J.-S. Optimization models for the machine scheduling problem with a single flexible maintenance activity. Engineering Optimization, v. 38, n. 1, p. 53‑71, 2006. doi:10.1080/03052150500270594.
