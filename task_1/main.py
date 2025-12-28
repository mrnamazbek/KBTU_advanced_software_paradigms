"""
main module for the configurable microservice simulator.
"""
import json


def load_config(config_file='config.json'):
    """
    load the configuration file.
    
    return a dictionary with data from config.json
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"error: file '{config_file}' not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"error: invalid JSON format in '{config_file}'!")
        print(f"details: {e}")
        return None


def load_service(service_name):
    """
    load the service by its name.
    
    service name -> create an instance of the class
    For example: "DataCollector" -> new DataCollector()
    """
    # simply import the needed module and class
    if service_name == 'DataCollector':
        from datacollector import DataCollector
        return DataCollector()
    
    elif service_name == 'Analyzer':
        from analyzer import Analyzer
        return Analyzer()
    
    elif service_name == 'AlertService':
        from alertservice import AlertService
        return AlertService()
    
    else:
        print(f"warning: unknown service '{service_name}' - skipping")
        return None


def main():
    """main function of the program"""
    # step 1: greeting
    print("=" * 60)
    print("  Configurable Microservice Simulator")
    print("  Industrial Monitoring System")
    print("=" * 60)
    print()
    
    # step 2: load the configuration
    config = load_config()
    
    if config is None:
        print("program completed due to configuration error.")
        return
    
    # get the list of active services
    active_services = config.get('active_services', [])
    
    # check if there are active services
    if not active_services:
        print("no active services in the configuration!")
        return
    
            # show which services will be started
    print(f"loaded configuration: {len(active_services)} service(s)")
    print(f"active services: {', '.join(active_services)}")
    print()
    
    # step 3: load all services
    services = []
    for service_name in active_services:
        service = load_service(service_name)
        if service is not None:
            services.append(service)
    
    # step 4: start all services
    print("-" * 60)
    print("starting services...")
    print("-" * 60)
    print()
    
    # start each service one by one
    for service in services:
        try:
            # call the run() method of each service
            service.run()
            print()
        except Exception as e:
            # if an error occurs, show it, but continue working
            print(f"error during service execution: {e}")
            print()
    
    # step 5: completion of work
    print("-" * 60)
    print("all services completed their work.")
    print("=" * 60)


# entry point into the program
if __name__ == "__main__":
    main()
