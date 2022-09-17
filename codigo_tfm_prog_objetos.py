# Designing an energy arbitrage strategy with linear programming

# Setting up the linear programming problem in PuLP

# We'll lay out the decision variables and add the contraints to a linear programming model in PuLP. 
# The markdown code snippets in this section all get put together to define a class at the end of the section, which describes our battery system. 
# This model of the system will be useful to simulate battery operation, stepping through time at a daily increment.

import time
import numpy as np
import pandas as pd
import pulp


# Putting all these methods together to define the `Battery` class, we are ready to ingest the data and proceed to simulating battery operation.


class Battery():

    def __init__(
            self,
            time_horizon,
            max_discharge_power_capacity,
            max_charge_power_capacity,
    ):
        # Set up decision variables for optimization.
        # These are the hourly charge and discharge flows for the optimization horizon, with their limitations.
        
        self.time_horizon = time_horizon

        self.charge = pulp.LpVariable.dicts(
            "charging_power",
            (f'c_t_{i}' for i in range(0, time_horizon)),
            lowBound=0,
            upBound=max_charge_power_capacity,
            cat='Continuous',
        )

        self.discharge = pulp.LpVariable.dicts(
            "discharging_power",
            (f'd_t_{i}' for i in range(0, time_horizon)),
            lowBound=0,
            upBound=max_discharge_power_capacity,
            cat='Continuous',
        )

        # Instantiate linear programming model to maximize the objective
        self.model = pulp.LpProblem("Energy arbitrage", pulp.LpMaximize)

    def set_objective(self, prices):
        # Create a model and objective function.
        # This uses price data, which must have one price for each point in the time horizon.
        
        try:
            assert len(prices) == self.time_horizon
        except AssertionError:
            raise AssertionError('Error: need one price for each hour in time horizon')

        # Objective is profit
        # This formula gives the daily profit from charging/discharging activities. Charging is a cost, discharging is a revenue
        
        self.model += (
                pulp.LpAffineExpression(
                    [
                        (self.charge[f'c_t_{i}'], -1 * prices[i])
                        for i in range(0, self.time_horizon)
                    ]
                )
                +
                pulp.LpAffineExpression(
                    [
                        (self.discharge[f'd_t_{i}'], prices[i])
                        for i in range(0, self.time_horizon)
                    ]
                )
        )

    def add_storage_constraints(
            self,
            efficiency,
            min_capacity,
            discharge_energy_capacity,
            discharge_efficiency,
            initial_level,
    ):
        # Storage level constraint 1
        # This says the battery cannot have less than zero energy, at any hour in the horizon
        # Note this is a place where round-trip efficiency is factored in.
        # The energy available for discharge is the round-trip efficiency times the energy that was charged.
        
        for hour_of_sim in range(1, self.time_horizon + 1):
            self.model += (
                    initial_level
                    +
                    pulp.LpAffineExpression(
                        [
                            (self.charge[f'c_t_{i}'], efficiency)
                            for i in range(0, hour_of_sim)
                        ]
                    )
                    -
                    pulp.LpAffineExpression(
                        [
                            (self.discharge[f'd_t_{i}'], discharge_efficiency)
                            for i in range(0, hour_of_sim)
                        ]
                    ) >= min_capacity
            )

        # Storage level constraint 2
        # Similar to 1
        # This says the battery cannot have more than the discharge energy capacity
    
        for hour_of_sim in range(1, self.time_horizon + 1):
            self.model += (
                    initial_level
                    +
                    pulp.LpAffineExpression(
                        [
                            (self.charge[f'c_t_{i}'], efficiency)
                            for i in range(0, hour_of_sim)
                        ]
                    )
                    -
                    pulp.LpAffineExpression(
                        [
                            (self.discharge[f'd_t_{i}'], discharge_efficiency)
                            for i in range(0, hour_of_sim)
                        ]
                    ) <= discharge_energy_capacity
            )

    def add_throughput_constraints(
            self,
            max_daily_discharged_throughput,
    ):
        # Maximum discharge throughput constraint
        # The sum of all discharge flow within a day cannot exceed this
        # Assumes the time horizon is at least 24 hours

        self.model += pulp.lpSum(
            self.discharge[f'd_t_{i}']
            for i in range(0, self.time_horizon)
        ) <= max_daily_discharged_throughput

    def solve_model(self):
        # Solve the optimization problem
        self.model.solve()

        # Show a warning if an optimal solution was not found
        if pulp.LpStatus[self.model.status] != 'Optimal':
            print('Warning: ' + pulp.LpStatus[self.model.status])

    def collect_output(self):
        # Collect hourly charging and discharging rates within the time horizon
        
        hourly_charges = np.array(
            [
                self.charge[f'c_t_{i}'].varValue
                for i in range(0, 24)
            ]
        )
        hourly_discharges = np.array(
            [
                self.discharge[f'd_t_{i}'].varValue
                for i in range(0, 24)
            ]
        )

        return hourly_charges, hourly_discharges


# # Run the simulation
# In this section, we'll define a function, `simulate_battery`, that simulates the operation of the battery for energy arbitrage over the course of a year. 
# Here are the inputs to the function:
#
# - `initial_level`, the initial level of battery charge at start of simulation (MWh)
# - `price_data`, the `DataFrame` with the hourly MP (€/MWh)
# - `max_discharge_power_capacity`, (MW)
# - `max_charge_power_capacity`, also (MW)
# - `discharge_energy_capacity` (MWh)
# - `efficiency`, the AC-AC Round-trip efficiency, (unitless)
# - `max_daily_discharged_throughput`, (MWh)
# - `time_horizon`, the optimization time horizon (h), assumed here to be greater than or equal to 24.
# - `start_day`, a pandas `Timestamp` for noon on the first simulation day
#
# The function returns several outputs that can be used to examine system operation:
#
# - `all_hourly_charges`, `all_hourly_discharges`, `all_hourly_state_of_energy`, charging and discharging activity, and state of energy, at an hourly time step (MWh)
# - `all_daily_discharge_throughput`, discharged throughput at a daily time step (MWh)


def simulate_battery(
        initial_level,
        price_data,
        max_discharge_power_capacity,
        max_charge_power_capacity,
        discharge_energy_capacity,
        efficiency,
        discharge_efficiency,
        max_daily_discharged_throughput,
        time_horizon,
        start_day,
        min_capacity,
        ):
    # Track simulation time
    tic = time.time()

    # Initialize output variables
    all_hourly_charges = np.empty(0)
    all_hourly_discharges = np.empty(0)
    all_hourly_state_of_energy = np.empty(0)
    all_daily_discharge_throughput = np.empty(0)

    # Set up decision variables for optimization by instantiating the Battery class
    battery = Battery(
        time_horizon=time_horizon,
        max_discharge_power_capacity=max_discharge_power_capacity,
        max_charge_power_capacity=max_charge_power_capacity,
    )

    #############################################
    # Run the optimization for each day of the year.
    #############################################

    # There are 365 24-hour periods (noon to noon) in the simulation, contained within 366 days

    for day_count in range(1):  # Set to sim length 
        print('Trying cycle {}'.format(day_count))

        #############################################
        # Select data and simulate daily operation
        #############################################

        # Retrieve the price data that will be used to calculate the objective
        data_for_this_day = price_data.loc[24 * day_count: 24 * day_count + time_horizon - 1]
        prices = data_for_this_day['value'].values

        # Create model and objective
        battery.set_objective(prices)

        # Set storage constraints
        battery.add_storage_constraints(
            efficiency=efficiency,
            min_capacity=min_capacity,
            discharge_energy_capacity=discharge_energy_capacity,
            discharge_efficiency=discharge_efficiency,
            initial_level=initial_level,
        )

        # Set maximum discharge throughput constraint
        battery.add_throughput_constraints(max_daily_discharged_throughput)

        # Solve the optimization problem and collect output
        battery.solve_model()
        hourly_charges, hourly_discharges = battery.collect_output()

        #############################################
        # Manipulate daily output for data analysis
        #############################################

        # Collect daily discharge throughput
        daily_discharge_throughput = sum(hourly_discharges)
        # Calculate net hourly power flow (kW), needed for state of energy.
        # Tanto la carga como la descarga han de tener en cuenta el rendimiento, debido a que no toda la energía estará disponible.
        net_hourly_activity = (hourly_charges * efficiency) - (hourly_discharges*discharge_efficiency)
        # Cumulative changes in energy over time (kWh) from some baseline
        cumulative_hourly_activity = np.cumsum(net_hourly_activity)
        # Add the baseline for hourly state of energy during the next time step (t2)
        
        state_of_energy_from_t2 = initial_level + cumulative_hourly_activity

        # Append output
    
        all_hourly_charges = np.append(all_hourly_charges, hourly_charges)
        all_hourly_discharges = np.append(
            all_hourly_discharges,
            hourly_discharges,
        )
        all_hourly_state_of_energy = np.append(
            all_hourly_state_of_energy,
            state_of_energy_from_t2,
        )
        all_daily_discharge_throughput = np.append(
            all_daily_discharge_throughput,
            daily_discharge_throughput,
        )

        #############################################
        # Set up the next day
        #############################################

        # El nivel inicial del siguiente periodo es el punto final del del periodo actual 

        initial_level = state_of_energy_from_t2[-1]

    toc = time.time()

    print('Total simulation time: ' + str(toc - tic) + ' seconds')

    return all_hourly_charges, all_hourly_discharges, all_hourly_state_of_energy, all_daily_discharge_throughput
