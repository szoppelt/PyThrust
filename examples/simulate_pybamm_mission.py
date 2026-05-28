import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import pybamm

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pythrust.propellers import PropellerDatabase
from pythrust.propulsion import (
    BatterySpec,
    MotorSpec,
    PropellerSpec,
    SystemSpec,
    PropulsionSolver,
)

def get_mission_throttle(t):
    """Define a simplified UAV flight mission throttle profile.
    
    - 0 to 60s (1 min)     : Takeoff & Climb (75% throttle)
    - 60s to 660s (10 min) : Cruise (50% throttle)
    - 660s to 720s (1 min) : Descend & Landing (35% throttle)
    """
    if t < 60.0:
        return 0.75
    elif t < 660.0:
        return 0.50
    elif t < 720.0:
        return 0.35
    else:
        return 0.0

def main():
    # 1. Load PyThrust databases
    db = PropellerDatabase()
    db.load(Path("data/propellers/apc_202602"))
    prop_entry = db.get("APC_13x6.5E")
    
    motor = MotorSpec(kv_rpm_per_v=860.0, resistance_ohm=0.0258, no_load_current_a=1.3, current_max_a=65.0)
    system = SystemSpec(resistance_ohm=0.05)
    propeller = PropellerSpec(diameter_m=0.3302)
    solver = PropulsionSolver()
    
    # 2. Setup PyBaMM Lithium-ion Model (Single Particle Model)
    print("Initializing PyBaMM Single Particle Model (SPM)...")
    model = pybamm.lithium_ion.SPM()
    parameter_values = model.default_parameter_values
    
    # Set the current as an input parameter for dynamic stepping
    parameter_values.update({"Current function [A]": "[input]"})
    
    sim = pybamm.Simulation(model, parameter_values=parameter_values)
    
    # Battery configuration scaling details
    cells_series = 4
    capacity_reference = parameter_values["Nominal cell capacity [A.h]"] # ~0.68 Ah
    capacity_pack = 5.0 # 5000 mAh target pack
    current_scaling_ratio = capacity_reference / capacity_pack
    
    # Simulation settings
    dt = 1.0 # 1s step
    total_time = 720.0
    time_steps = np.arange(0.0, total_time, dt)
    
    times = []
    throttles = []
    voltages = []
    currents = []
    thrusts_g = []
    soc_history = []
    
    # Initial states
    battery_voltage = 4.2 * cells_series # starting voltage
    last_current = 0.0
    
    print("Running dynamic mission profile simulation using PyBaMM...")
    
    for t in time_steps:
        throttle = get_mission_throttle(t)
        if throttle <= 0.0:
            break
            
        battery_spec = BatterySpec(voltage_v=battery_voltage)
        
        # Solve operating point at this voltage and throttle
        pt = solver.solve_operating_point(
            motor=motor,
            battery=battery_spec,
            system=system,
            propeller=propeller,
            prop_entry=prop_entry,
            rho=1.225,
            airspeed_mps=0.0,
            throttle=throttle
        )
        
        if not pt.is_feasible:
            print(f"System infeasible at t = {t}s due to: {pt.infeasible_reason}")
            break
            
        current = pt.battery_power_w / battery_voltage
        
        # Scale current for the reference cell in PyBaMM
        current_cell = current * current_scaling_ratio
        
        # Step PyBaMM model
        try:
            sim.step(dt=dt, inputs={"Current function [A]": current_cell})
        except Exception as e:
            print(f"PyBaMM step failed (battery depleted or voltage limit reached) at t = {t}s: {e}")
            break
            
        # Retrieve state from solver solution
        v_cell = sim.solution["Terminal voltage [V]"].data[-1]
        battery_voltage = v_cell * cells_series
        
        discharged_ah = sim.solution["Discharge capacity [A.h]"].data[-1]
        soc = 1.0 - (discharged_ah / capacity_reference)
        
        times.append(t)
        throttles.append(throttle * 100.0)
        voltages.append(battery_voltage)
        currents.append(current)
        thrusts_g.append(pt.thrust_n * 1000.0 / 9.80665)
        soc_history.append(soc * 100.0)
        
        # Stop if SoC drops below 2%
        if soc <= 0.02:
            print(f"Battery depleted (2% SoC) at t = {t}s")
            break
            
    # Convert lists to arrays
    times = np.array(times) / 60.0 # to minutes
    throttles = np.array(throttles)
    voltages = np.array(voltages)
    currents = np.array(currents)
    thrusts_g = np.array(thrusts_g)
    soc_history = np.array(soc_history)
    
    # Plotting
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))
    
    # Subplot 1 (Top-Left): Throttle Profile & Voltage
    color = 'C0'
    axs[0, 0].plot(times, throttles, color=color, label='Throttle (%)', linewidth=2)
    axs[0, 0].set_ylabel('Throttle (%)', color=color)
    axs[0, 0].tick_params(axis='y', labelcolor=color)
    axs[0, 0].grid(True)
    axs[0, 0].set_xlabel('Time (minutes)')
    axs[0, 0].set_title('Throttle & Voltage')
    
    ax0_twin = axs[0, 0].twinx()
    color = 'C3'
    ax0_twin.plot(times, voltages, color=color, label='Voltage (V)', linestyle='--', linewidth=1.8)
    ax0_twin.set_ylabel('Terminal Voltage (V)', color=color)
    ax0_twin.tick_params(axis='y', labelcolor=color)
    
    # Subplot 2 (Top-Right): State of Charge (%)
    axs[0, 1].plot(times, soc_history, color='C4', linewidth=2)
    axs[0, 1].set_ylabel('State of Charge (%)')
    axs[0, 1].set_xlabel('Time (minutes)')
    axs[0, 1].grid(True)
    axs[0, 1].set_title('State of Charge (%)')
    
    # Subplot 3 (Bottom-Left): Battery Current Draw (A)
    axs[1, 0].plot(times, currents, color='C1', linewidth=2)
    axs[1, 0].set_ylabel('Battery Current (A)')
    axs[1, 0].set_xlabel('Time (minutes)')
    axs[1, 0].grid(True)
    axs[1, 0].set_title('Battery Current Draw')
    
    # Subplot 4 (Bottom-Right): Produced Thrust (g)
    axs[1, 1].plot(times, thrusts_g, color='C2', linewidth=2)
    axs[1, 1].set_ylabel('Thrust (g)')
    axs[1, 1].set_xlabel('Time (minutes)')
    axs[1, 1].grid(True)
    axs[1, 1].set_title('Produced Thrust')
    
    fig.suptitle('UAV Propulsion System Simulation: PyBaMM Electrochemical Battery Model', fontsize=14, y=0.98)
    plt.tight_layout()
    
    # Save the output image
    output_dir = Path("docs/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_image = output_dir / "pybamm_mission_results.png"
    plt.savefig(output_image, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Successfully generated and saved PyBaMM simulation plot to: {output_image.resolve()}")

if __name__ == '__main__':
    main()
