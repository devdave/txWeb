"""

    A flask like reloader function for use with txweb

    In user script it must follow the pattern

    def main():
        my main func that starts twisted

    if __name__ == "__main__":
        from txweb.sugar.reloader import reloader
        reloader(main)
    else:
        TAC logic goes here but isn't necessary for short term dev work


    Originally found via https://blog.elsdoerfer.name/2010/03/09/twisted-twistd-autoreload/
    NOTE - pyutils appears to be dead or a completely different project
    That link lead to this code snippet - https://bitbucket.org/miracle2k/pyutils/src/tip/pyutils/autoreload.py

    I didn't like how the watching logic walked through sys.modules as I was just concerned with the immediate
    project files and not the entire ecosystem.   Instead it starts with the current working directory via os.getcwd
    and then walks downward to look over .py files

    sys.exit didn't work correctly so I switched to use os._exit as hardset.   I am not sure what to do if
    os._exit ever gets deprecated.

    I also removed the checks for where to run the reloader logic and it will always run as a thread.

    recopied from https://gist.github.com/devdave/05de2ed2fa2aa0a09ba931db36314e3e

"""
import pathlib
import os
import sys
import time

from logging import getLogger

log = getLogger(__name__)


try:
    import thread
except ImportError:
    try:
        import _thread as thread
    except ImportError:
        try:
            import dummy_thread as thread
        except ImportError:
            try:
                import _dummy_thread as thread
            except ImportError:
                print("Alright... so I tried importing thread, that failed, so I tried _thread, that failed too")
                print("..so then I tried dummy_thread, then _dummy_thread.  All failed")
                print(", at this point I am out of ideas here")
                raise RuntimeError("Failed to import threading library")
                sys.exit(-1)

RUN_RELOADER = True
SENTINEL_CODE = 7211
SENTINEL_NAME = "RELOADER_ACTIVE"
SENTINEL_OS_EXIT = True

try:
    """
       "Reason" is here https://code.djangoproject.com/ticket/2330

       TODO - Figure out why threading needs to be imported as this feels like a problem 
       within stdlib.
    """
    import threading
except ImportError:
    pass

_watch_list = {}
_win = (sys.platform == "win32")


def build_list(root_dir, watch_self=False):
    """
        Walk from root_dir down, collecting all files that end with ^*.py$ to watch

        This could get into a recursive hell loop but I don't use symlinks in my projects
        so just roll with it.

    :param root_dir: pathlib.Path current working dir to search
    :param watch_self: bool Watch all of txweb for changes
    :return: None
    """

    global _watch_list

    if watch_self is True:
        import txweb
        build_list(pathlib.Path(txweb.__file__).parent.absolute())


    for pathobj in root_dir.iterdir():
        if pathobj.is_dir():
            build_list(pathobj, watch_self=False)
        elif pathobj.name.endswith(".py") and not (pathobj.name.endswith(".pyc") or pathobj.name.endswith(".pyo")):
            stat = pathobj.stat()
            _watch_list[pathobj] = (stat.st_size, stat.st_ctime, stat.st_mtime,)
        else:
            pass


def file_changed():
    global _watch_list
    change_detected = False
    for pathname, (st_size, st_ctime, st_mtime) in _watch_list.items():
        pathobj = pathlib.Path(pathname)
        stat = pathobj.stat()
        if pathobj.exists() is False:
            raise Exception(f"Lost track of {pathname!r}")
        elif stat.st_size != st_size:
            change_detected = True
        elif stat.st_ctime != st_ctime:
            change_detected = True
        elif _win is False and stat.st_mtime != st_mtime:
            change_detected = True

        if change_detected:
            log.debug(f"RELOADING - {pathobj} changed")
            break

    return change_detected


def watch_thread(os_exit=SENTINEL_OS_EXIT, watch_self=False):
    exit_func = os._exit if os_exit is True else sys.exit

    build_list(pathlib.Path(os.getcwd()), watch_self=watch_self)

    while True:
        if file_changed():
            exit_func(SENTINEL_CODE)

        time.sleep(1)


def run_reloader():
    while True:
        args = [sys.executable] + sys.argv
        if _win:
            args = ['"%s"' % arg for arg in args]

        new_env = os.environ.copy()
        new_env[SENTINEL_NAME] = "true"
        log.info("Starting reloader process")
        # print("Running reloader process")
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_env)
        if exit_code != SENTINEL_CODE:
            return exit_code


def reloader_main(main_func, args, kwargs, watch_self=False):
    """

    :param main_func:
    :param args:
    :param kwargs:
    :return:
    """

    # If it is, start watcher thread and then run the main_func in the parent process as thread 0
    if os.environ.get(SENTINEL_NAME) == "true":

        thread.start_new_thread(watch_thread, (), {"os_exit": SENTINEL_OS_EXIT, "watch_self": watch_self})
        try:
            main_func(*args, **kwargs)
        except KeyboardInterrupt:
            pass

    else:
        # respawn this script into a blocking subprocess
        try:
            sys.exit(run_reloader())
        except KeyboardInterrupt:
            # I should just raise this because its already broken free of its rails
            pass


def reloader(main_func, args=None, kwargs=None, **more_options):
    """
        To avoid fucking with twisted as much as possible, the watcher logic is shunted into
        a thread while the main (twisted) reactor runs in the main thread.

    :param main_func: The function to run in the main/primary thread
    :param args: list of arguments
    :param kwargs: dictionary of arguments
    :param more_options: var trash currently
    :return: None
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    reloader_main(main_func, args, kwargs, **more_options)


"""

def main():
  #startup twisted here

if __name__ == "__main__":
  reloader(main)

"""