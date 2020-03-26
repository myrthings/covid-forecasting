import streamlit as st
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from math import exp, log

#beds in spain by region
spain_beds={'Andalucía':21349,
            'Aragón':5254,
            'Asturias':3785,
            'Baleares':3851,
            'Canarias':7551,
            'Cantabria':2020,
            'Castilla y León':9414,
            'Castilla-La Mancha':5589,
            'Cataluña':34612,
            'Ceuta':252,
            'C. Valenciana':13992,
            'Extremadura':3862,
            'Galicia':9809,
            'Madrid':20516,
            'Melilla':168,
            'Murcia':4909,
            'Navarra':2300,
            'País Vasco':8009,
            'La Rioja':1050,
            'All':158292}

#function to concatenate world and spanish data
def improve_data(world,spain):
    try:
        world.columns=list(world.columns[:4])+[dt.datetime.strptime(date,"%m/%d/%y").strftime("%d/%m/%Y") for date in world.columns[4:]]
    except:
        world.columns=list(world.columns[:4])+[dt.datetime.strptime(date,"%m/%d/%Y").strftime("%d/%m/%Y") for date in world.columns[4:]]

    spain.columns=list(spain.columns[:2])+[dt.datetime.strptime(date,"%Y-%m-%d").strftime("%d/%m/%Y") for date in spain.columns[2:]]
    
    
    world['Province/State']=world['Province/State'].fillna('All')
    selected_countries=list(world.loc[world['Province/State']!='All','Country/Region'].sort_values().unique())
    
    for country in selected_countries:
        all_data=pd.DataFrame(world[world['Country/Region']==country].iloc[:,5:].sum()).T
        all_data['Province/State']='All'
        all_data['Country/Region']=country
        world=pd.concat([world,all_data],axis=0)
        
    
    spain=spain.rename(columns={'CCAA':'Province/State'}).drop('cod_ine',axis=1)[:19]
    spain['Country/Region']='Spain'
        
    new=pd.concat([world,spain],axis=0).drop(['Lat','Long'],axis=1).reset_index(drop=True)
    
    return new
    
#function to separate the region you want to analize
def separate_region(country,region):

    data=pd.concat([confirmed[(confirmed['Country/Region']==country) & (confirmed['Province/State']==region)],
                      deaths[(deaths['Country/Region']==country) & (deaths['Province/State']==region)],
                       recovered[(recovered['Country/Region']==country) & (recovered['Province/State']==region)]],axis=0).drop(
                    ['Province/State','Country/Region'],axis=1)
    
    data=data.T
    data.columns=['Confirmed','Deaths','Recovered']
    data.index=pd.to_datetime(data.index,format="%d/%m/%Y").date
    data=data.sort_index(axis=0,ascending=True)
    data['New Cases']=data['Confirmed'].diff()
    data['New Deaths']=data['Deaths'].diff()
    data['New Recovered']=data['Recovered'].diff()
    data['Current']=data['Confirmed']-data['Deaths']-data['Recovered']
    data.loc[data['New Cases']<0,'New Cases']=0
    data.loc[data['New Deaths']<0,'New Deaths']=0
    data.loc[data['New Recovered']<0,'New Recovered']=0
    data['Change New']=data['New Cases'].pct_change()
    data['Change Deaths']=data['Deaths'].pct_change()
    data['Change Total']=data['Confirmed'].pct_change()
    
    return data[:-1]

#function to get the r of a given region
def get_r(data,column):
    line=data.loc[(data[column]>0)&(data[column]!=data[column].max()),column]
    #r=min(line.median(),line.mean())
    r=line.mean()
    while (r<=0 or r==1) and len(line)>5:
        st.write(r)
        line=line[:-1]
        r=round(min(line.median(),line.mean()),2)
    days_to_duplicate=round(log(2)/log(1+r),2) if r!=0 else None
    return round(1+r,2), days_to_duplicate

        

#function for forecasting data
def forecast_model(model,trozo,r):
    length=len(model)
    #trozo=trozo1
    if trozo>0:
        for num in range(trozo):
            model.append(model[-1]*r)
        
        #pico
        model.append(model[-1]*1.05)
        model.append(model[-1]*1.05)
        model.append(model[-1]*1)
        model.append(model[-1]*0.95)
        model.append(model[-1]*0.95)
        
        length=len(model)
        for num in range(len(df)+days_prediction-length):
            model.append(model[-1]*0.9)
    elif trozo>-2:
        model.append(model[-1]*1)
        model.append(model[-1]*0.95)
        model.append(model[-1]*0.95)
        
        length=len(model)
        for num in range(len(df)+days_prediction-length):
            model.append(model[-1]*0.9)
    
    elif trozo>-3:
        model.append(model[-1]*0.95)
        model.append(model[-1]*0.95)
        
        length=len(model)
        for num in range(len(df)+days_prediction-length):
            model.append(model[-1]*0.9)
        
    else:
        length=len(model)
        for num in range(len(df)+days_prediction-length):
            model.append(model[-1]*0.9)
    return model


#header explanation
'''
# COVID-19: Calculate the danger of a sanitary collapse :ambulance: :hospital:

Coronavirus is officially a pandemic. Since the first case in december the disease has spread fast
reaching almost every corner of the world. They said it's not a severe disease but the number of people
that needs hospital care is growing as fast as the new cases. Some governments are taking measures 
to prevent a sanitary collapse to be able to take care of all these people. I'm tackling
this challenge here. Let's see how some countries/regions are doing! 

'''

'''
> :warning: ***"All models are wrong, some are useful" George Box (statician). This model is a simplification
of how covid-19 can spread in other regions based on what happened in Hubei (Dec-Feb).*** :memo: ***
[Here](http://bit.ly/coronafightdata) you have a repository with the studies, predictions, datasets and more made
around the world with tech and data for you to understand better how covid-19 pandemic behaves.
Contrast the findings and don't use this to misinform.*** :pray: ***Thank you for spreading knowledge and not fear!***
'''

#st.write("[Here](https://medium.com/@myrbarnes) is how this model works.")


#get the world data
wconfirmed=pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",error_bad_lines=False)
wdeaths=pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv",error_bad_lines=False)
wrecovered=pd.read_csv("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv",error_bad_lines=False)

#get the spanish data
spconfirmed=pd.read_csv('https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_casos.csv')
spdeaths=pd.read_csv('https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_fallecidos.csv')
sprecovered=pd.read_csv('https://raw.githubusercontent.com/datadista/datasets/master/COVID%2019/ccaa_covid19_altas.csv')


#improve world data and add spanish data
confirmed=improve_data(wconfirmed,spconfirmed).fillna(0)
deaths=improve_data(wdeaths,spdeaths).fillna(0)
recovered=improve_data(wrecovered,sprecovered).fillna(0)


#sidebar
#st.sidebar.markdown("## Select the region of the world :globe_with_meridians: to study :microscope:")
#country=st.sidebar.selectbox("Country/Region: ",['--']+list(confirmed['Country/Region'].sort_values().unique()))
#region=st.sidebar.selectbox("Province/State: ",confirmed.loc[confirmed['Country/Region']==country,'Province/State'].sort_values().unique() if country!='--' else ['--'])
#st.sidebar.markdown("Data is from [here](https://github.com/CSSEGISandData/COVID-19) for the World and from [here](https://github.com/datadista/datasets/tree/master/COVID%2019) for Spain.")

#no sidebar
st.markdown("## :point_down: Select the region of the world to study")
country=st.selectbox("Country/Region: ",['--']+list(confirmed['Country/Region'].sort_values().unique()))
region=st.selectbox("Province/State: ",confirmed.loc[confirmed['Country/Region']==country,'Province/State'].sort_values().unique() if country!='--' else ['--'])
st.markdown("*Data is from [here](https://github.com/CSSEGISandData/COVID-19) for the World and from [here](https://github.com/datadista/datasets/tree/master/COVID%2019) for Spain.*")



#body of the study    
#if country=='--':
    # st.write(':point_left: **Select the country/region on the sidebar to start.**')
    #st.subheader(':point_left: Select the country/region on the sidebar to start.')
    #st.subheader(':point_up: Select the country/region on the sidebar to start.')
    

#if country!='This' and country!='--':
#    st.write('### :dizzy_face: *The app is suffering due to the high traffic, please, came back later* :dizzy_face:')

if country!='--':  
    
    ############################################################
    # FIRST PART: actual data
    ############################################################
    
    df=separate_region(country,region)
    
    if region=='All':
        st.write("## :globe_with_meridians: You're studying: **{}**".format(country))
    else:
        st.write("## :globe_with_meridians: You're studying: **{}** in **{}**".format(region,country))
        
    st.write("""
First, let's take a look at **how coronavirus is affecting the region**. In the chart below
you can see the distribution of *Confirmed Cases*, *Deaths* and *Recovered* people. We are interested in two parameters here:
 **how many days it takes to duplicate the cases** and **if the cases are growing or controlled** (i.e. if the reproduction rate $R_O$ of the virus is > or <1).""")
    
    #st.write(df)
    
    #st.line_chart(df[['New Cases','New Deaths','New Recovered']])
    
    # Plot the first chart
    fig = go.Figure()
    # Build the first line
    ConfTrace = go.Scatter(
        x=df.index[:-1:2],
        y=df['Confirmed'][:-1:2],
        name="Confirmed Cases",
        line=dict(color='MediumSeaGreen'),
        hovertemplate = # Custom tooltip
          '<br><b>Date</b>: %{x}<br>' +
          '<b>Infected</b>: %{y:.2s} people',
        line_shape='spline'
          )
    # Build the second line
    DeathTrace = go.Scatter(
        x=df.index[:-1:2], 
        y=df['Deaths'][:-1:2],
        name="Deaths",
        line=dict(color='Red'),
        hovertemplate =
          '<br><b>Date</b>: %{x}<br>' +
          '<b>Deaths</b>: %{y:.2s} people',
        line_shape='spline'
      )
    RecovTrace = go.Scatter(
        x=df.index[:-1:2], 
        y=df['Recovered'][:-1:2],
        name="Recovered",
        line=dict(color='Blue'),
        hovertemplate =
          '<br><b>Date</b>: %{x}<br>' +
          '<b>Recovered</b>: %{y:.2s} people',
        line_shape='spline'
      )
    # Add labels
    fig.update_layout(
          title="Current Data of Infected People",
          xaxis_title="Time (days)",
          yaxis_title="Nº of People Infected",
      )
    # Modify the legend
    fig.update_layout(
          legend=dict(
              x=0,
              y=-0.2,
              orientation="h"
          )
      )
    # Add the lines to the chart
    fig.add_trace(ConfTrace)
    fig.add_trace(DeathTrace)
    fig.add_trace(RecovTrace)
    # Draw the chart
    chart = st.plotly_chart(fig)
    
    #get the r
    r,days_duplicate=get_r(df[df.index>=df.index.max()-dt.timedelta(days=10)],"Change Total")
    days_duplicate=round(days_duplicate,2) if days_duplicate is not None else "Infinity"
    # Explain the chart
    controlled=(df.index.max()-df["New Cases"].idxmax()).days>=7

    terminar=False
    if len(df[df['New Cases']>0])<7:
        st.write(">### There's not enough cases in *{}* to create a forecast.".format(country))
        terminar=True
    
        
    elif region=='All' and controlled:
        st.write(">### For the last 10 days in",country," cases are duplicating every",days_duplicate,"days with an $R_0$ of",round(r,2),
                 ". The peak of new cases was on",df["New Cases"].idxmax(),". From that day the virus is growing at a lower rate.")
    
    elif region=='All':
        st.write(">### For the last 10 days in",country," cases are duplicating every",days_duplicate,"days with an $R_0$ of",round(r,2),
                 ". The number of cases is still growing.")
    
    elif region!='All' and controlled:
        st.write(">### For the last 10 days in",region," cases are duplicating every",days_duplicate,"days with an $R_0$ of",round(r,2),
                 ". The peak of new cases was on",df["New Cases"].idxmax()," From that day the virus is growing at a lower rate.")
    else:
        st.write(">### For the last 10 days in",region," cases are duplicating every",days_duplicate,"days with an $R_0$ of",round(r,2),
                 ". The number of cases is still growing")
        
    ############################################################
    # SECOND PART: forecast
    ############################################################
    
    if not terminar:
        
        st.write("### :date: Let's forecast the number of *real* cases in the near future...")
        st.write("""
Current numbers given by governments are *confirmed* cases of the virus achieved by using testing kits. However, to assess the risk of sanitary collapse we need to estimate how many *real* cases there are. 

This is a tough task to generalize because every country is doing a different number and different kinds of tests.
For that reason I based this study in **two models**:
    
- **:skull: Deaths model:** [This model](https://jamanetwork.com/journals/jama/fullarticle/2762130) uses **death rate** and **days until death** to give us a better idea of how many cases are in a given day. It's said that the **death rate** is almost constant (~1%), although we some differences between countries due to low-risk patients not being tested (and therefore not included in the numbers). We also know
that between the first symptoms and death there's an average of **22 days**.

- **:last_quarter_moon: Phase-adjusted model:** Studies say the virus can spread *before* symptoms. It takesan average of 5 days to develop
the symptoms. This means that people got infected more or less a week before their diagnosis. Therefore, by shifting current *detected* cases by a week we can estimate the *real* number of cases.
More [here](https://www.nature.com/articles/s41421-020-0148-0).

With this information and the days to duplicate we can forecast the real number of people that have the virus. Now, let's assume that **an average of 20% of the
people** infected will need hospital care, so we can forecast also the **number of beds** needed for the given region.
""")
        st.write("### :cop: ...and see how they change with social distancing.")
        st.write("""To stop the uncontrolled growth some governments are encouraging the citizens to stay at home and have
even restricted movements inside the country. This social distancing is a way to stop the virus. Below, you can **experiment with the date in which measures are enforced** to see how earlier or later enformecents affects the **healthcare system**. 
""")
        
        
        #parameters
        percentage_deaths=1
        st.markdown("### :point_down: Change the date government measures start.")# (after {} for {})".format(df[df['Confirmed']>50].index.min(),region if region!='All' else country))
        date_measures=st.date_input("Date of government measures to stop the virus: ")
        
        incubation_period=5
        symptom_to_death=17
        symptom_to_recovery=22
        percentage_hosp=0.2
        death_delay=symptom_to_death+incubation_period
        recovery_delay=symptom_to_death+incubation_period
        symptom_delay=incubation_period+round(symptom_to_death/2)
        
        
        #new r
        df2=df[df.index<date_measures+dt.timedelta(days=5)]
        r,days_duplicate=get_r(df2[(df2.index>df2.index.max()-dt.timedelta(days=15))&(df2.index<=date_measures)],"Change Total")
        time_to_measure=(df2.index.max()-date_measures).days
        #st.write(r,days_duplicate)
        
        #days to forecast
        days_prediction=100
        
        try:
            #deaths model
            death_model=list(map(lambda x: x*1/(percentage_deaths/100),list(df2['New Deaths'])[death_delay:]))
            while len(death_model)>5 and death_model[-1]<=0:
                death_model=death_model[:-1]
            length=len(death_model)
            death_model=forecast_model(death_model,len(df2)-length-time_to_measure,r)
            
            #phase adjusted model
            latency_model=list(df2['New Cases'])[symptom_delay:]
            while len(latency_model)>5 and latency_model[-1]<=0:
                latency_model=latency_model[:-1]
            length=len(latency_model)
            latency_model=forecast_model(latency_model,len(df2)-length-time_to_measure,r)
            
            #real new cases
            new_cases=list(df2['New Cases'])
            while len(new_cases)>5 and new_cases[-1]<=0:
                new_cases=new_cases[:-1]
            length=len(new_cases)
            new_cases=forecast_model(new_cases,len(df2)-length-time_to_measure+symptom_delay,r)
            
            #st.write(len(death_model),len(latency_model),len(new_cases))
            
            
            #new deaths
            new_deaths1=list(df2['New Deaths'])
            new_deaths2=[0]*death_delay+list(map(lambda x: (percentage_deaths/100)*x,death_model[:-death_delay]))
            new_deaths=new_deaths1[:]+new_deaths2[len(new_deaths1):]
            
            #new recovery for death model
            new_recov1=list(df2['New Recovered'])
            new_recov2=[0]*recovery_delay+list(map(lambda x: (1-(percentage_deaths/100))*x,death_model[:-recovery_delay]))
            new_recov=new_recov1[:]+new_recov2[len(new_recov1):]
            
            #new recovery for little model
            latency_cosa=[0]*recovery_delay+latency_model[:-recovery_delay]
            new_recov_latency=[latency_cosa[n]-new_deaths[n] for n in range(len(latency_cosa))]
            
            #dates
            fechas=list(df.index)+[df.index.max()+dt.timedelta(days=n) for n in range(days_prediction)]
            
            #st.write(len(death_model),len(latency_model),len(new_cases),len(new_deaths),len(new_recov),len(fechas))
            
            #st.write(df)
            
            
            #check the curves
            new_df=pd.DataFrame({'death_model':death_model,
                                'latency_model':latency_model,
                                'new_cases':new_cases,
                                'new_deaths':new_deaths,
                                'new_recov':new_recov,
                                'new_recov_lat':new_recov_latency,
                                'date':fechas}).set_index('date').fillna(0)
                
            #st.line_chart(new_df)
            
            new_df['total_cases']=new_df['new_cases'].cumsum()
            new_df['total_deaths']=new_df['new_deaths'].cumsum()
            new_df['total_recovery']=new_df['new_recov_lat'].cumsum()
            new_df['current_cases']=new_df['total_cases']-new_df['total_deaths']-new_df['total_recovery']
            new_df['bed_needs']=new_df['current_cases']*percentage_hosp
            
            #st.line_chart(new_df[['total_cases','total_deaths','total_recovery']])
            
            #get the beds for spain
            if country=='Spain':
                bed_num=spain_beds[region]
                new_df['current_beds']=bed_num
                #st.line_chart(new_df[['current_cases','bed_needs','current_beds']])
            
            new_df=new_df[new_df["current_cases"]>10]
            
            
            # Initialize the chart
            fig = go.Figure()
            # Build the first line
            currentTrace = go.Scatter(
                x=new_df.index[::2],
                y=new_df['current_cases'][::2],
                name="Predicted Cases at the Same Time",
                line=dict(color='MediumSeaGreen'),
                fill='tozeroy',
                hovertemplate = # Custom tooltip
                  '<br><b>Date</b>: %{x}<br>' +
                  '<b>Cases at the same time</b>: %{y:.2s}',
                line_shape='spline'
                  )
            # Build the second line
            bedTrace = go.Scatter(
                x=new_df.index[::2], 
                y=new_df['bed_needs'][::2],
                name="Predicted Cases with Hospitalization Needs",
                line=dict(color='Red'),
                fill='tozeroy',
                hovertemplate =
                  '<br><b>Date</b>: %{x}<br>' +
                  '<b>Patients with Hospitalization</b>: %{y:.2s} Needs',
                line_shape='spline'
              )
            # Build the first line
            df_plot=df[df.index>=new_df.index.min()]
            realTrace = go.Scatter(
                x=df_plot.index[::2],
                y=df_plot['Current'][::2],
                name="Current real cases",
                line=dict(color='Blue'),
                fill='tozeroy',
                mode='lines',
                hovertemplate = # Custom tooltip
                  '<br><b>Date</b>: %{x}<br>' +
                  '<b>Current cases at the same time</b>: %{y:.2s}',
                line_shape='spline'
                  )
            
            # Build the Today indicator
            max_chart=max(new_df['current_cases'].max(),bed_num) if country=='Spain' else new_df['current_cases'].max()
            todayTrace=go.Scatter(
                    x=[df.index.max(),df.index.max()],
                    y=[0,max_chart+10],
                    mode='lines',
                    line=dict(color='grey',dash='dash'),
                    name='Today')
    
            #Build the actual beds reference for spain
            if country=='Spain':
                actualBedsTrace = go.Scatter(
                    x=new_df.index[::2], 
                    y=new_df['current_beds'][::2],
                    name="Total Beds (Public and Private) in the Region",
                    line=dict(color='grey'),
                    hovertemplate =
                      '<br><b>Date</b>: %{x}<br>' +
                      '<b>Bed</b>: %{y:.2s} Needs',
                    line_shape='spline'
                  )
            
            # Add labels
            fig.update_layout(
                  title="Forecast of People Infected at the Same Time",
                  xaxis_title="Time (days)",
                  yaxis_title="Nº of People Infected",
              )
            # Modify the legend
            fig.update_layout(
                  legend=dict(
                      x=0,
                      y=-0.2,
                      orientation="h"
                  )
              )
            # Activate tooltip comparison mode  
            #fig.update_layout(hovermode='x')
            # Add the lines to the chart
            fig.add_trace(currentTrace)
            fig.add_trace(bedTrace)
            fig.add_trace(realTrace)
            fig.add_trace(todayTrace)
            if country=='Spain':
                fig.add_trace(actualBedsTrace)
            
            
            
            #write the conclusion
            max_beds=round(new_df['bed_needs'].max())
            max_beds=max_beds if max_beds<1000 else round(max_beds/1000)*1000
            day_max_beds=new_df['bed_needs'].idxmax()
            
            days_duplicate=round(days_duplicate,2) if days_duplicate is not None else "Infinity"
            
            
            if country=="Spain":
                bed_rate=max_beds/bed_num
                
                if bed_rate>1:
                    st.write(">### The peak beds needed is ~",int(max_beds),
                     ". It will occur around",day_max_beds,". That's {:0.2%} of the actual number of beds. <span style='color: red'>You will need more beds!</span>".format(bed_rate), unsafe_allow_html=True)
                elif bed_rate>0.5:
                    st.write(">### The peak beds needed is ~",int(max_beds),
                     ". It will occur around",day_max_beds,". That's {:0.2%} of the actual beds. <span style='color: green'>Great if they can all be used for COVID-19!</span>".format(bed_rate), unsafe_allow_html=True)
                else:
                    st.write(">### The peak beds needed is ~",int(max_beds),
                     ". It will occur around",day_max_beds,". That's {:0.2%} of the actual beds. <span style='color: green'>This is great!</span>".format(bed_rate), unsafe_allow_html=True)
            else:
                st.write(">### The date of peak necessity will be around",day_max_beds,
                     ". The healthcare system will need ~", int(max_beds)," beds. Make sure there are enough :pray:!")
            
            st.write("*During the 10 days before",date_measures,"the cases duplicated every", days_duplicate,"days.*")
            # Draw the chart
            chart = st.plotly_chart(fig)
            
            
        except:
            st.write("### :warning: There's not enough data before that date to create a forecast, select other :warning:")
            
        # Warning
        st.write(""">:warning: *Note: Forecasting the covid pandemic is a complex problem. Although this model uses real data, assumptions made to forecast are based on Hubei (China) case and do not necessarily
match the reality for any other country. Take this as an experiment to see how little variations in time can change a lot the scenario for the health system. Don't forget to follow your local
government health and safety regulations!*""")
        
        st.write("""### :question: FAQ
- **Why sometimes it grows so high?**

The higher $$R_{0}$$, the faster the growth. For early phases of the data the changes are usually higher because it is easier to grow from 1 to 2 than to 1000 to 2000 in one day.
It's also possible to do 4 test and get 2 positive, than to do 40000 to get 20000 positives in one day. Data is constrained also with by the number of tests done.
        
- **It's better to start social distancing earlier than later. Why in some cases this doesn't happen in this model?** 

For forecasting purposes the $$R_{0}$$ used is the one 10 days before measures start. This lead to little changes in the data that can change completely the model.

                 """)
        
        
        # Bibliography
        st.write("""### :book: Parameters bibliography

- Percentage of deaths: 1% [*MIDAS Network*](https://github.com/midas-network/COVID-19)
- Incubation period: 5 days [*MIDAS Network*](https://github.com/midas-network/COVID-19)
- Period from symptoms to recovery: 22 days [*MIDAS Network*](https://github.com/midas-network/COVID-19)
- Period from symptom to death: 17 days [*MIDAS Network*](https://github.com/midas-network/COVID-19)
- Percentage of people with hospitalization needs: 20% [*Information is Beautiful*](https://informationisbeautiful.net/visualizations/covid-19-coronavirus-infographic-datapack/)
- Period from the start of social distancing to decrease the reproduction number: 5 days [*Reference from Hubei*](https://jamanetwork.com/journals/jama/fullarticle/2762130)
- Reproduction number after social distancing measures: 0.9 [*hypothesis for Hubei*](https://www.nature.com/articles/s41421-020-0148-0)
- Number of hospital beds for Spain: data from [Spanish Ministry of health](https://www.mscbs.gob.es/ciudadanos/hospitales.do?tipo=camas)
""")
        
        #Math part
        st.write("""### :bar_chart: The math behind it
I chosed to use sequences and series instead of the [SIR](https://flattenthecurve.herokuapp.com/)
or [SEIR](http://gabgoh.github.io/COVID/index.html) differential equations models to use the actual experimental data.
""")
        
        st.write("First we get the vector of new cases:")
        st.latex('n<dsd+ip: NC_{n}=NC_{n-ip}*r')
        st.latex('n<dsd+ip+5: NC_{n}=NC_{n-ip}')
        st.latex('n>=dsd+ip+5: NC_{n}=NC_{n-ip}*0.9')
        
        st.write("Then we get the accumulated number of cases:")
        st.latex('AC_{n}=\sum_{i=0}^{n} NC_{i}')
        
        st.write("With this data we get the new deaths and accumulated deaths. And the same for recovered cases:")
        st.latex('ND_{n}=NC_{n-sd}*dr \quad ; \quad AD_{n}=\sum_{i=0}^{n} ND_{i}')
        st.latex('NR_{n}=NC_{n-sr}*(1-dr) ; AR_{n}=\sum_{i=0}^{n} NR_{i}')
            
        st.write("At the end we calculate the number of cases day by day and the ones with hospitalize needs:")
        st.latex('CC_{n}=AC_{n}-AD_{n}-AR_{n}')
        st.latex('HC_{n}=CC_{n}*hr')
        
        st.write('''
*Legend:*

**NC**: New Cases, **AC**: Acumulated Cases, **CC**: Current Cases, **HC**: Hospitalized Cases,

**ND**: New Deaths, **AD**: Acumulated Deaths,

**NR**: New Recovered, **AR**: Acumulated Recovered,

**dr**: death rate, **hr**: hospitalized rate, **dsd**: date social distancing starts,
**sd**: from syptoms to death, **sr**: from sypmtoms to recovery, **ip**: incubation period in days.
                 ''')
        
                 
        # End
        st.write(""">### :bug: Report a bug? Enrich data from your country? More ideas? Check [the project](https://github.com/myrthings/covid-forecasting) on Github!""")

            
        
        
        
## pie
st.write("----------")
st.write("Made with :heart: in Lorca by [myrthings](https://github.com/myrthings)")
        
