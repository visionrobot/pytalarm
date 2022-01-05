#!/usr/bin/env python

# pytalarm.py

# Description: A Python program for the Gnome / Mate desktop
# to make the computer act like an alarm clock.
#
# Contact email: visionrobot@gmail.com
#
# URL: https://github.com/visionrobot/pytalarm

import re
import string
import datetime
import glob

import threading
import subprocess

import os
import sys

if sys.version_info > (3, 0):
    print("Running on python3.")
    import configparser
else:
    print("Running on python2.")
    import ConfigParser as configparser

from shutil import copyfile

import time
from time import sleep
from threading import Timer

import sys
import signal
import json

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

gi.require_version('Notify', '0.7')
from gi.repository import Notify as notify

if sys.platform == "win32":
    import winsound
else:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator

APPINDICATOR_ID = 'pytalarm'

DEF_PAD = 10
DEF_PAD_SMALL = 5

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

sPytAlarmVersion = "Pytalarm 1.1.1"
sPytAlarmURL = "https://github.com/visionrobot/pytalarm"
sCreditText = "visionrobot@gmail.com"

pidfile = "/var/tmp/pytalarm.pid"
sIconDir = "/usr/share/pytalarm/icons/"
sIcon = sIconDir + "pytalarm.svg"
sActiveIcon = sIconDir + "pytalarm-active.svg"

class MainWindow(Gtk.ApplicationWindow):

    def __init__(self):
        window = Gtk.Window.__init__(self, title="Pytalarm")

        self.set_icon_from_file(sIcon)

        self.set_default_size(300, 30)

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)
        self.set_resizable(True)

    def delete_event(self, window, event):
        window.hide()
        app.bwMainActive = 0

class ListAlarmsWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Alarms list")

        #self.set_default_size(300, 10)
        self.set_default_size(1, 1)

    def delete_event(self, window, event):
        window.hide()
        app.bwListAlarmsActive = 0

class AlarmWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Set an alarm")

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)
        self.set_resizable(False)

    def delete_event(self, window, event):
        app.alarm.save_window("windowAddAlarm")
        app.bwAddAlarmActive = 0
        window.hide()

class AboutWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="About")

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)
        self.set_resizable(False)

    def delete_event(self, window, event):
        app.alarm.save_window("windowAbout")
        app.bwAboutActive = 0
        window.hide()

class LastAlarmsWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Last alarms")

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)
        self.set_resizable(True)

    def delete_event(self, window, event):
        app.alarm.save_window("windowLastAlarms")
        app.bwLastAlarmsActive = 0
        window.hide()

class SchedWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Repetition settings")

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)
        self.set_resizable(True)

    def delete_event(self, window, event):
        app.bwSchedActive = 0
        app.alarm.save_window("windowSched")
        window.hide()

class PytAlarm(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

        self.bStartLoad = 1

        self.bAddAlarmMode = 1
        self.init_settings()

        self.windowListAlarms = None
        self.windowAddAlarm = None
        self.windowSched = None
        self.windowLastAlarms = None
        self.windowAbout = None

        self.marked_date = 31 * [0]

        self.sSoundDir = "/usr/share/pytalarm/sounds/"
        sRootDir = ""
        if sys.platform == "win32":
            sRootDir = os.path.dirname(sys.argv[0])
            if sRootDir == "":
                sRootDir = "./"
            self.sSoundDir = os.path.abspath(sRootDir + "/../../" + self.sSoundDir) + "/"

        sHome = ""
        if (sys.platform == "linux") or (sys.platform == "linux2") or (sys.platform == "linux3"):
            sHome = os.getenv("HOME")

        if sys.platform == "win32":
            sHome = os.getenv("USERPROFILE")

        if (sHome == ""):
            sHome = "./"
        if (not sHome.endswith('/')):
            sHome = sHome + "/"
        self.sConfigDir = sHome + ".config/pytalarm/"
        if not os.path.exists(self.sConfigDir):
            os.makedirs(self.sConfigDir)
        # print(sHome + " " + self.sConfigDir)
        self.sConfigFile = self.sConfigDir + "config.conf"

        self.toggleDay = 8 * [0]
        self.toggleDaySettings = 8 * [0]

        self.sDayName = 8 * [0]
        self.sDayName[1] = "Monday"
        self.sDayName[2] = "Tuesday"
        self.sDayName[3] = "Wednesday"
        self.sDayName[4] = "Thursday"
        self.sDayName[5] = "Friday"
        self.sDayName[6] = "Saturday"
        self.sDayName[7] = "Sunday"

        self.toggleMonth = 13 * [0]
        self.toggleMonthSettings = 13 * [0]

        self.sMonthName = 13 * [0]
        self.sMonthName[1] = "January"
        self.sMonthName[2] = "February"
        self.sMonthName[3] = "March"
        self.sMonthName[4] = "April"
        self.sMonthName[5] = "May"
        self.sMonthName[6] = "June"
        self.sMonthName[7] = "July"
        self.sMonthName[8] = "August"
        self.sMonthName[9] = "September"
        self.sMonthName[10] = "October"
        self.sMonthName[11] = "November"
        self.sMonthName[12] = "December"

    def init_settings(self):
        # print("init_settings")

        if self.bAddAlarmMode:
            self.sAlarmID = ""
            self.sName = "Untitled"

            self.sHour = "9"
            self.sMinutes = "00"
            self.sDate = ""
            self.sDateTime = ""

            self.bAddHM = 0

            date = datetime.datetime.today()

            self.sCron = 6 * [0]
            self.sCron[1] = self.sMinutes
            self.sCron[2] = self.sHour
            self.sCron[3] = "*"
            self.sCron[4] = "*"
            self.sCron[5] = "*"

            self.sDaysSelected = ""
            self.sMonthsSelected = ""
            # self.sMonthsSelected = str(date.month)

            self.sCronEntry = ""
            for i in range(1, 6):
                self.sCronEntry = self.sCronEntry + self.sCron[i] + " "

            self.sScript = ""
            self.bAlarmActive = 1
            self.bCalendarSelected = 0

            self.sSound = ""
            self.sSoundListCount = 0

            self.sSettings = ""

        else:
            self.load_settings()

    def load_settings(self):
        self.bStartLoad = 1

        self.entryName.set_text(self.sName)

        if "," in str(self.sHour):
            for i in re.split(',', self.sHour):
                self.sHour = i
        adj = Gtk.Adjustment(int(self.sHour), 0, 24, 1, 5, 0)
        self.spinnerHour.set_adjustment(adj)

        if "," in str(self.sMinutes):
            for i in re.split(',', self.sMinutes):
                self.sMinutes = i
        adj = Gtk.Adjustment(int(self.sMinutes), 0, 59, 1, 5, 0)
        self.spinnerMinutes.set_adjustment(adj)

        if self.sCron[2] == "*":
            self.toggleEachHour.set_active(1)

        if (self.sCron[3] == "*") and (self.sCron[4] == "*") and (self.sCron[5] == "*"):
            self.toggleEveryday.set_active(1)
            self.bCalendarSelected = 0
        else:
            self.toggleEveryday.set_active(0)

        self.sMonthsSelected = ""
        if not self.sCron[4] == "*":
            self.sMonthsSelected = self.sCron[4]

        self.sDaysSelected = ""
        if not self.sCron[5] == "*":
            self.sDaysSelected = self.sCron[5]

        if not self.sDaysSelected == "*":
            for i in re.split(',', self.sDaysSelected):
                if not i == '':
                    self.toggleDaySettings[int(i)] = 1

        if not self.sMonthsSelected == "*":
            for i in re.split(',', self.sMonthsSelected):
                if not i == '':
                    self.toggleMonthSettings[int(i)] = 1

        if self.sSound == "None":
            self.sSound = self.sSoundList[3]

        for i in range(0, self.sSoundListCount + 1):
            if self.sSoundList[i] == self.sSound:
                self.bStartLoad = 1
                self.comboSound.set_active(int(i - 1))

        self.entryCron.set_text(self.sCronEntry)
        self.entryScript.set_text(self.sScript)
        self.toggleActive.set_active(self.bAlarmActive)

        # self.sSettings = self.sName + " | " + self.sCronEntry + " | " + self.sSound + " | " + str(self.bAlarmActive);
        # self.labelAlarmInfo.set_text(self.sSettings)

    def setsHour(self):
        self.sHour = self.spinnerHour.get_value_as_int()
        if int(self.sHour) < 10:
            self.sHour = "0" + str(self.sHour)

    def setsMinutes(self):
        self.sMinutes = self.spinnerMinutes.get_value_as_int()
        if int(self.sMinutes) < 10:
            self.sMinutes = "0" + str(self.sMinutes)

    def save_strings(self):
        if self.bCalendarSelected:
            self.sDateTime = str(self.sDate) + " "
        else:
            self.sDateTime = " "

        self.sName = self.entryName.get_text()

        if self.toggleEachHour.get_active():
            self.sHour = "*"
        else:
            self.setsHour()
        self.setsMinutes()

        self.sound_save()
        self.entryCron_update()

        self.toggleActive.set_active(self.bAlarmActive)

        # self.sSettings = self.sName + " | " + self.sCronEntry + " | " + self.sSound + " | " + str(self.bAlarmActive);
        # self.labelAlarmInfo.set_text(self.sSettings)

    def toggle_addHM(self, widget):
        if self.toggleAddHM.get_active():
            self.bAddHM = 1
            self.toggleAddHM.set_active(0)

            self.setsHour()
            self.setsMinutes()

            bMinInCron = 0
            if "," in str(self.sCron[1]):
                for i in re.split(',', self.sCron[1]):
                    if str(i) == str(self.sMinutes):
                        bMinInCron = 1
            else:
                if str(self.sCron[1]) == str(self.sMinutes):
                    bMinInCron = 1
            if not bMinInCron:
                if self.sCron[1] == "*":
                    self.sCron[1] = str(self.sMinutes)
                else:
                    self.sCron[1] = str(self.sCron[1]) + "," + str(self.sMinutes)

            bHInCron = 0
            if "," in str(self.sCron[2]):
                for i in re.split(',', self.sCron[2]):
                    if str(i) == str(self.sHour):
                        bHInCron = 1
            else:
                if str(self.sCron[2]) == str(self.sHour):
                    bHInCron = 1
            if not bHInCron:
                if self.sCron[2] == "*":
                    self.sCron[2] = str(self.sHour)
                else:
                    self.sCron[2] = str(self.sCron[2]) + "," + str(self.sHour)

        self.entryCron_update()

    def toggle_each_hour(self, widget):
        if self.toggleEachHour.get_active():
            self.sHour = "*"
            self.sCron[2] = "*"
        else:
            self.setsHour()

        self.save_strings()

    def toggle_everyday(self, widget):
        if self.toggleEveryday.get_active():
            self.bCalendarSelected = 0

            self.sMonthsSelected = ""
            self.sDaysSelected = ""

            self.sCron[3] = "*"
            self.sCron[4] = "*"
            self.sCron[5] = "*"

            for i in range(1, 8):
                self.toggleDaySettings[i] = 0
            for i in range(1, 13):
                self.toggleMonthSettings[i] = 0

        self.save_strings()

    def calendar_selected(self, widget):
        self.bCalendarSelected = 1

        year, month, day = self.calendar.get_date()
        month = month + 1

        mytime = time.mktime((year, month, day, 0, 0, 0, 0, 0, -1))
        sDT = time.strftime("%x", time.localtime(mytime))
        self.sDate = "%s" % sDT
        # date = datetime.datetime.strptime(self.sDate, '%m/%d/%Y')

        self.sCron[3] = str(day)
        self.sCron[4] = str(month)

        self.sMonthsSelected = str(month)
        self.toggleEveryday.set_active(0)

        # self.entryCron_update()
        self.save_strings()

    def entryCron_update(self):

        if not "," in str(self.sCron[1]):
            self.sCron[1] = str(self.sMinutes)

        if self.toggleEachHour.get_active():
            self.sCron[2] = "*"
        else:
            if not "," in str(self.sCron[2]):
                self.sCron[2] = str(self.sHour)

        if self.sDaysSelected == "":
            if not self.bCalendarSelected:
                self.sCron[5] = "*"
        else:
            self.sCron[5] = self.sDaysSelected

        if self.sMonthsSelected == "":
            if not self.bCalendarSelected:
                self.sCron[4] = "*"
        else:
            self.sCron[4] = self.sMonthsSelected

        self.sCronEntry = ""
        for i in range(1, 6):
            self.sCronEntry = self.sCronEntry + self.sCron[i] + " "

        self.entryCron.set_text(self.sCronEntry)

    def entryCron_changed(self, widget):
        self.sCronEntry = self.entryCron.get_text()

        self.save_strings()

    def entryScript_changed(self, widget):
        self.sScript = self.entryScript.get_text()

        self.save_strings()

    def save_time(self, widget):
        if self.toggleEachHour.get_active():
            self.sHour = "*"
        else:
            self.setsHour()
        self.setsMinutes()

        self.save_strings()

    def sound_save(self):
        self.sSound = str(self.comboSound.get_active_text())

    def on_comboSound_changed(self, combo):
        text = combo.get_active_text()
        if text != None:
            self.sSound = text

        if self.bStartLoad:
            self.bStartLoad = 0
        else:
            if sys.platform == "win32":
                winsound.PlaySound(self.sSound, winsound.SND_ALIAS)
            else:
                sSoundFile = self.sSoundDir + self.sSound
                bashCommand = "/usr/bin/aplay -q " + sSoundFile
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

        self.save_strings()

    def wListAlarms_reload(self):
        if app.bwListAlarmsActive:
            # save the window coordinates
            self.save_window("windowListAlarms")

            self.windowListAlarms.destroy()
            self.windowListAlarms = None

            # restore the window coordinates
            self.windowListAlarms = ListAlarmsWindow()
            (x, y, w, h) = self.restore_window("windowListAlarms")
            self.windowListAlarms.move(x, y)
            self.windowListAlarms.resize(w, h)

            self.draw_gtk_listalarms(self.windowListAlarms)

            self.windowListAlarms.show_all()

    def save_alarm(self, widget):

        self.save_strings()

        buf = "%s" % (str(self.sSettings))
        # self.labelAlarmInfo.set_text(buf)

        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        # lets create the config file
        # cfgFile = open(self.sConfigFile, 'a')

        if self.sAlarmID == "":
            timestamp = time.time()
            self.sAlarmID = 'Alarm_' + str(timestamp)

        if not config.has_section(self.sAlarmID):
            config.add_section(self.sAlarmID)

        config.set(self.sAlarmID, 'Name', str(self.sName))
        config.set(self.sAlarmID, 'Cron', str(self.sCronEntry))
        config.set(self.sAlarmID, 'ScheduleMinutes', str(self.sCron[1]))
        config.set(self.sAlarmID, 'ScheduleHour', str(self.sCron[2]))
        config.set(self.sAlarmID, 'ScheduleDays', str(self.sCron[3]))
        config.set(self.sAlarmID, 'ScheduleMonths', str(self.sCron[4]))
        config.set(self.sAlarmID, 'ScheduleDOW', str(self.sCron[5]))
        config.set(self.sAlarmID, 'Sound', str(self.sSound))
        config.set(self.sAlarmID, 'Script', str(self.sScript))
        config.set(self.sAlarmID, 'Active', str(self.bAlarmActive))
        copyfile(self.sConfigFile, self.sConfigFile + ".bak")

        with open(self.sConfigFile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

        self.save_window("windowAddAlarm")
        self.windowAddAlarm.hide()
        app.bwAddAlarmActive = 0

        self.wListAlarms_reload()

    def clone_alarm(self, widget):

        # cfgFile = open(self.sConfigFile, 'a')
        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        model, treeiter = self.tree_selection.get_selected()
        if treeiter != None:
            # print("sAlarmID: " + model[treeiter][0])
            sAlarmID = model[treeiter][0]
        else:
            return 1

        sCron = 6 * [0]
        sName = config.get(sAlarmID, 'Name')
        sCronEntry = config.get(sAlarmID, 'Cron')
        sCron[1] = config.get(sAlarmID, 'ScheduleMinutes')
        sCron[2] = config.get(sAlarmID, 'ScheduleHour')
        sCron[3] = config.get(sAlarmID, 'ScheduleDays')
        sCron[4] = config.get(sAlarmID, 'ScheduleMonths')
        sCron[5] = config.get(sAlarmID, 'ScheduleDOW')
        sSound = config.get(sAlarmID, 'Sound')
        sScript = config.get(sAlarmID, 'Script')
        bAlarmActive = config.getboolean(sAlarmID, 'Active')

        timestamp = time.time()
        sNewAlarmID = 'Alarm_' + str(timestamp)

        config.add_section(sNewAlarmID)
        config.set(sNewAlarmID, 'Name', str(sName))
        config.set(sNewAlarmID, 'Cron', str(sCronEntry))
        config.set(sNewAlarmID, 'ScheduleMinutes', str(sCron[1]))
        config.set(sNewAlarmID, 'ScheduleHour', str(sCron[2]))
        config.set(sNewAlarmID, 'ScheduleDays', str(sCron[3]))
        config.set(sNewAlarmID, 'ScheduleMonths', str(sCron[4]))
        config.set(sNewAlarmID, 'ScheduleDOW', str(sCron[5]))
        config.set(sNewAlarmID, 'Sound', str(sSound))
        config.set(sNewAlarmID, 'Script', str(sScript))
        config.set(sNewAlarmID, 'Active', str(bAlarmActive))

        copyfile(self.sConfigFile, self.sConfigFile + ".bak")
        with open(self.sConfigFile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

        self.wListAlarms_reload()

    def save_window(self, sWName):
        # print(self.sConfigFile)
        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        # cfgFile = open(self.sConfigFile, 'w')

        sSection = "General"
        if not config.has_section(sSection):
            config.add_section(sSection)

        if (sWName == "windowListAlarms"):
            window = self.windowListAlarms
        if (sWName == "windowAddAlarm"):
            window = self.windowAddAlarm
        if (sWName == "windowSched"):
            window = self.windowSched
        if (sWName == "windowLastAlarms"):
            window = self.windowLastAlarms
        if (sWName == "windowAbout"):
            window = self.windowAbout

        # print(sWName)
        (x, y) = window.get_position()
        # print(str(x) + " | " + str(y))
        # exec("(x, y) = self.%s.get_position()" % (sWName))
        config.set(sSection, sWName + 'X', str(x))
        config.set(sSection, sWName + 'Y', str(y))

        (w, h) = window.get_size()
        # print(str(w) + " | " + str(h))
        # exec("(w, h) = self.%s.get_size()" % (sWName))
        config.set(sSection, sWName + 'W', str(w))
        config.set(sSection, sWName + 'H', str(h))

        with open(self.sConfigFile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    def restore_window(self, sWName):

        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        sSection = "General"
        if config.has_section(sSection):
            try:
                x = config.get(sSection, sWName + 'X')
            except:
                x = 200
            try:
                y = config.get(sSection, sWName + 'Y')
            except:
                y = 150
            try:
                w = config.get(sSection, sWName + 'W')
            except:
                w = 400
            try:
                h = config.get(sSection, sWName + 'H')
            except:
                h = 300
            return (int(x), int(y), int(w), int(h))
        return (200, 150, 400, 300)

    def toggle_day(self, toggle, nCB):
        i = nCB
        if self.toggleDay[i].get_active():
            self.toggleDaySettings[i] = 1
            self.bCalendarSelected = 0
            self.toggleEveryday.set_active(0)
        else:
            self.toggleDaySettings[i] = 0

        self.sDaysSelected = ""
        for j in range(1, 8):
            if self.toggleDaySettings[j]:
                if self.sDaysSelected == "":
                    self.sDaysSelected = str(j)
                else:
                    self.sDaysSelected = self.sDaysSelected + "," + str(j)
        # self.labelDayRInfo.set_text(self.sDaysSelected)

        self.entryCron_update()

    def toggle_month(self, toggle, nCB):
        i = nCB
        if self.toggleMonth[i].get_active():
            self.toggleMonthSettings[i] = 1
            self.bCalendarSelected = 0
        else:
            self.toggleMonthSettings[i] = 0

        self.sMonthsSelected = ""
        for j in range(1, 13):
            if self.toggleMonthSettings[j]:
                if self.sMonthsSelected == "":
                    self.sMonthsSelected = str(j)
                else:
                    self.sMonthsSelected = self.sMonthsSelected + "," + str(j)
        # self.labelMonthRInfo.set_text(self.sMonthsSelected)

        self.entryCron_update()

    def toggle_active(self, toggle):
        self.bAlarmActive = toggle.get_active()
        # print(self.bAlarmActive)

        self.save_strings()

    def on_cronInfo_clicked(self, widget):
        dialog = Gtk.MessageDialog(self.windowAddAlarm, 0, Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK, "Cron info")
        dialog.format_secondary_text(
            # "You can replace each star in the cron settings with the following values: \n
            "At the moment the cron settings are not availabe for edit \nmin | hour | day of month (1-31) | month (1-12) | day of week (0 - 7) \n*     | *      | *                             | *                    | *")
        dialog.run()
        dialog.destroy()

    def on_wAddAlarm_close_clicked(self, widget):
        self.save_window("windowAddAlarm")
        self.windowAddAlarm.hide()
        app.bwAddAlarmActive = 0

    def on_wListAlarms_clone_clicked(self, widget):
        self.clone_alarm(widget)

    def on_wListAlarms_del_clicked(self, widget):

        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        # cfgFile = open(self.sConfigFile, 'w')

        configSection = self.selectedAlarm

        if config.remove_section(configSection):
            print(bcolors.WARNING + "delete " + configSection + bcolors.ENDC)
            with open(self.sConfigFile, 'w') as configfile:
                try:
                    config.write(configfile)
                    configfile.close()
                except Exception as err:
                    print(bcolors.FAIL + err + bcolors.ENDC)

            self.save_window("windowListAlarms")

            self.windowListAlarms.destroy()
            self.windowListAlarms = None

            # restore the window coordinates
            self.windowListAlarms = ListAlarmsWindow()
            (x, y, w, h) = self.restore_window("windowListAlarms")
            self.windowListAlarms.move(x, y)
            self.windowListAlarms.resize(w, h)

            self.draw_gtk_listalarms(self.windowListAlarms)

            self.windowListAlarms.show_all()

    def on_wListAlarms_close_clicked(self, widget):
        self.save_window("windowListAlarms")
        self.windowListAlarms.hide()
        app.bwListAlarmsActive = 0

    def on_sched_clicked(self, widget):
        if not app.bwSchedActive:
            self.windowSched = SchedWindow()
            self.draw_gtk_sched(self.windowSched)
            (x, y, w, h) = self.restore_window("windowSched")
            self.windowSched.move(x, y)
            # self.windowSched.resize(w, h)
            self.windowSched.show_all()
            app.bwSchedActive = 1

    def on_sched_close_clicked(self, widget):
        self.save_window("windowSched")
        self.windowSched.hide()
        app.bwSchedActive = 0

    def on_select_days_clicked(self, widget):
        for i in range(1, 8):
            self.toggleDay[i].set_active(1)
            self.toggleDaySettings[i] = 1

    def on_unselect_days_clicked(self, widget):
        for i in range(1, 8):
            self.toggleDay[i].set_active(0)
            self.toggleDaySettings[i] = 0

    def on_select_months_clicked(self, widget):
        for i in range(1, 13):
            self.toggleMonth[i].set_active(1)
            self.toggleMonthSettings[i] = 1

    def on_unselect_months_clicked(self, widget):
        for i in range(1, 13):
            self.toggleMonth[i].set_active(0)
            self.toggleMonthSettings[i] = 0

    def center_window(self, window):
        (width, height) = window.get_size()

        # the screen contains all monitors
        screen = window.get_screen()

        # collect data about each monitor
        monitors = []
        nmons = screen.get_n_monitors()
        for m in range(nmons):
            mg = screen.get_monitor_geometry(m)
            monitors.append(mg)

        # current monitor
        curmon = screen.get_monitor_at_window(screen.get_active_window())

        width = int(monitors[curmon].width / 2) - int(width / 2)
        height = int(monitors[curmon].height / 2) - int(height / 2)
        window.move(width, height)

    def draw_gtk_sched(self, window):
        self.windowSched = window

        vboxS = Gtk.VBox(False, DEF_PAD)
        window.add(vboxS)

        # Days
        hboxRDL = Gtk.HBox(False, 1)
        vboxS.pack_start(hboxRDL, False, True, DEF_PAD)

        labelDayRepeat = Gtk.Label("Repeat in the following days:")
        hboxRDL.pack_start(labelDayRepeat, False, False, 0)

        self.labelDayRInfo = Gtk.Label("")
        hboxRDL.pack_start(self.labelDayRInfo, False, False, 0)

        hboxRD1 = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRD1, False, True, DEF_PAD)

        for i in range(1, 4):
            self.toggleDay[i] = Gtk.CheckButton(self.sDayName[i])
            self.toggleDay[i].connect("toggled", self.toggle_day, i)
            hboxRD1.pack_start(self.toggleDay[i], False, False, 0)
            self.toggleDay[i].set_active(self.toggleDaySettings[i])

        hboxRD2 = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRD2, False, True, DEF_PAD)

        for i in range(4, 8):
            self.toggleDay[i] = Gtk.CheckButton(self.sDayName[i])
            self.toggleDay[i].connect("toggled", self.toggle_day, i)
            hboxRD2.pack_start(self.toggleDay[i], False, False, 0)
            self.toggleDay[i].set_active(self.toggleDaySettings[i])

        hboxSD = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxSD, False, False, DEF_PAD)

        buttonSD = Gtk.Button("Select all days")
        buttonSD.connect("clicked", self.on_select_days_clicked)
        hboxSD.pack_start(buttonSD, False, False, DEF_PAD)

        buttonSD = Gtk.Button("Unselect all days")
        buttonSD.connect("clicked", self.on_unselect_days_clicked)
        hboxSD.pack_start(buttonSD, False, False, DEF_PAD)

        # Months
        hboxRML = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRML, False, False, DEF_PAD)

        labelMonthRepeat = Gtk.Label("Repeat in the following months:")
        hboxRML.pack_start(labelMonthRepeat, False, False, 0)

        self.labelMonthRInfo = Gtk.Label("")
        hboxRML.pack_start(self.labelMonthRInfo, False, False, 0)

        hboxRM1 = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM1, False, False, DEF_PAD)

        for i in range(1, 5):
            self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
            self.toggleMonth[i].connect("toggled", self.toggle_month, i)
            hboxRM1.pack_start(self.toggleMonth[i], False, False, 0)
            self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxRM2 = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM2, False, False, DEF_PAD)

        for i in range(5, 9):
            self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
            self.toggleMonth[i].connect("toggled", self.toggle_month, i)
            hboxRM2.pack_start(self.toggleMonth[i], False, False, 0)
            self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxRM3 = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM3, False, False, DEF_PAD)

        for i in range(9, 13):
            self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
            self.toggleMonth[i].connect("toggled", self.toggle_month, i)
            hboxRM3.pack_start(self.toggleMonth[i], False, False, 0)
            self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxSM = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxS.pack_start(hboxSM, False, False, DEF_PAD)

        buttonSM = Gtk.Button("Select all months")
        buttonSM.connect("clicked", self.on_select_months_clicked)
        hboxSM.pack_start(buttonSM, False, False, DEF_PAD)

        buttonSM = Gtk.Button("Unselect all months")
        buttonSM.connect("clicked", self.on_unselect_months_clicked)
        hboxSM.pack_start(buttonSM, False, False, DEF_PAD)

        bboxB = Gtk.HButtonBox()
        vboxS.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox(False, 1)
        bboxB.pack_start(hboxB, False, True, DEF_PAD)

        buttonClose = Gtk.Button("Close")
        buttonClose.connect("clicked", self.on_sched_close_clicked)
        hboxB.pack_start(buttonClose, False, False, DEF_PAD)

    def draw_gtk_addalarm(self, window):
        # print("draw_gtk_addalarm")

        self.windowAddAlarm = window

        vboxW = Gtk.VBox(False, DEF_PAD)
        self.windowAddAlarm.add(vboxW)

        hboxW = Gtk.HBox(False, 1)
        vboxW.pack_start(hboxW, False, True, 0)

        # The name of the alarm
        labelName = Gtk.Label("Alarm name:")
        hboxW.pack_start(labelName, False, True, 0)

        self.entryName = Gtk.Entry()
        self.entryName.set_text(self.sName)
        hboxW.pack_start(self.entryName, False, True, DEF_PAD)

        hboxC = Gtk.HBox(False, DEF_PAD)
        vboxW.pack_start(hboxC, False, True, DEF_PAD)

        # Calendar widget
        framePtd = Gtk.Frame()
        hboxC.pack_start(framePtd, False, True, DEF_PAD)

        vboxC = Gtk.VBox(True, DEF_PAD_SMALL)
        framePtd.add(vboxC)

        self.calendar = Gtk.Calendar()
        vboxC.add(self.calendar)
        self.calendar.connect("day_selected", self.calendar_selected)

        # The time spinners
        framePtt = Gtk.Frame()
        hboxC.pack_start(framePtt, False, True, DEF_PAD)

        vboxPtt = Gtk.VBox(True, DEF_PAD_SMALL)
        framePtt.add(vboxPtt)

        hboxPtt = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxPtt.pack_start(hboxPtt, False, True, DEF_PAD)

        vboxHour = Gtk.VBox(False, 0)
        hboxPtt.pack_start(vboxHour, True, True, 5)

        labelHour = Gtk.Label("Hour")
        labelHour.set_alignment(0, 0.5)
        vboxHour.pack_start(labelHour, False, True, 0)

        self.spinnerHour = Gtk.SpinButton()
        if self.bAddAlarmMode:
            self.sHour = int(time.strftime("%H"))
        else:
            if self.sHour == "*":
                self.sHour = int(time.strftime("%H"))
        if "," in str(self.sHour):
            for i in re.split(',', self.sHour):
                self.sHour = i
        adj = Gtk.Adjustment(int(self.sHour), 0, 24, 1, 5, 0)
        self.spinnerHour.set_adjustment(adj)
        self.spinnerHour.set_wrap(True)
        adj.connect("value_changed", self.save_time)
        vboxHour.pack_start(self.spinnerHour, False, True, 0)

        vboxMinutes = Gtk.VBox(False, 0)
        hboxPtt.pack_start(vboxMinutes, True, True, 5)

        labelMinutes = Gtk.Label("Minutes")
        labelMinutes.set_alignment(0, 0.5)
        vboxMinutes.pack_start(labelMinutes, False, True, 0)

        self.spinnerMinutes = Gtk.SpinButton()
        if self.bAddAlarmMode:
            self.sMinutes = int(time.strftime("%M"))

        if "," in str(self.sMinutes):
            for i in re.split(',', self.sMinutes):
                self.sMinutes = i
        adj = Gtk.Adjustment(int(self.sMinutes), 0, 59, 1, 5, 0)
        self.spinnerMinutes.set_adjustment(adj)
        self.spinnerMinutes.set_wrap(True)
        adj.connect("value_changed", self.save_time)
        vboxMinutes.pack_start(self.spinnerMinutes, False, True, 0)

        # Repeat settings
        bboxB = Gtk.HButtonBox()
        vboxPtt.pack_start(bboxB, False, False, 0)

        vboxB = Gtk.VBox(False, 1)
        bboxB.pack_start(vboxB, False, True, DEF_PAD)

        self.toggleAddHM = Gtk.CheckButton("Add hour/minutes")
        self.toggleAddHM.connect("toggled", self.toggle_addHM)
        vboxB.pack_start(self.toggleAddHM, True, True, 0)

        self.toggleEachHour = Gtk.CheckButton("Repeat each hour")
        self.toggleEachHour.connect("toggled", self.toggle_each_hour)
        vboxB.pack_start(self.toggleEachHour, True, True, 0)

        self.toggleEveryday = Gtk.CheckButton("Repeat everyday")
        self.toggleEveryday.connect("toggled", self.toggle_everyday)
        vboxB.pack_start(self.toggleEveryday, True, True, 0)

        # Repeat settings
        hboxB = Gtk.HBox(False, 1)
        bboxB.pack_start(hboxB, False, True, DEF_PAD)

        buttonRepeat = Gtk.Button("Other scheduled settings..")
        buttonRepeat.connect("clicked", self.on_sched_clicked)
        hboxB.pack_start(buttonRepeat, False, False, DEF_PAD)

        # cron like settings
        hboxCron = Gtk.HBox(True, DEF_PAD_SMALL)
        vboxW.add(hboxCron)

        labelCron = Gtk.Label("Cron like settings: ")
        hboxCron.pack_start(labelCron, False, True, 0)

        self.entryCron = Gtk.Entry()
        self.entryCron.set_max_length(50)
        self.entryCron.set_text(self.sCronEntry)
        self.entryCron.set_editable(0)
        self.entryCron.connect("changed", self.entryCron_changed)
        Gtk.Widget.set_tooltip_text(self.entryCron, "At the moment the cron settings are not available for edit")
        hboxCron.pack_start(self.entryCron, False, True, DEF_PAD)

        buttonInfo = Gtk.Button("Cron short info")
        buttonInfo.connect("clicked", self.on_cronInfo_clicked)
        hboxCron.add(buttonInfo)

        # The activation option
        framePd = Gtk.Frame()
        vboxW.pack_start(framePd, True, True, DEF_PAD)

        vboxPd = Gtk.VBox(True, DEF_PAD_SMALL)
        framePd.add(vboxPd)

        # hboxPd = Gtk.HBox (False, 3)
        # vboxPd.pack_start(hboxPd, False, True, 0)

        # labelAlarm = Gtk.Label("Alarm:")
        # hboxPd.pack_start(labelAlarm, False, True, 0)

        # self.labelAlarmInfo = Gtk.Label("")
        # hboxPd.pack_start(self.labelAlarmInfo, False, True, 0)

        # Sound played by the alarm
        hboxS = Gtk.HBox(False, 3)
        vboxPd.pack_start(hboxS, False, True, 0)

        self.labelSound = Gtk.Label("Alarm Sound: ")
        hboxS.pack_start(self.labelSound, False, True, 0)

        self.comboSound = Gtk.ComboBoxText()
        self.comboSound.set_entry_text_column(0)
        self.comboSound.connect("changed", self.on_comboSound_changed)
        self.sSoundList = 100 * [0]
        self.sSoundListCount = 0
        for file in sorted(glob.glob(self.sSoundDir + "*.wav")):
            file = re.sub(self.sSoundDir, '', file)
            self.comboSound.append_text(file)
            self.sSoundListCount += 1
            self.sSoundList[self.sSoundListCount] = file
        hboxS.pack_start(self.comboSound, False, False, 0)

        self.labelEmpty = Gtk.Label("")
        hboxS.pack_start(self.labelEmpty, False, True, 50)
        self.labelScript = Gtk.Label("Script to run: ")
        hboxS.pack_start(self.labelScript, False, True, 0)
        self.entryScript = Gtk.Entry()
        self.entryScript.set_max_length(100)
        self.entryScript.set_text(self.sScript)
        self.entryScript.set_editable(1)
        self.entryScript.connect("changed", self.entryScript_changed)
        Gtk.Widget.set_tooltip_text(self.entryScript, "Input the script to run together with the alarm")
        hboxS.pack_start(self.entryScript, False, True, DEF_PAD)

        # Activate the alarm
        self.toggleActive = Gtk.CheckButton("Activate the alarm")
        self.toggleActive.connect("toggled", self.toggle_active)
        Gtk.Widget.set_tooltip_text(self.toggleActive, "Enable/Disable the alarm")
        vboxPd.pack_start(self.toggleActive, True, True, 0)

        bboxS = Gtk.HButtonBox()
        vboxW.pack_start(bboxS, False, False, 0)

        # Save the settings
        buttonSave = Gtk.Button("Save the alarm")
        buttonSave.connect("clicked", self.save_alarm)
        bboxS.add(buttonSave)

        buttonCancel = Gtk.Button("Cancel")
        buttonCancel.connect("clicked", self.on_wAddAlarm_close_clicked)
        bboxS.add(buttonCancel)

        if self.bAddAlarmMode:
            self.sName = self.entryName.get_text()

            self.toggleEachHour.set_active(0)
            self.toggleEveryday.set_active(1)

            self.comboSound.set_active(3)

            self.toggleActive.set_active(1)
            self.bAlarmActive = True

            self.save_strings()

    def toggle_renderer(self, cell, path, column):
        self.alarm_liststore[path][column] = not self.alarm_liststore[path][column]

        # cfgFile = open(self.sConfigFile, 'a')
        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        configSection = self.alarm_liststore[path][0]
        bAlarmActive = self.alarm_liststore[path][column]
        config.set(configSection, 'Active', str(bAlarmActive))
        with open(self.sConfigFile, 'w') as configfile:
            config.write(configfile)
            configfile.close()

    def draw_gtk_listalarms(self, window):
        # print("draw_gtk_listalarms")

        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        self.alarm_liststore = Gtk.ListStore(str, str, str, str, str, str, bool)
        self.current_filter = None

        sCron = 6 * [0]
        sList = list()
        i = 0
        for configSection in config.sections():
            sAlarmID = configSection
            if bool(re.search('Alarm', sAlarmID)):
                i += 1
                sName = config.get(sAlarmID, 'Name')
                sCronEntry = config.get(sAlarmID, 'Cron')
                sCron[1] = config.get(sAlarmID, 'ScheduleMinutes')
                sCron[2] = config.get(sAlarmID, 'ScheduleHour')
                sCron[3] = config.get(sAlarmID, 'ScheduleDays')
                sCron[4] = config.get(sAlarmID, 'ScheduleMonths')
                sCron[5] = config.get(sAlarmID, 'ScheduleDOW')
                sSound = config.get(sAlarmID, 'Sound')
                sScript = config.get(sAlarmID, 'Script')
                bAlarmActive = config.getboolean(sAlarmID, 'Active')

                sList = [(sAlarmID, sName, sCron[2] + ":" + sCron[1], sCron[3], sCron[4], sCron[5], bAlarmActive)]

                for alarm_ref in sList:
                    self.alarm_liststore.append(list(alarm_ref))

        self.alarm_liststore.set_sort_column_id(1, 0)

        if i < 10:
            i = 350
        else:
            i = 500

        window.set_default_size(570, i)

        vboxW = Gtk.VBox(False, DEF_PAD)
        window.add(vboxW)

        hboxW = Gtk.HBox(False, 1)
        vboxW.pack_start(hboxW, False, True, 0)

        labelName = Gtk.Label("Alarm list:")
        hboxW.pack_start(labelName, False, True, 0)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        vboxW.pack_start(grid, False, True, DEF_PAD)

        self.filter = self.alarm_liststore.filter_new()
        self.treeview = Gtk.TreeView.new_with_model(self.alarm_liststore);
        self.treeview.set_headers_clickable(True)

        for i, column_title in enumerate(["Id", "Name", "Time", "Days ", "Months", "Day of week", "Active"]):
            if column_title == "Active":
                renderer = Gtk.CellRendererToggle()
                renderer.connect('toggled', self.toggle_renderer, 6)
                column = Gtk.TreeViewColumn(column_title, renderer, active=i)
            else:
                renderer = Gtk.CellRendererText()
                column = Gtk.TreeViewColumn(column_title, renderer, text=i)

            column.set_clickable(True)
            column.set_sort_indicator(True)
            column.set_sort_column_id(i)

            self.treeview.append_column(column)

            if column_title == "Id":
                column.set_visible(False)

        self.tree_selection = self.treeview.get_selection()
        self.tree_selection.connect("changed", self.on_treeview_selection_changed)

        self.treeview.connect('row-activated', self.on_treeview_row_activated)
        self.treeview.connect('button-press-event', self.on_treeview_button_press_event)

        self.popup = Gtk.Menu()
        menu_item_edit = Gtk.MenuItem("Edit")
        menu_item_edit.show()
        menu_item_edit.connect('activate', self.on_treeview_menu_edit)
        self.popup.append(menu_item_edit)
        menu_item_clone = Gtk.MenuItem("Clone")
        menu_item_clone.show()
        menu_item_clone.connect('activate', self.on_treeview_menu_clone)
        self.popup.append(menu_item_clone)
        menu_item_delete = Gtk.MenuItem("Delete")
        menu_item_delete.show()
        menu_item_delete.connect('activate', self.on_treeview_menu_delete)
        self.popup.append(menu_item_delete)

        # setting up the layout, putting the treeview in a scrollwindow
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        scrollable_treelist.add(self.treeview)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
        vboxW.pack_start(scrollable_treelist, False, False, DEF_PAD)

        bboxB = Gtk.HButtonBox()
        vboxW.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox(False, 1)
        bboxB.pack_start(hboxB, False, True, DEF_PAD)

        buttonAddAlarm = Gtk.Button("Add new alarm")
        buttonAddAlarm.connect("clicked", self.on_wListAlarms_addnew_clicked)
        # buttonAddAlarm.grab_default()
        hboxB.pack_start(buttonAddAlarm, False, False, DEF_PAD)

        buttonCloneAlarm = Gtk.Button("Clone selected alarm")
        buttonCloneAlarm.connect("clicked", self.on_wListAlarms_clone_clicked)
        hboxB.pack_start(buttonCloneAlarm, False, False, DEF_PAD)

        buttonDelAlarm = Gtk.Button("Delete selected alarm")
        buttonDelAlarm.connect("clicked", self.on_wListAlarms_del_clicked)
        hboxB.pack_start(buttonDelAlarm, False, False, DEF_PAD)

        buttonClose = Gtk.Button("Close")
        # buttonClose.connect("clicked", lambda w: Gtk.main_quit())
        buttonClose.connect("clicked", self.on_wListAlarms_close_clicked)
        hboxB.pack_start(buttonClose, False, False, DEF_PAD)

    def on_treeview_selection_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            self.selectedAlarm = str(model[treeiter][0])
            # print("You selected ", self.selectedAlarm)

    def on_wListAlarms_addnew_clicked(self, widget):

        if not app.bwAddAlarmActive:
            self.bAddAlarmMode = 1
            self.bStartLoad = 1

            self.init_settings()

            # create the window and the widgets
            self.windowAddAlarm = AlarmWindow()
            self.draw_gtk_addalarm(self.windowAddAlarm)
            (x, y, w, h) = self.restore_window("windowAddAlarm")
            self.windowAddAlarm.move(x, y)
            # self.windowAddAlarm.resize(w, h)
            app.bwAddAlarmActive = 1

            self.windowAddAlarm.show_all()

    def on_treeview_menu_edit(self, widget):
        model, treeiter = self.tree_selection.get_selected()
        if treeiter != None:
            self.editAlarm(model[treeiter][0])
        return 0

    def on_treeview_menu_clone(self, widget):
        self.on_wListAlarms_clone_clicked(self)
        return 0

    def on_treeview_menu_delete(self, widget):
        self.on_wListAlarms_del_clicked(self)
        return 0

    def editAlarm(self, configSection):
        # print("editAlarm")

        # we are in edit mode
        self.bAddAlarmMode = 0

        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        self.sAlarmID = configSection
        self.sName = config.get(configSection, 'Name')

        self.sCronEntry = config.get(configSection, 'Cron')
        self.sCron[1] = config.get(configSection, 'ScheduleMinutes')
        self.sCron[2] = config.get(configSection, 'ScheduleHour')
        self.sCron[3] = config.get(configSection, 'ScheduleDays')
        self.sCron[4] = config.get(configSection, 'ScheduleMonths')
        self.sCron[5] = config.get(configSection, 'ScheduleDOW')

        self.sMinutes = self.sCron[1]
        self.sHour = self.sCron[2]

        self.sScript = config.get(configSection, 'Script')
        self.sSound = config.get(configSection, 'Sound')
        self.bAlarmActive = config.getboolean(configSection, 'Active')

        # create the window and the widgets
        self.windowAddAlarm = AlarmWindow()
        self.draw_gtk_addalarm(self.windowAddAlarm)
        (x, y, w, h) = self.restore_window("windowAddAlarm")
        self.windowAddAlarm.move(x, y)
        # self.windowAddAlarm.resize(w, h)

        self.load_settings()

        # show the widgets
        self.windowAddAlarm.show_all()

    def on_treeview_row_activated(self, treeview, path, column):
        model = treeview.get_model()
        self.editAlarm(model[path][0])
        return 0

    def on_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)
                self.popup.popup(None, None, None, None, event.button, event.time)
        else:
            return False
        return True

    def isTimeToRun_alarm(self, sAlarmID, sName, sSound, sScript, sCron):
        date = datetime.datetime.today()
        nCDay = int(date.day)
        nCMonth = int(date.month)
        nCYear = int(date.year)
        nCDOW = int(date.weekday()) + 1

        nCHour = int(time.strftime("%H"))
        nCMinutes = int(time.strftime("%M"))

        bCDOW = 0
        if not sCron[5] == "*":
            if "," in str(sCron[5]):
                for i in re.split(',', str(sCron[5])):
                    if nCDOW == int(i):
                        bCDOW = 1
            if "-" in str(sCron[5]):
                parts = re.split('-', str(sCron[5]))
                for i in range(int(parts[0]), int(parts[1]) + 1):
                    if nCDOW == int(i):
                        bCDOW = 1
            if "/" in str(sCron[5]):
                parts = re.split('/', str(sCron[5]))
                if nCDOW % int(parts[1]) == 0:
                    bCDOW = 1
            if bCDOW == 0 and str.isdigit(sCron[5]):
                if nCDOW == int(sCron[5]):
                    bCDOW = 1
        else:
            bCDOW = 1

        if not bCDOW:
            return 0

        bCMonth = 0
        if not sCron[4] == "*":
            if "," in str(sCron[4]):
                for i in re.split(',', str(sCron[4])):
                    if nCMonth == int(i):
                        bCMonth = 1
            if "-" in str(sCron[4]):
                parts = re.split('-', str(sCron[4]))
                for i in range(int(parts[0]), int(parts[1]) + 1):
                    if nCMonth == int(i):
                        bCMonth = 1
            if "/" in str(sCron[4]):
                parts = re.split('/', str(sCron[4]))
                if nCMonth % int(parts[1]) == 0:
                    bCMonth = 1
            if bCMonth == 0 and str.isdigit(sCron[4]):
                if nCMonth == int(sCron[4]):
                    bCMonth = 1
        else:
            bCMonth = 1

        if not bCMonth:
            return 0

        bCDay = 0
        if not sCron[3] == "*":
            if "," in str(sCron[3]):
                for i in re.split(',', str(sCron[3])):
                    if nCDay == int(i):
                        bCDay = 1
            if "-" in str(sCron[3]):
                parts = re.split('-', str(sCron[3]))
                for i in range(int(parts[0]), int(parts[1]) + 1):
                    if nCDay == int(i):
                        bCDay = 1
            if "/" in str(sCron[3]):
                parts = re.split('/', str(sCron[3]))
                if nCDay % int(parts[1]) == 0:
                    bCDay = 1
            if bCDay == 0 and str.isdigit(sCron[3]):
                if nCDay == int(sCron[3]):
                    bCDay = 1
        else:
            bCDay = 1

        if not bCDay:
            return 0

        bCHour = 0
        if not sCron[2] == "*":
            if "," in str(sCron[2]):
                for i in re.split(',', str(sCron[2])):
                    if nCHour == int(i):
                        bCHour = 1
            if "-" in str(sCron[2]):
                parts = re.split('-', str(sCron[2]))
                for i in range(int(parts[0]), int(parts[1]) + 1):
                    if nCHour == int(i):
                        bCHour = 1
            if "/" in str(sCron[2]):
                parts = re.split('/', str(sCron[2]))
                if nCHour % int(parts[1]) == 0:
                    bCHour = 1
            if bCHour == 0 and str.isdigit(sCron[2]):
                if nCHour == int(sCron[2]):
                    bCHour = 1
        else:
            bCHour = 1

        if not bCHour:
            return 0

        bCMinutes = 0
        if not sCron[1] == "*":
            if "," in str(sCron[1]):
                for i in re.split(',', str(sCron[1])):
                    if nCMinutes == int(i):
                        bCMinutes = 1
            if "-" in str(sCron[1]):
                parts = re.split('-', str(sCron[1]))
                for i in range(int(parts[0]), int(parts[1]) + 1):
                    if nCMinutes == int(i):
                        bCMinutes = 1
            if "/" in str(sCron[1]):
                parts = re.split('/', str(sCron[1]))
                if nCMinutes % int(parts[1]) == 0:
                    bCMinutes = 1
            if bCMinutes == 0 and str.isdigit(sCron[1]):
                if nCMinutes == int(sCron[1]):
                    bCMinutes = 1
        else:
            bCMinutes = 1

        if not bCMinutes:
            return 0

        if not app.bAlarmOn:
            if int(nCHour) < 10:
                nCHour = "0" + str(nCHour)
            if int(nCMinutes) < 10:
                nCMinutes = "0" + str(nCMinutes)
            if int(nCDay) < 10:
                nCDay = "0" + str(nCDay)
            if int(nCMonth) < 10:
                nCMonth = "0" + str(nCMonth)
            sTime = str(nCYear) + "." + str(nCMonth) + "." + str(nCDay) + " " + str(nCHour) + ":" + str(nCMinutes)
            sList = [(sName, sTime)]

            bSkip = 0
            for sTmpList in app.sLastAddedList:
                for sTmpName, sTmpTime in sTmpList:
                    if sName == sTmpName and sTime == sTmpTime:
                        bSkip = 1
            if bSkip == 0:
                for alarm_ref in sList:
                    app.lastalarms_liststore.append(list(alarm_ref))
                    app.sLastAddedList.append(sList)

        app.sAlarmStarted = sAlarmID
        app.play_alarm(sName, sSound, sScript)

    def check_alarm(self):
        config = configparser.ConfigParser()
        config.read(self.sConfigFile)

        sCron = 6 * [0]
        for configSection in config.sections():
            sAlarmID = configSection
            if bool(re.search('Alarm', sAlarmID)):
                sName = config.get(sAlarmID, 'Name')
                sCronEntry = config.get(sAlarmID, 'Cron')
                sCron[1] = config.get(sAlarmID, 'ScheduleMinutes')
                sCron[2] = config.get(sAlarmID, 'ScheduleHour')
                sCron[3] = config.get(sAlarmID, 'ScheduleDays')
                sCron[4] = config.get(sAlarmID, 'ScheduleMonths')
                sCron[5] = config.get(sAlarmID, 'ScheduleDOW')
                sSound = config.get(sAlarmID, 'Sound')
                sScript = config.get(sAlarmID, 'Script')
                bAlarmActive = config.getboolean(sAlarmID, 'Active')
                if bAlarmActive:
                    self.isTimeToRun_alarm(sAlarmID, sName, sSound, sScript, sCron)

    def draw_gtk_lastalarms(self, window):

        window.set_default_size(570, 500)

        vboxW = Gtk.VBox(False, DEF_PAD)
        window.add(vboxW)

        labelLast = Gtk.Label()
        labelLast.set_markup("Last started alarms:")
        vboxW.pack_start(labelLast, False, True, 0)

        self.current_filter = None
        app.lastalarms_liststore.set_sort_column_id(1, 0)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        vboxW.pack_start(grid, False, True, DEF_PAD)

        self.filter = app.lastalarms_liststore.filter_new();
        self.treeview = Gtk.TreeView.new_with_model(app.lastalarms_liststore);
        self.treeview.set_headers_clickable(True)

        for i, column_title in enumerate(["Name", "Time"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)

            column.set_clickable(True)
            column.set_sort_indicator(True)
            column.set_sort_column_id(i)

            self.treeview.append_column(column)

        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
        scrollable_treelist.add(self.treeview)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
        vboxW.pack_start(scrollable_treelist, False, False, DEF_PAD)

        bboxB = Gtk.HButtonBox()
        vboxW.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox(False, 1)
        bboxB.pack_start(hboxB, False, True, DEF_PAD)

        buttonClose = Gtk.Button("Close")
        buttonClose.connect("clicked", self.on_wLastAlarms_close_clicked)
        hboxB.pack_start(buttonClose, False, False, DEF_PAD)

        buttonClear = Gtk.Button("Clear list")
        buttonClear.connect("clicked", self.on_wLastAlarms_clear_clicked)
        hboxB.pack_start(buttonClear, False, False, DEF_PAD)

    def draw_gtk_about(self, window):

        vboxW = Gtk.VBox(False, DEF_PAD)
        window.add(vboxW)

        image = Gtk.Image()
        image.set_from_file(sIcon)
        image.show()
        vboxW.pack_start(image, False, True, 0)

        labelApp = Gtk.Label()
        labelApp.set_markup("<big>" + sPytAlarmVersion + "</big>")
        vboxW.pack_start(labelApp, False, True, 0)

        hboxW1 = Gtk.HBox(False, 1)
        vboxW.pack_start(hboxW1, False, True, 0)

        labelGH = Gtk.Label()
        labelGH.set_markup("For a new version go to: <a href=\"" + sPytAlarmURL + "\" "
                                                                                      "title=\"Click to open the page\">" + sPytAlarmURL + "</a>.")
        labelGH.set_line_wrap(True)
        vboxW.pack_start(labelGH, False, True, 0)

        hboxW2 = Gtk.HBox(False, 1)
        vboxW.pack_start(hboxW2, False, True, 0)

        labelName = Gtk.Label("Credit list:")
        hboxW2.pack_start(labelName, False, True, 0)

        tvCredit = Gtk.TextView()
        wTBCredit = Gtk.TextBuffer()
        wTBCredit.set_text("Contact email: " + str(sCreditText))
        tvCredit.set_buffer(wTBCredit)
        tvCredit.set_editable(0)
        vboxW.pack_start(tvCredit, False, True, DEF_PAD)

        hboxW2 = Gtk.HBox(False, 1)
        vboxW.pack_start(hboxW2, False, True, 0)

        labelLicense = Gtk.Label("License:")
        hboxW2.pack_start(labelLicense, False, True, 0)

        sLicenseText = "PytAlarm is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License \nas published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. \n \nPytAlarm is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty \nof MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details."

        tvLicense = Gtk.TextView()
        wTBLicense = Gtk.TextBuffer()
        wTBLicense.set_text(sLicenseText)
        tvLicense.set_buffer(wTBLicense)
        tvLicense.set_editable(0)
        vboxW.pack_start(tvLicense, False, True, DEF_PAD)

        bboxB = Gtk.HButtonBox()
        vboxW.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox(False, 1)
        bboxB.pack_start(hboxB, False, True, DEF_PAD)

        buttonClose = Gtk.Button("Close")
        buttonClose.connect("clicked", self.on_wAbout_close_clicked)
        hboxB.pack_start(buttonClose, False, False, DEF_PAD)

    def on_wAbout_close_clicked(self, widget):
        self.save_window("windowAbout")
        self.windowAbout.hide()
        app.bwAboutActive = 0

    def on_wLastAlarms_close_clicked(self, widget):
        self.save_window("windowLastAlarms")
        self.windowLastAlarms.hide()
        app.bwLastAlarmsActive = 0

    def on_wLastAlarms_clear_clicked(self, widget):
        app.lastalarms_liststore.clear()

    def addAlarm_activate(self):
        self.windowAddAlarm = AlarmWindow()
        self.draw_gtk_addalarm(self.windowAddAlarm)
        (x, y, w, h) = self.restore_window("windowAddAlarm")
        self.windowAddAlarm.move(x, y)
        self.windowAddAlarm.resize(w, h)
        self.windowAddAlarm.show_all()

    def listAlarms_activate(self):
        self.windowListAlarms = ListAlarmsWindow()
        self.draw_gtk_listalarms(self.windowListAlarms)
        (x, y, w, h) = self.restore_window("windowListAlarms")
        self.windowListAlarms.move(x, y)
        self.windowListAlarms.resize(w, h)

        self.windowListAlarms.show_all()

    def lastAlarms_activate(self):
        self.windowLastAlarms = LastAlarmsWindow()
        self.draw_gtk_lastalarms(self.windowLastAlarms)
        (x, y, w, h) = self.restore_window("windowLastAlarms")
        self.windowLastAlarms.move(x, y)
        self.windowLastAlarms.resize(w, h)

        self.windowLastAlarms.show_all()

    def about_activate(self):

        self.windowAbout = AboutWindow()
        self.draw_gtk_about(self.windowAbout)
        (x, y, w, h) = self.restore_window("windowAbout")
        self.windowAbout.move(x, y)
        # self.windowAbout.resize(w, h)

        self.windowAbout.show_all()

    def do_activate(self):
        # print("do_activate")

        self.listAlarms_activate()

    def do_startup(self):
        # print("do_startup")

        Gtk.Application.do_startup(self)

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

class Application(Gtk.Application):

    def __init__(self):
        super(Application, self).__init__()

        # print("init App")

        self.bwAddAlarmActive = 0
        self.bwListAlarmsActive = 0
        self.bwLastAlarmsActive = 0
        self.bwSchedActive = 0
        self.bwAboutActive = 0

        self.bAlarmOn = 0
        self.nAlarmTs = 0
        self.sAlarmStopped = ""
        self.sAlarmStarted = ""

        self.lastalarms_liststore = Gtk.ListStore(str, str)
        self.sLastAddedList = []

        sRootDir = ""
        if sys.platform == "win32":
            sPidFileDir = os.getenv("TMP")
            self.pidfile = sPidFileDir + "\pytalarm.pid"

            sRootDir = os.path.dirname(sys.argv[0])
            if sRootDir == "":
                sRootDir = "./"
            sRDir = os.path.abspath(sRootDir + "/../../")

            sIcon = sRootDir + sIcon
            sActiveIcon = sRootDir + sActiveIcon

        self.alarm = None

    def start_indicator(self):
        self.status_icon = Gtk.StatusIcon()
        self.status_icon.set_from_file(sIcon)
        # self.status_icon.set_from_stock(Gtk.STOCK_YES)
        self.status_icon.connect("popup-menu", self.status_right_click_event)

    def start_linux_indicator(self):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, sIcon,
                                                    appindicator.IndicatorCategory.APPLICATION_STATUS)
        # self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, "semi-starred-symbolic", appindicator.IndicatorCategory.APPLICATION_STATUS)

        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_indicator_menu())

    def status_right_click_event(self, icon, button, time):
        self.build_indicator_menu()
        self.indicator_menu.popup(None, None, None, self.status_icon, button, time)

    def build_indicator_menu(self):
        self.indicator_menu = Gtk.Menu()

        item_stop = Gtk.MenuItem('Stop the alarm')
        item_stop.connect('activate', self.stop_alarm)
        Gtk.Widget.set_tooltip_text(item_stop, "Stop the alarm sound, if it is running")
        self.indicator_menu.append(item_stop)

        separator = Gtk.SeparatorMenuItem()
        self.indicator_menu.append(separator)

        item_show = Gtk.MenuItem('List alarms')
        item_show.connect('activate', self.list_alarms)
        Gtk.Widget.set_tooltip_text(item_show, "Manage your alarms")
        self.indicator_menu.append(item_show)

        separator = Gtk.SeparatorMenuItem()
        self.indicator_menu.append(separator)

        item_add = Gtk.MenuItem('Add alarm')
        item_add.connect('activate', self.add_alarm)
        self.indicator_menu.append(item_add)

        separator = Gtk.SeparatorMenuItem()
        self.indicator_menu.append(separator)

        item_last = Gtk.MenuItem('Last alarms')
        item_last.connect('activate', self.last_alarms)
        self.indicator_menu.append(item_last)

        separator = Gtk.SeparatorMenuItem()
        self.indicator_menu.append(separator)

        item_about = Gtk.MenuItem('About')
        item_about.connect('activate', self.about)
        self.indicator_menu.append(item_about)

        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.app_quit)
        Gtk.Widget.set_tooltip_text(item_quit, "Quit the application")
        self.indicator_menu.append(item_quit)

        self.indicator_menu.show_all()

        return self.indicator_menu

    def stop_alarm(self, widget):
        # print("Stop alarm")

        if sys.platform == "win32":
            sPidFileDir = os.getenv("TMP")
            self.alarmPidFile = sPidFileDir + "/alarmsound.pid"
            if os.path.isfile(self.alarmPidFile):
                f = open(self.alarmPidFile, "r")
                for line in f:
                    sPid = line.strip().lower()
                f.close()
                process = subprocess.Popen("taskkill /F /PID " + str(sPid))
                os.remove(self.alarmPidFile)
        else:
            bashCommand = "pkill -f /dev/shm/alarmsound.sh"
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

        app.bAlarmOn = 0
        if sys.platform == "win32":
            self.status_icon.set_from_file(self.sIcon)
        else:
            app.indicator.set_icon(sIcon)

        nAlarmTs2 = time.time()
        if (nAlarmTs2 - app.nAlarmTs < 61):
            app.sAlarmStopped = app.sAlarmStarted
        else:
            app.sAlarmStopped = ""

    def play_alarm(self, sName, sSoundFile, sScript):
        # print("Play alarm")

        if app.bAlarmOn:
            nAlarmTs2 = time.time()
            if (nAlarmTs2 - app.nAlarmTs > 61):
                app.bAlarmOn = 0
                if sys.platform == "win32":
                    self.status_icon.set_from_file(self.sIcon)
                else:
                    app.indicator.set_icon(sIcon)
            return 0
        else:
            nAlarmTs2 = time.time()
            if (nAlarmTs2 - app.nAlarmTs < 61):
                return 0

            app.bAlarmOn = 1
            app.nAlarmTs = time.time()

            if sys.platform == "win32":
                self.status_icon.set_from_file(sActiveIcon)
            else:
                app.indicator.set_icon(sActiveIcon)

        if sys.platform != "win32":
            notify.Notification.new("Alarm: " + time.strftime("%H:%M") + " ", sName, sIcon).show()
            sSoundFile = app.alarm.sSoundDir + sSoundFile

        if os.path.exists(sSoundFile):

            if sys.platform == "win32":
                sTmpDir = os.getenv("TMP")
                sAlarmScript = sTmpDir + "/alarmsound.py"
                if os.path.exists(sAlarmScript):
                    os.remove(sAlarmScript)

                sCommand = "import winsound; import os; \nsPid = str(os.getpid()); sPidFileDir = os.getenv(\"TMP\"); alarmPidFile = sPidFileDir + \"/alarmsound.pid\"; f = file(alarmPidFile, 'w'); f.write(sPid); f.close(); sSoundFile = \"" + sSoundFile + "\"; \nfor i in range(1,60): winsound.PlaySound(sSoundFile, winsound.SND_ALIAS)"
                scriptFile = open(sAlarmScript, "w")
                scriptFile.write(sCommand)
                scriptFile.close()

                process = subprocess.Popen("python " + str(sAlarmScript))
            else:
                sAlarmScript = "/dev/shm/alarmsound.sh"
                bashCommand = "s=0; while [ $s -lt 60 ]; do /usr/bin/aplay -q " + sSoundFile + "; sleep 0.5; s=$((s+1)); done"

                scriptFile = open(sAlarmScript, "w")
                scriptFile.write(bashCommand)
                scriptFile.close()

                bashCommand = "/bin/chmod u+x " + sAlarmScript
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

                bashCommand = "/bin/bash " + sAlarmScript
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

                if sScript != "":
                    bashCommand = "/bin/bash " + sScript
                    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

    def build_menu(self, window):
        appGrid = Gtk.Grid()
        appMenubar = Gtk.MenuBar()

        # Stop alarm menu
        winStopAlarmMenu = Gtk.Menu()
        winStopAlarm1mi = Gtk.MenuItem.new_with_label("Stop alarm")

        winStopAlarm2mi = Gtk.MenuItem.new_with_label("Stop alarm")
        winStopAlarm2mi.connect("activate", self.stop_alarm)
        winStopAlarmMenu.append(winStopAlarm2mi)

        winStopAlarm1mi.set_submenu(winStopAlarmMenu)
        appMenubar.add(winStopAlarm1mi)

        # File menu
        winFileMenu = Gtk.Menu()
        winFile1mi = Gtk.MenuItem.new_with_label("File")

        # winAlarmsMenu = Gtk.Menu()
        # winAlarmsmi = Gtk.MenuItem.new_with_label("Alarms")
        # winAlarmsMenu.append(winAlarmsmi)
        # winFile1mi.set_submenu(winAlarmsMenu)

        winListAlarmsmi = Gtk.MenuItem.new_with_label("List alarms")
        winListAlarmsmi.connect("activate", self.list_alarms)
        winFileMenu.append(winListAlarmsmi)

        winAddAlarmmi = Gtk.MenuItem.new_with_label("Add alarm")
        winAddAlarmmi.connect("activate", self.last_alarms)
        winFileMenu.append(winAddAlarmmi)

        winLastAlarmsmi = Gtk.MenuItem.new_with_label("Last alarms")
        winLastAlarmsmi.connect("activate", self.last_alarms)
        winFileMenu.append(winLastAlarmsmi)

        separator = Gtk.SeparatorMenuItem()
        winFileMenu.append(separator)

        winExitmi = Gtk.MenuItem.new_with_label("Exit")
        winExitmi.connect("activate", self.app_quit)
        winFileMenu.append(winExitmi)

        winFile1mi.set_submenu(winFileMenu)
        appMenubar.add(winFile1mi)

        # Help menu
        winHelpMenu = Gtk.Menu()
        winHelp1mi = Gtk.MenuItem.new_with_label("Help")

        winAboutmi = Gtk.MenuItem.new_with_label("About")
        winAboutmi.connect("activate", self.about)
        winHelpMenu.append(winAboutmi)

        winHelp1mi.set_submenu(winHelpMenu)
        appMenubar.add(winHelp1mi)

        appGrid.attach(appMenubar, 0, 0, 1, 1)

        image = Gtk.Image()
        image.set_from_file(sIcon)
        image.show()
        appGrid.attach(image, 0, 1, 1, 1)


        vboxLabel = Gtk.VBox(False, DEF_PAD)
        labelTray = Gtk.Label()
        labelTray.set_markup("\n\rContact email: <a href='" + str(sCreditText) + "'>" + str(sCreditText) + "</a>\n\rURL: <a href='" + str(sPytAlarmURL) + "'>" + str(sPytAlarmURL) + "</a>\n\rCheck the icon tray for the Pytalarm clock icon!")
        vboxLabel.pack_start(labelTray, False, True, 0)
        appGrid.attach(vboxLabel, 0, 2, 1, 1)

        window.add(appGrid)

        return self

    def list_alarms(self, widget):
        if not app.bwListAlarmsActive:
            app.alarm = PytAlarm()
            app.bwListAlarmsActive = 1
            app.alarm.listAlarms_activate()
        else:
            app.alarm.windowListAlarms.present()
        return 0

    def list_alarms2(self):
        if not app.bwListAlarmsActive:
            app.alarm = PytAlarm()
            app.bwListAlarmsActive = 1
            app.alarm.listAlarms_activate()
        else:
            app.alarm.windowListAlarms.present()
        return 0

    def add_alarm(self, widget):
        if not app.bwAddAlarmActive:
            app.alarm = PytAlarm()
            app.bwAddAlarmActive = 1
            app.alarm.addAlarm_activate()
        else:
            app.alarm.windowAddAlarm.present()
        return 0

    def last_alarms(self, widget):
        if not app.bwLastAlarmsActive:
            app.alarm = PytAlarm()
            app.bwLastAlarmsActive = 1
            app.alarm.lastAlarms_activate()
        else:
            app.alarm.windowLastAlarms.present()
        return 0

    def about(self, widget):
        if not app.bwAboutActive:
            app.alarm = PytAlarm()
            app.bwAboutActive = 1
            app.alarm.about_activate()
        else:
            app.alarm.windowAbout.present()
        return 0

    def do_activate(self):

        self.wMainWindow = MainWindow()
        self.build_menu(self.wMainWindow)

        self.wMainWindow.show_all()
        self.wMainWindow.destroy()

        #self.wMainWindow.set_position()

        (x, y) = self.wMainWindow.get_position()
        print(str(x) + " | " + str(y))


    def do_startup(self):

        Gtk.Application.do_startup(self)

    def quitApp(self, par):

        app.quit()

    # app_quit()

    def app_quit(self, widget):
        # print(quit)

        # stop the alarm thread
        self.rt.stop()

        if sys.platform != "win32":
            notify.uninit()

        if os.path.isfile(pidfile):
            os.remove(pidfile)

        Gtk.main_quit()

        quit()


def main():
    print(bcolors.OKGREEN + "main" + bcolors.ENDC)

    return 0

if __name__ == "__main__":
    app = Application()

    pid = str(os.getpid())

    if os.path.isfile(pidfile):
        print("\033[93m%s already exists\033[0m" % pidfile)
        # print("%s already exists" % pidfile)
        f = open(pidfile, "r")
        for line in f:
            sPid = line.strip().lower()

        try:
            os.kill(int(sPid), 0)
        except OSError:
            if os.path.isfile(pidfile):
                os.remove(pidfile)
        else:
            sys.exit()

    try:
        f = open(pidfile, 'w')
        f.write(pid)
        f.close()
        print(bcolors.OKGREEN + "Pidfile was opened for write." + bcolors.ENDC)
    except OSError:
        print(bcolors.FAIL + "Pidfile wasn't opened for write." + bcolors.ENDC)
        if os.path.isfile(pidfile):
            os.remove(pidfile)

    try:
        app.alarm = PytAlarm()

        if sys.platform == "win32":
            app.start_indicator()
        else:
            app.start_linux_indicator()

            notify.init(APPINDICATOR_ID)
            notify.Notification.new("Message", "Pytalarm window is hidden", None).show()

        app.rt = RepeatedTimer(1, app.alarm.check_alarm)
        try:
            app.run(sys.argv)
            Gtk.main()
        finally:
            app.rt.stop()

        # while True:
        #    app.alarm.check_alarm()
        #    time.sleep(0.1)
        #    while Gtk.events_pending():
        #        Gtk.main_iteration()

        if os.path.isfile(pidfile):
            os.remove(pidfile)

    finally:
        if os.path.isfile(pidfile):
            os.remove(pidfile)
