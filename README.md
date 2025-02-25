#CryptoStrategy
O CryptoStrategy é um projeto em Python que implementa uma estratégia automatizada de negociação baseada na análise técnica dos dados históricos de ativos financeiros. Utilizando a biblioteca yfinance, o script coleta dados de mercado para diversos tickers e aplica uma série de cálculos para identificar oportunidades de compra e venda.

#Funcionalidades
- Coleta de Dados: Utiliza a yfinance para baixar dados históricos (preços de abertura, fechamento, alta, baixa) de ativos financeiros.
- Cálculo de Indicadores Técnicos:
 - Média móvel e desvio padrão para a análise dos preços de fechamento.
 - Cálculo de limites superior e inferior (similar às bandas de Bollinger) para definir zonas de sobrecompra ou sobrevenda.
- Análise de Volatilidade: Cálculo do ATR (Average True Range) para mensurar a volatilidade do ativo.
- Geração de Sinais de Negociação:
 - Sinais de Compra e Venda baseados na comparação do preço de fechamento com os limites calculados.
 - Sinais de manutenção que indicam a continuidade da tendência de compra ou venda.
- Cálculo de Retorno Total: Avalia o desempenho da estratégia ao somar os retornos das operações realizadas.
- Otimização de Parâmetros: Testa diferentes tamanhos de janela para os indicadores técnicos, permitindo identificar a configuração que maximiza o retorno.
- Determinação de Tendência e Stop Loss: Identifica a tendência atual do mercado e calcula o stop loss para limitar perdas em operações revertidas.
# Como Utilizar
**1.Configuração:**
 - Defina os tickers desejados e ajuste os parâmetros de datas para a coleta dos dados históricos.
 - Escolha as janelas para o cálculo dos indicadores técnicos e do ATR.
**2. Execução:**
 - Rode o script principal ou utilize o notebook incluído para uma análise interativa.
 - Observe os sinais gerados e o retorno total da estratégia para avaliar o desempenho.
**3. Otimização:**
 - Utilize a função de otimização para testar diferentes tamanhos de janela e encontrar a configuração que ofereça o melhor retorno.
# Requisitos
- Python 3.x
- Bibliotecas:
 - yfinance
 - pandas
 - numpy
 - datetime

# Contribuições
Este projeto é open source e está aberto para contribuições. Sinta-se à vontade para sugerir melhorias, reportar problemas ou enviar pull requests.
