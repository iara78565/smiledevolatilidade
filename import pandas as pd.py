import pandas as pd
import requests
import matplotlib.pyplot as plt
import random

# Função para obter a lista de empresas disponíveis no link
def obter_empresas_aleatorias(url, num_empresas=10):
    """
    Obtém uma lista de empresas aleatórias a partir do link fornecido.
    """
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Erro ao acessar o site de empresas.")
        return []
    
    # O site retornará as empresas em formato HTML. Vamos fazer o parsing e extrair os códigos das ações.
    # Assumindo que temos uma lista de empresas no formato de uma tabela ou lista, vamos simular aqui.
    # No caso real, seria necessário um parser de HTML como o BeautifulSoup para extrair os dados da página.
    
    # Exemplo simplificado: Aqui estamos usando uma lista estática de empresas para simulação
    empresas = ['ABEV3', 'PETR4', 'ITUB4', 'VALE3', 'B3SA3', 'BRFS3', 'LREN3', 'MGLU3', 'SULA11', 'CSNA3']
    
    return random.sample(empresas, num_empresas)

# Função para obter as cotações de opções para uma empresa e vencimento específico
def obter_dados_opcoes(subjacente, vencimento):
    """
    Obtém as cotações das opções (CALL e PUT) para uma empresa e vencimento específico.
    """
    url = f'https://opcoes.net.br/listaopcoes/completa?idAcao={subjacente}&listarVencimentos=false&cotacoes=true&vencimentos={vencimento}'
    response = requests.get(url)
    
    # Verifica se a requisição foi bem-sucedida
    if response.status_code != 200:
        print(f"Erro ao acessar a API para o vencimento {vencimento}: {response.status_code}")
        return pd.DataFrame()
    
    try:
        data = response.json()
        cotacoes = data['data']['cotacoesOpcoes']
        rows = [
            [i[0].split('_')[0], i[2], i[3], i[5], i[8], i[9], i[10]]  # Dados relevantes como strike, tipo, volatilidade, etc.
            for i in cotacoes
        ]
        return pd.DataFrame(rows, columns=['ativo', 'tipo', 'modelo', 'strike', 'preco', 'negocios', 'volume'])
    except KeyError:
        print(f"Erro ao processar os dados das opções para o vencimento {vencimento}.")
        return pd.DataFrame()

# Função para plotar o Smile de Volatilidade
def plotar_smile_volatilidade(df_opcoes, subjacente, vencimento):
    """
    Plota o gráfico de Smile de Volatilidade para as opções CALL e PUT de uma empresa.
    """
    df_opcoes['strike'] = pd.to_numeric(df_opcoes['strike'], errors='coerce')
    df_opcoes['volatilidade'] = pd.to_numeric(df_opcoes['preco'], errors='coerce')  # Utilizando o preço como proxy da volatilidade
    df_opcoes = df_opcoes.dropna(subset=['strike', 'volatilidade'])

    plt.figure(figsize=(10, 6))

    for tipo in ['CALL', 'PUT']:
        df_tipo = df_opcoes[df_opcoes['tipo'] == tipo]
        plt.plot(df_tipo['strike'], df_tipo['volatilidade'], label=f'{tipo} Options')

    plt.title(f'Smile de Volatilidade - {subjacente} - Vencimento {vencimento}')
    plt.xlabel('Strike')
    plt.ylabel('Volatilidade Implícita (%)')
    plt.legend()
    plt.grid(True)
    plt.show()

# Função principal para gerar a análise para 10 empresas
def analisar_smile_volatilidade():
    url_empresas = 'https://opcoes.net.br/acoes'  # Link para pegar a lista de ações
    empresas_aleatorias = obter_empresas_aleatorias(url_empresas)

    for empresa in empresas_aleatorias:
        print(f'Analisando empresa: {empresa}')
        vencimento = '2025-01-24'  # Defina o vencimento das opções
        df_opcoes = obter_dados_opcoes(empresa, vencimento)
        
        if not df_opcoes.empty:
            plotar_smile_volatilidade(df_opcoes, empresa, vencimento)
        else:
            print(f"Nenhum dado encontrado para {empresa} no vencimento {vencimento}.")
            
# Chama a função principal
analisar_smile_volatilidade()
