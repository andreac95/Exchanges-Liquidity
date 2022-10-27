try:
    from pycoingecko import CoinGeckoAPI
except:
    pip install pycoingecko
import pandas as pd
import requests
import seaborn as sb
import matplotlib.pyplot as plt
import plotly.express as px
import sys
from millify import millify
import altair as alt
import streamlit as st

cg = CoinGeckoAPI()
crypto_list = cg.get_coins_list()

##################### STREAMLIT 

st.set_page_config(layout="wide")
st.markdown("<h1 style='text-align: center; color: black;'>Exchanges Liquidity for Hedging</h1>", unsafe_allow_html=True)

with st.form(key='Search', clear_on_submit=False): 
    
    # Define inputs
    
    col_conv = {'green': 3, 'yellow': 2, 'red': 1, None: 0}  # Trustscore conversion    
    all_quotes = ['USDT', 'USDC', 'USD', 'BUSD', 'BTC', 'EUR']
    crypto = st.text_input("Input a crypto", value="", type="default", label_visibility="visible").lower()
    all_exchanges = ['All', 'Binance', 'Huobi', 'OKEX', 'Gate', 'Bitfinex', 'Bittrex',  'Kraken', 'Bitstamp', 'FTX_spot']
    exchange = st.selectbox("Select the exchange", all_exchanges, index=0)
    quote = st.selectbox('Select the quote (for plotting)', all_quotes, index=0)
    submit_button = st.form_submit_button(label='Search')
    
    prova_dict = {'xrp': 'ripple', 'ape': 'apecoin', 'atm': 'atletico-madrid', 
                  'chess': 'tranchess', 'city': 'manchester-city-fan-token', 'comp': 'compound-governance-token', 'crb': 'crb-coin', 
                  'dfi': 'defichain', 'flux': 'zelcash', 'gmt': 'gmt-token', 'grt': 'the-graph', 'kmd': 'komodo', 'lrc': 'loopring'}
    
if submit_button:     
    try:
        if crypto in prova_dict.keys():
            crypto_id = prova_dict[crypto]
        else:
            crypto_id = next((item for item in crypto_list if item['symbol'] == crypto), None)['id']
    except TypeError:
        st.title('Crypto not found!')
        raise st.experimental_rerun()
        
    # Getting the values
    
    df_pairs = pd.DataFrame(columns=['Exchange', 'Base', 'Quote', 'Volume 24h (EUR)', '+2% Depth (EUR)', '-2% Depth (EUR)', 'Last Traded'])
    usd_to_eur = float(pd.DataFrame(requests.get('https://v6.exchangerate-api.com/v6/cd12440f1e8c2480d70af173/pair/USD/EUR').json(), index=[0])['conversion_rate'])
        
    if exchange == "All":
        for i in all_exchanges[1:]:
            depth_prova = cg.get_exchanges_tickers_by_id(id=i.lower(), depth='true', coin_ids=crypto_id)['tickers']
           
            for pair in depth_prova:
                if pair['target'] in all_quotes:
                    date = pair['last_traded_at'].split('T')[0] + ' ' + ((pair['last_traded_at'].split('T')[1]).split('+'))[0]
                    df_pairs = df_pairs.append({'Exchange': i, 'Base': pair['base'], 'Quote': pair['target'], 'Volume 24h (EUR)': float(pair['converted_volume']['usd'])*usd_to_eur,
                                 '+2% Depth (EUR)': float(pair['cost_to_move_up_usd'])*usd_to_eur, '-2% Depth (EUR)': float(pair['cost_to_move_down_usd'])*usd_to_eur,
                                 'Last Traded': date, 'LiquidityScore (0-3)': col_conv[pair['trust_score']]}, ignore_index=True)
                                                     
    else:
        try:
            depth_prova = cg.get_exchanges_tickers_by_id(id=exchange.lower(), depth='true', coin_ids=crypto_id)['tickers']
            
            for pair in depth_prova:
                if pair['target'] in all_quotes:
                    date = pair['last_traded_at'].split('T')[0] + ' ' + ((pair['last_traded_at'].split('T')[1]).split('+'))[0]
                    df_pairs = df_pairs.append({'Exchange': exchange, 'Base': pair['base'], 'Quote': pair['target'], 'Volume 24h (EUR)': float(pair['converted_volume']['usd'])*usd_to_eur,
                                 '+2% Depth (EUR)': float(pair['cost_to_move_up_usd'])*usd_to_eur, '-2% Depth (EUR)': float(pair['cost_to_move_down_usd'])*usd_to_eur,
                                 'Last Traded': date, 'LiquidityScore (0-3)': col_conv[pair['trust_score']]}, ignore_index=True)
        except:
            print('')
    
    # Display the table with the data + metrics
    
    df_pairs = df_pairs.replace('XBT', 'BTC')
    df_pairs = df_pairs.replace('USD', 'USDT')
    
    if exchange == 'All': 
        max_idx = (df_pairs['Volume 24h (EUR)']).idxmax()
        max_exchange = df_pairs['Exchange'][max_idx]
        max_quote = df_pairs['Quote'][max_idx]
        max_p2 = df_pairs['Exchange'][df_pairs['+2% Depth (EUR)'].idxmax()]
        max_m2 = df_pairs['Exchange'][df_pairs['-2% Depth (EUR)'].idxmax()]
        delta_vol = (df_pairs['Volume 24h (EUR)'][(df_pairs['Exchange'] != max_exchange) & (df_pairs['Quote'] == max_quote)].nlargest(2)).iloc[0]
        delta_depth_plus = (df_pairs['+2% Depth (EUR)'][(df_pairs['Exchange'] != max_exchange) & (df_pairs['Quote'] == max_quote)].nlargest(2)).iloc[0]
        delta_depth_minus = (df_pairs['-2% Depth (EUR)'][(df_pairs['Exchange'] != max_exchange) & (df_pairs['Quote'] == max_quote)].nlargest(2)).iloc[0]
        max_quote = df_pairs['Quote'][max_idx]
        st.header(f'Best Liquidity for {crypto.upper()} found on {max_exchange}', anchor=None)
        prova = df_pairs['Volume 24h (EUR)'][max_idx]
        delta_vol = (max(df_pairs['Volume 24h (EUR)'])/delta_vol)*100
        delta_depth_plus = ((df_pairs['+2% Depth (EUR)'][max_idx])/delta_depth_plus)*100
        delta_depth_minus = ((df_pairs['-2% Depth (EUR)'][max_idx])/delta_depth_minus)*100
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label=f'24h Volumes on {max_exchange}', value=millify(prova, precision=2), delta=f"{round(delta_vol, 2)}%")
        col2.metric(label=f'+2% Depth on {max_p2}', value=millify(df_pairs['+2% Depth (EUR)'][max_idx], precision=2), delta=f'{round(delta_depth_plus, 2)}%')
        col3.metric(label=f'-2% Depth on {max_m2}', value=millify(df_pairs['-2% Depth (EUR)'][max_idx], precision=2), delta=f"{round(delta_depth_minus, 2)}%")
        col4.metric(label=f'LiquidityScore on {max_exchange}', value=df_pairs['LiquidityScore (0-3)'][max_idx])
        st.dataframe(df_pairs, use_container_width=True)
    #    st.dataframe(df_pairs.style.highlight_max(axis=0), use_container_width=True)
            
        # Plot Bin and Treemap volumes for specific pairs
    
        base = df_pairs['Base'][0]
        quote = quote.upper()
        sel_pair = base + '/' + quote
        df_plotting = (df_pairs.loc[(df_pairs['Quote'] == quote) & (df_pairs['Base'] == base)]).sort_values('Volume 24h (EUR)', ascending=False)
        df_plotting = (df_plotting.groupby(['Exchange', 'Base', 'Quote'], as_index=False)['Volume 24h (EUR)'].sum()).sort_values('Volume 24h (EUR)', ascending=False)
    
        # STREAMLIT PLOT
        
        st.header(f'{sel_pair} Volumes Plot')
#       st.markdown("<h1 style='text-align: center; color: red;'>f'{sel_pair} Volumes Plot'</h1>", unsafe_allow_html=True)
        bars = alt.Chart().mark_bar().encode(
        x=alt.X('Exchange:O', sort=None),
        y='Volume 24h (EUR):Q',
        color='Exchange:N')
        error_bars = alt.Chart().mark_errorbar(extent='ci').encode(
        x='Exchange:O',
        y='Volume 24h (EUR):Q')
        c = alt.layer(bars, data=df_plotting)   
        st.altair_chart(c, use_container_width=True)
    
    else:
        max_idx = (df_pairs['Volume 24h (EUR)']).idxmax()
        st.title(f'Liquidity for {crypto.upper()} on {exchange}', anchor=None)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(label='24h Volumes (EUR)', value=millify(df_pairs['Volume 24h (EUR)'][max_idx], precision=2))
        col2.metric(label='+2% Depth (EUR)', value=millify(df_pairs['+2% Depth (EUR)'][max_idx], precision=2))
        col3.metric(label='-2% Depth (EUR)', value=millify(df_pairs['-2% Depth (EUR)'][max_idx], precision=2))
        col4.metric(label='Trust Score (0-3)', value=df_pairs['LiquidityScore (0-3)'][max_idx])
        st.dataframe(df_pairs, use_container_width=True)
#    st.bar_chart(data=df_plotting, x='Exchange', y='Volume 24h (EUR)', use_container_width=False)
