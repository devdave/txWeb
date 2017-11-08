
import os
import sys
import threading
import pathlib
import time

import subprocess


def tprint(*str_in):
    print(f"\t{threading.current_thread().name}: ", *str_in)

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
    while kill_switch.wait(1) == False:

        for pyfile, mtime in manifest.items():

            if pyfile.stat().st_mtime != mtime:
                tprint(f"Modified - {pyfile}")
                kill_switch.set()
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
            self.kill_switch.set()
            raise
        else:
            tprint("Process is live")

        while True:
            try:
                returncode = process.wait(.5)
                tprint(f"Got returncode {returncode}")

                self.ret_val = returncode
                self.kill_switch.set()

            except subprocess.TimeoutExpired:
                if self.check_kill(process) == False:
                    return
                
            except (subprocess.CompletedProcess, subprocess.CalledProcessError,) as exp:
                self.ret_val = exp.returncode
                tprint(f"Process closed/failed with {self.ret_val}")                
                self.kill_switch.set()
                return
            except:
                self.kill_switch.set()
                raise

            
def main():

    entry_point = pathlib.Path(sys.argv[1])
    kill_switch = threading.Event()
    threads = []
    
    
    additional = None
    if len(sys.argv) > 2:
        additional = pathlib.Path(sys.argv[2])
        

    run_failed = False

    while True:
        try:
            if kill_switch.is_set():
                kill_switch.clear()

            watch_thread = threading.Thread(target=watcher, args=(entry_point,kill_switch,additional), name="watcher")
            watch_thread.start()

            if run_failed == True:
                run_failed = False
                tprint("Waiting for a repair")
                accum_time = 0
                while True:
                    watch_thread.join(.5)
                    accum_time += .5
                    if accum_time > 30:
                        tprint("Excessive wait")
                        kill_switch.set()
                        return
                    
                del watch_thread
                continue

            run_thread = Runner(kill_switch, entry_point)
            run_thread.start()

            while True:
                run_thread.join(.5)

                if run_thread.is_alive() == False:
                    tprint("run thread is dead")
                    break


            if run_thread.ret_val == run_thread.CRASH:
                tprint("process crashed")
                return
            else:
                tprint(f"process return code {run_thread.ret_val}")
                kill_switch.set()
                run_failed = True
            
            if kill_switch.is_set() == False:
                kill_switch.set()

            watch_thread.join()

            del run_thread, watch_thread


        except KeyboardInterrupt:
            kill_switch.set()
            tprint("Interrupted - shutting down")            
            return


if __name__ == "__main__":
    print(sys.executable)
    main()
