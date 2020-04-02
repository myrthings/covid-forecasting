# COVID-19: Calculate the danger of a healthcare collapse :ambulance: :hospital:
This respository is the code for [this app](https://covid-forecasting.herokuapp.com/). It forecasts the impact of social distancing to stop the spread of the COVID-19 virus in different countries, and how much it affects the healthcare system.

<p align="center"> 
<img src="gif-covid.gif">
</p>

## Context 🦠
In December 2019 the first cases of COVID-19 or SARS-COV-2 appeared in the city of Wuhan, in the state of Hubei, in China. Since that day, the disease started to spread every day faster and further than the day before. The 23rd of June, government authorities locked down the region (size of France, for Europeans to compare) with just 300 cases diagnosed. The number of cases rose for more than a week due to the incubation period of the disease, but then, started to fall. On March, the disease "curved" in Wuhan and they started to control the cases. The city is expected to open again in April.

## Solution :microscope:
The impact of the lockdown was studied as it was happening and some of the results are [here](https://jamanetwork.com/journals/jama/fullarticle/2762130), [here](https://www.nature.com/articles/s41421-020-0148-0) and [here](https://github.com/midas-network/COVID-19). I used the result of all of these experimental studies to forecast the impact of government measures in regions all over the world (that have data [here](https://github.com/CSSEGISandData/COVID-19)).

## Development :gear:
[Streamlit](https://www.streamlit.io/) is used to quickly create a pretty GUI for the data and results. The app is deployed in [Heroku](https://www.heroku.com/)

## Version 👩‍💻
- **V.1:** First version. The user can change the region on a sidebar and then the date of the government measures in the body.
- **V.2:** Deleted the sidebar because of problems when a lot of traffic running on Heroku.
- **V.3:** Update Streamlit to version 57. Caching for data load. Sidebar returned.
