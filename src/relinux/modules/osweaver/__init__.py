# -*- coding: utf-8 -*-
'''
OSWeaver Module for relinux
@author: Joel Leclerc (MiJyn) <lkjoel@ubuntu.com>
'''

from relinux import threadmanager, config, gui, configutils, fsutil, utilities
if config.python3:
    import tkinter as Tkinter
else:
    import Tkinter
import os
import copy

relinuxmodule = True
relinuxmoduleapi = "0.4a1"
modulename = "OSWeaver"

# Just in case config.ISOTree doesn't include a /
isotreel = config.ISOTree + "/"
tmpsys = config.TempSys + "/"
aptcache = {}
page = {}


def runThreads(threads, **options):
    threadmanager.threadLoop(threads, **options)


def run(adict):
    global aptcache, page
    configs = adict["config"]["OSWeaver"]
    isodir = configutils.getValue(configs[configutils.isodir])
    config.ISOTree = isodir + "/.ISO_STRUCTURE/"
    print(config.ISOTree)
    config.TempSys = isodir + "/.TMPSYS/"
    aptcache = adict["aptcache"]
    ourgui = adict["gui"]
    from relinux.modules.osweaver import isoutil, squashfs, tempsys
    threads = []
    threads.extend(tempsys.threads)
    threads.extend(squashfs.threads)
    threads.extend(isoutil.threads)
    threads_ = utilities.remDuplicates(threads)
    threads = threads_
    pagenum = ourgui.wizard.add_tab()
    page = gui.Frame(ourgui.wizard.page(pagenum))
    ourgui.wizard.add_page_body(pagenum, _("OSWeaver"), page)
    page.frame = gui.Frame(page)
    page.details = gui.VerticalScrolledFrame(page, borderwidth=1, relief=Tkinter.SOLID)
    page.details.output = gui.Label(page.details.interior, text=config.GUIStream.getvalue(), anchor=Tkinter.NW, justify=Tkinter.LEFT)
    def onWrite():
        page.details.output.config(text=config.GUIStream.getvalue())
        page.details.canvas.yview_moveto(1.0)
    config.GUIStream.writefunc.append(onWrite)
    page.details.output.pack(fill=Tkinter.BOTH, expand=True, anchor=Tkinter.NW, side=Tkinter.LEFT)
    page.details.pack(fill=Tkinter.BOTH, expand=True, side=Tkinter.BOTTOM, anchor=Tkinter.SW)
    '''page.details.buttonstate = True
    def showDetails():
        if page.details.buttonstate:
            page.details.output.pack(fill=Tkinter.BOTH, expand=True, anchor=Tkinter.NW, side=Tkinter.LEFT)
            page.showdetails.config(text="<< Hide details")
            page.details.buttonstate = False
        else:
            page.details.output.pack_forget()
            page.showdetails.config(text="Show details >>")
            page.details.buttonstate = True
    page.showdetails = gui.Button(page, text="Show details >>", command=showDetails)
    page.showdetails.pack(side=Tkinter.BOTTOM, anchor=Tkinter.SW)'''
    page.progress = gui.Progressbar(page)
    page.progress.pack(fill=Tkinter.X, expand=True, side=Tkinter.BOTTOM,
                          anchor=Tkinter.S)
    page.frame.pack(fill=Tkinter.BOTH, expand=True, anchor=Tkinter.CENTER)
    page.chframe = gui.VerticalScrolledFrame(page.frame)
    page.chframe.pack(fill=Tkinter.BOTH, expand=True, anchor=Tkinter.N)
    page.chframe.boxes = []
    page.chframe.dispthreads = []
    x = 0
    y = 0
    usedeps = gui.Checkbutton(page.chframe.interior, text="Ignore dependencies")
    usedeps.grid(row=y, column=x)
    y += 1
    label = gui.Label(page.chframe.interior, text="Select threads to run:")
    label.grid(row=y, column=x)
    y += 1
    class customCheck(gui.Checkbutton):
        def __init__(self, parent, *args, **kw):
            gui.Checkbutton.__init__(self, parent, *args, **kw)
            self.id = len(page.chframe.boxes)
            self.ignoreauto = True
            self.value.trace("w", self.autoSelect)

        def autoSelect(self, *args):
            id_ = self.id
            if self.ignoreauto:
                self.ignoreauto = False
                return
            if self.value.get() < 1:
                return
            if len(threads[id_]["deps"]) <= 0 or usedeps.value.get() > 0:
                return
            tns = []
            for i in threads[id_]["deps"]:
                tns.append(i["tn"])
            for i in range(len(threads)):
                if threads[i]["tn"] in tns:
                    page.chframe.boxes[i].value.set(1)
    for i in threads:
        temp = customCheck(page.chframe.interior, text=i["tn"])
        temp.value.set(1)
        temp.grid(row=y, column=x, sticky=Tkinter.NW)
        page.chframe.boxes.append(temp)
        x += 1
        if x >= 3:
            x = 0
            y += 1
    if x != 0:
        y += 1
    def selBoxes(all_):
        val = 0
        if all_ == None:
            for i in range(len(threads)):
                page.chframe.boxes[i].ignoreauto = True
                if page.chframe.boxes[i].value.get() < 1:
                    page.chframe.boxes[i].value.set(1)
                else:
                    page.chframe.boxes[i].value.set(0)
            return
        if all_:
            val = 1
        for i in range(len(threads)):
            page.chframe.boxes[i].ignoreauto = True
            page.chframe.boxes[i].value.set(val)
    selall = gui.Button(page.chframe.interior, text="Select all", command=lambda: selBoxes(True))
    selall.grid(row=y, column=x)
    x += 1
    selnone = gui.Button(page.chframe.interior, text="Select none", command=lambda: selBoxes(False))
    selnone.grid(row=y, column=x)
    x += 1
    togglesel = gui.Button(page.chframe.interior, text="Toggle", command=lambda: selBoxes(None))
    togglesel.grid(row=y, column=x)
    y += 1
    x = 0
    threadsrunninglabel = gui.Label(page.chframe.interior, text="Threads running:")
    threadsrunninglabel.grid(row=y, column=x, columnspan=3)
    y += 1
    page.progress.threads = {}
    def startThreads():
        if os.getuid() != 0:
            page.isnotroot.pack_forget()
            page.isnotroot.pack(fill=Tkinter.X)
            return
        numthreads = 0
        for i in range(len(page.chframe.boxes)):
            if page.chframe.boxes[i].value.get() < 1:
                threads[i]["enabled"] = False
            else:
                threads[i]["enabled"] = True
                numthreads += 1
            tfdeps = False
            if usedeps.value.get() > 0:
                tfdeps = True
        def postStart(threadid, threadsrunning, threads):
            txt = ""
            for i in range(len(threadsrunning)):
                tn = threadmanager.getThread(threadsrunning[i], threads)["tn"]
                if i == len(threadsrunning) - 1:
                    if len(threadsrunning) == 1:
                        txt = tn
                    elif len(threadsrunning) == 2:
                        txt += " and " + tn
                    else:
                        txt += ", and " + tn
                elif i == 0:
                    txt = tn
                else:
                    txt += ", " + tn
            threadsrunninglabel.config(text="Threads running: " + txt)
        def setProgress(tn, progress):
            page.progress.threads[tn] = progress
            totprogress = 0
            for i in page.progress.threads.keys():
                totprogress += utilities.floatDivision(float(page.progress.threads[i]), 100)
            page.progress.setProgress(utilities.calcPercent(totprogress, numthreads))
        def postEnd(threadid, threadsrunning, threads):
            tn = threadmanager.getThread(threadid, threads)["tn"]
            setProgress(tn, 100)
            postStart(threadid, threadsrunning, threads)
        runThreads(threads, deps=tfdeps, poststart=postStart, postend=postEnd, threadargs={"setProgress": setProgress})
        # lambda: runThreads(threads)
    page.button = gui.Button(page.frame, text="Start!", command=startThreads)
    page.button.pack()
    page.isnotroot = gui.Label(page.frame, text="You are not root!")