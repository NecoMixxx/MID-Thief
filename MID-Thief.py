import os
import mido
from time import sleep as time
import threading

cycle = True
Is_Pause = True
Is_Playing = False
outport = mido.open_output()
mid = None


def cycle_func():
    while True:
        Key_func = input("Do you want to exit the program? (yes/no): \n").strip().lower()
        if Key_func == "yes":
            return False  
        elif Key_func == "no":
            return True   
        print("Invalid input. Please enter 'yes' or 'no'.")

def main():
    print("Welcome to the MIDI Thief program!")
    print("This program allows you to load and manipulate MIDI files.")
    print("Please follow the instructions below to get started.")

def Load_MIDI(Name=None):
    if not Name:
        Name = input("Enter the name of the MIDI file: ").strip()
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "Tracks_MIDI")
    os.makedirs(folder_path, exist_ok=True)
    
    rel_path = f"Tracks_MIDI/{Name}.mid"
    abs_file_path = os.path.join(folder_path, f"{Name}.mid")
    
    try:
        mid = mido.MidiFile(abs_file_path)
        print(f"Successfully loaded {rel_path}.")
        return mid
    except FileNotFoundError:
        print(f"File {rel_path} not found. Please check the file name and try again.")
        return None
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return None

def play_MIDI():
    global Is_Pause, Is_Playing
    if mid is None:
        print("No MIDI file loaded. Please load a MIDI file first.")
        return

    Is_Playing = True  
    Is_Pause = False
    print("Playing MIDI file...") 
    for msg in mid.play():
        if not Is_Playing:
            break
        while Is_Pause:
            time(0.05)  
        outport.send(msg)
    Is_Pause = False
    return Is_Pause
            

def pause_MIDI():
    global Is_Pause
    print("Pausing MIDI playback...")
    Is_Pause = True
    
    for channel in range(16):
        outport.send(mido.Message('control_change', channel=channel, control=64, value=0))
        outport.send(mido.Message('control_change', channel=channel, control=123, value=0))
        outport.send(mido.Message('control_change', channel=channel, control=120, value=0))
    outport.panic()

main()
try:
    while cycle:
        raw_input = input("Press 'Break' to exit or enter command (e.g. 'load T'): \n").strip()

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
            Is_Pause = False
            time(1)

except FileNotFoundError:
    print("File not found. Please check the file name and try again.")
except ValueError as e:
    print(f"Invalid input: {e}")
finally:
    print("Exiting the program.")