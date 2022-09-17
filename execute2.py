from ctypes.wintypes import PINT
from json import load
from re import X
from tkinter import CENTER
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


max_charge_power_capacity = 10. #MW
max_discharge_power_capacity = 10. #MW
dod_batery=1.-0.92 # El valor máximo de descarga que usemos para la simulación # TODO Cambiar valor según la tecnología a simular
initial_level=(dod_batery*max_discharge_power_capacity)*5 # TODO Cambiar valor según la tecnología a simular

all_hourly_charges = np.load('apoyo_sim_1.npy',allow_pickle=True)
all_hourly_discharges = np.load('apoyo_sim_2.npy',allow_pickle=True)
all_hourly_state_of_energy = np.load('apoyo_sim_3.npy',allow_pickle=True)
all_daily_discharge_throughput = np.load('apoyo_sim_4.npy',allow_pickle=True)

tabla=pd.read_csv('data_pmd\export_PrecioMedioHorarioComponenteMercadoDiario _2022.csv', sep=';')
all_data_sim_time = pd.DataFrame(data=tabla)
all_data_sim_time.index = pd.DatetimeIndex(pd.to_datetime(all_data_sim_time['datetime'], format='%Y/%m/%d %H:%M'))
all_data_sim_time = all_data_sim_time.iloc[: , 1:]
#print(all_data_sim_time.head())
#print(all_data_sim_time.tail())

#These indicate flows during the hour of the datetime index
all_data_sim_time['Charging power (kW)'] = all_hourly_charges
all_data_sim_time['Discharging power (kW)'] = all_hourly_discharges
all_data_sim_time['Power output (kW)'] =  all_hourly_discharges - all_hourly_charges
#This is the state of power at the beginning of the hour of the datetime index 
all_data_sim_time['State of Energy (kWh)'] = np.append(initial_level, all_hourly_state_of_energy[0:-1])
all_data_sim_time['Revenue generation (€)'] = all_data_sim_time['Discharging power (kW)'] * all_data_sim_time['value']
all_data_sim_time['Charging cost (€)'] = all_data_sim_time['Charging power (kW)']* all_data_sim_time['value']
all_data_sim_time['Profit (€)'] = all_data_sim_time['Revenue generation (€)']- all_data_sim_time['Charging cost (€)']
all_data_sim_time['Revenue generation (€)'].sum()

# Resultados y comprobaciones

print(f"Beneficios totales: {(all_data_sim_time['Profit (€)'].sum())} (€)")
avg_profit=np.average(all_data_sim_time['Profit (€)'])
max_profit=np.max(all_data_sim_time['Profit (€)'])
min_profit=np.min(all_data_sim_time['Profit (€)'])
print(f'Beneficio medio diario: {avg_profit} (€)')
print(f'Beneficio máximo horario: {max_profit} (€)')
print(f'Beneficio mínimo horario: {min_profit} (€)')
pm_min = np.min(all_data_sim_time['value'])
pm_max = np.max(all_data_sim_time['value'])
print(f'Precio Marginal Máximo (€/MWh): {pm_max}')
print(f'Precio Marginal Mínimo (€/MWh): {pm_min}')
e_descargada=sum(all_daily_discharge_throughput)
print(f'Energía total descargada en un año: {e_descargada} (MWh)')

# Guardamos el dataframe de resultados para trabajar con ellos en Excel:

df = pd.DataFrame(all_data_sim_time)
df.to_csv('data_graphs\export_resultados_hidro_2022.csv') # TODO Cambiar nombre según archivo a exportar

# Gráficas de resultados
# TODO quitar comentarios para plotear gráficas

mpl.rcParams["figure.figsize"] = [6,5]
mpl.rcParams["figure.dpi"] = 100
mpl.rcParams.update({"font.size":12})
plt.hist(all_hourly_discharges - all_hourly_charges)
plt.title('Hourly power output')
plt.ylabel('Nº de Horas')
plt.xlabel('MW')
plt.show()

#plt.hist(all_hourly_state_of_energy)
#plt.xlabel('MWh')
#plt.title('Hourly state of energy')
#plt.show()

#all_data_sim_time['Profit (€)'].resample('M').sum().plot()
#plt.title('Beneficio mensual (€)')
#plt.xlabel('Mes')
#plt.ylabel('Beneficio (€)')
#plt.show()

#all_data_sim_time['value'].resample('Y').plot()
#plt.title('Precio marginal horario (€/MWh)')
#plt.ylabel('Precio marginal (€/MWh)')
#plt.xlabel('Mes')
#plt.show()
