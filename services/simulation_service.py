from simulation import PhishingSimulation

_sim = PhishingSimulation()

def start_simulation(emails):
    _sim.start_simulation(emails)
    
def process_responses():
    _sim.process_responses()

def send_reminders():
    _sim.send_reminders()
    
def get_report():
    return _sim.get_simulation_report()

def get_state():
    return _sim.state.users
