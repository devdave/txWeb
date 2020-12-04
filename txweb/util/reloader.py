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
import typing as T
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
        except ImportError as missing_import:
            print("Alright... so I tried importing thread, that failed, so I tried _thread, that failed too")
            print("..so then I tried dummy_thread, then _dummy_thread.  All failed")
            print(", at this point I am out of ideas here")
            raise RuntimeError("Failed to import threading library") from missing_import


RUN_RELOADER = True
SENTINEL_CODE = 7211
SENTINEL_NAME = "RELOADER_ACTIVE"
SENTINEL_OS_EXIT = True

"""
   "Reason" is here https://code.djangoproject.com/ticket/2330
   TODO - Figure out why threading needs to be imported as this feels like a problem within stdlib.
"""
try:
    import threading
except ImportError:
    pass

WATCH_LIST = {}
_win = (sys.platform == "win32")


def build_list(
        root_dir: T.Union[pathlib.Path, str],
        watch_self: bool = False,
        ignore_prefix: T.Optional[T.List[str]] = None):
    """
        Walk from root_dir down, collecting all files that end with ^*.py$ to watch

        This could get into a recursive hell loop but I don't use symlinks in my projects
        so just roll with it.

    :param root_dir: pathlib.Path current working dir to search
    :param watch_self: bool Watch all of txweb for changes
    :param ignore_prefix: simple check that if provided compares file names to the prefix and skips if they match
    :return: None
    """

    global WATCH_LIST

    if watch_self is True:
        import txweb
        log.info("RELOADER: Watching self")
        build_list(pathlib.Path(txweb.__file__).parent.absolute(), ignore_prefix=ignore_prefix)

    def is_list(obj):
        return obj is not None and isinstance(obj, list)

    for pathobj in root_dir.iterdir():
        if pathobj.is_dir():
            build_list(pathobj, watch_self=False, ignore_prefix=ignore_prefix)
        elif pathobj.name.endswith(".py") and not (pathobj.name.endswith(".pyc") or pathobj.name.endswith(".pyo")):
            stat = pathobj.stat()
            if is_list(ignore_prefix) and any([pathobj.name.startswith(prefix) for prefix in ignore_prefix]) is False:
                WATCH_LIST[pathobj] = (stat.st_size, stat.st_ctime, stat.st_mtime,)
            else:
                # print("Ignoring", pathobj.name)
                pass
        else:
            pass


def file_changed() -> bool:
    """
        Scans the watched list of files for change in size, created & modified timestamps
    :return:
    """
    global WATCH_LIST
    change_detected = False
    for pathname, (st_size, st_ctime, st_mtime) in WATCH_LIST.items():
        pathobj = pathlib.Path(pathname)
        stat = pathobj.stat()
        if pathobj.exists() is False:
            raise Exception(f"Lost track of {pathname!r}")

        if stat.st_size != st_size:
            change_detected = True
        elif stat.st_ctime != st_ctime:
            change_detected = True
        elif _win is False and stat.st_mtime != st_mtime:
            change_detected = True

        if change_detected:
            print(f"RELOADING - {pathobj} changed")
            break

    return change_detected


def watch_thread(os_exit: bool = SENTINEL_OS_EXIT, watch_self: bool = False, ignore_prefix=None):
    """

    :param os_exit: flag to decide whether to use sys.exit or os._exit
    :param watch_self: Should reloader watch its own source code
    :param ignore_prefix: Ignore files starting with this prefix
    :return:
    """
    exit_func = os._exit if os_exit is True else sys.exit

    build_list(pathlib.Path(os.getcwd()), watch_self=watch_self, ignore_prefix=ignore_prefix)

    while True:
        if file_changed():
            exit_func(SENTINEL_CODE)

        time.sleep(1)


def run_reloader():
    """
        Respawns the user's program/script and hangs until it returns.

    :return:
    """
    args = [sys.executable] + sys.argv
    if _win:
        args = ['"%s"' % arg for arg in args]

    new_env = os.environ.copy()
    new_env[SENTINEL_NAME] = "true"
    log.info("Starting reloader process")

    while True:
        exit_code = os.spawnve(os.P_WAIT, sys.executable, args, new_env)
        if exit_code != SENTINEL_CODE:
            return exit_code


def reloader_main(main_func, *args, watch_self=False, ignore_prefix=None, **kwargs) -> None:
    """

        Right...  This checks to see if it is running as a child process with the sentinel flag set in its
        process environment and if it isn't, it spawns a child process that run's the user's provided entry point
        "main function".

        Meanwhile in the child process, a watcher thread scans the user application source code files for changes.

    :param main_func:  The entry point to the user application
    :param watch_self: Should reloader also watch it's own source code for changes?
    :param args: arguments for the main_func
    :param ignore_prefix: Files to ignore by their prefix/starts with.
    :param kwargs: keyword arguments for the main func
    :return:
    """

    # If it is, start watcher thread and then run the main_func in the parent process as thread 0
    if os.environ.get(SENTINEL_NAME) == "true":

        thread.start_new_thread(
            watch_thread,
            (),
            {"os_exit": SENTINEL_OS_EXIT, "watch_self": watch_self, "ignore_prefix": ignore_prefix})
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


def reloader(main_func, *args, watch_self=False, ignore_prefix=None, **kwargs):
    """
        See Reloader main for how this works.

        WARNING - This assumes that the cwd (current working directory) is the base directory
        of the project to be watched.

    :param main_func: The function to run in the main/primary thread
    :param args: list of arguments
    :param watch_self: Should reloader also watch it's own src code for changes?
    :param ignore_prefix: Files to ignore based on their prefix (eg test_ files)
    :param kwargs: dictionary of arguments
    :return: None
    """
    if args is None:
        args = ()
    if kwargs is None:
        kwargs = {}

    reloader_main(main_func, *args, watch_self=watch_self, ignore_prefix=ignore_prefix, **kwargs)
