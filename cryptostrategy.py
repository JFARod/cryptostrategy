import yfinance as yf
import pandas as pd
import numpy as np
import datetime

def coletar_dados(tickers, start_date = '1970-01-01', end_date = datetime.date.today()):
    """
    Coleta os dados históricos dos tickers especificados entre as datas informadas.

    Parâmetros:
    - tickers: lista de strings com os tickers (ex.: ['PETR4.SA', 'VALE3.SA', ...])
    - start_date: string ou objeto datetime representando a data de início (ex.: '2000-01-01')
    - end_date: string ou objeto datetime representando a data de término (ex.: '2024-09-30')

    Retorna:
    - dados: dicionário onde a chave é o ticker e o valor é um DataFrame com os dados históricos
    """
    dados = {}
    for ticker in tickers:
        #print(f"Baixando dados para {ticker}...")
        df = yf.download(ticker, start=start_date, end=end_date)
        if df.empty:
            print(f"Aviso: Nenhum dado encontrado para {ticker}.")
        dados[ticker] = df
    return dados

def calcular_indicadores(df, janela):
    """
    Calcula indicadores técnicos a partir dos dados históricos.

    Parâmetros:
      - df: DataFrame contendo, no mínimo, a coluna 'Close'.
      - janela: tamanho da janela para cálculo dos indicadores.

    Retorna:
      - df_ind: DataFrame com as colunas adicionais:
          'Media_Movel', 'Desvio_Padrao', 'Limite_Superior' e 'Limite_Inferior'.
    """
    df_ind = df.copy()
    # Calcula a média móvel e o desvio padrão móvel para a coluna 'Close'
    df_ind['Media_Movel'] = df_ind['Close'].rolling(window=janela).mean()
    df_ind['Desvio_Padrao'] = df_ind['Close'].rolling(window=janela).std()
    # Calcula os limites (semelhante às bandas de Bollinger, usando 1.96 para aproximadamente 95% de confiança)
    df_ind['Limite_Superior'] = df_ind['Media_Movel'] + (1.96 * df_ind['Desvio_Padrao'])
    df_ind['Limite_Inferior'] = df_ind['Media_Movel'] - (1.96 * df_ind['Desvio_Padrao'])
    
    return df_ind

def calcular_atr(df, janela):
    """
    Calcula o ATR (Average True Range) para os dados históricos.

    Parâmetros:
      - df: DataFrame contendo as colunas 'High', 'Low' e 'Close'.
      - janela: tamanho da janela para calcular o ATR (média móvel do True Range).

    Retorna:
      - df_atr: DataFrame com uma coluna adicional 'ATR' contendo o Average True Range.
    """
    df_atr = df.copy()
    
    # Calcula o True Range (TR)
    # TR é o maior valor entre:
    #   1. High - Low
    #   2. abs(High - Close anterior)
    #   3. abs(Low - Close anterior)
    df_atr['Previous_Close'] = df_atr['Close'].shift(1)
    df_atr['TR1'] = df_atr['High'] - df_atr['Low']
    df_atr['TR2'] = (df_atr['High'] - df_atr['Previous_Close']).abs()
    df_atr['TR3'] = (df_atr['Low'] - df_atr['Previous_Close']).abs()
    
    df_atr['True_Range'] = df_atr[['TR1', 'TR2', 'TR3']].max(axis=1)
    
    # Calcula o ATR como a média móvel do True Range
    df_atr['ATR'] = df_atr['True_Range'].rolling(window=janela).mean()
    
    # Limpa as colunas auxiliares
    df_atr.drop(['Previous_Close', 'TR1', 'TR2', 'TR3'], axis=1, inplace=True)
    
    return df_atr

def calcular_todos_indicadores(df, janela_indicadores, janela_atr):
    """
    Calcula os indicadores técnicos (média móvel, desvio padrão, limites) e o ATR,
    e junta os resultados em um único DataFrame.

    Parâmetros:
      - df: DataFrame contendo os dados históricos (deve ter as colunas 'Close', 'High' e 'Low').
      - janela_indicadores: janela para o cálculo dos indicadores técnicos (média móvel, etc.).
      - janela_atr: janela para o cálculo do ATR.

    Retorna:
      - df_total: DataFrame com os dados originais e as colunas calculadas:
           'Media_Movel', 'Desvio_Padrao', 'Limite_Superior', 'Limite_Inferior' e 'ATR'.
    """
    # Calcula os indicadores técnicos (usando a função calcular_indicadores)
    df_ind = calcular_indicadores(df, janela_indicadores)
    
    # Calcula o ATR (usando a função calcular_atr)
    df_atr = calcular_atr(df, janela_atr)
    
    # Junta os DataFrames, usando o índice (datas) como chave
    df_total = pd.concat([df_ind, df_atr[['ATR']]], axis=1)
    
    return df_total

def gerar_sinais(df):
    """
    Gera sinais de negociação para o DataFrame e adiciona uma coluna
    com o número de dias consecutivos que o sinal se manteve.

    Sinais:
      - 'Compra' quando o preço de fechamento cai abaixo do Limite_Inferior e o sinal muda para compra.
      - 'Manter Compra' quando a condição de compra persiste.
      - 'Venda' quando o preço de fechamento ultrapassa o Limite_Superior e o sinal muda para venda.
      - 'Manter Venda' quando a condição de venda persiste.
      - 'Nenhum' quando nenhuma condição é atendida, reiniciando o contador.
    
    Parâmetros:
      - df: DataFrame que deve conter as colunas 'Close', 'Limite_Superior' e 'Limite_Inferior'.

    Retorna:
      - df: DataFrame com as colunas 'Sinal' e 'Dias_Sinal' adicionadas.
    """
    df = df.copy()
    df['Sinal'] = 'Nenhum'
    df['Dias_Sinal'] = 0
    estado = None  # Estado atual: 'Compra' ou 'Venda'
    contador = 0   # Contador de dias consecutivos com o mesmo sinal
    
    for index, row in df.iterrows():
        if row['Close'] < row['Limite_Inferior']:
            if estado != 'Compra':
                estado = 'Compra'
                contador = 1
                df.at[index, 'Sinal'] = 'Compra'
            else:
                contador += 1
                df.at[index, 'Sinal'] = 'Manter Compra'
        elif row['Close'] > row['Limite_Superior']:
            if estado != 'Venda':
                estado = 'Venda'
                contador = 1
                df.at[index, 'Sinal'] = 'Venda'
            else:
                contador += 1
                df.at[index, 'Sinal'] = 'Manter Venda'
        else:
            estado = None
            contador = 0
            df.at[index, 'Sinal'] = 'Nenhum'
        
        df.at[index, 'Dias_Sinal'] = contador
        
    return df

def calcular_retorno_total(df, janela):
    """
    Calcula o retorno total da estratégia para um determinado tamanho de janela.
    
    1. Aplica o cálculo dos indicadores técnicos (média móvel, desvio padrão, limites).
    2. Gera os sinais de negociação (Compra, Manter Compra, Venda, Manter Venda ou Nenhum).
    3. Percorre o DataFrame para acumular os retornos:
         - Ao receber um sinal de Compra, registra o preço de compra.
         - Ao receber um sinal de Venda (ou Manter Venda) e se houver um preço de compra registrado, calcula a diferença.
    4. Retorna o retorno total e o DataFrame com os sinais e a coluna de retorno.
    
    Parâmetros:
      - df: DataFrame com os dados históricos (deve conter, pelo menos, 'Close', 'High' e 'Low').
      - janela: Tamanho da janela para os cálculos dos indicadores.
      
    Retorna:
      - retorno_total: Soma de todos os retornos calculados.
      - df_estrategia: DataFrame resultante com as colunas calculadas.
    """
    # Calcula os indicadores técnicos com a janela definida
    df_ind = calcular_indicadores(df, janela)
    
    # Gera os sinais (incluindo a contagem de dias, se desejado)
    df_sinais = gerar_sinais(df_ind)
    
    # Inicializa a coluna de retorno
    df_sinais['Retorno'] = 0.0
    preco_compra = None
    
    # Percorre o DataFrame para calcular o retorno das operações
    for index, row in df_sinais.iterrows():
        # Se sinal de compra (inicial ou manutenção) e não estamos em posição, registra o preço
        if row['Sinal'] in ['Compra'] and preco_compra is None:
            preco_compra = row['Close']
        # Se sinal de venda (ou manutenção de venda) e já estamos em posição de compra, realiza a operação
        elif row['Sinal'] in ['Venda'] and preco_compra is not None:
            df_sinais.at[index, 'Retorno'] = row['Close'] - preco_compra
            preco_compra = None  # Encerra a operação
        # Se não houver sinal de compra ou venda, permanece sem operação
        # (Você pode adaptar a lógica se desejar manter posições por mais de um dia)
    
    retorno_total = df_sinais['Retorno'].sum()
    return retorno_total, df_sinais

def otimizar_janela(df, janela_min=1, janela_max=99):
    """
    Testa diferentes tamanhos de janela para os indicadores e calcula o retorno total
    da estratégia para cada um. Retorna um DataFrame com os resultados ordenados pelo
    retorno total (do maior para o menor).

    Parâmetros:
      - df: DataFrame com os dados históricos (deve conter 'Close', 'High', 'Low', etc.).
      - janela_min: Tamanho mínimo da janela a ser testada (ex.: 10).
      - janela_max: Tamanho máximo da janela a ser testada (ex.: 98).

    Retorna:
      - resultados_df: DataFrame com as colunas 'Janela' e 'Retorno_Total',
        ordenado do maior retorno para o menor.
    """
    resultados = {}
    
    for janela in range(janela_min, janela_max + 1):
        retorno_total, _ = calcular_retorno_total(df, janela)
        resultados[janela] = retorno_total
        #print(f"Janela: {janela} dias, Retorno Total: {retorno_total:.2f}")
    
    # Converte os resultados para DataFrame
    resultados_df = pd.DataFrame(list(resultados.items()), columns=['Janela', 'Retorno_Total'])
    resultados_df = resultados_df.sort_values(by='Retorno_Total', ascending=False)
    return resultados_df

def determinar_tendencia_e_stoploss(df):
    """
    Determina a tendência atual e, caso haja reversão, calcula o stop loss 
    com base numa perda máxima de 25% para operações long e 25% de perda para operações short.
    
    Estratégia:
      - Tendência é definida comparando o último preço ('Close') com a 'Media_Movel':
          * Se Close > Media_Movel, tendência é 'Alta' (favorável para posições long)
          * Caso contrário, 'Baixa' (favorável para posições short)
          
      - Para detectar reversão, são analisados os sinais efetivos (excluindo 'Nenhum'):
          * Se o último sinal efetivo for 'Venda' ou 'Manter Venda' após uma sequência de compra
            => reversão de long para short.
            Stop Loss para long é calculado como 75% do preço de compra (perda de 25%).
          
          * Se o último sinal efetivo for 'Compra' ou 'Manter Compra' após uma sequência de venda
            => reversão de short para long.
            Stop Loss para short é calculado como 125% do preço de venda (perda de 25% para short,
            pois o prejuízo ocorre se o preço sobe 25% acima do preço de venda).
    
    Parâmetros:
      - df: DataFrame contendo, pelo menos, as colunas 'Close', 'Media_Movel' e 'Sinal'.
            Esse DataFrame deve ter sido gerado previamente com as funções de indicadores e geração de sinais.
    
    Retorna:
      - tendencia: String "Alta" ou "Baixa", definida pela comparação do último preço com a média móvel.
      - posicao_revertida: String "Long" ou "Short" indicando a operação que foi revertida, ou None se não houver reversão.
      - stop_loss: Valor numérico do stop loss calculado, ou None se não houver reversão detectada.
    """
    df = df.copy()
    
    # Define a tendência atual comparando o último valor de 'Close' com 'Media_Movel'
    ultimo = df.iloc[-1]
    tendencia = "Alta" if ultimo['Close'] > ultimo['Media_Movel'] else "Baixa"
    
    # Extraímos os sinais efetivos (excluindo 'Nenhum')
    sinais_efetivos = df[df['Sinal'] != 'Nenhum']
    
    stop_loss = None
    posicao_revertida = None  # Indica se houve reversão: "Long" ou "Short"
    
    if len(sinais_efetivos) >= 2:
        sinal_atual = sinais_efetivos.iloc[-1]['Sinal']
        sinal_anterior = sinais_efetivos.iloc[-2]['Sinal']
        
        # Caso 1: Reversão de uma posição long (compra) para short (venda)
        if sinal_atual in ['Venda', 'Manter Venda'] and sinal_anterior in ['Compra', 'Manter Compra']:
            posicao_revertida = "Long"
            # Localiza o preço de compra da última sequência de compra
            indices_compra = sinais_efetivos[sinais_efetivos['Sinal'].isin(['Compra', 'Manter Compra'])].index
            if len(indices_compra) > 0:
                preco_compra = df.loc[indices_compra[-1], 'Close']
                stop_loss = preco_compra * 0.75  # 25% de perda tolerada em operações long
                
        # Caso 2: Reversão de uma posição short (venda) para long (compra)
        elif sinal_atual in ['Compra', 'Manter Compra'] and sinal_anterior in ['Venda', 'Manter Venda']:
            posicao_revertida = "Short"
            # Localiza o preço de venda da última sequência de venda
            indices_venda = sinais_efetivos[sinais_efetivos['Sinal'].isin(['Venda', 'Manter Venda'])].index
            if len(indices_venda) > 0:
                preco_venda = df.loc[indices_venda[-1], 'Close']
                stop_loss = preco_venda * 1.25  # Stop loss acima do preço de venda para limitar a perda de 25%
    
    return tendencia, posicao_revertida, stop_loss
