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
    
    state = MESSAGE.CONT
    while state == MESSAGE.CONT:
        state = yield state, None

        for pyfile, mtime in manifest.items():
            if pyfile.stat().st_mtime != mtime:
                state = yield MESSAGE.CHANGED, pyfile
                if state != MESSAGE.CONT:
                    return

                manifest = new_manifest({})



def run_process(entry_point):

    chdir = entry_point.parent.resolve()
    target = entry_point.resolve()
    status = MESSAGE.CONT

    try:
        process = subprocess.Popen([sys.executable, str(entry_point.resolve())], cwd=chdir)
        print("Process started")
    except Exception as ex:
        # yield MESSAGE.CRASHED
        raise

    status = yield MESSAGE.CONT, None

    while status == MESSAGE.CONT:
        try:
            return_code = process.wait(.5)
            status = yield MESSAGE.GRACEFUL, return_code

        except subprocess.TimeoutExpired:
            status = yield MESSAGE.CONT, None
        except subprocess.CalledProcessError as exc:
            status = yield MESSAGE.ERROR, exc.returncode

    process.terminate()


class RUNMODE(Names):
    NORMAL = NamedConstant()
    RESCAN = NamedConstant()


def safe_stop(coroutine):
    try:
        coroutine.send(MESSAGE.STOP)
    except StopIteration:
        return True

    return False

def safe_start(coroutine, *args, **kwargs):
    #somewhat misnomer, more conveniance for now
    cogen = coroutine(*args, **kwargs)
    cogen.send(None)
    return cogen

def main():
    entry_point = pathlib.Path(sys.argv[1])
    additional = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else None

    watcher = safe_start(watch_files, entry_point, additional)
    process = safe_start(run_process, entry_point)
    
    
    try:
        while True:
            
            watch_state, watch_detail = watcher.send(MESSAGE.CONT)

            if watch_state != MESSAGE.CONT:
                print(f"Watch: {watch_state}:{watch_detail}")

                assert watch_state == MESSAGE.CHANGED, f"Watcher state unexpected {watch_state}:{watch_detail}"
                safe_stop(process)
                del process
                process = safe_start(run_process, entry_point)
                
            proc_state, proc_detail = process.send(MESSAGE.CONT)

            if proc_state != MESSAGE.CONT:
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
