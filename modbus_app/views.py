# modbus_app/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from .models import Signal
from .forms import SignalForm
from .modbus_communication import write_to_register, set_updated_bits_callback, bit_to_int, int_to_bit, restart_modbus_server, data_bank, start_modbus_server
from django.db.models import Max
import json
import sys
import os
import time
import logging
import threading
import subprocess
import modbus_project.config as config  # Import the config module

logger = logging.getLogger(__name__)
cycmp_event = threading.Event()

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        server_ip_address = request.POST.get('server_ip_address', config.DEFAULT_SERVER_IP_ADDRESS)
        server_port = int(request.POST.get('server_port', config.DEFAULT_SERVER_PORT))
        tool_ip_address = request.POST.get('tool_ip_address', config.DEFAULT_TOOL_IP_ADDRESS)
        tool_module_name = request.POST.get('tool_module_name', config.DEFAULT_MODULE_NAME)

        config_username = config.DEFAULT_USERNAME
        config_password = config.DEFAULT_PASSWORD

        if username == config_username and password == config_password:
            # Update config values with the new ones
            config.update_current_config('CURRENT', 'CURRENT_SERVER_IP_ADDRESS', server_ip_address)
            config.update_current_config('CURRENT', 'CURRENT_SERVER_PORT', str(server_port))
            config.update_current_config('CURRENT', 'CURRENT_TOOL_IP_ADDRESS', tool_ip_address)
            config.update_current_config('CURRENT', 'CURRENT_TOOL_MODULE_NAME', tool_module_name)

            # Log the external script execution
            logger.info('Running external script webjsondatagetter.py')
            script_path = os.path.join('scripts', 'webjsondatagetter.py')
            project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

            try:
                result = subprocess.run(
                    ['python', script_path,
                     '--ip_address', tool_ip_address,
                     '--username', config_username,
                     '--password', config_password,
                     '--module_name', tool_module_name,
                     '--file_path', config.DEFAULT_CONFIG_JSON_FILE_PATH,
                     '--log_file_path', config.DEFAULT_LOG_FILE_PATH],
                    capture_output=True,
                    text=True,
                    check=True,
                    env={**os.environ, 'PYTHONPATH': project_path}
                )
                logger.info('External script execution completed successfully')
                logger.info('Script output: %s', result.stdout)
            except subprocess.CalledProcessError as e:
                logger.error('Error running external script: %s', e.stderr)
                return render(request, 'login.html', {
                    'error': 'Error running external script',
                    'server_ip_address': server_ip_address,
                    'server_port': server_port,
                    'tool_ip_address': tool_ip_address,
                    'tool_module_name': tool_module_name
                })

            # Load the signals from the updated config file
            logger.info('Loading signals from config file')
            call_command('load_signals')
            logger.info('Signals loaded successfully')

            # Authenticate and log in the user
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                # Start the Modbus server after successful login
                modbus_thread = threading.Thread(target=start_modbus_server, args=(server_ip_address, server_port))
                modbus_thread.daemon = True
                modbus_thread.start()
                return redirect('home')
            else:
                return render(request, 'login.html', {
                    'error': 'Invalid username or password',
                    'server_ip_address': server_ip_address,
                    'server_port': server_port,
                    'tool_ip_address': tool_ip_address,
                    'tool_module_name': tool_module_name
                })
        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password',
                'server_ip_address': server_ip_address,
                'server_port': server_port,
                'tool_ip_address': tool_ip_address,
                'tool_module_name': tool_module_name
            })
    return render(request, 'login.html', {
        'server_ip_address': config.DEFAULT_SERVER_IP_ADDRESS,
        'server_port': config.DEFAULT_SERVER_PORT,
        'tool_ip_address': config.DEFAULT_TOOL_IP_ADDRESS,
        'tool_module_name': config.DEFAULT_MODULE_NAME
    })

def logout_view(request):
    logout(request)
    os.system("pkill -f runserver")  # This command stops the Django development server
    sys.exit(0)  # Exit the script to close the page
    return redirect('login')

def get_max_port(direction):
    max_port = Signal.objects.filter(direction=direction).aggregate(Max('port'))['port__max']
    return max_port if max_port is not None else 16

@login_required
def home(request):
    max_input_port = get_max_port('in')
    max_output_port = get_max_port('out')

    if request.method == 'POST':
        signals = Signal.objects.filter(direction='in').order_by('port')
        bit_array = [0] * max_input_port
        for signal in signals:
            new_state = int(request.POST.get(f'state_{signal.id}'))
            signal.state = new_state
            signal.save()
            bit_array[max_input_port - signal.port] = new_state  # Reverse the input mapping order

        write_to_register(bit_array)  # Send the reversed bit array to the tool
        return redirect('home')

    inputs = Signal.objects.filter(direction='in').order_by('port')
    outputs = Signal.objects.filter(direction='out').order_by('port')

     # Read the latest OK_COUNTER value from the config file
    ok_counter = config.get_current_config('CURRENT', 'OK_COUNTER')

    return render(request, 'home.html', {
        'inputs': inputs,
        'outputs': outputs,
        'ip_address': config.CURRENT_SERVER_IP_ADDRESS,
        'port': config.CURRENT_SERVER_PORT,
        'tool_ip_address': config.CURRENT_TOOL_IP_ADDRESS,
        'ok_counter': ok_counter,  
        'max_length': max(max_input_port, max_output_port),
    })

@csrf_exempt
def api_data(request):
    if request.method == 'POST':
        signals = Signal.objects.all()
        data = {
            'inputs': list(signals.filter(direction='in').values()),
            'outputs': list(signals.filter(direction='out').values())
        }
        return JsonResponse(data)
    elif request.method == 'GET':
        signals = Signal.objects.all()
        data = {
            'inputs': list(signals.filter(direction='in').values()),
            'outputs': list(signals.filter(direction='out').values())
        }
        return JsonResponse(data)
    else:
        return JsonResponse({"error": "Invalid HTTP method"}, status=400)
    
def update_signal(request, signal_id):
    signal = Signal.objects.get(id=signal_id)
    if request.method == 'POST':
        form = SignalForm(request.POST, instance=signal)
        if form.is_valid():
            signal = form.save(commit=False)
            signals = Signal.objects.filter(direction='in').order_by('port')
            bit_array = [0] * 16
            for i, sig in enumerate(signals):
                if sig.id == signal.id:
                    bit_array[16 - sig.port] = signal.state  # Reverse the input mapping order
                else:
                    bit_array[16 - sig.port] = sig.state  # Reverse the input mapping order

            write_to_register(list(reversed(bit_array)))  # Send the reversed bit array to the tool
            signal.save()
            return redirect('home')
    else:
        form = SignalForm(instance=signal)
    return render(request, 'update_signal.html', {'form': form})

@csrf_exempt
def change_server_settings(request):
    if request.method == 'POST':
        new_ip = request.POST.get('ip_address')
        new_port = int(request.POST.get('port'))
        logger.info(f'Changing server settings to IP: {new_ip}, Port: {new_port}')
        success = restart_modbus_server(new_ip, new_port)
        if success:
            config.update_current_config('CURRENT', 'CURRENT_SERVER_IP_ADDRESS', new_ip)
            config.update_current_config('CURRENT', 'CURRENT_SERVER_PORT', str(new_port))
            logger.info(f'Successfully changed server settings to IP: {new_ip}, Port: {new_port}')
            return JsonResponse({'ip_address': new_ip, 'port': new_port})
        else:
            logger.error(f'Failed to restart server with new settings IP: {new_ip}, Port: {new_port}')
            return JsonResponse({'ip_address': config.CURRENT_SERVER_IP_ADDRESS, 'port': config.CURRENT_SERVER_PORT, 'error': 'Failed to restart server with new settings'}, status=400)
    return HttpResponseBadRequest("Invalid request method")

@csrf_exempt
def check_tool_connection(request):
    try:
        current_state = data_bank.get_holding_registers(2048, 1)
        connected = current_state and current_state[0] != 0
    except Exception as e:
        logger.error(f'Error checking tool connection: {e}')
        connected = False
    
    return JsonResponse({'connected': connected})

@csrf_exempt
def force_stop(request):
    if request.method == 'POST':
        max_input_port = get_max_port('in')
        bit_array = [0] * max_input_port
        write_to_register(bit_array)
        global stop_continuous_tests
        stop_continuous_tests = True
        logger.info('Force stop executed, all signals set to 0 and continuous tests stopped')
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'}, status=400)

stop_continuous_tests = False

def update_outputs(received_bits):
    logger.info(f'Updating outputs with received bits: {received_bits}')
    max_output_port = get_max_port('out')
    bit_list = [int(bit) for bit in received_bits]  # Do not reverse here
    signals = Signal.objects.filter(direction='out').order_by('port')
    for signal in signals:
        signal.state = bit_list[max_output_port - signal.port]  # Reverse the order for correct mapping
        signal.save()
        logger.info(f'Updated signal {signal.name} to state {signal.state}')

def event_stream():
    while True:
        outputs = Signal.objects.filter(direction='out').values()
        yield f"data: {json.dumps(list(outputs))}\n\n"
        time.sleep(0.1)  # Adjust the sleep time as necessary

def sse(request):
    return StreamingHttpResponse(event_stream(), content_type='text/event-stream')

def tool_status_stream():
    while True:
        current_state = data_bank.get_holding_registers(2048, 1)
        connected = current_state[0] != 0 if current_state else False
        yield f"data: {json.dumps({'connected': connected})}\n\n"
        time.sleep(0.1)  # Adjust the sleep time as necessary

def tool_status_sse(request):
    return StreamingHttpResponse(tool_status_stream(), content_type='text/event-stream')

# Function to update the Ok Counter in the config file
def update_ok_counter(value):
    config.update_current_config('CURRENT', 'OK_COUNTER', str(value))
    logger.info(f'Updated Ok Counter to {value} in config file')

# Global variables to track the state of each test cycle
current_test_cycle = 0
current_rotation_cycle = 0
in_counter_rotation = False

@csrf_exempt
def continuous_tests(request):
    global stop_continuous_tests
    stop_continuous_tests = False
    global current_test_cycle
    global current_rotation_cycle
    global in_counter_rotation

    if request.method == 'POST':
        data = json.loads(request.body)
        number_of_tests = data.get('number_of_tests', 0)
        with_counter_rotation = data.get('with_counter_rotation', False)
        logger.info(f'Starting continuous tests with {number_of_tests} tests, with_counter_rotation={with_counter_rotation}')

        # Identify positions of En, CW, CCW, CyCmp, OK signals (case-insensitive)
        en_signal = Signal.objects.filter(name__iexact='En').first()
        cw_signal = Signal.objects.filter(name__iexact='CW').first()
        ccw_signal = Signal.objects.filter(name__iexact='CCW').first()
        cycmp_signal = Signal.objects.filter(name__iexact='CyCmp').first()
        ok_signal = Signal.objects.filter(name__iexact='OK').first()

        if not (en_signal and cw_signal and ccw_signal and cycmp_signal and ok_signal):
            logger.error('One or more required signals (En, CW, CCW, CyCmp, OK) are missing')
            return JsonResponse({'error': 'Missing required signals'}, status=400)

        max_input_port = get_max_port('in')
        en_port = max_input_port - en_signal.port
        cw_port = max_input_port - cw_signal.port
        ccw_port = max_input_port - ccw_signal.port
        cycmp_port = max_input_port - cycmp_signal.port
        ok_port = max_input_port - ok_signal.port

        logger.info(f'Signal positions - En: {en_port}, CW: {cw_port}, CCW: {ccw_port}, CyCmp: {cycmp_port}, OK: {ok_port}')

        config.update_current_config('CURRENT', 'OK_COUNTER', '0')  # Reset Ok Counter before tests

        def cycmp_callback(received_bits):
            global current_test_cycle
            global current_rotation_cycle
            global in_counter_rotation
            logger.debug(f'cycmp_callback triggered with received_bits: {received_bits}')
            if received_bits[cycmp_port] == '1':
                if in_counter_rotation:
                    if current_rotation_cycle != current_test_cycle:
                        logger.info('Step 4 (counter rotation): CyCmp is 1')
                        if received_bits[ok_port] == '1':
                            ok_counter = int(config.OK_COUNTER) + 1
                            config.update_current_config('CURRENT', 'OK_COUNTER', str(ok_counter))
                            logger.info('Step 5 (counter rotation): OK is 1, increased OK counter')
                        current_rotation_cycle = current_test_cycle
                else:
                    if current_rotation_cycle != current_test_cycle:
                        logger.info('Step 4: CyCmp is 1')
                        if received_bits[ok_port] == '1':
                            ok_counter = int(config.OK_COUNTER) + 1
                            config.update_current_config('CURRENT', 'OK_COUNTER', str(ok_counter))
                            logger.info('Step 5: OK is 1, increased OK counter')
                        current_rotation_cycle = current_test_cycle
                cycmp_event.set()

        set_updated_bits_callback(cycmp_callback)

        input_signals = Signal.objects.filter(direction='in').order_by('port')
        initial_bit_array = [0] * max_input_port
        for signal in input_signals:
            initial_bit_array[max_input_port - signal.port] = signal.state

        for test_number in range(number_of_tests):
            if stop_continuous_tests:
                break
            logger.info(f'Starting test {test_number + 1}')

            current_test_cycle += 1
            current_rotation_cycle = -1  # Reset rotation cycle for each new test
            in_counter_rotation = False

            # Step 1: Send En = 1, CW = 0, CCW = 0
            bit_array = initial_bit_array[:]
            bit_array[en_port] = 1
            bit_array[cw_port] = 0
            bit_array[ccw_port] = 0
            write_to_register(bit_array)
            logger.info(f'Step 1: Sent bit array {bit_array}')

            # Step 2: Wait 0.2s
            time.sleep(0.2)
            logger.info('Step 2: Waited 0.2s')

            # Step 3: Send En = 1, CW = 1, CCW = 0
            bit_array[cw_port] = 1
            write_to_register(bit_array)
            logger.info(f'Step 3: Sent bit array {bit_array}')

            # Step 4: Wait until CyCmp = 1
            cycmp_event.clear()
            start_time = time.time()
            while not cycmp_event.is_set():
                if stop_continuous_tests:
                    break
                if time.time() - start_time > 5:  # Timeout after 5 seconds to prevent infinite loop
                    logger.error('Step 4: Timeout waiting for CyCmp to be 1')
                    break
                time.sleep(0.01)

            if stop_continuous_tests:
                break

            logger.debug('Waiting for cycmp_event to be set')
            cycmp_event.wait()  # Wait until the CyCmp signal is received and handled

            # Step 6: Wait 0.4s
            time.sleep(0.4)
            logger.info('Step 6: Waited 0.4s')

            if with_counter_rotation:
                logger.info(f'Starting counter rotation test {test_number + 1}')
                in_counter_rotation = True

                # Step 1 (counter rotation): Send En = 1, CW = 0, CCW = 0
                bit_array[en_port] = 1
                bit_array[cw_port] = 0
                bit_array[ccw_port] = 0
                write_to_register(bit_array)
                logger.info(f'Step 1 (counter rotation): Sent bit array {bit_array}')

                # Step 2 (counter rotation): Wait 0.2s
                time.sleep(0.2)
                logger.info('Step 2 (counter rotation): Waited 0.2s')

                # Step 3 (counter rotation): Send En = 1, CW = 0, CCW = 1
                bit_array[cw_port] = 0
                bit_array[ccw_port] = 1
                write_to_register(bit_array)
                logger.info(f'Step 3 (counter rotation): Sent bit array {bit_array}')

                # Step 4 (counter rotation): Wait until CyCmp = 1
                cycmp_event.clear()
                start_time = time.time()
                while not cycmp_event.is_set():
                    if stop_continuous_tests:
                        break
                    if time.time() - start_time > 5:  # Timeout after 5 seconds to prevent infinite loop
                        logger.error('Step 4 (counter rotation): Timeout waiting for CyCmp to be 1')
                        break
                    time.sleep(0.01)

                if stop_continuous_tests:
                    break

                logger.debug('Waiting for cycmp_event to be set (counter rotation)')
                cycmp_event.wait()  # Wait until the CyCmp signal is received and handled

                # Step 6 (counter rotation): Wait 0.4s
                time.sleep(0.4)
                logger.info('Step 6 (counter rotation): Waited 0.4s')
                in_counter_rotation = False

        # After the tests are completed
        ok_counter = config.get_current_config('CURRENT', 'OK_COUNTER')
        logger.info(f'Continuous tests completed with OK counter: {ok_counter}')
        
        set_updated_bits_callback(update_outputs)  # Reset the callback to the original function
        return JsonResponse({'success': True, 'ok_counter': ok_counter})
    return JsonResponse({'error': 'Invalid request method'}, status=400)


def update_output_indicators():
    current_state = data_bank.get_holding_registers(2048, 1)
    if current_state:
        bin_list = int_to_bit(current_state[0], length=config.CURRENT_OUTPUT_BIT_ARRAY_LENGTH)
        received_bits = "".join(map(str, bin_list))  # Direct bit list without reversing
        bit_list = [int(bit) for bit in received_bits]  # Do not reverse here
        signals = Signal.objects.filter(direction='out').order_by('port')
        for signal in signals:
            signal.state = bit_list[config.CURRENT_OUTPUT_BIT_ARRAY_LENGTH - signal.port]  # Reverse the order for correct mapping
            signal.save()
        logger.info(f'Updated output indicators with received bits: {received_bits}')


# Register the callback
set_updated_bits_callback(update_outputs)
