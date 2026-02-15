import traci

def run_agentic_simulation():
    # Start the simulation
    traci.start(["sumo-gui", "-c", "simulation.sumocfg"])
    
    # 1. Discover all Agents (Traffic Lights)
    agents = traci.trafficlight.getIDList()
    print(f"System Initialized: {len(agents)} agents online.")

    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        
        # We only want our agents to 'think' every 5 steps to avoid flickering
        if step % 5 == 0:
            for node_id in agents:
                # SENSE: Perception of the current intersection
                lanes = traci.trafficlight.getControlledLanes(node_id)
                
                # Check for Emergency Vehicles (Research Priority)
                emergency_nearby = False
                for lane in lanes:
                    vehicles = traci.lane.getLastStepVehicleIDs(lane)
                    for v in vehicles:
                        if traci.vehicle.getTypeID(v) == "emergency":
                            emergency_nearby = True
                            target_lane = lane
                            break

                # ACT: Decision Tree
                if emergency_nearby:
                    # Logic: Force immediate green for the emergency vehicle
                    print(f"Agent {node_id}: 🚨 EMERGENCY DETECTED. Clearing corridor.")
                    # We skip standard logic to prioritize life-safety
                    # (Advanced logic would go here)
                
                else:
                    # Standard Load Balancing: Find the busiest lane
                    lane_loads = {l: traci.lane.getLastStepHaltingNumber(l) for l in lanes}
                    busiest_lane = max(lane_loads, key=lane_loads.get)
                    
                    if lane_loads[busiest_lane] > 3: # Threshold: 3 cars waiting
                        print(f"Agent {node_id}: High load on {busiest_lane}. Adjusting timers.")
                        # Extend the current green phase for this node
                        traci.trafficlight.setPhaseDuration(node_id, 25)

        step += 1

    traci.close()

if __name__ == "__main__":
    run_agentic_simulation()