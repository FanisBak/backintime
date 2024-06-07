import os
import subprocess
import re
import dbus
from tools import isRoot, processExists, pidsWithName
from distutils.version import StrictVersion

class SleepMode(object):
    """
    Put the system into sleep mode after the current snapshot has finished.
    This should work for KDE, Gnome, Unity, Cinnamon, XFCE, Mate and E17.
    """
    DBUS_SLEEP = {'gnome':   {'bus':          'sessionbus',
                              'service':      'org.gnome.SessionManager',
                              'objectPath':   '/org/gnome/SessionManager',
                              'method':       'Suspend',
                              'interface':    'org.gnome.SessionManager',
                              'arguments':    ()
                             },
                  'kde':     {'bus':          'sessionbus',
                              'service':      'org.kde.Solid.PowerManagement',
                              'objectPath':   '/org/kde/Solid/PowerManagement/Actions/SuspendSession',
                              'method':       'suspend',
                              'interface':    'org.kde.Solid.PowerManagement.Actions.SuspendSession',
                              'arguments':    ()
                             },
                  'xfce':    {'bus':          'sessionbus',
                              'service':      'org.xfce.SessionManager',
                              'objectPath':   '/org/xfce/SessionManager',
                              'method':       'Suspend',
                              'interface':    'org.xfce.Session.Manager',
                              'arguments':    ()
                             },
                  'mate':    {'bus':          'sessionbus',
                              'service':      'org.mate.SessionManager',
                              'objectPath':   '/org/mate/SessionManager',
                              'method':       'Suspend',
                              'interface':    'org.mate.SessionManager',
                              'arguments':    ()
                             },
                  'e17':     {'bus':          'sessionbus',
                              'service':      'org.enlightenment.Remote.service',
                              'objectPath':   '/org/enlightenment/Remote/RemoteObject',
                              'method':       'Suspend',
                              'interface':    'org.enlightenment.Remote.Core',
                              'arguments':    ()
                             },
                  'e19':     {'bus':          'sessionbus',
                              'service':      'org.enlightenment.wm.service',
                              'objectPath':   '/org/enlightenment/wm/RemoteObject',
                              'method':       'Suspend',
                              'interface':    'org.enlightenment.wm.Core',
                              'arguments':    ()
                             },
                  'z_freed': {'bus':          'systembus',
                              'service':      'org.freedesktop.login1',
                              'objectPath':   '/org/freedesktop/login1',
                              'method':       'Suspend',
                              'interface':    'org.freedesktop.login1.Manager',
                              'arguments':    (True,)
                             }
                 }

    def __init__(self):
        self.is_root = isRoot()
        if self.is_root:
            self.proxy, self.args = None, None
        else:
            self.proxy, self.args = self._prepair()
        self.activate_sleep = False
        self.started = False

    def _prepair(self):
        """
        Try to connect to the given dbus services. If successful it will
        return a callable dbus proxy and those arguments.
        """
        try:
            if 'DBUS_SESSION_BUS_ADDRESS' in os.environ:
                sessionbus = dbus.bus.BusConnection(os.environ['DBUS_SESSION_BUS_ADDRESS'])
            else:
                sessionbus = dbus.SessionBus()
            systembus  = dbus.SystemBus()
        except:
            return((None, None))
        des = list(self.DBUS_SLEEP.keys())
        des.sort()
        for de in des:
            dbus_props = self.DBUS_SLEEP[de]
            try:
                if dbus_props['bus'] == 'sessionbus':
                    bus = sessionbus
                else:
                    bus = systembus
                interface = bus.get_object(dbus_props['service'], dbus_props['objectPath'])
                proxy = interface.get_dbus_method(dbus_props['method'], dbus_props['interface'])
                return((proxy, dbus_props['arguments']))
            except dbus.exceptions.DBusException:
                continue
        return((None, None))

    def canSleep(self):
        """
        Indicate if a valid dbus service is available to put the system into sleep mode.
        """
        return(not self.proxy is None or self.is_root)

    def askBeforeQuit(self):
        """
        Indicate if SleepMode is ready to fire and so the application
        shouldn't be closed.
        """
        return(self.activate_sleep and not self.started)

    def sleep(self):
        """
        Run 'kill -SIGSTOP' if we are root or
        call the dbus proxy to start the sleep mode.
        """
        if not self.activate_sleep:
            return(False)
            
        if self.is_root:
            syncfs()
            self.started = True
            if processExists('backintime'):
            	pids = pidsWithName('backintime')
            	proc = subprocess.Popen(['kill', '-SIGSTOP', pids[0] ])
            	proc.communicate()
            	return proc.returncode
            	
        if self.proxy is None:
            return(False)
        else:
            syncfs()
            self.started = True
            return(self.proxy(*self.args))

def syncfs():
    """
    Sync the filesystem to ensure all pending changes are written to disk.
    """
    subprocess.call(['sync'])
