import json
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
P=Path(__file__).parent
st.set_page_config(page_title='ABM 2.0 | Амурская область',layout='wide')
st.markdown('''<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');html,body,[data-testid="stApp"],button,input{font-family:Montserrat,sans-serif!important}[data-testid="stApp"]{background:#041735;color:#fff}[data-testid="stSidebar"]{background:#061e44}h1,h2,h3,p,label{color:#fff!important}div[data-testid="stMetric"]{background:#092957;border:1px solid #1747bd;border-radius:12px;padding:12px}div[data-testid="stMetricValue"]{color:#4bd7ff!important}</style>''',unsafe_allow_html=True)
@st.cache_data
def load():
    return [pd.read_csv(P/f) for f in ['indicators.csv','age_targets.csv','age_rates.csv','projects.csv','abm_age_sex.csv','abm_total.csv','validation_2036.csv']],json.loads((P/'municipalities.geojson').read_text())
(ind,ages,rates,projects,abm,total,validation),geo=load()
mos=sorted(ind.loc[ind.mo!='АО','mo'].unique())
with st.sidebar:
    st.title('АМУРСКАЯ ОБЛАСТЬ')
    mo=st.selectbox('Муниципалитет',['АО']+mos,format_func=lambda s:'Вся область' if s=='АО' else s)
    year=st.slider('Год',2026,2036,2036)
    page=st.radio('Раздел',['Карта и прогноз','Все показатели','Возрастная структура','Мероприятия','Проверка ABM'])
    st.caption('Медицина — #00AEFF · Немедицинские — #F02A91')
def val(m,name,y):
    x=ind[(ind.mo==m)&(ind.metric==name)].sort_values('year')
    return float(np.interp(y,x.year,x.value)) if len(x) else None
def pop(m,y):
    return float(np.interp(y,total.year,total.abm)) if m=='АО' else float(abm[(abm.mo==m)&(abm.year==y)].abm.sum())
def nice(x,d=0):return '—' if x is None else f'{x:,.{d}f}'.replace(',',' ').replace('.',',')
def style(fig,h=350):
    fig.update_layout(height=h,paper_bgcolor='#041735',plot_bgcolor='#041735',font_color='#e7f6ff',margin=dict(l=10,r=10,t=25,b=10),legend=dict(orientation='h'),xaxis=dict(gridcolor='#1747bd'),yaxis=dict(gridcolor='#1747bd'))
    return fig
st.caption('АГЕНТ-ОРИЕНТИРОВАННАЯ МОДЕЛЬ · 29 МО · 2026–2036')
st.title('СЦЕНАРНОЕ МОДЕЛИРОВАНИЕ НАСЕЛЕНИЯ И СМЕРТНОСТИ')
st.subheader(f'{"Амурская область" if mo=="АО" else mo} · {year}')
a,b,c,d=st.columns(4)
a.metric('Население ABM',nice(pop(mo,year)))
b.metric('ОПЖ мужчин',nice(val(mo,'ОПЖ мужчины',year),1))
c.metric('ОПЖ женщин',nice(val(mo,'ОПЖ женщины',year),1))
d.metric('КСР',nice(val(mo,'Коэффициент суммарной рождаемости',year),2))
if mo=='АО':
    st.info('ABM в 2036 году: 753 200 жителей; контрольный прогноз — 752 878. Совпадение получено с балансирующей калибровкой, а не независимым доказательством эффекта проектов.')
else:
    v=validation[validation.mo==mo]
    if len(v):st.info(f'Отклонение ABM от контрольного прогноза в 2036 году: {v.iloc[0].error_pct:+.2f}%. Эффект отдельных проектов на смертность пока не идентифицирован.')
if page=='Карта и прогноз':
    l,r=st.columns([1.4,1])
    with l:
        df=pd.DataFrame({'mo':mos,'population':[pop(m,year) for m in mos]})
        fig=px.choropleth_mapbox(df,geojson=geo,locations='mo',featureidkey='properties.NAME',color='population',hover_name='mo',mapbox_style='carto-positron',zoom=4.6,center={'lat':52.6,'lon':127.5},opacity=.7,color_continuous_scale=['#aee8ff','#4bd7ff','#00aeff','#0255ff'])
        fig.update_traces(marker_line_color='#00aeff',marker_line_width=1)
        fig.update_layout(height=550,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor='#041735',font_color='white')
        st.plotly_chart(fig,use_container_width=True)
        st.caption('Контуры 29 МО — предоставленный GeoJSON. Подложка Carto; Яндекс Карты потребуют отдельного подключения API.')
    with r:
        if mo=='АО':x=total
        else:x=abm[abm.mo==mo].groupby('year',as_index=False)[['abm','target']].sum()
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=x.year,y=x.abm,name='ABM',line=dict(color='#00aeff',width=3)))
        fig.add_trace(go.Scatter(x=x.year,y=x.target,name='Контроль',line=dict(color='#aee8ff',dash='dot')))
        st.plotly_chart(style(fig,310),use_container_width=True)
        subset=projects if mo=='АО' else projects[projects.mo.isin([mo,'АО'])]
        counts=subset.category.value_counts()
        fig=go.Figure(go.Bar(x=['Медицинские','Немедицинские'],y=[counts.get('Медицинские',0),counts.get('Немедицинские',0)],marker_color=['#00aeff','#f02a91']))
        st.plotly_chart(style(fig,220),use_container_width=True)
elif page=='Все показатели':
    st.caption('Между опорными годами значения интерполированы для визуализации; это не отдельный ежегодный прогноз.')
    names=ind.metric.unique()
    st.dataframe(pd.DataFrame({'Показатель':names,'Значение':[val(mo,n,year) for n in names]}),use_container_width=True,hide_index=True)
    kind=st.selectbox('Возрастные коэффициенты',sorted(rates.group.unique()))
    y=min([2026,2031,2036],key=lambda t:abs(t-year))
    g=rates[(rates.mo==mo)&(rates.group==kind)&(rates.year==y)]
    st.caption(f'Возрастные коэффициенты: опорный год {y}; единицы из Excel, без изменения масштаба.')
    st.dataframe(g[['gender','age','value','unit']],use_container_width=True,hide_index=True)
    if len(g):
        fig=px.line(g,x='age',y='value',color='gender',markers=True,color_discrete_map={'М':'#00aeff','Ж':'#f02a91'})
        st.plotly_chart(style(fig),use_container_width=True)
elif page=='Возрастная структура':
    g=abm[abm.year==year]
    if mo!='АО':g=g[g.mo==mo]
    g=g.groupby(['gender','age_bin'],as_index=False).abm.sum()
    g['age']=g.age_bin.map(lambda k:f'{k*5}–{k*5+4}' if k<17 else '85+')
    g['signed']=np.where(g.gender=='М',-g.abm,g.abm)
    fig=px.bar(g,x='signed',y='age',color='gender',orientation='h',barmode='relative',color_discrete_map={'М':'#00aeff','Ж':'#f02a91'})
    st.plotly_chart(style(fig,580),use_container_width=True)
    st.warning('Текущий экспорт ABM содержит пятилетние группы. Однолетние возраста нельзя достоверно восстановить без повторного экспорта реестра агентов.')
elif page=='Мероприятия':
    f=st.radio('Тип',['Все','Медицинские','Немедицинские'],horizontal=True)
    p=projects if mo=='АО' else projects[projects.mo.isin([mo,'АО'])]
    if f!='Все':p=p[p.category==f]
    st.metric('Распознанных записей',len(p))
    st.dataframe(p[['mo','title','category','settlement','address','period','investment']],use_container_width=True,hide_index=True)
    st.warning('Пока нет геокодированных координат и причинно идентифицированного вклада проектов в предотвращённые смерти. Не приписываем каждому проекту выдуманный эффект.')
elif page=='Проверка ABM':
    st.dataframe(validation,use_container_width=True,hide_index=True)
    st.download_button('Скачать CSV',validation.to_csv(index=False).encode('utf-8-sig'),'validation_2036.csv')
    st.warning('В текущей версии балансирующая миграция подгоняет население к контрольным значениям; рождаемость, смертность и миграция ещё не откалиброваны независимо.')
st.divider()
st.caption('Источники: ии3.xlsx; проекты дорожной карты ии.xlsx; контуры мо.geojson; результаты первого прогона ABM. Исследовательский прототип.')
