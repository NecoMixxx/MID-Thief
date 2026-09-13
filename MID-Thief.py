import os
import mido
from time import sleep as time
import threading

cycle = True
Is_Pause = True
Is_Playing = False
mid = None
vol: int = 67
Track_cycle: bool = True

def cycle_func():
    while True:
        Key_func = input("Do you want to exit the program? (yes/no): \n").strip().lower()
        if Key_func == "yes":
            return False   
        elif Key_func == "no":
            return True   
        print("Invalid input. Please enter 'yes' or 'no'.")

def main():
    pass

def Load_MIDI(Name=None):
    if not Name:
        Name = input("Enter the name of the MIDI file: ").strip()
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "Tracks_MIDI")
    os.makedirs(folder_path, exist_ok=True)
    
    rel_path = f"Tracks_MIDI/{Name}.mid"
    abs_file_path = os.path.join(folder_path, f"{Name}.mid")
    
    try:
        loaded_mid = mido.MidiFile(abs_file_path)
        print(f"Successfully loaded {rel_path}.")
        return loaded_mid
    except FileNotFoundError:
        print(f"File {rel_path} not found. Please check the file name and try again.")
        return None
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return None

def play_MIDI():
    global Is_Pause, Is_Playing, Track_cycle
    if mid is None:
        print("No MIDI file loaded. Please load a MIDI file first.")
        return

    Is_Playing = True   
    Is_Pause = False
    print("Playing MIDI file...") 
    Volume(vol)
    for msg in mid.play():
        if not Is_Playing:
            break
        while Is_Pause:
            time(0.05)   
        outport.send(msg)
    if Track_cycle and Is_Playing: 
        Is_Playing = False
        return play_MIDI()
    Is_Playing = False
            
def pause_MIDI():
    global Is_Pause
    print("Pausing MIDI playback...")
    Is_Pause = True
    
    for channel in range(16):
        outport.send(mido.Message('control_change', channel=channel, control=64, value=0))
        outport.send(mido.Message('control_change', channel=channel, control=123, value=0))
        outport.send(mido.Message('control_change', channel=channel, control=120, value=0))
    outport.panic()

def help():
    print("\nAvailable commands:")
    print("  load <filename> - Load a MIDI file (without .mid extension)")
    print("  start           - Start playing the loaded MIDI file")
    print("  pause           - Pause the playback")
    print("  play            - Resume playback if paused")
    print("  timetrack       - Display total duration of the loaded file")
    print("  volume [0-127]  - Set master volume level (prompts if parameter omitted)")
    print("  loop            - Toggle automatic track looping ON/OFF")
    print("  help            - Show this help message")
    print("  break           - Exit the program\n")

def timetrack():
    if mid is None:
        print("No MIDI file loaded. Please load a MIDI file first.")
        return

    total_time = mid.length
    print(f"Total time of the MIDI file: {total_time:.2f} seconds")

def Volume(volume_track=None):
    global vol
    if volume_track is None:
        while True:
            try:   
                volume_track = int(input("Please enter the volume as a number from 0 to 127: "))
                if 0 <= volume_track <= 127:
                    break
                else:
                    print("Value out of bounds. Please enter a number from 0 to 127.")
            except ValueError as e:
                print(f"Invalid input: {e}")

    for channel in range(16):
        outport.send(mido.Message('control_change', channel=channel, control=7, value=volume_track))
    vol = volume_track
    print(f"Volume set to: {vol}")
    return vol


main()
try:
    while cycle:
        raw_input = input("Write command or help: \n").strip()

        parts = raw_input.split(maxsplit=1) 
        command = parts[0].lower() if parts else ""

        if command == "break":
            cycle = cycle_func()
            time(1)

        elif command == "load":
            if len(parts) > 1:
                track_name = parts[1].strip()
                mid = Load_MIDI(track_name)
            else:
                mid = Load_MIDI(Name=None)
            time(1)

        elif command == "start":
            if not Is_Playing:
                threading.Thread(target=play_MIDI).start()
                Is_Pause = False 
            else:
                print("MIDI is already playing!")
            time(1)
        
        elif command == "pause" and not Is_Pause:
            pause_MIDI()
            Is_Pause = True
            time(1)

        elif command == "play" and Is_Pause:
            print("Resuming MIDI playback...")
            Is_Pause = False
            time(1)

        elif command == "stop":
            Is_Playing = False
            Is_Pause = False
            pause_MIDI()
            print("MIDI is already stoping")

        elif command == "help":
            help()
            time(1)

        elif command == "timetrack":
            timetrack()
            time(1)

        elif command == "volume":
            if len(parts) > 1 and parts[1].isdigit() and 0 <= int(parts[1]) <= 127:
                vol = Volume(int(parts[1].strip()))
            elif len(parts) == 1:
                vol = Volume(volume_track=None)
            else:
                print("You need to enter a number from 0 to 127.")

        elif command == "loop":
            Track_cycle = not Track_cycle
            print(f"Looping is now {'enabled' if Track_cycle else 'disabled'}.")

except FileNotFoundError:
    print("File not found. Please check the file name and try again.")
except ValueError as e:
    print(f"Invalid input: {e}")
finally:
    print("Exiting the program.")