
import os
import sys
import threading
import pathlib
import time

import subprocess


#Constants
PROCESS = 1
WATCH = 2


def tprint(*str_in):
    print(f"\t{threading.current_thread().name}: ", *str_in)



class EventReason(threading.Event):

    def __init__(self, *args, **kwargs):
        self.reason = None
        #lock should be fine
        self._er_lock = threading.Lock()
        super().__init__(*args, **kwargs)

    def set(self, reason=None):
        if self.is_set() == True:
            return

        with self._er_lock:
            self.reason = None

        super().set()

    def clear(self):
        with self._er_lock:
            self.reason = None

    def why(self):
        with self._er_lock:
            return self.reason






def watcher(entry_point, kill_switch, additional):
    base_dir = entry_point.parent
    manifest = {}
    #build manifest
    for pyfile in base_dir.glob("**/*.py"):
        manifest[pyfile] = pyfile.stat().st_mtime
        # tprint(f"Watching {pyfile}")

    if additional is not None:
        for pyfile in additional.glob("**/*.py"):
            manifest[pyfile] = pyfile.stat().st_mtime
            # tprint(f"Watching {pyfile}")

    #begin the loop
    while kill_switch.is_set() == False:

        time.sleep(.5)
        for pyfile, mtime in manifest.items():

            if pyfile.stat().st_mtime != mtime:
                tprint(f"Modified - {pyfile}")
                kill_switch.set(WATCH)
                return

            
    if kill_switch.is_set() == True:
        tprint("Kill switch set, aborting")
        
        
class Runner(threading.Thread):

    CRASH = "crashed on start"

    def __init__(self, kill_switch, entry_point):
        super().__init__(name="runner")
        
        tprint(f"runner.init: {entry_point.resolve()}")
        tprint(f"runner.init: {entry_point.parent.resolve()}")

        self.kill_switch = kill_switch

        self.entry_point = entry_point.resolve()
        self.base_dir = entry_point.parent.resolve()
        self.ret_val = 0


    def check_kill(self, process):
        if self.kill_switch.is_set():
            tprint("Kill switch is set, exiting")
            process.terminate()
            self.ret_val = 0
            return False

        return True

    def run(self):
    
        try:
            process = subprocess.Popen([sys.executable, str(self.entry_point.resolve())], cwd=self.base_dir)
        except:
            tprint("Crashed!!")
            self.ret_val = self.CRASH
            self.kill_switch.set(PROCESS)
            raise
        else:
            tprint("Process is live")

        while self.kill_switch.is_set() == False:
            try:
                returncode = process.wait(.5)
                tprint(f"Got returncode {returncode}")

                self.ret_val = returncode
                self.kill_switch.set(PROCESS)

            except subprocess.TimeoutExpired:
                pass                
            except (subprocess.CompletedProcess, subprocess.CalledProcessError,) as exp:
                self.ret_val = exp.returncode
                tprint(f"Process closed/failed with {self.ret_val}")                
                self.kill_switch.set(PROCESS)
                return
            except:
                self.ret_val = self.CRASH
                self.kill_switch.set(PROCESS)
                raise

        if process.returncode is None:
            process.terminate()
            time.sleep(1)

            
def main():

    entry_point = pathlib.Path(sys.argv[1])
    kill_switch = EventReason()
    threads = []
    
    
    additional = None
    if len(sys.argv) > 2:
        additional = pathlib.Path(sys.argv[2])
        

    run_failed = False

    while True:
        print(f"Running {entry_point}.")
        try:
            if kill_switch.is_set():
                kill_switch.clear()

            watch_thread = threading.Thread(target=watcher, args=(entry_point,kill_switch,additional), name="watcher")
            watch_thread.start()

            if run_failed == True:
                run_failed = False
                tprint("Waiting for repair")
                accum_time = 0
                while kill_switch.wait(.5) == False:
                    
                    accum_time += .5
                    if accum_time > 60:
                        tprint("Excessive wait")
                        kill_switch.set()
                        return
                    
                del watch_thread
                continue

            run_thread = Runner(kill_switch, entry_point)
            run_thread.start()

            while kill_switch.is_set() == False:
                kill_switch.wait(.5)
                

            tprint(f"process return code {run_thread.ret_val}")

            if kill_switch.why() == WATCH:
                #file changed, reloading
                pass

            elif kill_switch.why() == PROCESS:
                return
                # if run_thread.ret_val == 0:
                #     return
                # elif run_thread.ret_val == run_thread.CRASH:
                #     tprint("process crashed")
                #     #End loop
                #     return
                # elif run_thread.ret_val != 0:
                #     run_failed = True
                                    
            time.sleep(2)
            del run_thread, watch_thread


        except KeyboardInterrupt:
            kill_switch.set()
            tprint("Interrupted - shutting down")            
            return


if __name__ == "__main__":
    print(sys.executable)
    main()
