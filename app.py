import streamlit as st
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection


url = 'https://docs.google.com/spreadsheets/d/1GT-lA0T4XvYePkuIftZBX-dvcqGSujZ3QM3mXRSieTY/edit?usp=sharing'
if not 'data' in st.session_state:
    conn = st.experimental_connection("gsheets", type=GSheetsConnection,ttl=600)
    st.session_state['data'] = conn.read(usecols=[0, 1, 2]).dropna()

data = st.session_state['data']
    


def expected_score(rating_1,rating_2):
    expected_score_1 = (1.0 / (1.0 + pow(10, ((rating_2-rating_1) / 400))))
    expected_score_2 = (1.0 / (1.0 + pow(10, ((rating_1-rating_2) / 400))))
    return [expected_score_1,expected_score_2]

def k_factor(games_played):
    if games_played < 5:
        return 48
    elif games_played < 20:
        return 36
    else: 
        return 24

def rating_change(player,opponent,result):
    player_rating = data[data.Player == player].Rating.tolist()[0]
    opponent_rating = data[data.Player == opponent].Rating.tolist()[0]
    player_games_played = data[data.Player == player]['Games Played'].tolist()[0]
    
    k = k_factor(player_games_played)
    
    if not result in ['Win','Loss','Draw']:
        return 'Invalid Result'
    if result == 'Win':
            r = 1
    elif result == 'Loss':
            r = 0
    else:
        r = 0.5
    
    player_expected_score = expected_score(player_rating,opponent_rating)[0]
    
    rating_change = round(k * (r - player_expected_score))
    new_rating = player_rating + rating_change
    
    return {'old_rating':player_rating,'new_rating':new_rating,'rating_change':rating_change}

    


st.title('Ramsey Chess ELO')
container = st.empty()
with container:
    st.dataframe(data.sort_values(by='Rating',ascending=False).reset_index(drop=True),hide_index=True,use_container_width = True)
results = ['Win','Draw','Loss']

with st.expander('Submit a Result'):

    p = st.selectbox('Player',data.Player.tolist()) 
    o = st.selectbox('Opponent',[i for i in data.Player.tolist() if not i == p])
    r = st.selectbox('Result',results)
    opposite_result = results[2-results.index(r)]

    button_cols = st.columns(3)

    metric_container = st.container()

    with button_cols[0]:
        if st.button('Submit Result'):
            with metric_container:
                st.subheader('Rating Updates')
                cols = st.columns(2)

                player_changes = rating_change(p,o,r)
                por = round(player_changes['old_rating'])
                pnr = round(player_changes['new_rating'])
                prc = round(player_changes['rating_change'])

                opp_changes = rating_change(o,p,opposite_result)
                oor = round(opp_changes['old_rating'])
                onr = round(opp_changes['new_rating'])
                orc = round(opp_changes['rating_change'])


                with cols[0]:
                    st.metric(p,f'{por} -> {pnr}',prc)
                with cols[1]:
                    st.metric(o,f'{oor} -> {onr}',orc)

                data['Games Played'] = np.where(data['Player'].isin([o,p]),data['Games Played'] + 1,data['Games Played'])
                data['Rating'] = np.where(data['Player'].isin([p]),pnr,data['Rating'])
                data['Rating'] = np.where(data['Player'].isin([o]),onr,data['Rating'])

            st.session_state['data'] = data
            with container:
                st.dataframe(data.sort_values(by='Rating',ascending=False).reset_index(drop=True),hide_index=True,use_container_width = True)
    with button_cols[1]:
        if st.button('Update Database'):
            conn = st.experimental_connection("gsheets", type=GSheetsConnection,ttl=600)
            conn.update(data=data)
            st.rerun()
    with button_cols[2]:
        if st.button('Refresh'):
            st.cache_data.clear()
            conn = st.experimental_connection("gsheets", type=GSheetsConnection,ttl=600)
            st.session_state['data'] = conn.read(usecols=[0, 1, 2]).dropna()
            st.rerun()
