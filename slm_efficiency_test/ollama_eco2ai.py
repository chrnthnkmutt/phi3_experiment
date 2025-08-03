from openai import OpenAI
import time
import psutil
import os

# Try to import eco2ai components
try:
    import eco2ai
    ECO2AI_AVAILABLE = True
    print("eco2ai available for carbon tracking")
except ImportError as e:
    print(f"eco2ai not available: {e}")
    ECO2AI_AVAILABLE = False

# Initialize carbon tracking
carbon_tracking_enabled = False
tracker = None

if ECO2AI_AVAILABLE:
    try:
        # Initialize eco2ai tracker
        tracker = eco2ai.Tracker(
            project_name="ollama_inference", 
            experiment_description="Ollama energy and carbon consumption tracking",
            file_name="ollama_carbon_consumption.csv"
        )
        carbon_tracking_enabled = True
        print("Carbon tracking initialized successfully")
    except Exception as e:
        print(f"Failed to initialize carbon tracker: {e}")
        carbon_tracking_enabled = False

if not carbon_tracking_enabled:
    print("Falling back to basic system monitoring...")
    start_time = None
    
    # Try to get initial GPU info if possible
    gpu_info_available = False
    try:
        import pynvml
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        if gpu_count > 0:
            gpu_info_available = True
            initial_gpu_power = []
            for i in range(gpu_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    initial_gpu_power.append(power)
                except:
                    initial_gpu_power.append(0)
            print(f"GPU power monitoring available for {gpu_count} GPU(s)")
    except:
        pass

client = OpenAI(
  base_url = 'http://localhost:11434/v1',
  api_key='ollama', # required, but unused
)

# Start monitoring
if carbon_tracking_enabled:
    tracker.start()
    print("Started carbon tracking...")
else:
    start_time = time.time()
    start_cpu_percent = psutil.cpu_percent(interval=None)
    start_memory = psutil.virtual_memory().percent
    print("Started basic system monitoring...")

response = client.chat.completions.create(
  model="qwen2.5:1.5b_cpu",
  messages=[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Who won the world series in 2020?"},
  {"role": "assistant", "content": "The LA Dodgers won in 2020."},
  {"role": "user", "content": "Where was it played?"}
  ],
  stream=True
)

# Collect the streaming response
response_text = ""
for chunk in response:
    if chunk.choices[0].delta.content is not None:
        content = chunk.choices[0].delta.content
        print(content, end="", flush=True)
        response_text += content

print()  # Add a newline after the streaming response

# Stop monitoring
if carbon_tracking_enabled:
    emissions = tracker.stop()
    print(f"Stopped carbon tracking. Emissions: {emissions} kg CO2")
else:
    end_time = time.time()
    end_cpu_percent = psutil.cpu_percent(interval=1)
    end_memory = psutil.virtual_memory().percent
    duration = end_time - start_time
    print(f"Stopped basic monitoring. Duration: {duration:.2f} seconds")
    
    # Try to get final GPU power if available
    if gpu_info_available:
        try:
            final_gpu_power = []
            total_power_change = 0
            for i in range(len(initial_gpu_power)):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                    final_gpu_power.append(power)
                    power_change = abs(power - initial_gpu_power[i])
                    total_power_change += power_change
                except:
                    final_gpu_power.append(0)
            print(f"GPU power usage change detected: {total_power_change:.1f}W total")
        except:
            pass

print(f"\nComplete response: {response_text}")

# Get monitoring results
if carbon_tracking_enabled:
    try:
        print(f"\nCarbon footprint results:")
        print(f"CO2 emissions: {emissions} kg")
        print("Carbon data saved to ollama_carbon_consumption.csv")
    except Exception as e:
        print(f"Error getting carbon tracking results: {e}")
else:
    print(f"\nBasic system monitoring results:")
    print(f"Duration: {duration:.2f} seconds")
    print(f"CPU usage change: {start_cpu_percent:.1f}% -> {end_cpu_percent:.1f}%")
    print(f"Memory usage change: {start_memory:.1f}% -> {end_memory:.1f}%")
    if gpu_info_available and 'total_power_change' in locals():
        print(f"GPU power activity detected: {total_power_change:.1f}W variation")
