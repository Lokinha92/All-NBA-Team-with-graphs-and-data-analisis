import pandas as pd
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import networkx as nx

dataset = pd.read_csv("./dataset/dataset.csv", sep=';', encoding='iso-8859-1')

# Seleção de atributos
dataset.drop(['Age', 'Rk', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%',
              'FT', 'FTA', 'FT%', 'ORB', 'DRB'], axis=1, inplace=True)

# Tratamento de domínio no atributo posição
dataset.loc[dataset['Pos'] == 'PF-SF', 'Pos'] = 'SF'
dataset.loc[dataset['Pos'] == 'SG-PG', 'Pos'] = 'SG'
dataset.loc[dataset['Pos'] == 'SF-SG', 'Pos'] = 'SG'

# Cálculo do Coef. de desempenho
def calcular_desempenho(row):
    if row['Pos'] == 'PG':
        return (row['PTS'] * (2 * row['eFG%']) + 1 * row['G'] + 2 * row['AST'] + 1 * row['STL'] + 1 * row['BLK'] + 1 * row['TRB']) - (1.5 * (row['TOV'] + row['PF']))
    elif row['Pos'] == 'SF':
        return (row['PTS'] * (2* row['eFG%']) + 1 * row['G'] + 1.5 * row['AST'] + 1 * row['STL'] + 1 * row['BLK'] + 1 * row['TRB']) - (1 * (row['TOV'] + row['PF']))
    elif row['Pos'] == 'SG':
        return (row['PTS'] * (2 * row['eFG%']) + 1 * row['G'] + 1.75 * row['AST'] + 1 * row['STL'] + 1 * row['BLK'] + 1 * row['TRB']) - (1 * (row['TOV'] + row['PF']))
    elif row['Pos'] == 'PF':
        return (row['PTS'] * (2 * row['eFG%']) + 1 * row['G'] + 1.25 * row['AST'] + 2 * row['STL'] + 1.75 * row['BLK'] + 1.5 * row['TRB']) - (1 * (row['TOV'] + row['PF']))
    elif row['Pos'] == 'C':
        return (row['PTS'] * (2* row['eFG%']) + 1 * row['G'] + 1.25 * row['AST'] + 1.25 * row['STL'] + 2 * row['BLK'] + 2 * row['TRB']) - (1 * (row['TOV'] + row['PF']))
    else:
        return 0
 
# adicionando atributo "COEF.Desempenho" ao dataset 
dataset['COEF.Desempenho'] = dataset.apply(calcular_desempenho, axis=1)

# atributos já utilizados, limpado eles do dataset
dataset.drop(['G','eFG%','TRB','AST','STL','BLK','TOV','PF','PTS'], axis=1, inplace=True)

# criação do grafo
grafo = nx.Graph()

# adicionando nós ao grafo
for _, jogador in dataset.iterrows():
    grafo.add_node(jogador['Player'], posicao=jogador['Pos'], desempenho=jogador['COEF.Desempenho']) # --> Vértices com atributos

grafo.clear_edges()

# Ligando as arestas e ponderando com a soma
posicoes = ['PG', 'SG', 'SF', 'PF', 'C']
for i in range(len(posicoes) - 1):
    posicao_atual = posicoes[i]
    proxima_posicao = posicoes[i + 1]

    jogadores_posicao_atual = [jogador for jogador, dados in grafo.nodes(data=True) if dados['posicao'] == posicao_atual]
    jogadores_proxima_posicao = [jogador for jogador, dados in grafo.nodes(data=True) if dados['posicao'] == proxima_posicao]

    for jogador_atual in jogadores_posicao_atual:
        for jogador_proxima_posicao in jogadores_proxima_posicao:
            peso_aresta = grafo.nodes[jogador_atual]['desempenho'] + grafo.nodes[jogador_proxima_posicao]['desempenho']
            grafo.add_edge(jogador_atual, jogador_proxima_posicao, peso=peso_aresta)

# Removendo nós isolados (de precaução)
grafo.remove_nodes_from(list(nx.isolates(grafo)))

# Iterando sob as regiões, em busca do caminho de maior peso, resultando na seleção
caminho_maximizado = []
peso_total = 0


def calcular_peso(jogador1, jogador2):
    return grafo[jogador1][jogador2]['peso']

for i in range(len(posicoes) - 1):
    posicao_atual = posicoes[i]
    proxima_posicao = posicoes[i + 1]

    
    jogadores_posicao_atual = [jogador for jogador, dados in grafo.nodes(data=True) if dados['posicao'] == posicao_atual]
    jogadores_proxima_posicao = [jogador for jogador, dados in grafo.nodes(data=True) if dados['posicao'] == proxima_posicao]

    max_peso_aresta = 0
    aresta_max_peso = None

    for jogador_atual in jogadores_posicao_atual:
        for jogador_proxima_posicao in jogadores_proxima_posicao:
            if jogador_atual != jogador_proxima_posicao:
                peso_aresta = calcular_peso(jogador_atual, jogador_proxima_posicao)
                if peso_aresta > max_peso_aresta:
                    max_peso_aresta = peso_aresta
                    aresta_max_peso = (jogador_atual, jogador_proxima_posicao)

    # Adicionar a aresta de maior peso ao caminho
    if aresta_max_peso is not None:
        caminho_maximizado.append(aresta_max_peso)
        peso_total += max_peso_aresta

jogadores_unicos = set()
for aresta in caminho_maximizado:
    jogadores_unicos.update(aresta)

# Resultado
print("Time Ideal:", list(jogadores_unicos))
print("desempenho:", peso_total)
print(dataset.shape)

# Desenha o grafo
posicoes = nx.spring_layout(grafo)
nx.draw(grafo, pos=posicoes, with_labels=True, font_size=8, font_color="black", node_size=500, node_color="palegreen", edge_color="gray", width=[grafo[u][v]['peso'] / 300 for u, v in grafo.edges()])

plt.show()
