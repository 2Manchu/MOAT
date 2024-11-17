#    *       )                  (      *     
#  (  `   ( /(  (      *   )    )\ ) (  `    
#  )\))(  )\()) )\   ` )  /((  (()/( )\))(   
# ((_)()\((_)((((_)(  ( )(_))\  /(_)|(_)()\  
# (_()((_) ((_)\ _ )\(_(_()|(_)(_)) (_()((_) 
# |  \/  |/ _ (_)_\(_)_   _| __| _ \|  \/  | 
# | |\/| | (_) / _ \   | | | _||   /| |\/| | 
# |_|  |_|\___/_/ \_\  |_| |___|_|_\|_|  |_| 
#

import serial
import threading
from threading import Event
import time
import yaml

output_enabled = False
write_enabled = False

testing_complete = Event()

def send_command(ser, command):
    if (command == 'domu_escape'):
        ser.write(b'\x1d')
    else:
        ser.write((command + '\n').encode())

def read_from_port(ser):
    while True:
        if ser.in_waiting:
            response = ser.readline().decode().strip()
            if response and output_enabled:
                print(response)
            if response == "TESTING COMPLETE":
                testing_complete.set()


def launch_interference(ser, command, core):
    # set up the command being used for contention generation
    stressng_cmd = ""
    match command:
        case "bw":
            stressng_cmd = "stress-ng --stream 1 --stream-l3-size 1M --aggressive"
        case "cache":
            stressng_cmd = "stress-ng --cache 1 --cache-level 2 --cache-ways 16 --icache 1 --vm 1 --vm-bytes 32K --vm-method prime-1 --vm-hang 0 --matrix 1 --matrix-yx --matrix-size 128 --aggressive"
        case "io":
            stressng_cmd = "stress-ng --udp 1 --udp-flood 1 --aggressive"

    # connect to the console of the DomU running on the appropriate core
    # turn off serial output because otherwise we'll get spammed with Ubuntu bootup log
    send_command(ser, f"xl console core{core}")
    time.sleep(3)

    # initiate contention gen
    print(f"Starting {command} stress on core {core}...")
    send_command(ser, stressng_cmd)
    time.sleep(2)
    # escape from the console of the DomU with CTRL + ]
    send_command(ser, "domu_escape")
    time.sleep(2)

    return

def start_domus(ser, core):
    cfg_path = "/run/media/root-mmcblk0p2/ubuntu/core%d.cfg" % (core)
    command = "xl create %s" % (cfg_path)
    print(f"Starting DomU on core {core}")

    send_command(ser, command)
    time.sleep(5)
    return

def kill_domus(ser, num_generators):
    for i in range(0, num_generators):
        command = "xl destroy core%d" % (i+1)
        print(f"Stopping DomU on core {i+1}")

        send_command(ser, command)
        time.sleep(0.5)
    return

def test_suite(ser, num_generators, interference_type, base_command, base_loops, run_type):
    global output_enabled
    global write_enabled
    global testing_complete

    output_enabled = False

    # start each domU and allow time for them to boot
    for i in range(0, num_generators):
        start_domus(ser, i+1)

    print("Waiting 5 seconds for DomU environments to initialize...")
    time.sleep(5)

    # start interference generators on appropriate cores
    for i in range(0, num_generators):
        launch_interference(ser, interference_type[i], i+1)

    print(f"Running {run_type} test...")
    # start the base program
    # these results are saved on the SD card
    script_path = "/run/media/root-mmcblk0p2/launch_base.sh"
    script_command = f'{script_path} \'{base_command}\' {base_loops} {run_type}'
    print(script_command)
    send_command(ser, script_command)

    # Wait on an event from the serial reader to detect the "TESTING COMPLETE" phrase
    testing_complete.wait()
    print("Testing complete. Exiting...")
    testing_complete.clear()

    kill_domus(ser, num_generators)
    return

def yaml_test_parser(ser):

    # read the YAML File
    with open('test.yaml', 'r') as file:
        test_seq = yaml.safe_load(file)
    
    # Get Number of Tests
    num_tests = test_seq['sequence_vals']['num_tests']
    print(f"Number of Tests: {num_tests}")
    for i in range(num_tests):
        run_type = test_seq['test_sequence'][i]['test_name']
        print(f"Test Name: {run_type}")
        num_generators = test_seq['test_sequence'][i]['number_of_generators']
        print(f"Number of Generators: {num_generators}")
        interference_type = [""] * num_generators
        for j in range(num_generators):
            interference_type[j] = test_seq['test_sequence'][i]['type_of_generators'][j]

        base_command = test_seq['test_sequence'][i]['baseline_program']
        print(f"Base Command: {base_command}")
        base_loops = test_seq['test_sequence'][i]['loop_numbers']

        test_suite(ser, num_generators, interference_type, base_command, base_loops, run_type)
        time.sleep(1)

def manual_test_parser(ser):
    interference_type = [""] * 3

    print("Enter number of contention generators (0-3): ", end="")
    num_generators = int(input())
    # assign an interference generator to each core
    for i in range(0, num_generators):
        print(f"Contention type (bw, cache) to run on core {i+1}: ", end="")
        interference_type[i] = input().lower()
    
    print("Enter baseline program (stress-ng command, excl. --metrics or --yaml): ", end="")
    base_command = input()

    print("Number of times base program should loop: ", end="")
    base_loops = int(input())

    print("Enter run name (such as name of base program being run): ", end="")
    run_type=input()

    test_suite(ser, num_generators, interference_type, base_command, base_loops, run_type)


def main(port="/dev/ttyUSB0", baud=115200):
    global output_enabled

    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Connected to {port} at {baud} baud.")

        # Start a thread to read from the serial port
        read_thread = threading.Thread(target=read_from_port, args=(ser,))
        read_thread.daemon = True
        read_thread.start()

        while True:
            print("Select Terminal (T), MOATerm Suite (M), YAML Test Sequence(Y) or Exit\n", end="")
            choice = input()
            if (choice == "T" or choice == "t" or 
                choice == "Terminal" or choice == "terminal"):
                # terminal mode
                while True:
                    output_enabled = True
                    command = input()
                    if command.lower() == 'exit':
                        break
                    send_command(ser, command)
                output_enabled = False
            elif (choice == "M" or choice == "m" or 
                  choice == "MOATerm" or choice == "moaterm"):
                # Execute MOATerm suite
                manual_test_parser(ser)
            elif (choice == "Y" or choice == "y" or 
                  choice == "YAML" or choice == "yaml"):
                # Execute YAML test sequence
                # TODO implement this
                yaml_test_parser(ser)
            elif (choice == 'exit' or choice == 'Exit'):
                break
            else:
                print("Invalid selection (enter y/n/exit)")
        
        ser.close()
        print("Connection closed.")
    except serial.SerialException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()