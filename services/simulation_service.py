from simulation import PhishingSimulation

_sim = PhishingSimulation()

def start_simulation(emails, template_id="security_incident"):
    """Start simulation with specified template"""
    _sim.start_simulation(emails, template_id)
    
def process_responses():
    """Process incoming email responses"""
    _sim.process_responses()

def send_reminders():
    """Send reminders to non-responders"""
    _sim.send_reminders()
    
def get_report():
    """Get simulation statistics report"""
    return _sim.get_simulation_report()

def get_state():
    """Get current user state"""
    return _sim.state.users

def get_templates():
    """Get list of available templates"""
    return _sim.template_service.list_templates()