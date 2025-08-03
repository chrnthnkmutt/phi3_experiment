from openai import OpenAI
import time
import psutil
import os

# Try to import pyJoules components
try:
    from pyJoules.energy_meter import EnergyMeter
    from pyJoules.device.rapl_device import RaplDevice
    from pyJoules.device.nvidia_device import NvidiaGPUDevice
    from pyJoules.handler.csv_handler import CSVHandler
    PYJOULES_AVAILABLE = True
except ImportError as e:
    print(f"pyJoules not available: {e}")
    PYJOULES_AVAILABLE = False

# Initialize energy monitoring
energy_monitoring_enabled = False
meter = None
csv_handler = None

if PYJOULES_AVAILABLE:
    devices = []
    
    # Add RAPL device for CPU energy monitoring
    try:
        rapl_device = RaplDevice()
        devices.append(rapl_device)
        print("CPU energy monitoring enabled")
    except Exception as e:
        print(f"CPU energy monitoring not available: {e}")

    # Try to add NVIDIA GPU monitoring (if available)
    try:
        import pynvml
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        if device_count > 0:
            nvidia_device = NvidiaGPUDevice()
            # Test if the device can actually get energy readings
            try:
                test_energy = nvidia_device.get_energy()
                if test_energy is not None:
                    devices.append(nvidia_device)
                    print(f"GPU monitoring enabled ({device_count} GPU(s) found)")
                else:
                    print("GPU found but energy monitoring not supported")
            except Exception as inner_e:
                print(f"GPU found but energy monitoring failed: {inner_e}")
        else:
            print("No NVIDIA GPUs found")
    except ImportError:
        print("GPU monitoring not available: pynvml not installed")
    except Exception as e:
        print(f"GPU monitoring not available: {e}")

    # Create energy meter only if we have devices
    if devices:
        try:
            meter = EnergyMeter(devices)
            csv_handler = CSVHandler('energy_consumption.csv')
            energy_monitoring_enabled = True
            print("Energy monitoring initialized successfully")
        except Exception as e:
            print(f"Failed to initialize energy meter: {e}")
            energy_monitoring_enabled = False
    else:
        print("No energy monitoring devices available")

if not energy_monitoring_enabled:
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

# Optional: Add CSV handler to save results
# (Already initialized above if energy monitoring is available)

client = OpenAI(
  base_url = 'http://localhost:11434/v1',
  api_key='ollama', # required, but unused
)

# Start monitoring
if energy_monitoring_enabled:
    meter.start(tag='ollama_inference')
    print("Started energy monitoring...")
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
if energy_monitoring_enabled:
    meter.stop()
    print("Stopped energy monitoring")
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
if energy_monitoring_enabled:
    try:
        trace = meter.get_trace()
        print(f"\nEnergy consumption:")
        for sample in trace:
            print(f"Tag: {sample.tag}")
            print(f"Duration: {sample.duration} seconds")
            for domain, energy in sample.energy.items():
                print(f"{domain}: {energy} microjoules")

        # Save to CSV (optional)
        if trace and csv_handler:
            csv_handler.process(trace)
            csv_handler.save_data()
            print("Energy data saved to energy_consumption.csv")
    except Exception as e:
        print(f"Error getting energy trace: {e}")
else:
    print(f"\nBasic system monitoring results:")
    print(f"Duration: {duration:.2f} seconds")
    print(f"CPU usage change: {start_cpu_percent:.1f}% -> {end_cpu_percent:.1f}%")
    print(f"Memory usage change: {start_memory:.1f}% -> {end_memory:.1f}%")
    if gpu_info_available and 'total_power_change' in locals():
        print(f"GPU power activity detected: {total_power_change:.1f}W variation")