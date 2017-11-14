"""
    runner v2
"""
import sys
from constantly import NamedConstant, Names
import subprocess
import pathlib
import time

class MESSAGE(Names):
    STOP = NamedConstant()
    CONT = NamedConstant()
    CHANGED = NamedConstant()
    CRASHED = NamedConstant()
    GRACEFUL = NamedConstant()
    ERROR = NamedConstant()

def find_files(manifest, entry_point, additional):

    for pyfile in entry_point.parent.glob("**/*.py"):
        manifest[pyfile] = pyfile.stat().st_mtime

    if additional:
        for pyfile in additional.glob("**/*.py"):
            manifest[pyfile] = pyfile.stat().st_mtime

    #don't need to do this, but meh
    return manifest

def watch_files(entry_point, additional = None):

    new_manifest = lambda m:find_files(m, entry_point, additional)
    manifest = new_manifest({})
    
    state = EVENT.CONT    
    while state == EVENT.CONT:
        state = yield state, None

        for pyfile, mtime in manifest.items():
            if pyfile.stat().st_mtime != mtime:
                state = yield EVENT.CHANGED, pyfile
                if state != EVENT.CONT:
                    return

                manifest = new_manifest({})



def run_process(entry_point):

    chdir = entry_point.parent.resolve()
    target = entry_point.resolve()
    status = EVENT.CONT

    try:
        process = subprocess.Popen([sys.executable, str(entry_point.resolve())], cwd=chdir)
        print("Process started")
    except Exception as ex:
        # yield EVENT.CRASHED
        raise

    status = yield EVENT.CONT, None

    while status == EVENT.CONT:
        try:
            return_code = process.wait(.5)
            status = yield EVENT.GRACEFUL, return_code

        except subprocess.TimeoutExpired:
            status = yield EVENT.CONT, None
        except subprocess.CalledProcessError as exc:
            status = yield EVENT.ERROR, exc.returncode

    process.terminate()
        

class RUNMODE(Names):
    NORMAL = NamedConstant()
    RESCAN = NamedConstant()


def safe_stop(coroutine):
    try:
        coroutine.send(EVENT.STOP)
    except StopIteration:
        return True

    return False

def main():
    entry_point = pathlib.Path(sys.argv[1])
    additional = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None

    watcher = watch_files(entry_point, additional)
    process = run_process(entry_point)
    
    
    try:
        process.send(None)
        watcher.send(None)
        while True:
            
            watch_state, watch_detail = watcher.send(EVENT.CONT)

            if watch_state != EVENT.CONT:
                print(f"Watch: {watch_state}:{watch_detail}")

                assert watch_state == EVENT.CHANGED, f"Watcher state unexpected {watch_state}:{watch_detail}"
                safe_stop(process)
                del process
                process = run_process(entry_point)
                process.send(None)
                
            proc_state, proc_detail = process.send(EVENT.CONT)

            if proc_state != EVENT.CONT:
                print(f"Process ended with {proc_detail}")
                return

            time.sleep(1)
            
                
    
    except KeyboardInterrupt:
        print("Got interrupted: cleaning up")
        if process:
            safe_stop(process)

    except Exception as ex:
        try:
            if process:            
                safe_stop(process)
        except Exception as ex2:
            print(ex2)
            
        raise


if __name__ == "__main__": main()