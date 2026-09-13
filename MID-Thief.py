import os
import sys
import shutil
import array
import wave
import threading
import platform
from time import sleep as time
import tkinter as tk
from tkinter import filedialog
import mido

if platform.system() == "Windows":
    base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    os.environ["PATH"] = base_dir + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(base_dir)
        except Exception:
            pass

import fluidsynth

system_name = platform.system()
if system_name == "Windows":
    driver = "dsound"
elif system_name == "Darwin":
    driver = "coreaudio"
elif system_name == "Linux":
    driver = "alsa"
else:
    driver = None

active_bank = "gm_florestan.sf2"

fs = fluidsynth.Synth()
if driver:
    fs.start(driver=driver)
else:
    fs.start()

sf_id = None
cycle = True
is_pause = False
is_playing = False
mid = None
vol: int = 67
track_cycle: bool = True
channel_programs = [0] * 16 
current_sec = 0.0 
seek_target = None
is_seeking = False
seek_direction = ""
tail = False


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def clean_path(path_str: str) -> str:
    if not path_str:
        return ""
    path_str = path_str.strip()
    if path_str.startswith("&"):
        path_str = path_str[1:].strip()
    while len(path_str) > 1 and ((path_str.startswith("'") and path_str.endswith("'")) or (path_str.startswith('"') and path_str.endswith('"'))):
        path_str = path_str[1:-1].strip()
    return path_str


def silence_all():
    for channel in range(16):
        fs.cc(channel, 64, 0)
        fs.cc(channel, 123, 0)
        fs.cc(channel, 120, 0)


def cycle_func():
    while True:
        key_func = input("Do you really want to exit the program? (yes/no): \n").strip().lower()
        if key_func == "yes":
            return False   
        elif key_func == "no":
            return True   
        print("Invalid input. Please enter 'yes' or 'no' :-/")


def process_sf2_drop(file_path):
    file_path = clean_path(file_path)
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return

    base_dir = get_base_dir()
    sf_folder = os.path.join(base_dir, "Sound Fonts")
    os.makedirs(sf_folder, exist_ok=True)

    orig_name = os.path.basename(file_path)
    dest_path = os.path.join(sf_folder, orig_name)

    try:
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
        print(f"[+] Saved SoundFont to 'Sound Fonts/{orig_name}'")
        soundfont(orig_name)
    except Exception as e:
        print(f"[!] Error processing SoundFont file: {e}")


def import_midi_file(file_path):
    file_path = clean_path(file_path)
    if not os.path.isfile(file_path):
        print(f"[!] File not found: {file_path}")
        return

    base_dir = get_base_dir()
    midi_folder = os.path.join(base_dir, "Tracks_MIDI")
    os.makedirs(midi_folder, exist_ok=True)

    dest_path = os.path.join(midi_folder, os.path.basename(file_path))
    try:
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copy2(file_path, dest_path)
        print(f"[+] Imported MIDI track to 'Tracks_MIDI/{os.path.basename(file_path)}'")
    except Exception as e:
        print(f"[!] Error importing MIDI: {e}")


def process_startup_args():
    global mid, is_playing, is_pause
    if len(sys.argv) <= 1:
        return

    args = sys.argv[1:]

    if "--import" in args:
        idx = args.index("--import")
        if idx + 1 < len(args):
            import_midi_file(args[idx + 1])
            sys.exit(0)

    if "--sf2" in args:
        idx = args.index("--sf2")
        if idx + 1 < len(args):
            process_sf2_drop(args[idx + 1])
            sys.exit(0)

    if "--export" in args:
        idx = args.index("--export")
        if idx + 1 < len(args):
            file_path = clean_path(args[idx + 1])
            if os.path.isfile(file_path):
                print(f"[>] Opening export dialog for: {os.path.basename(file_path)}")
                mid = load_midi(file_path)
                if mid:
                    default_out = os.path.splitext(os.path.basename(file_path))[0] + ".wav"
                    export_to_wav(output_filename=default_out)
                sys.exit(0)

    for arg in args:
        cleaned_arg = clean_path(arg)
        if not os.path.isfile(cleaned_arg):
            continue

        ext = os.path.splitext(cleaned_arg)[1].lower()

        if ext in ['.sf2', '.sf3']:
            process_sf2_drop(cleaned_arg)

        elif ext in ['.mid', '.midi']:
            print(f"[>] Auto-playing track dropped at launch: {os.path.basename(cleaned_arg)}")
            mid = load_midi(cleaned_arg)
            if mid:
                is_playing = False
                time(0.1)
                threading.Thread(target=play_midi, daemon=True).start()
                is_pause = False


def main():
    base_dir = get_base_dir()
    default_sf = os.path.join(base_dir, "Sound Fonts", active_bank)
    if os.path.isfile(default_sf):
        soundfont(active_bank)
    
    process_startup_args()
    help_command()


def load_midi(name=None):
    global is_playing, is_pause, current_sec, is_seeking
    is_playing = False
    is_pause = False
    is_seeking = False
    time(0.1)

    if not name:
        name = input("Enter the name of the MIDI file (without .mid) or drag & drop file here: ").strip()

    name = clean_path(name)

    if os.path.isfile(name):
        abs_file_path = name
        rel_path = os.path.basename(name)
    else:
        base_dir = get_base_dir()
        folder_path = os.path.join(base_dir, "Tracks_MIDI")
        os.makedirs(folder_path, exist_ok=True)
        
        clean_name = name[:-4] if name.lower().endswith((".mid", ".midi")) else name
        rel_path = f"Tracks_MIDI/{clean_name}.mid"
        abs_file_path = os.path.join(folder_path, f"{clean_name}.mid")

    try:
        loaded_mid = mido.MidiFile(abs_file_path)
        current_sec = 0.0
        print(f"[+] File '{rel_path}' successfully loaded :-)")
        return loaded_mid
    except FileNotFoundError:
        print(f"[!] File '{rel_path}' not found. Check file name and directory :/")
        return None
    except Exception as e:
        print(f"[!] Error loading MIDI: {e}")
        return None


def play_midi():
    global is_pause, is_playing, track_cycle, channel_programs, current_sec, seek_target, is_seeking, seek_direction
    if mid is None:
        print("[!] No MIDI file loaded.")
        return

    is_playing = True   
    is_pause = False
    print("[>] Playing MIDI file...")
    volume(vol)

    while is_playing:
        current_sec = 0.0
        silence_all()

        for msg in mid:
            if not is_playing:
                break

            while is_pause:
                time(0.05)

            if is_seeking:
                if seek_target is not None:
                    target = seek_target
                    if target < current_sec:
                        break

                    current_sec += msg.time

                    if msg.type == 'program_change':
                        channel_programs[msg.channel] = msg.program
                        fs.program_change(msg.channel, msg.program)
                    elif msg.type == 'control_change':
                        fs.cc(msg.channel, msg.control, msg.value)
                    elif msg.type == 'pitchwheel':
                        fs.pitch_bend(msg.channel, msg.pitch)

                    if current_sec >= target:
                        is_seeking = False
                        seek_target = None
                        silence_all()
                        for ch in range(16):
                            fs.program_change(ch, channel_programs[ch])
                            fs.cc(ch, 7, vol)
                        print(f"[{seek_direction}] Seek completed. Resuming at: {current_sec:.2f} sec.")
                    continue

            if msg.time > 0:
                time(msg.time)
            current_sec += msg.time

            if msg.type == 'note_on':
                fs.noteon(msg.channel, msg.note, msg.velocity)
            elif msg.type == 'note_off':
                fs.noteoff(msg.channel, msg.note)
            elif msg.type == 'control_change':
                fs.cc(msg.channel, msg.control, msg.value)
            elif msg.type == 'pitchwheel':
                fs.pitch_bend(msg.channel, msg.pitch)
            elif msg.type == 'program_change':
                channel_programs[msg.channel] = msg.program
                fs.program_change(msg.channel, msg.program)

        if is_seeking:
            continue

        if track_cycle and is_playing:
            continue
        else:
            break

    is_playing = False


def pause_midi():
    global is_pause
    print("[||] Playback paused.")
    is_pause = True
    silence_all()


def seek(sec=None):
    global seek_target, is_seeking, is_pause, current_sec, seek_direction

    if mid is None:
        print("[!] No MIDI file loaded.")
        return

    if sec is None:
        try:
            sec = float(input(f"Enter target time in seconds (0 - {mid.length:.2f}): ").strip())
        except ValueError:
            print("[!] Invalid number format :/")
            return

    if not (0 <= sec <= mid.length):
        print(f"[!] Time out of bounds! Range: 0 to {mid.length:.2f} seconds.")
        return

    seek_direction = "REWIND <<" if sec < current_sec else "FAST FORWARD >>"
    seek_target = sec
    is_seeking = True
    is_pause = False
    print(f"[{seek_direction}] Seeking to {sec:.2f} seconds...")
    if not is_playing:
        threading.Thread(target=play_midi, daemon=True).start()


def help_command():
    print("\n=================== MIDI Thief Player ===================")
    print(" Drag & Drop:")
    print("   * Drag and drop any .mid or .sf2 file into this terminal window anytime!")
    print(" Track Control:")
    print("   import / load [name/path] - Load a MIDI file")
    print("   start                     - Start playing loaded track")
    print("   pause                     - Pause playback")
    print("   play                      - Resume playback")
    print("   stop                      - Stop playback completely")
    print("   seek [seconds]            - Cassette-style seek to target time")
    print("   current_sec               - Show current playback timestamp")
    print("   timetrack                 - Display total duration of loaded track")
    print("   loop                      - Toggle auto-looping (ON / OFF)")
    print("\n Audio & Synthesis:")
    print("   volume [0-127]            - Set master volume level")
    print("   soundfont / sf [num/name] - Change active SoundFont soundbank (.sf2)")
    print("   tail                      - Toggle reverb tail recording")
    print("   export [name.wav]         - Export current MIDI to WAV audio file")
    print("\n System Integration:")
    print("   help                      - Show this menu")
    print("   break                     - Exit the application")
    print("=========================================================\n")


def timetrack():
    if mid is None:
        print("[!] No MIDI file loaded.")
        return
    print(f"[i] Total duration: {mid.length:.2f} sec. (Current: {current_sec:.2f} sec.)")


def volume(volume_track=None):
    global vol
    if volume_track is None:
        while True:
            try:   
                volume_track = int(input("Enter volume level (0 - 127): "))
                if 0 <= volume_track <= 127:
                    break
                print("[!] Value out of bounds (0-127).")
            except ValueError as e:
                print(f"[!] Invalid input: {e}")

    for channel in range(16):
        fs.cc(channel, 7, volume_track)
    vol = volume_track
    print(f"[+] Volume set to: {vol}")
    return vol


def soundfont(soundbank_name=None):
    global active_bank, sf_id, channel_programs, vol

    base_dir = get_base_dir()
    folder_path = os.path.join(base_dir, "Sound Fonts")
    os.makedirs(folder_path, exist_ok=True)

    available_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.sf2', '.sf3'))])

    if soundbank_name is not None:
        soundbank_name = clean_path(str(soundbank_name))

    if soundbank_name and soundbank_name.isdigit():
        idx = int(soundbank_name) - 1
        if 0 <= idx < len(available_files):
            soundbank_name = available_files[idx]
        else:
            print(f"[!] Invalid index: {soundbank_name}. Total available SoundFonts: {len(available_files)}")
            return None

    if not soundbank_name:
        if not available_files:
            print("[!] No .sf2/.sf3 files found in 'Sound Fonts' folder.")
            return None

        print("\n--- Available SoundFonts ---")
        for index, file_name in enumerate(available_files, 1):
            print(f" {index}. {file_name}")
        print("----------------------------\n")
        
        user_input = input("Enter soundbank number/name or drag .sf2 file here: ").strip()
        user_input = clean_path(user_input)

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(available_files):
                soundbank_name = available_files[idx]
            else:
                print("[!] Invalid index.")
                return None
        else:
            soundbank_name = user_input

    if not soundbank_name:
        return None

    if os.path.isfile(soundbank_name):
        process_sf2_drop(soundbank_name)
        return active_bank

    target_file = None
    for item in available_files:
        if item.lower() == soundbank_name.lower() or os.path.splitext(item)[0].lower() == soundbank_name.lower():
            target_file = item
            break

    if not target_file:
        ext = os.path.splitext(soundbank_name)[1]
        target_file = soundbank_name if ext else f"{soundbank_name}.sf2"

    abs_file_path = os.path.join(folder_path, target_file)

    try:
        if os.path.isfile(abs_file_path):
            active_bank = target_file
            if sf_id is not None:
                fs.sfunload(sf_id)
            sf_id = fs.sfload(abs_file_path)
            
            volume(vol)
            for ch in range(16):
                fs.program_change(ch, channel_programs[ch])

            print(f"[+] Active SoundFont changed to: Sound Fonts/{active_bank}")
            return active_bank
        else:
            print(f"[!] SoundFont file 'Sound Fonts/{target_file}' not found.")
            return None
    except Exception as e:
        print(f"[!] Error changing SoundFont: {e}")
        return None


def export_to_wav(output_filename=None):
    if mid is None:
        print("[!] No MIDI file loaded.")
        return

    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    output_path = filedialog.asksaveasfilename(
        title="Select directory and filename for WAV export",
        defaultextension=".wav",
        initialfile=output_filename if output_filename else "output.wav",
        filetypes=[("WAV Audio", "*.wav"), ("All Files", "*.*")]
    )
    root.destroy()

    if not output_path:
        print("[!] Export canceled.")
        return

    # Поиск пути к SoundFont (проверяем все возможные расположения)
    base_dir = get_base_dir()
    sf_name = os.path.basename(active_bank)
    
    possible_paths = [
        active_bank if os.path.isabs(active_bank) else "",
        os.path.join(base_dir, "Sound Fonts", sf_name),
        os.path.join(os.getcwd(), "Sound Fonts", sf_name),
        os.path.join(os.path.dirname(sys.executable), "Sound Fonts", sf_name)
    ]

    sf_path = None
    for p in possible_paths:
        if p and os.path.isfile(p):
            sf_path = p
            break

    if not sf_path:
        print(f"[!] Active SoundFont file not found: {sf_name}")
        return

    print(f"[+] Exporting MIDI to {output_path} using SoundFont: {sf_path}...")

    temp_fs = fluidsynth.Synth()
    temp_fs.sfload(sf_path)

    for ch in range(16):
        temp_fs.cc(ch, 7, vol)
        temp_fs.program_change(ch, channel_programs[ch])

    sample_rate = 44100

    def render_audio_bytes(num_samples):
        if num_samples <= 0:
            return b""
        samples = temp_fs.get_samples(num_samples)
        if isinstance(samples, bytes):
            return samples
        elif hasattr(samples, 'tobytes'):
            return samples.tobytes()
        else:
            return array.array('h', samples).tobytes()

    try:
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(2)      
            wav_file.setsampwidth(2)     
            wav_file.setframerate(sample_rate)

            for msg in mid:
                if msg.time > 0:
                    num_samples = int(msg.time * sample_rate)
                    if num_samples > 0:
                        raw_data = render_audio_bytes(num_samples)
                        wav_file.writeframes(raw_data)

                if msg.type == 'note_on':
                    temp_fs.noteon(msg.channel, msg.note, msg.velocity)
                elif msg.type == 'note_off':
                    temp_fs.noteoff(msg.channel, msg.note)
                elif msg.type == 'control_change':
                    temp_fs.cc(msg.channel, msg.control, msg.value)
                elif msg.type == 'pitchwheel':
                    temp_fs.pitch_bend(msg.channel, msg.pitch)
                elif msg.type == 'program_change':
                    temp_fs.program_change(msg.channel, msg.program)

            if tail:
                tail_samples = int(2.0 * sample_rate)
                raw_tail = render_audio_bytes(tail_samples)
                wav_file.writeframes(raw_tail)

        print(f"[+] Export completed successfully: {output_path} :-)")
    except Exception as e:
        print(f"[!] Error during WAV export: {e}")
    finally:
        temp_fs.delete()


main()

try:
    while cycle:
        raw_input = input("Command (type 'help' for options): \n").strip()
        cleaned_input = clean_path(raw_input)

        if os.path.isfile(cleaned_input):
            ext = os.path.splitext(cleaned_input)[1].lower()
            if ext in ['.mid', '.midi']:
                print(f"[>] File dropped into console: {os.path.basename(cleaned_input)}")
                loaded_mid = load_midi(cleaned_input)
                if loaded_mid:
                    mid = loaded_mid
                    is_playing = False
                    time(0.1)
                    threading.Thread(target=play_midi, daemon=True).start()
                    is_pause = False
                continue
            elif ext in ['.sf2', '.sf3']:
                process_sf2_drop(cleaned_input)
                continue

        parts = raw_input.split(maxsplit=1) 
        command = parts[0].lower() if parts else ""

        if command == "break":
            cycle = cycle_func()
            time(0.5)

        elif command in ["import", "load"]:
            if len(parts) > 1:
                mid = load_midi(parts[1].strip())
            else:
                mid = load_midi(name=None)
            time(0.5)

        elif command == "start":
            if not is_playing:
                threading.Thread(target=play_midi, daemon=True).start()
                is_pause = False 
            else:
                print("MIDI is already playing! -_-")
            time(0.5)
        
        elif command == "pause":
            if not is_pause and is_playing:
                pause_midi()
            time(0.5)

        elif command == "play":
            if is_pause:
                print("[>] Resuming MIDI playback...")
                is_pause = False
            time(0.5)

        elif command == "stop":
            is_playing = False
            is_pause = False
            silence_all()
            print("[x] MIDI stopped.")

        elif command == "help":
            help_command()
            time(0.5)

        elif command == "timetrack":
            timetrack()
            time(0.5)

        elif command == "volume":
            if len(parts) > 1 and parts[1].isdigit() and 0 <= int(parts[1]) <= 127:
                vol = volume(int(parts[1].strip()))
            else:
                vol = volume(volume_track=None)

        elif command == "loop":
            track_cycle = not track_cycle
            print(f"[+] Looping is now {'ENABLED' if track_cycle else 'DISABLED'}.")

        elif command in ["soundfont", "sf"]:
            if len(parts) > 1:
                soundfont(parts[1].strip())
            else:
                soundfont(soundbank_name=None)

        elif command == "export":
            if len(parts) > 1:
                export_to_wav(output_filename=parts[1].strip())
            else:
                export_to_wav(output_filename=None)

        elif command == "tail":
            tail = not tail
            print(f"[+] Reverb tail is now {'ENABLED' if tail else 'DISABLED'}.")

        elif command == "current_sec":
            print(f"[i] Current playback position: {current_sec:.2f} sec.")

        elif command == "seek":
            if mid is None:
                print("[!] No MIDI file loaded.")
            elif len(parts) > 1:
                try:
                    target_sec = float(parts[1].strip())
                    seek(sec=target_sec)
                except ValueError:
                    print("[!] Please enter a valid number of seconds :-/")
            else:
                seek(sec=None)

except Exception as err:
    print(f"[!] Application error: {err}")
finally:
    is_playing = False
    silence_all()
    fs.delete()
    print("Exiting MIDI Thief Player. Goodbye!")