#!/bin/env python3
import subprocess
import glob
import shlex
import cmd as cmdPrompt


def chunk_names(m):
    return dict(sorted(list(map(lambda x: (int(x.split("_")[-1].split(".JPG")[0]),x), m))))


path = "lsblk -l | grep mmcblk0p1 | awk '{ print $7 }'"
imv = "imv"
files = chunk_names(list(glob.iglob("/run/media/fox/6364-66352/DCIM/*CANON/*.JPG",recursive=True)))
ssh = "trinity"

options = {"rsync": "rsync",
           "flags": "-HPavzc",
           "path": "./www/pics/albums",
           "hook": "./bin/rsync-pics",
           "includes": ["*/"],
           "excludes": ["*"],
           "ssh": "trinity",
           "folder": "",
           "local_path":"/home/fox/Media/6364-66352/DCIM/101CANON/*.JPG"}

local_path="/home/fox/Media/6364-66352/DCIM/101CANON/*.JPG"
remote_path="./www/pics/albums"
rsync="rsync -RHPavzc --no-implied-dirs --rsync-path=\"./bin/rsync-pics\" ~/Media/6364-66352/DCIM/101CANON/*.JPG trinity:./www/pics/albums/$1"


def create_flags(flag, items):
    ret = ""
    for i in items:
        ret += "--{0}=\"{1}\" ".format(flag, i.split("/")[-1])
    return ret


def construct_rsync(rsync):
    shell = ""
    folder = ""
    rsync["includes"] = create_flags("include", rsync["includes"])
    rsync["excludes"] = create_flags("exclude", rsync["excludes"])
    if rsync["hook"]:
        shell = rsync["hook"]
        if rsync["folder"]:
            shell = "mkdir -p {path}/{folder} && ".format(path=rsync["path"],folder=rsync["folder"]) + shell
        shell = "--rsync-path=\"{shell}\"".format(shell=shell)
    ret = "{rsync} {flags} {shell} {includes} {excludes} {local} {ssh}:{remote}/{folder}".format(**rsync, shell=shell, local=local_path, remote=remote_path)
    return ret


def ranges(numbers):
    r = []
    pivot = None
    for n,nn in enumerate(numbers):
        if n+1 >= len(numbers):
            r.append((pivot,nn))
            break
        if len(list(range(nn, numbers[n+1]))) == 1:
            if not pivot:
                pivot = nn
        else:
            if pivot:
                r.append((pivot, nn))
                pivot = None
            else:
                r.append(nn)
    return r


def print_ranges(r):
    return ",".join("-".join(str(nn) for nn in i) if isinstance(i,tuple) else str(i) for i in r)


def expand_files(args):
    ret = []
    for i in args:
        if i in files.keys():
            ret.append(files[i])
        elif not isinstance(i,int):
            ret.append(i)
    return ret


def expand(args):
    def _expand(x):
        l = x.split("-")
        if len(l) > 1:
            return list(range(int(l[0]),int(l[1])+1))
        if l[0] == "*":
            return files
        if l[0].isdigit():
            return [int(l[0])]
        else:
            return [l[0]]
    ret = []
    for i in args:
        ret.extend(_expand(i))
    return expand_files(ret)



_commands = {}
def cmd(name):
    def _(fn):
        _commands[name] = fn
    return _


@cmd("?")
def help(args):
    print ("""
v - view image
c - create album
b - batch commands
u - upload (maybe current batch?)
l - list files
""")


@cmd("q")
def quit(args):
    import sys
    sys.exit()

@cmd("l")
def list_files(args):
    for k,v in files.items():
        print(v)

@cmd("v")
def view_pic(args):
    mode = None
    if "ascii" in args: mode, *args = args
    if mode == "ascii":
        for i in args:
            output = subprocess.run(["img2txt", i], stderr=subprocess.PIPE)
    else:
        try:
            pics = ["imv"] + [files[int(i)] for i in args]
        except ValueError:
            pics = ["imv"] + args
        try:
            output = subprocess.run(pics,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except KeyboardInterrupt:
            pass


@cmd("ls")
def upload_pics(args):
    cmd = "ssh %s ls %s" % (ssh, remote_path)
    output = subprocess.run(cmd.split(), stderr=subprocess.PIPE)
    return None


@cmd("u")
def upload_pics(args):
    folder, *pics = args
    options["folder"] = folder
    options["excludes"] = ["*"]
    options["includes"].extend(pics)
    cmd = construct_rsync(options)
    output = subprocess.run(cmd, shell=True)
    return None


@cmd("r")
def display_ranges(args):
    print(print_ranges(ranges(sorted(list(files.keys())))))


@cmd("o")
def display_options(args):
    print(options)


class PicsShell(cmdPrompt.Cmd):
    intro = None
    prompt ="> "
    file = None

    def onecmd(self, s):
        cmd, *args = s.split(" ")
        args = expand(args)
        if cmd in _commands.keys():
            ret = _commands[cmd](args)
        return self.postcmd(False, "Exit!")




if __name__ == "__main__":
    PicsShell().cmdloop()








