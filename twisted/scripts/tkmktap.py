
# Twisted, the Framework of Your Internet
# Copyright (C) 2001 Matthew W. Lefkowitz
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of version 2.1 of the GNU Lesser General Public
# License as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""Implementation module for the graphical version of the `mktap` command.
"""

# System imports
import Tkinter, tkMessageBox, StringIO, os, sys

# Twisted imports
from twisted.internet import tksupport, reactor, app
from twisted.scripts import mktap
from twisted.python import failure, usage

class TkMkAppFrame(Tkinter.Frame):
    """
    A frame with all the necessary widgets to configure a Twisted Application.
    """

    # Plugin currently selected
    coil = None
    
    # Options instance currently displayed
    options = None

    # Frame options are displayed in
    optFrame = None

    def __init__(self, master, coil):
        Tkinter.Frame.__init__(self, master)

        self.setupMkTap()
        self.reset(coil)


    def setupMkTap(self):
        # Create all of the "mktap" option widgets
        appFrame = Tkinter.Frame(self)

        f = Tkinter.Frame(appFrame)
        listLabel = Tkinter.Label(f, text='TAp Type')
        self.typeList = Tkinter.Listbox(f)
        self.typeList['height'] = 3
        for t in ('pickle', 'xml', 'source'):
            self.typeList.insert(Tkinter.END, t)
        self.typeList.selection_set(0)

        listLabel.pack(side=Tkinter.TOP)
        self.typeList.pack(side=Tkinter.TOP)
        f.pack(side=Tkinter.LEFT, anchor=Tkinter.N)

        f = Tkinter.Frame(appFrame)
        encLabel = Tkinter.Label(f, text='Passphrase')
        self.passphrase = Tkinter.Entry(f)

        encLabel.pack(side=Tkinter.LEFT)
        self.passphrase.pack(side=Tkinter.LEFT)
        f.pack(side=Tkinter.TOP, anchor=Tkinter.E)

        f = Tkinter.Frame(appFrame)
        self.append = Tkinter.BooleanVar()
        appLabel = Tkinter.Label(f, text='Append')
        appButton = Tkinter.Checkbutton(f, variable=self.append)

        appLabel.pack(side=Tkinter.LEFT)
        appButton.pack(side=Tkinter.LEFT)
        f.pack(side=Tkinter.LEFT, anchor=Tkinter.E)

        f = Tkinter.Frame(appFrame)
        tapLabel = Tkinter.Label(f, text='TAp filename')
        self.tapfile = Tkinter.Entry(f)

        tapLabel.pack(side=Tkinter.LEFT)
        self.tapfile.pack(side=Tkinter.LEFT)
        f.pack(side=Tkinter.TOP, anchor=Tkinter.E)

        f = Tkinter.Frame(appFrame)
        s = Tkinter.StringVar()
        s.set(str(os.getuid()))
        uidLabel = Tkinter.Label(f, text='UID')
        self.uid = Tkinter.Entry(f, text=s)

        uidLabel.pack(side=Tkinter.LEFT)
        self.uid.pack(side=Tkinter.LEFT)
        f.pack(side=Tkinter.BOTTOM)

        f = Tkinter.Frame(appFrame)
        s = Tkinter.StringVar()
        s.set(str(os.getgid()))
        gidLabel = Tkinter.Label(f, text='GID')
        self.gid = Tkinter.Entry(f, text=s)

        gidLabel.pack(side=Tkinter.LEFT)
        self.gid.pack(side=Tkinter.LEFT)
        f.pack(side=Tkinter.BOTTOM)

        appFrame.grid(row=0, column=0, columnspan=3, sticky=Tkinter.N + Tkinter.S)


    def reset(self, coil):
        """
        Remove the existing coil-specific widgets and then create and add
        new ones based on the given plugin object.
        """
        try:
            opt = coil.load().Options()
        except:
            f = StringIO.StringIO()
            traceback.print_stack(file=f)
            # XXX - Why is this so narrow?
            tkMessageBox.showerror(title="Options Error", message=f.getvalue(), parent=self)
            return

        if self.optFrame:
            self.optFrame.forget()
            self.optFrame.destroy()
            self.optFrame = None

        self.coil = coil
        self.options = opt
        self.optFrame = TkConfigFrame(self, self.options)
        self.optFrame.grid(row=1, column=0)

        self.tapfile.delete(0, Tkinter.END)
        try:
            self.tapfile.insert(Tkinter.END, self.coil.tapname)
        except AttributeError:
            self.tapfile.insert(Tkinter.END, self.coil.name)
    
    
    def copyOptions(self):
        # Snarf the data out of the widgets and place them into the Options
        # instance.
        for (opt, var) in self.optFlags + self.optParameters:
            self.options[opt] = var.get()

        self.options['filename'] = self.tapfile.get()
        self.options['passphrase'] = self.passphrase.get()

        self.options['append'] = self.append.get()
        self.options['encrypted'] = len(self.options['passphrase'])

        self.options['uid'] = int(self.uid.get())
        self.options['gid'] = int(self.gid.get())
        
        self.options['type'] = self.typeList.curselection()[0]
        self.options['help'] = 0


    def createApplication(self):
        self.copyOptions()

        if self.options['append'] and os.path.exists(self.options['filename']):
            a = twistd.loadApplication(self.options, None)
        else:
            a = app.Application(self.coil.name, self.options['uid'], self.options['gid'])

        try:
            self.coil.load().updateApplication(a, self.options)
        except usage.UsageError:
            f = StringIO.StringIO()
            traceback.print_stack(file=f)
            tkMessageBox.showerror(title="Usage Error", message=f.getvalue(), parent=self)
        else:
            a.save()


    def destroy(self):
        reactor.stop()
        Tkinter.Frame.destroy(self)


class TkConfigFrame(Tkinter.Frame):
    optFrame = None
    paramFrame = None
    commandFrame = None

    subCmdFrame = None
    previousCommand = None

    optFlags = None
    optParameters = None


    def __init__(self, master, options):
        Tkinter.Frame.__init__(self, master)
        self.options = options

        self.setupOptFlags()
        self.setupOptParameters()
        self.setupSubCommands()


    def setupOptFlags(self):
        self.optFlags = []
        if hasattr(self.options, 'optFlags'):
            self.optFrame = f = Tkinter.Frame(self)
            for (flag, _, desc) in self.options.optFlags:
                b = Tkinter.BooleanVar()
                c = Tkinter.Checkbutton(f, text=desc, variable=b, wraplen=200)
                c.pack()
                self.optFlags.append((flag, b))
            f.grid(row=1, column=1)


    def setupOptParameters(self):
        self.optParameters = []
        if hasattr(self.options, 'optParameters'):
            i = 0
            self.paramFrame = f = Tkinter.Frame(self)
            for (flag, _, default, desc) in self.options.optParameters:
                s = Tkinter.StringVar()
                if default:
                    s.set(default)
                l = Tkinter.Label(f, text=desc, wraplen=200)
                t = Tkinter.Entry(f, text=s)
                l.grid(row=i, column=0)
                t.grid(row=i, column=1)
                self.optParameters.append((flag, t))
                i += 1
            f.grid(row=1, column=2)


    def setupSubCommands(self):
        self.optMap = {}
        if hasattr(self.options, 'subCommands'):
            self.commandFrame = f = Tkinter.Frame(self)
            self.cmdList = Tkinter.Listbox(f)
            for (cmd, _, opt, desc) in self.options.subCommands:
                self.cmdList.insert(Tkinter.END, cmd)
                self.optMap[cmd] = opt()
            self.cmdList.pack()
            self.subCmdPoll = reactor.callLater(0.1, self.pollSubCommands)
            f.grid(row=1, column=3)


    def pollSubCommands(self):
        s = self.cmdList.curselection()
        if len(s):
            s = s[0]
            if s != self.previousCommand:
                if self.subOptFrame:
                    self.subOptFrame.forget()
                    self.subOptFrame.destroy()
                    self.subOptFrame = TkConfigFrame(self.commandFrame, self.optMap[s])
                    self.subOptFrame.pack()


class TkAppMenu(Tkinter.Menu):
    def __init__(self, master, create, callback, items):
        Tkinter.Menu.__init__(self, master)

        cmdMenu = Tkinter.Menu(self)
        self.add_cascade(label="Actions", menu=cmdMenu)
        
        cmdMenu.add_command(label='Create', command=create)
        cmdMenu.add_separator()
        cmdMenu.add_command(label='Quit', command=reactor.stop)

        tapMenu = Tkinter.Menu(self)
        self.add_cascade(label="Applications", menu=tapMenu)

        for item in items:
            tapMenu.add_command(label=item, command=lambda i=item: callback(i))


def run():
    taps = mktap.loadPlugins()
    r = Tkinter.Tk()
    r.withdraw()
    
    keyList = taps.keys()
    keyList.sort()

    config = TkMkAppFrame(r, taps.values()[0])
    menu = TkAppMenu(
        r,
        config.createApplication,
        lambda i, d = taps, c = config: c.reset(d[i]),
        keyList
    )


    config.pack()
    r['menu'] = menu

    r.deiconify()
    tksupport.install(r)
    reactor.run()

if __name__ == '__main__':
    run()
