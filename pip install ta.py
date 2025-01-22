import requests

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from arch import arch_model

# Função para coletar dados de volatilidade do site "https://opcoes.net.br/acoes"
def get_option_data(ticker):
    url = f"https://opcoes.net.br/acoes/{ticker}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Erro ao acessar o site para a ação {ticker}")
        return None
    
    
    
    
    strikes = []
    vols_call = []
    vols_put = []
    
    try:
        table = soup.find('table', {'class': 'table table-hover'})  # Tabela com os dados de volatilidade
        rows = table.find_all('tr')[1:]  # Ignora o cabeçalho
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 0:
                try:
                    strike = float(cols[0].text.strip().replace('R$', '').replace('.', '').replace(',', '.'))
                    iv_call = float(cols[1].text.strip().replace('%', '').replace(',', '.'))  # Volatilidade das calls
                    iv_put = float(cols[2].text.strip().replace('%', '').replace(',', '.'))  # Volatilidade das puts
                    
                    strikes.append(strike)
                    vols_call.append(iv_call)
                    vols_put.append(iv_put)
                except ValueError as ve:
                    print(f"Erro ao converter valores: {ve}")
        
        return strikes, vols_call, vols_put
    
    except Exception as e:
        print(f"Erro ao extrair dados da ação {ticker}: {e}")
        return None

# Função para ajustar o modelo GARCH
def fit_garch_model(data):
    returns = 100 * data.pct_change().dropna()  # Retornos em porcentagem
    model = arch_model(returns, vol='Garch', p=1, q=1)
    results = model.fit()
    return results

# Função para plotar a volatilidade condicional
def plot_volatility(results):
    plt.figure(figsize=(10, 6))
    plt.plot(results.conditional_volatility, label='Volatilidade Condicional (GARCH)')
    plt.title('Volatilidade Condicional Estimada pelo Modelo GARCH')
    plt.xlabel('Data')
    plt.ylabel('Volatilidade Estimada')
    plt.legend()
    plt.grid(True)
    plt.show()

# Função para gerar o gráfico de Smile de Volatilidade
def plot_vol_smile(strikes, vols_call, vols_put, ticker):
    plt.figure(figsize=(10, 6))
    plt.plot(strikes, vols_call, label='Volatilidade Implícita (Call)', color='blue', marker='o')
    plt.plot(strikes, vols_put, label='Volatilidade Implícita (Put)', color='red', marker='o')
    plt.title(f'Smile de Volatilidade para {ticker}')
    plt.xlabel('Strike')
    plt.ylabel('Volatilidade Implícita (%)')
    plt.legend()
    plt.grid(True)
    plt.show()

# Exemplo de uso:
ticker = 'PETR4'  # Ticker da ação (exemplo: Petrobras)
# Coleta os dados de volatilidade e strikes
option_data = get_option_data(ticker)

if option_data is None:
    print("Não foi possível obter os dados de opções.")
else:
    strikes, vols_call, vols_put = option_data
    
    # Verifique se os dados estão sendo coletados corretamente
    if len(strikes) == 0 or len(vols_call) == 0 or len(vols_put) == 0:
        print("Dados insuficientes para gerar o gráfico.")
    else:
        # Plotar o gráfico do Smile de Volatilidade
        plot_vol_smile(strikes, vols_call, vols_put, ticker)
        
        # Se desejar ajustar o modelo GARCH, pode-se coletar preços históricos para o cálculo da volatilidade condicional
        # Exemplo: usar preços históricos para calcular a volatilidade com GARCH
        # Baixar dados históricos com yfinance (por exemplo, PETR4)

        data = yf.download(f'{ticker}.SA', start="2020-01-01", end="2021-01-01")['Adj Close']
        
        # Ajustar o modelo GARCH aos dados de preços históricos
        garch_results = fit_garch_model(data)
        
        # Plotar a volatilidade condicional
        plot_volatility(garch_results)
