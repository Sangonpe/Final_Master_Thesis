# Código para el almacenaminto

from tkinter import CENTER
import pandas as pd
import numpy as np
import codigo_tfm_prog_objetos as tfm


if __name__ == '__main__':
    # Fichero del cual obtenemos los precios de la energía 
    precios = pd.read_csv('data_pmd\export_PrecioMedioHorarioComponenteMercadoDiario _2019.csv', sep=';') # TODO Crear carpeta data_pmd para guardar los ficheros a leer
    

    # Parámetros de nuestro almacenamiento:

    max_charge_power_capacity = 10. #MW
    max_discharge_power_capacity = 10. #MW
    dod_batery=1-0.92 # TODO Cambiar valor según la tecnología a simular
    initial_level=(dod_batery*max_discharge_power_capacity)*5 # TODO Cambiar valor según la tecnología a simular

    all_hourly_charges, all_hourly_discharges, all_hourly_state_of_energy, all_daily_discharge_throughput =(
    tfm.simulate_battery(
        initial_level=initial_level, #MWh - Empieza descargada al mínimo
        price_data=precios,
        max_discharge_power_capacity=max_discharge_power_capacity, #MW
        max_charge_power_capacity=max_charge_power_capacity, #MW
        discharge_energy_capacity= 5. * max_discharge_power_capacity, #MWh # TODO Cambiar valor según la tecnología a simular
        efficiency=0.86, # TODO Cambiar valor según la tecnología a simular
        discharge_efficiency=0.86, # TODO Cambiar valor según la tecnología a simular
        max_daily_discharged_throughput= 5. * (max_discharge_power_capacity), #MWh # TODO Cambiar valor según la tecnología a simular
        time_horizon=24, #Horas
        start_day=None,
        min_capacity=(dod_batery*max_discharge_power_capacity)*5, #MWh # TODO Cambiar valor según la tecnología a simular
        )
)

np.save("apoyo_sim_1.npy",all_hourly_charges)
np.save("apoyo_sim_2.npy",all_hourly_discharges)
np.save("apoyo_sim_3.npy",all_hourly_state_of_energy)
np.save("apoyo_sim_4.npy",all_daily_discharge_throughput)
