import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("Rm|nr-fa|ΣTi")

model.setParam("TimeLimit", 600) # limite de execução (segundos)

# Dados
dft = pd.read_csv("arquivo.csv", sep=";")
dfm = pd.read_csv("arquivo.csv", sep=";")

tarefas = dft["tarefa"].to_list()
d = dft.set_index("tarefa")["di"].to_dict()
p = {}
colunas_pi = [col for col in dft.columns if col.startswith('pi')]
for _, row in dft.iterrows():
    for col in colunas_pi:
        k = int(col.replace('pi', ''))
        p[row['tarefa'], k] = row[col]

maquinas = dfm["maquina"].to_list()
w = dfm.set_index("maquina")["wk"].to_dict()
u = dfm.set_index("maquina")["uk"].to_dict()
v = dfm.set_index("maquina")["vk"].to_dict()

n = len(tarefas)

M = ... # parâmetro Big-M

# Variáveis
T = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ti")
x = model.addVars([(i, k) for i in tarefas + [n + 1] for k in maquinas], vtype=GRB.BINARY, name="xik")
s = model.addVars(tarefas + [n + 1], maquinas, vtype=GRB.CONTINUOUS, lb=0, name="sik")
C = model.addVars(tarefas + [n + 1], maquinas, vtype=GRB.CONTINUOUS, lb=0, name="Cik")
z = model.addVars([(i, j) for i in tarefas + [n + 1] for j in tarefas + [n + 1] if i < j], vtype=GRB.BINARY, name="zij")

# Função objetivo
model.setObjective(gp.quicksum(T[i] for i in tarefas), GRB.MINIMIZE)

# Restrições
for i in tarefas:
    # (52): garante que cada tarefa seja processada em apenas uma máquina
    model.addConstr(gp.quicksum(x[i, k] for k in maquinas) == 1)

for k in maquinas:
    # (53): estabelece que cada máquina deve realizar um período de manutenção
    model.addConstr(x[n + 1, k] == 1)

for i in tarefas:
    for k in maquinas:
        # (54): calculam o tempo de conclusão de cada tarefa
        model.addConstr(s[i, k] + p[i, k] <= C[i, k] + M * (1 - x[i, k]))

for k in maquinas:
    # (55): define o tempo de conclusão da manutenção
    model.addConstr(s[n + 1, k] + w[k] == C[n + 1, k])

for i in tarefas + [n + 1]:
    for j in tarefas + [n + 1]:
        if i < j:         
            for k in maquinas:
                # (56) e (57): asseguram que duas tarefas não sejam processadas simultaneamente
                model.addConstr(C[i, k] <= s[j, k] + M * (3 - x[i, k] - x[j, k] - z[i, j]))
                model.addConstr(C[j, k] <= s[i, k] + M * (2 - x[i, k] - x[j, k] + z[i, j]))

for k in maquinas:
    # (58) e (59): estabelece o intervalo da manutenção
    model.addConstr(s[n + 1, k] >= u[k])
    model.addConstr(C[n + 1, k] <= v[k])

for i in tarefas:
    for k in maquinas:
        # (60): definição do atraso de cada tarefa
        model.addConstr(C[i, k] - d[i] <= T[i] + M * (1 - x[i, k]))

# Otimização
model.optimize()

# Impressão dos resultados
if model.Status == GRB.OPTIMAL:
    print("\nTarefas e seus atrasos:\n")
    for i in tarefas:
        for k in maquinas:
            if x[i, k].X > 0.5:
                print(f"Tarefa {i} (Máquina {k}): {T[i].X:.2f}")
    
    print(f"\nSoma dos atrasos = {model.ObjVal:.2f}")
    
    print("\nPeríodo de manutenção por máquina:")
    for k in maquinas:
        print(f"Máquina {k}: {s[n + 1, k].X:.2f} até {C[n + 1, k].X:.2f}")

elif model.SolCount > 0:
    print("\nTarefas e seus atrasos:\n")
    for i in tarefas:
        for k in maquinas:
            if x[i, k].X > 0.5:
                print(f"Tarefa {i} (Máquina {k}): {T[i].X:.2f}")
                
    print("\nO modelo encontrou uma solução viável, mas não foi possível comprovar a otimalidade.")
    print(f"\nSoma dos atrasos = {model.ObjVal:.2f}")
    
    print("\nPeríodo de manutenção por máquina:")
    for k in maquinas:
        print(f"Máquina {k}: {s[n + 1, k].X:.2f} até {C[n + 1, k].X:.2f}")

else:
    print("Nenhuma solução viável encontrada.")

# Referências
# CHEN, J.-S. Optimization models for the machine scheduling problem with a single flexible maintenance activity. Engineering Optimization, v. 38, n. 1, p. 53‑71, 2006. doi:10.1080/03052150500270594.
