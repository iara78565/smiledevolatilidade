import pandas as pd
import requests
import matplotlib.pyplot as plt
import random
import mibian

# Função para obter uma lista de 10 empresas aleatórias
def obter_empresas_aleatorias(url, num_empresas=10):
    """
    Coleta um conjunto de empresas aleatórias a partir de um site de opções.
    
    Parâmetros:
    url (str): URL de onde são retiradas as empresas.
    num_empresas (int): Número de empresas a serem selecionadas (padrão: 10).
    
    Retorna:
    List[str]: Lista de empresas aleatórias.
    """
    # Fazendo uma requisição para o site
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Erro ao acessar o site de empresas.")
        return []  # Retorna uma lista vazia se houver erro
    
    # Exemplo de empresas. Aqui você poderia adicionar uma lógica para pegar empresas reais do site
    empresas = ['ABEV3', 'PETR4', 'ITUB4', 'VALE3', 'B3SA3', 'BRFS3', 'LREN3', 'MGLU3', 'SULA11', 'CSNA3']
    
    # Retorna uma lista aleatória de empresas
    return random.sample(empresas, num_empresas)

# Função para pegar dados das opções de uma empresa e vencimento
def obter_dados_opcoes(subjacente, vencimento):
    """
    Coleta dados de opções de uma empresa para um vencimento específico.
    
    Parâmetros:
    subjacente (str): Código da ação (ex: 'PETR4').
    vencimento (str): Data de vencimento da opção (ex: '2025-01-24').
    
    Retorna:
    pd.DataFrame: DataFrame com dados sobre as opções (CALL e PUT), como strike e preço.
    """
    url = f'https://opcoes.net.br/listaopcoes/completa?idAcao={subjacente}&listarVencimentos=false&cotacoes=true&vencimentos={vencimento}'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erro ao acessar os dados da opção para o vencimento {vencimento}.")
        return pd.DataFrame()  # Retorna um DataFrame vazio em caso de erro
    
    try:
        data = response.json()  # Converte o conteúdo da resposta para JSON
        cotacoes = data['data']['cotacoesOpcoes']
        
        # Extrai os dados mais importantes para cada opção (tipo, strike, preço, etc.)
        rows = [
            [i[0].split('_')[0], i[2], i[3], i[5], i[8], i[9], i[10]]  # Exemplo de dados: ativo, tipo, strike, preço, etc.
            for i in cotacoes
        ]
        return pd.DataFrame(rows, columns=['ativo', 'tipo', 'modelo', 'strike', 'preco', 'negocios', 'volume'])
    except KeyError:
        print("Erro ao processar os dados das opções.")
        return pd.DataFrame()  # Retorna um DataFrame vazio se houver erro ao processar os dados

# Função para calcular a volatilidade implícita usando o modelo Black-Scholes
def calcular_volatilidade_implicita(preco_acao, strike, preco_opcao, tipo_opcao, dias_ate_vencimento, taxa_juros):
    """
    Calcula a volatilidade implícita de uma opção (CALL ou PUT) usando o modelo de Black-Scholes.
    
    Parâmetros:
    preco_acao (float): Preço atual da ação.
    strike (float): Preço de exercício da opção.
    preco_opcao (float): Preço da opção (CALL ou PUT).
    tipo_opcao (str): Tipo de opção ('CALL' ou 'PUT').
    dias_ate_vencimento (int): Quantos dias faltam até o vencimento.
    taxa_juros (float): Taxa de juros livre de risco (em percentual).
    
    Retorna:
    float: Volatilidade implícita calculada.
    """
    tipo = 'C' if tipo_opcao == 'CALL' else 'P'  # Define se é CALL ou PUT
    
    # Usando o modelo de Black-Scholes para calcular a volatilidade implícita
    opcao = mibian.BS([preco_acao, strike, taxa_juros, dias_ate_vencimento], 
                      callPrice=preco_opcao if tipo == 'C' else None, 
                      putPrice=preco_opcao if tipo == 'P' else None)
    
    return opcao.impliedVolatility  # Retorna a volatilidade implícita

# Função para gerar e adicionar dados de volatilidade no gráfico de Smile de Volatilidade
def plotar_smile_volatilidade(df_opcoes, tipo_opcao, preco_acao, dias_ate_vencimento, taxa_juros, all_strikes, all_volatilidades):
    """
    Adiciona os dados de volatilidade implícita ao gráfico do Smile de Volatilidade.
    
    Parâmetros:
    df_opcoes (pd.DataFrame): DataFrame com os dados das opções (CALL ou PUT).
    tipo_opcao (str): Tipo de opção ('CALL' ou 'PUT').
    preco_acao (float): Preço da ação subjacente.
    dias_ate_vencimento (int): Dias até o vencimento.
    taxa_juros (float): Taxa de juros livre de risco.
    all_strikes (list): Lista para armazenar os strikes das opções.
    all_volatilidades (list): Lista para armazenar as volatilidades implícitas das opções.
    
    Retorna:
    tuple: Tupla contendo as listas de strikes e volatilidades atualizadas.
    """
    # Converte os valores de 'strike' e 'preço' para números
    df_opcoes['strike'] = pd.to_numeric(df_opcoes['strike'], errors='coerce')
    df_opcoes['preco'] = pd.to_numeric(df_opcoes['preco'], errors='coerce')  # Preço da opção

    # Calcula a volatilidade implícita para cada opção
    for _, row in df_opcoes.iterrows():
        volatilidade_implicita = calcular_volatilidade_implicita(preco_acao, row['strike'], row['preco'], row['tipo'], dias_ate_vencimento, taxa_juros)
        all_strikes.append(row['strike'])  # Adiciona o strike à lista
        all_volatilidades.append(volatilidade_implicita)  # Adiciona a volatilidade à lista

    return all_strikes, all_volatilidades  # Retorna as listas atualizadas

# Função principal que orquestra a análise e gera os gráficos
def analisar_smile_volatilidade():
    """
    Função principal para realizar a análise do Smile de Volatilidade para 10 empresas e gerar gráficos.
    """
    # URL para pegar a lista de ações
    url_empresas = 'https://opcoes.net.br/acoes'
    empresas_aleatorias = obter_empresas_aleatorias(url_empresas)  # Coleta 10 empresas aleatórias

    # Listas para armazenar os dados das opções de CALL e PUT
    all_strikes_call = []
    all_volatilidades_call = []
    all_strikes_put = []
    all_volatilidades_put = []

    # Parâmetros de exemplo para o preço da ação, taxa de juros e dias até o vencimento
    preco_acao_exemplo = 50  # Exemplo de preço da ação
    taxa_juros = 5  # Exemplo de taxa de juros (5%)
    dias_ate_vencimento = 30  # Exemplo: 30 dias até o vencimento
    vencimento = '2025-01-24'  # Data de vencimento das opções

    # Para cada empresa aleatória, vamos pegar os dados das opções e calcular a volatilidade implícita
    for empresa in empresas_aleatorias:
        print(f'Analisando empresa: {empresa}')
        df_opcoes = obter_dados_opcoes(empresa, vencimento)  # Coleta os dados das opções
        
        if not df_opcoes.empty:
            # Se houver dados, separa as opções CALL e PUT
            df_call = df_opcoes[df_opcoes['tipo'] == 'CALL']
            all_strikes_call, all_volatilidades_call = plotar_smile_volatilidade(df_call, 'CALL', preco_acao_exemplo, dias_ate_vencimento, taxa_juros, all_strikes_call, all_volatilidades_call)

            df_put = df_opcoes[df_opcoes['tipo'] == 'PUT']
            all_strikes_put, all_volatilidades_put = plotar_smile_volatilidade(df_put, 'PUT', preco_acao_exemplo, dias_ate_vencimento, taxa_juros, all_strikes_put, all_volatilidades_put)
        else:
            print(f"Nenhum dado encontrado para {empresa} no vencimento {vencimento}.")
    
    # Gerando os gráficos de Smile de Volatilidade para CALL e PUT
    plt.figure(figsize=(12, 6))

    # Gráfico de CALL
    plt.subplot(1, 2, 1)
    plt.scatter(all_strikes_call, all_volatilidades_call, color='blue', label='CALL Options', alpha=0.5)
    plt.title('Smile de Volatilidade - CALL Options')
    plt.xlabel('Strike')
    plt.ylabel('Volatilidade Implícita (%)')
    plt.grid(True)
    plt.legend()

    # Gráfico de PUT
    plt.subplot(1, 2, 2)
    plt.scatter(all_strikes_put, all_volatilidades_put, color='red', label='PUT Options', alpha=0.5)
    plt.title('Smile de Volatilidade - PUT Options')
    plt.xlabel('Strike')
    plt.ylabel('Volatilidade Implícita (%)')
    plt.grid(True)
    plt.legend()

    plt.tight_layout()  # Ajusta o layout para que os gráficos não se sobreponham
    plt.show()  # Exibe os gráficos

# Chama a função principal para rodar a análise
analisar_smile_volatilidade()

# Salvar a imagem do gráfico em vez de apenas mostrar
plt.savefig('grafico_smile_volatilidade.png')  # Salva o gráfico como uma imagem PNG
print("Gráfico salvo como 'grafico_smile_volatilidade.png'")




