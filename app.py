import streamlit as st
import traci
import threading
import time
import queue # Added for thread-safe communication  

# --- At the top of your file ---
import pandas as pd

# --- Inside your run_simulation function ---
# Before the while loop starts, create a list to hold data
stats_log = []

# --- Inside the while loop (after traci.simulationStep()) ---
if step % 50 == 0:
    # Gather real-time research metrics
    avg_speed = traci.simulation.getAverageSpeed()
    # Total CO2 in mg/s
    co2 = sum([traci.lane.getCO2Emission(l) for l in traci.trafficlight.getControlledLanes("N1")]) 
    
    stats_log.append({"Step": step, "Avg Speed": avg_speed, "CO2": co2})
    
    # Save to a CSV every 50 steps so you don't lose data if it crashes
    pd.DataFrame(stats_log).to_csv("research_results.csv", index=False)

# --- UI CONFIGURATION ---
st.set_page_config(page_title="ASTO Dashboard", layout="wide")
st.title("🚦 Agentic AI Traffic Orchestrator")

# Initialize the command queue globally (outside the thread)
if 'cmd_pipe' not in st.session_state:
    st.session_state.cmd_pipe = queue.Queue()

def run_simulation(cmd_pipe):
    """ Background thread for SUMO engine """
    try:
        traci.start([
            "sumo-gui", 
            "-c", "simulation.sumocfg", 
            "--start", 
            "--quit-on-end", 
            "--delay", "100"
        ])
        
        step = 0
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            time.sleep(0.05) 

            # PROCESS COMMANDS FROM THE PIPE
            try:
                # Check if there is a message without blocking
                cmd = cmd_pipe.get_nowait()
                if cmd == "EMERGENCY":
                    veh_id = f"em_{step}"
                    traci.vehicle.add(vehID=veh_id, routeID="loop", typeID="emergency")
                    traci.vehicle.setColor(veh_id, (255, 0, 0, 255)) 
                elif "ACCIDENT" in cmd:
                    edge = cmd.split(":")[1]
                    vehs = traci.edge.getLastStepVehicleIDs(edge)
                    if vehs:
                        traci.vehicle.setStop(vehs[0], edge, pos=250, duration=100)
            except queue.Empty:
                pass # No commands this step

            # AGENT LOGIC
            if step % 10 == 0:
                for tls in traci.trafficlight.getIDList():
                    for l in traci.trafficlight.getControlledLanes(tls):
                        if traci.lane.getLastStepOccupancy(l) > 0.7:
                            traci.trafficlight.setPhaseDuration(tls, 25)
            step += 1
            
        traci.close()
    except Exception as e:
        print(f"Simulation Error: {e}")

# --- UI LAYOUT ---
with st.sidebar:
    st.header("🕹️ Control Center")
    if st.button("🚀 Start Simulation"):
        # Pass the queue into the thread
        thread = threading.Thread(target=run_simulation, args=(st.session_state.cmd_pipe,), daemon=True)
        thread.start()
        st.success("Simulation Engine Online")

    st.divider()
    if st.button("🚨 Dispatch Ambulance"):
        st.session_state.cmd_pipe.put("EMERGENCY")
        st.warning("Ambulance queued...")

    edge_choice = st.selectbox("Select Road for Crash", ["E1", "E2", "E3", "E4"])
    if st.button("💥 Simulate Crash"):
        st.session_state.cmd_pipe.put(f"ACCIDENT:{edge_choice}")
        st.error(f"Crash queued on {edge_choice}")

col1, col2 = st.columns(2)
with col1:
    st.info("The SUMO-GUI window will pop up. Your 4070 Ti is managing the physics, while this browser manages the AI commands.")

with col2:
    st.write("### Research Data")
    st.write("- Connection: Python Queue (Thread-Safe)")
    st.write("- Logic: Multi-Agent Occupancy Control")