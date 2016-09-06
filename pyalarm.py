#!/usr/bin/env python

# alarm.py

# Description: A simple Python program to make the computer act
# like an alarm clock.

import re
import string
import datetime
import glob

import os
import sys

import threading
import subprocess
import ConfigParser

import time
from time import sleep

import sys
import signal
import json

from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify

APPINDICATOR_ID = 'pyalarm'

class ListWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="List of the alarms")

        self.set_border_width(5)
	self.connect("delete-event", self.delete_event)
        #self.connect("delete-event", Gtk.main_quit)
        #self.connect("destroy", lambda x: Gtk.main_quit())

	#self.set_default_size(500, 500)
        self.set_resizable(True)

    def delete_event(self, window, event):
        #Gtk.main_quit()
        window.hide()
	app.bwListAlarmsActive = 0

class AlarmWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Set an alarm")

        self.set_border_width(5)
	self.connect("delete-event", self.delete_event)

        self.set_resizable(False)

    def delete_event(self, window, event):
	window.hide()
	app.bwAddAlarmActive = 0

class SchedWindow(Gtk.ApplicationWindow):

    def __init__(self):
        Gtk.Window.__init__(self, title="Repetition settings")

        self.set_border_width(5)
        self.connect("delete-event", self.delete_event)

        self.set_resizable(True)

    def delete_event(self, window, event):
	window.hide()

class PyAlarm(Gtk.Application):
    DEF_PAD = 10
    DEF_PAD_SMALL = 5

    def __init__(self):
        #print "init AddAlarm"

        Gtk.Application.__init__(self)

	self.bStartLoad = 1

	self.bAddAlarmMode = 1
	self.init_settings()

	self.windowAddAlarm = None
	self.bwAddAlarmActive = 0

	self.sched_window = None
	self.bwSchedActive = 0

	self.windowListAlarms = None
	self.bwListAlarmsActive = 0

        self.marked_date = 31*[0]

	self.sSoundDir = "/usr/share/pyalarm/sounds/"

	self.sConfigDir = os.getenv("HOME") + "/.config/pyalarm/"
	if not os.path.exists(self.sConfigDir):
           os.makedirs(self.sConfigDir)

	self.sConfigFile = self.sConfigDir + "config.conf"

	self.toggleDay = 8*[0]
	self.toggleDaySettings = 8*[0]

	self.sDayName = 8*[0]
        self.sDayName[1] = "Monday"
        self.sDayName[2] = "Tuesday"
	self.sDayName[3] = "Wednesday"
	self.sDayName[4] = "Thursday"
	self.sDayName[5] = "Friday"
	self.sDayName[6] = "Saturday"
	self.sDayName[7] = "Sunday"

	self.toggleMonth = 13*[0]
	self.toggleMonthSettings = 13*[0]

	self.sMonthName = 13*[0]
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
	#print "init_settings"

        if self.bAddAlarmMode:
		self.sAlarmID = ""
                self.sName = "Untitled"

                self.sHour = "9"
                self.sMinutes = "00"
                self.sDate = ""
                self.sDateTime = ""

                date = datetime.datetime.today()

	        self.sCron = 6*[0]
                self.sCron[1] = self.sMinutes
                self.sCron[2] = self.sHour
                self.sCron[3] = "*"
                self.sCron[4] = "*"
                self.sCron[5] = "*"

                self.sDaysSelected = ""
                self.sMonthsSelected = ""
                #self.sMonthsSelected = str(date.month)

	        self.sCronEntry = ""
                for i in range(1,6):
                        self.sCronEntry = self.sCronEntry + self.sCron[i] + " "

                self.bAlarmActive = 1
                self.bCalendarSelected = 0

		self.sSound = ""
		self.sSoundListCount = 0

                self.sSettings = ""

	else:
		self.load_settings()

    def load_settings(self):
	#print "load settings"

	self.bStartLoad = 1

	self.entryName.set_text(self.sName)

        adj = Gtk.Adjustment(int(self.sHour), 0, 24, 1, 5, 0)
        self.spinnerHour.set_adjustment(adj)

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
		sList = re.split(',', self.sDaysSelected)
		for i in sList:
			if not i == '':
				self.toggleDaySettings[int(i)] = 1

	if not self.sMonthsSelected == "*":
		sList = re.split(',', self.sMonthsSelected)
	        for i in sList:
			if not i == '':
				self.toggleMonthSettings[int(i)] = 1

	if self.sSound == "None":
		self.sSound = self.sSoundList[3]

	for i in range(0,self.sSoundListCount+1):
		if self.sSoundList[i] == self.sSound:
			self.bStartLoad = 1
			self.comboSound.set_active(int(i-1))

	self.entryCron.set_text(self.sCronEntry)
	self.toggleActive.set_active(self.bAlarmActive)

        self.sSettings = self.sName + " | " + self.sCronEntry + " | " + self.sSound + " | " + str(self.bAlarmActive);
        self.labelDateTime.set_text(self.sSettings)

    def save_strings(self):
        if self.bCalendarSelected:
                self.sDateTime = str(self.sDate) + " "
        else:
                self.sDateTime = " "

        self.sName = self.entryName.get_text()

	if self.toggleEachHour.get_active():
		self.sHour = "*"
	else:
	        self.sHour = self.spinnerHour.get_value_as_int()
        self.sMinutes = self.spinnerMinutes.get_value_as_int()
        #self.sDateTime = self.sDateTime + str(self.sHour) + ":" +  str(self.sMinutes)

	self.sound_save()
	self.entryCron_update()

	self.toggleActive.set_active(self.bAlarmActive)

        self.sSettings = self.sName + " | " + self.sCronEntry + " | " + self.sSound + " | " + str(self.bAlarmActive);
        self.labelDateTime.set_text(self.sSettings)

    def toggle_each_hour(self, widget):
	if self.toggleEachHour.get_active():
		self.sHour = "*"
		self.sCron[2] = "*"

	self.save_strings()

    def toggle_everyday(self, widget):
        if self.toggleEveryday.get_active():
                self.bCalendarSelected = 0

		self.sMonthsSelected = ""
		self.sDaysSelected = ""

		self.sCron[3] = "*"
		self.sCron[4] = "*"
		self.sCron[5] = "*"

	        for i in range(1,8):
			self.toggleDaySettings[i] = 0
	        for i in range(1,13):
                        self.toggleMonthSettings[i] = 0

	self.save_strings()

    def calendar_selected(self, widget):
        self.bCalendarSelected = 1

	year, month, day = self.calendar.get_date()
	mytime = time.mktime((year, month+1, day, 0, 0, 0, 0, 0, -1))
        sDT = time.strftime("%x", time.localtime(mytime))

        self.sDate = "%s" % sDT
	date = datetime.datetime.strptime(self.sDate, '%m/%d/%Y')

	self.sCron[3] = str(date.day)
	self.sCron[4] = str(date.month)

	self.sMonthsSelected = str(date.month)
	self.toggleEveryday.set_active(0)

#	self.entryCron_update()
	self.save_strings()

    def entryCron_update(self):
        self.sCron[1] = str(self.sMinutes)
	if self.toggleEachHour.get_active():
		self.sCron[2] = "*"
	else:
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
	for i in range(1,6):
		self.sCronEntry = self.sCronEntry + self.sCron[i] + " "

	self.entryCron.set_text(self.sCronEntry)

    def entryCron_changed(self, widget):
        self.sCronEntry = self.entryCron.get_text()

        self.save_strings()

    def save_time(self, widget):
	if self.toggleEachHour.get_active():
		self.sHour = "*"
	else:
		self.sHour = self.spinnerHour.get_value_as_int()
        self.sMinutes = self.spinnerMinutes.get_value_as_int()

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
	        bashCommand = "/usr/bin/aplay -q " + self.sSoundDir + self.sSound
		process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

	self.save_strings()

    def save_alarm(self, widget, label):
	#print "save_alarm"

        self.save_strings()

        buf = "%s" % (str(self.sSettings))
        label.set_text(buf)

	config = ConfigParser.ConfigParser()
	config.read(self.sConfigFile)

	# lets create the config file
	cfgfile = open(self.sConfigFile, 'a')

	if self.sAlarmID == "":
		timestamp = time.time()
		self.sAlarmID = 'Alarm_' + str(timestamp)

	if not config.has_section(self.sAlarmID):
		config.add_section(self.sAlarmID)

	config.set(self.sAlarmID,'Name', self.sName)
	config.set(self.sAlarmID,'Cron', self.sCronEntry)
	config.set(self.sAlarmID,'ScheduleMinutes', self.sCron[1])
	config.set(self.sAlarmID,'ScheduleHour', self.sCron[2])
	config.set(self.sAlarmID,'ScheduleDays', self.sCron[3])
	config.set(self.sAlarmID,'ScheduleMonths', self.sCron[4])
	config.set(self.sAlarmID,'ScheduleDOW', self.sCron[5])
	config.set(self.sAlarmID,'Sound', self.sSound)
	config.set(self.sAlarmID,'Active', str(self.bAlarmActive))
	config.write(cfgfile)
	cfgfile.close()

        self.save_window("windowAddAlarm")
	self.windowAddAlarm.hide()
	app.bwAddAlarmActive = 0

	if app.bwListAlarmsActive:
                # save the window coordinates
                self.save_window("windowListAlarms")

		self.windowListAlarms.destroy()
		self.windowListAlarms = None

		# restore the window coordinates
	        self.windowListAlarms = ListWindow()
        	(x,y,w,h) = self.restore_window("windowListAlarms")
	        self.windowListAlarms.move(x, y)
		self.windowListAlarms.resize(w, h)

	        self.draw_gtk_listalarms(self.windowListAlarms)

	        self.windowListAlarms.show_all()

    def save_window(self, sWName):

        config = ConfigParser.ConfigParser()
        config.read(self.sConfigFile)

        cfgfile = open(self.sConfigFile, 'w')

	sSection = "General"
        if not config.has_section(sSection):
               config.add_section(sSection)

        if sWName == "windowAddAlarm":
		(x, y) = self.windowAddAlarm.get_position()
                config.set(sSection,sWName + 'X', x)
                config.set(sSection,sWName + 'Y', y)

		(w,h) = self.windowAddAlarm.get_size()
                config.set(sSection,sWName + 'W', w)
                config.set(sSection,sWName + 'H', h)

        if sWName == "windowListAlarms":
		(x, y) = self.windowListAlarms.get_position()
                config.set(sSection,sWName + 'X', x)
                config.set(sSection,sWName + 'Y', y)

		(w,h) = self.windowListAlarms.get_size()
                config.set(sSection,sWName + 'W', w)
                config.set(sSection,sWName + 'H', h)

        config.write(cfgfile)
        cfgfile.close()

    def restore_window(self, sWName):

        config = ConfigParser.ConfigParser()
        config.read(self.sConfigFile)

	sSection = "General"
	if config.has_section(sSection):
		if sWName == "windowAddAlarm":
	                x = config.get(sSection,sWName + 'X')
	                y = config.get(sSection,sWName + 'Y')
			w = config.get(sSection,sWName + 'W')
                        h = config.get(sSection,sWName + 'H')
			return (int(x), int(y), int(w), int(h))

		if sWName == "windowListAlarms":
        	        x = config.get(sSection,sWName + 'X')
	                y = config.get(sSection,sWName + 'Y')
                        w = config.get(sSection,sWName + 'W')
                        h = config.get(sSection,sWName + 'H')
			return (int(x), int(y), int(w), int(h))
	return (0, 0, 800, 600)

    def toggle_day(self, toggle, nCB):
        i = nCB
	if self.toggleDay[i].get_active():
		self.toggleDaySettings[i] = 1
		self.bCalendarSelected = 0
		self.toggleEveryday.set_active(0)
	else:
		self.toggleDaySettings[i] = 0

	self.sDaysSelected = ""
	for j in range(1,8):
		if self.toggleDaySettings[j]:
			if self.sDaysSelected == "":
				self.sDaysSelected = str(j)
			else:
				self.sDaysSelected = self.sDaysSelected + "," + str(j)
        #self.labelDayRInfo.set_text(self.sDaysSelected)

	self.entryCron_update()

    def toggle_month(self, toggle, nCB):
        i = nCB
        if self.toggleMonth[i].get_active():
                self.toggleMonthSettings[i] = 1
		self.bCalendarSelected = 0
        else:
                self.toggleMonthSettings[i] = 0

	self.sMonthsSelected = ""
	for j in range(1,13):
	        if self.toggleMonthSettings[j]:
	                if self.sMonthsSelected == "":
				self.sMonthsSelected = str(j)
	                else:
				self.sMonthsSelected = self.sMonthsSelected + "," + str(j)
        #self.labelMonthRInfo.set_text(self.sMonthsSelected)

	self.entryCron_update()

    def on_cronInfo_clicked(self, widget):
        dialog = Gtk.MessageDialog(self.windowAddAlarm, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "Cron info")
        dialog.format_secondary_text(
            #"You can replace each star in the cron settings with the following values: \n
	    "At the moment the cron settings are not availabe for edit \nmin | hour | day of month (1-31) | month (1-12) | day of week (0 - 7) \n*    | *       | *                               | *                      | *")
        dialog.run()
        dialog.destroy()

    def toggle_active(self, toggle):
	if toggle.get_active():
		self.bAlarmActive = 1
	else:
		self.bAlarmActive = 0
	#print self.bAlarmActive

	self.save_strings()

    def on_switch_activated(self, widget, gparam):
        if self.switchActive.get_active():
            self.bAlarmActive = 1
        else:
	    self.bAlarmActive = 0
	#print self.bAlarmActive

	self.save_strings()

    def on_wAddAlarm_close_clicked(self, widget):
        self.save_window("windowAddAlarm")
	self.windowAddAlarm.hide()
	app.bwAddAlarmActive = 0

    def on_wListAlarms_addnew_clicked(self, widget):

	if not app.bwAddAlarmActive:
	        self.bAddAlarmMode = 1
	        self.bStartLoad = 1

	        self.init_settings()

	        # create the window and the widgets
	        self.windowAddAlarm = AlarmWindow()
	        self.draw_gtk_addalarm(self.windowAddAlarm)
	        (x,y,w,h) = self.restore_window("windowAddAlarm")
	        self.windowAddAlarm.move(x, y)
	        #self.windowAddAlarm.resize(w, h)
		app.bwAddAlarmActive = 1

        	self.windowAddAlarm.show_all()

    def treeview_selection_changed(self, selection):
	model, treeiter = selection.get_selected()
	if treeiter != None:
		self.selectedAlarm = str(model[treeiter][0])
	        #print "You selected ", self.selectedAlarm

    def on_wListAlarms_del_clicked(self, widget):

        config = ConfigParser.ConfigParser()
        config.read(self.sConfigFile)

	cfgfile = open(self.sConfigFile, 'w')

	configSection = self.selectedAlarm

	if config.remove_section(configSection):
		print "delete " + configSection
		config.write(cfgfile)
		cfgfile.close()

		self.save_window("windowListAlarms")

 	        self.windowListAlarms.destroy()
	        self.windowListAlarms = None

	        # restore the window coordinates
	        self.windowListAlarms = ListWindow()
	        (x,y,w,h) = self.restore_window("windowListAlarms")
	        self.windowListAlarms.move(x, y)
	        self.windowListAlarms.resize(w, h)

	        self.draw_gtk_listalarms(self.windowListAlarms)

	        self.windowListAlarms.show_all()

    def on_wListAlarms_close_clicked(self, widget):
        self.save_window("windowListAlarms")
	self.windowListAlarms.hide()
	app.bwListAlarmsActive = 0

    def on_sched_clicked(self, widget):
	if not self.bwSchedActive:
	        self.windowSched = SchedWindow()
	        self.draw_gtk_sched(self.windowSched)
		self.sched_window.show_all()
		self.bwSchedActive = 1

    def on_sched_close_clicked(self, widget):
        self.windowSched.hide()
	self.bwSchedActive = 0

    def on_select_days_clicked(self, widget):
        for i in range(1,8):
                self.toggleDay[i].set_active(1)
		self.toggleDaySettings[i] = 1

    def on_unselect_days_clicked(self, widget):
        for i in range(1,8):
                self.toggleDay[i].set_active(0)
		self.toggleDaySettings[i] = 0

    def on_select_months_clicked(self, widget):
	for i in range(1,13):
                self.toggleMonth[i].set_active(1)
		self.toggleMonthSettings[i] = 1

    def on_unselect_months_clicked(self, widget):
        for i in range(1,13):
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

        width = int(monitors[curmon].width/2) - int(width/2)
        height = int(monitors[curmon].height/2) - int(height/2)
        window.move(width, height)

    def draw_gtk_sched(self, window):
        self.sched_window = window

        vboxS = Gtk.VBox(False, self.DEF_PAD)
        window.add(vboxS)

	# Days
        hboxRDL = Gtk.HBox (False, 1)
        vboxS.pack_start(hboxRDL, False, True, self.DEF_PAD)

        labelDayRepeat = Gtk.Label("Repeat in the following days:")
        hboxRDL.pack_start(labelDayRepeat, False, False, 0)

        self.labelDayRInfo = Gtk.Label("")
        hboxRDL.pack_start(self.labelDayRInfo, False, False, 0)

        hboxRD1 = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRD1, False, True, self.DEF_PAD)

        for i in range(1,4):
                self.toggleDay[i] = Gtk.CheckButton(self.sDayName[i])
                self.toggleDay[i].connect("toggled", self.toggle_day, i)
                hboxRD1.pack_start(self.toggleDay[i], False, False, 0)
		self.toggleDay[i].set_active(self.toggleDaySettings[i])

        hboxRD2 = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRD2, False, True, self.DEF_PAD)

        for i in range(4,8):
                self.toggleDay[i] = Gtk.CheckButton(self.sDayName[i])
                self.toggleDay[i].connect("toggled", self.toggle_day, i)
                hboxRD2.pack_start(self.toggleDay[i], False, False, 0)
		self.toggleDay[i].set_active(self.toggleDaySettings[i])

        hboxSD = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxSD, False, False, self.DEF_PAD)

        buttonSD = Gtk.Button("Select all days")
        buttonSD.connect("clicked", self.on_select_days_clicked)
        hboxSD.pack_start(buttonSD, False, False, self.DEF_PAD)

        buttonSD = Gtk.Button("Unselect all days")
        buttonSD.connect("clicked", self.on_unselect_days_clicked)
        hboxSD.pack_start(buttonSD, False, False, self.DEF_PAD)

	# Months
        hboxRML = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRML, False, False, self.DEF_PAD)

        labelMonthRepeat = Gtk.Label("Repeat in the following months:")
        hboxRML.pack_start(labelMonthRepeat, False, False, 0)

        self.labelMonthRInfo = Gtk.Label("")
        hboxRML.pack_start(self.labelMonthRInfo, False, False, 0)

        hboxRM1 = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM1, False, False, self.DEF_PAD)

        for i in range(1,5):
                self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
                self.toggleMonth[i].connect("toggled", self.toggle_month, i)
                hboxRM1.pack_start(self.toggleMonth[i], False, False, 0)
		self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxRM2 = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM2, False, False, self.DEF_PAD)

        for i in range(5,9):
                self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
                self.toggleMonth[i].connect("toggled", self.toggle_month, i)
                hboxRM2.pack_start(self.toggleMonth[i], False, False, 0)
		self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxRM3 = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxRM3, False, False, self.DEF_PAD)

        for i in range(9,13):
                self.toggleMonth[i] = Gtk.CheckButton(self.sMonthName[i])
                self.toggleMonth[i].connect("toggled", self.toggle_month, i)
                hboxRM3.pack_start(self.toggleMonth[i], False, False, 0)
		self.toggleMonth[i].set_active(self.toggleMonthSettings[i])

        hboxSM = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxS.pack_start(hboxSM, False, False, self.DEF_PAD)

        buttonSM = Gtk.Button("Select all months")
        buttonSM.connect("clicked", self.on_select_months_clicked)
        hboxSM.pack_start(buttonSM, False, False, self.DEF_PAD)

        buttonSM = Gtk.Button("Unselect all months")
        buttonSM.connect("clicked", self.on_unselect_months_clicked)
        hboxSM.pack_start(buttonSM, False, False, self.DEF_PAD)

        bboxB = Gtk.HButtonBox ()
        vboxS.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox (False, 1)
        bboxB.pack_start(hboxB, False, True, self.DEF_PAD)

        buttonClose = Gtk.Button("Close")
        buttonClose.connect("clicked", self.on_sched_close_clicked)
        hboxB.pack_start(buttonClose, False, False, self.DEF_PAD)

    def draw_gtk_addalarm(self, window):
	#print "draw_gtk_addalarm"

	self.windowAddAlarm = window

        vboxW = Gtk.VBox(False, self.DEF_PAD)
        self.windowAddAlarm.add(vboxW)

	hboxW = Gtk.HBox (False, 1)
        vboxW.pack_start(hboxW, False, True, 0)

	# The name of the alarm
        labelName = Gtk.Label("Alarm name:")
        hboxW.pack_start(labelName, False, True, 0)

        self.entryName = Gtk.Entry()
	self.entryName.set_text(self.sName)
        hboxW.pack_start(self.entryName, False, True, self.DEF_PAD)

        hboxC = Gtk.HBox(False, self.DEF_PAD)
        vboxW.pack_start(hboxC, False, True, self.DEF_PAD)

	# Calendar widget
        framePtd = Gtk.Frame()
        hboxC.pack_start(framePtd, False, True, self.DEF_PAD)

	vboxC = Gtk.VBox(True, self.DEF_PAD_SMALL)
        framePtd.add(vboxC)

        self.calendar = Gtk.Calendar()
        #self.calendar.mark_day(19)
        #self.marked_date[19-1] = 1
        vboxC.add(self.calendar)
        self.calendar.connect("day_selected", self.calendar_selected)

        # The time spinners
        framePtt = Gtk.Frame()
        hboxC.pack_start(framePtt, False, True, self.DEF_PAD)

        vboxPtt = Gtk.VBox(True, self.DEF_PAD_SMALL)
        framePtt.add(vboxPtt)

        hboxPtt = Gtk.HBox(True, self.DEF_PAD_SMALL)
	vboxPtt.pack_start(hboxPtt, False, True, self.DEF_PAD)

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
        adj = Gtk.Adjustment(int(self.sMinutes), 0, 59, 1, 5, 0)
	self.spinnerMinutes.set_adjustment(adj)
        self.spinnerMinutes.set_wrap(True)
	adj.connect("value_changed", self.save_time)
        vboxMinutes.pack_start(self.spinnerMinutes, False, True, 0)

        # Repeat settings
        bboxB = Gtk.HButtonBox ()
        vboxPtt.pack_start(bboxB, False, False, 0)

        vboxB = Gtk.VBox (False, 1)
        bboxB.pack_start(vboxB, False, True, self.DEF_PAD)

        self.toggleEachHour = Gtk.CheckButton("Repeat each hour")
        self.toggleEachHour.connect("toggled", self.toggle_each_hour)
        vboxB.pack_start(self.toggleEachHour, True, True, 0)

        self.toggleEveryday = Gtk.CheckButton("Repeat everyday")
        self.toggleEveryday.connect("toggled", self.toggle_everyday)
	vboxB.pack_start(self.toggleEveryday, True, True, 0)

        # Repeat settings
        hboxB = Gtk.HBox (False, 1)
        bboxB.pack_start(hboxB, False, True, self.DEF_PAD)

        buttonRepeat = Gtk.Button("Other scheduled settings..")
	buttonRepeat.connect("clicked", self.on_sched_clicked)
        hboxB.pack_start(buttonRepeat, False, False, self.DEF_PAD)

	# cron like settings
        hboxCron = Gtk.HBox(True, self.DEF_PAD_SMALL)
        vboxW.add(hboxCron)

	labelCron = Gtk.Label("Cron like settings:")
        hboxCron.pack_start(labelCron, False, True, 0)

        self.entryCron = Gtk.Entry()
	self.entryCron.set_max_length(50)
        self.entryCron.set_text(self.sCronEntry)
	self.entryCron.set_editable(0)
	self.entryCron.connect("changed", self.entryCron_changed)
        hboxCron.pack_start(self.entryCron, False, True, self.DEF_PAD)

        buttonInfo = Gtk.Button("Cron short info")
        buttonInfo.connect("clicked", self.on_cronInfo_clicked)
        hboxCron.add(buttonInfo)

	# The activation option
        framePd = Gtk.Frame()
        vboxW.pack_start(framePd, True, True, self.DEF_PAD)

        vboxPd = Gtk.VBox(True, self.DEF_PAD_SMALL)
        framePd.add(vboxPd)

        hboxPd = Gtk.HBox (False, 3)
        vboxPd.pack_start(hboxPd, False, True, 0)

        labelAlarm = Gtk.Label("Alarm:")
        hboxPd.pack_start(labelAlarm, False, True, 0)

        self.labelDateTime = Gtk.Label("")
        hboxPd.pack_start(self.labelDateTime, False, True, 0)

	# Sound played by the alarm
        hboxSound = Gtk.HBox (False, 3)
        vboxPd.pack_start(hboxSound, False, True, 0)

        self.labelSound = Gtk.Label("Alarm Sound:")
        hboxSound.pack_start(self.labelSound, False, True, 0)

        self.comboSound = Gtk.ComboBoxText()
        self.comboSound.set_entry_text_column(0)
        self.comboSound.connect("changed", self.on_comboSound_changed)
	self.sSoundList = 100*[0]
	self.sSoundListCount = 0
        for file in sorted(glob.glob(self.sSoundDir + "*.wav")):
                file = re.sub(self.sSoundDir, '', file)
                self.comboSound.append_text(file)
		self.sSoundListCount += 1
		self.sSoundList[self.sSoundListCount] = file
        hboxSound.pack_start(self.comboSound, False, False, 0)

	# Activate the alarm
        self.toggleActive = Gtk.CheckButton("Activate the alarm")
        self.toggleActive.connect("toggled", self.toggle_active)
        vboxPd.pack_start(self.toggleActive, True, True, 0)

        bboxS = Gtk.HButtonBox ()
        vboxW.pack_start(bboxS, False, False, 0)

	# Save the settings
        buttonSave = Gtk.Button("Save the alarm")
        buttonSave.connect("clicked", self.save_alarm, self.labelDateTime)
        bboxS.add(buttonSave)
        #buttonSave.grab_default()

        buttonCancel = Gtk.Button("Cancel")
	buttonCancel.connect("clicked", self.on_wAddAlarm_close_clicked)
        bboxS.add(buttonCancel)
        #buttonCancel.grab_default()

	if self.bAddAlarmMode:
		self.sName = self.entryName.get_text()

		self.toggleEachHour.set_active(0)
		self.toggleEveryday.set_active(1)

                self.comboSound.set_active(3)

		self.toggleActive.set_active(1)
                self.bAlarmActive = 1

		self.save_strings()

    def draw_gtk_listalarms(self, window):
	#print "draw_gtk_listalarms"

	config = ConfigParser.ConfigParser()
	config.read(self.sConfigFile)

	alarm_liststore = Gtk.ListStore(str, str, str, str, str, str, str)
        self.current_filter = None

	sCron = 6*[0]
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
			bAlarmActive = config.getint(sAlarmID, 'Active') 

			if bAlarmActive:
				sAlarmActive = "Active"
			else:
				sAlarmActive = "Inactive"

			sList = [(sAlarmID, sName, sCron[2] + ":" + sCron[1], sCron[3], sCron[4], sCron[5], sAlarmActive)]

	        	for alarm_ref in sList:
		            alarm_liststore.append(list(alarm_ref))

	alarm_liststore.set_sort_column_id(1, 0)

	if i < 15:
		i = i*50
	else:
		i = 500

	window.set_default_size(700, i)

        vboxW = Gtk.VBox(False, self.DEF_PAD)
        window.add(vboxW)

        hboxW = Gtk.HBox (False, 1)
        vboxW.pack_start(hboxW, False, True, 0)

        labelName = Gtk.Label("Alarm list:")
        hboxW.pack_start(labelName, False, True, 0)

	grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
	vboxW.pack_start(grid, False, True, self.DEF_PAD)

	self.filter = alarm_liststore.filter_new()
        self.treeview = Gtk.TreeView.new_with_model(self.filter)
	self.treeview.set_headers_clickable(True)
	for i, column_title in enumerate(["Id", "Name", "Time", "Days ", "Months", "Day of week", "Active"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
	    #if column_title == "Name":
		#column.set_clickable(True)
            	#column.set_sort_column_id(0)
		#column.set_sort_indicator(True)
            self.treeview.append_column(column)
	    if column_title == "Id":
		    column.set_visible(False)

	tree_selection = self.treeview.get_selection()
	tree_selection.connect("changed", self.treeview_selection_changed)

	self.treeview.connect('row-activated', self.treeview_row_activated)

        #setting up the layout, putting the treeview in a scrollwindow
        scrollable_treelist = Gtk.ScrolledWindow()
        scrollable_treelist.set_vexpand(True)
	scrollable_treelist.add(self.treeview)
        grid.attach(scrollable_treelist, 0, 0, 8, 10)
	vboxW.pack_start(scrollable_treelist, False, False, self.DEF_PAD)

        bboxB = Gtk.HButtonBox ()
        vboxW.pack_start(bboxB, False, False, 0)

        hboxB = Gtk.HBox (False, 1)
        bboxB.pack_start(hboxB, False, True, self.DEF_PAD)

        buttonAddAlarm = Gtk.Button("Add new alarm")
        buttonAddAlarm.connect("clicked", self.on_wListAlarms_addnew_clicked)
        #buttonAddAlarm.grab_default()
        hboxB.pack_start(buttonAddAlarm, False, False, self.DEF_PAD)

        buttonDelAlarm = Gtk.Button("Delete selected alarm")
        buttonDelAlarm.connect("clicked", self.on_wListAlarms_del_clicked)
        #buttonDelAlarm.grab_default()
        hboxB.pack_start(buttonDelAlarm, False, False, self.DEF_PAD)

        buttonClose = Gtk.Button("Close")
        #buttonClose.connect("clicked", lambda w: Gtk.main_quit())
	buttonClose.connect("clicked", self.on_wListAlarms_close_clicked)
	#buttonClose.grab_default()
	hboxB.pack_start(buttonClose, False, False, self.DEF_PAD)

    def editAlarm(self, configSection):
	#print "editAlarm"

	# we are in edit mode
	self.bAddAlarmMode = 0

        config = ConfigParser.ConfigParser()
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

        self.sSound = config.get(configSection, 'Sound')
        self.bAlarmActive = config.getint(configSection, 'Active')

	# create the window and the widgets
        self.windowAddAlarm = AlarmWindow()
        self.draw_gtk_addalarm(self.windowAddAlarm)
	(x,y,w,h) = self.restore_window("windowAddAlarm")
        self.windowAddAlarm.move(x, y)
	#self.windowAddAlarm.resize(w, h)

	self.load_settings()

	# show the widgets
        self.windowAddAlarm.show_all()

    def treeview_row_activated(self, treeview, path, column):
	model = treeview.get_model()

	self.editAlarm(model[path][0])

	return 0

    def isTimeToRun_alarm(self, sAlarmID, sName, sSound, sCron):
	date = datetime.datetime.today()
	nCDay = int(date.day)
	nCMonth = int(date.month)
	nCDOW = int(date.weekday()) + 1

	nCHour = int(time.strftime("%H"))
	nCMinutes = int(time.strftime("%M"))

	bCDOW = 0
	if not sCron[5] == "*":
		sList = re.split(',', sCron[5])
		for i in sList:
			if nCDOW == int(i):
				bCDOW = 1
	else:
		bCDOW = 1

	if not bCDOW:
		return 0

	bCMonth = 0
	if not sCron[4] == "*":
		sList = re.split(',', sCron[4])
		for i in sList:
                        if nCMonth == int(i):
                                bCMonth = 1
	else:
		bCMonth = 1

        if not bCMonth:
                return 0

        bCDay = 0
        if not sCron[3] == "*":
                sList = re.split(',', sCron[3])
                for i in sList:
                        if nCDay == int(i):
                                bCDay = 1
        else:
                bCDay = 1

        if not bCDay:
                return 0

	if not sCron[2] == "*":
		if not int(sCron[2]) == nCHour:
			return 0

        if not int(sCron[1]) == nCMinutes:
                return 0

	app.sAlarmStarted = sAlarmID
	app.play_alarm(sName, sSound)

    def check_alarm(self):
        config = ConfigParser.ConfigParser()
        config.read(self.sConfigFile)

	sCron = 6*[0]
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
                        bAlarmActive = config.getint(sAlarmID, 'Active')

                        if bAlarmActive:
                                self.isTimeToRun_alarm(sAlarmID, sName, sSound, sCron)

    def addAlarm_activate(self):
	#print "addAlarm_activate"

        if not app.bwAddAlarmActive:
                self.windowAddAlarm = AlarmWindow()
                self.draw_gtk_addalarm(self.windowAddAlarm)
                (x,y,w,h) = self.restore_window("windowAddAlarm")
                self.windowAddAlarm.move(x, y)
                self.windowAddAlarm.resize(w, h)
                self.windowAddAlarm.show_all()
                app.bwAddAlarmActive = 1

    def listAlarms_activate(self):
	#print "listAlarms_activate"

        if not app.bwListAlarmsActive:
                self.windowListAlarms = ListWindow()
                self.draw_gtk_listalarms(self.windowListAlarms)
                (x,y,w,h) = self.restore_window("windowListAlarms")
                self.windowListAlarms.move(x, y)
                self.windowListAlarms.resize(w, h)

                self.windowListAlarms.show_all()
                app.bwListAlarmsActive = 1

    def do_activate(self):
	#print "do_activate"

	self.listAlarms_activate()

    def do_startup(self):
	#print "do_startup"

        Gtk.Application.do_startup(self)

class Application(Gtk.ApplicationWindow):

    def __init__(self):
        #print "init App"

        self.bwAddAlarmActive = 0
        self.bwListAlarmsActive = 0

	self.bAlarmOn = 0
	self.nAlarmMin = 0
        self.sAlarmStopped = ""
	self.sAlarmStarted = ""

	self.pidfile = "/var/tmp/pyalarm.pid"
	self.alarm = None

        self.sIcon = "/usr/share/pyalarm/icons/pyalarm.svg"
        self.sActiveIcon = "/usr/share/pyalarm/icons/pyalarm-active.svg"

    def start_indicator(self):
	#sIcon = "/usr/share/pyalarm/icons/pyalarm.svg"
	indicator = appindicator.Indicator.new(APPINDICATOR_ID, app.sIcon, appindicator.IndicatorCategory.SYSTEM_SERVICES)

	indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
	indicator.set_menu(self.build_menu())
	notify.init(APPINDICATOR_ID)

	notify.Notification.new("Message", "Pyalarm window is hidden", None).show()

	#Gdk.threads_init()

	while True:
		app.alarm.check_alarm()

		time.sleep(0.1)

		while Gtk.events_pending():
			Gtk.main_iteration()
			#Gtk.main()

		if app.bAlarmOn:
			indicator.set_icon(app.sActiveIcon)
		else:
			indicator.set_icon(app.sIcon)

        if os.path.isfile(app.pidfile):
                os.unlink(app.pidfile)

    def build_menu(self):
	menu = Gtk.Menu()

	item_stop = Gtk.MenuItem('Stop the alarm')
	item_stop.connect('activate', self.stop_alarm)
	menu.append(item_stop)

	separator = Gtk.SeparatorMenuItem()
	menu.append(separator)

	item_show = Gtk.MenuItem('List alarms')
	item_show.connect('activate', self.list_alarms)
	menu.append(item_show)

	separator = Gtk.SeparatorMenuItem()
	menu.append(separator)

	item_add = Gtk.MenuItem('Add alarm')
	item_add.connect('activate', self.add_alarm)
	menu.append(item_add)

	separator = Gtk.SeparatorMenuItem()
	menu.append(separator)

	item_quit = Gtk.MenuItem('Quit')
	item_quit.connect('activate', self.app_quit)
	menu.append(item_quit)

	menu.show_all()
	#Gtk.MenuItem('Trigger alarm').activate();

	return menu

    def stop_alarm(self, widget):
	#print "Stop alarm"

	bashCommand = "pkill -f /dev/shm/alarm.sh"
	process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

	app.bAlarmOn = 0
	if app.nAlarmMin == int(time.strftime("%M")):
		app.sAlarmStopped = app.sAlarmStarted
	else:
		app.sAlarmStopped = ""

    def play_alarm(self, sName, sSoundFile):
	#print "Play alarm"

	if not app.bAlarmOn:
		if app.sAlarmStarted == app.sAlarmStopped:
			return 0

		app.bAlarmOn = 1
		app.nAlarmMin = int(time.strftime("%M"))
	else:
		if not app.nAlarmMin == int(time.strftime("%M")) :
			app.bAlarmOn = 0
		return 0

	notify.Notification.new("Alarm: ", sName, app.sIcon).show()

	sScript = "/dev/shm/alarm.sh"

	sSoundFile = app.alarm.sSoundDir + sSoundFile

	if  os.path.exists(sSoundFile):
		bashCommand = "s=0; while [ $s -lt 60 ]; do /usr/bin/aplay -q " + sSoundFile + "; sleep 0.5; s=$((s+1)); done"
	        #process = subprocess.Popen("bash " + bashCommand.split(), stdout=subprocess.PIPE)

		text_file = open(sScript, "w")
		text_file.write(bashCommand)
		text_file.close()

		bashCommand = "/bin/chmod u+x " + sScript
		process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

		bashCommand = "/bin/bash " + sScript
		process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)

    def list_alarms(self, widget):
	#print "List alarms"

	if not app.bwListAlarmsActive:
		app.alarm = PyAlarm()
		app.alarm.listAlarms_activate()
		app.bwListAlarmsActive = 1

    def add_alarm(self, widget):
	#print "Add alarm"

	if not app.bwAddAlarmActive:
		app.alarm = PyAlarm()
		app.alarm.addAlarm_activate()
		app.bwAddAlarmActive = 1
	return 0

    def app_quit(self, widget):
	#print quit
	notify.uninit()
	if os.path.isfile(app.pidfile):
		os.unlink(app.pidfile)
	Gtk.main_quit()
	quit()

def main():
    print "main"

    return 0

if __name__ == "__main__":
	app = Application()

	pid = str(os.getpid())
	#print app.pidfile

	if os.path.isfile(app.pidfile):
	    print "%s already exists, exiting" % app.pidfile
	    sys.exit()
	file(app.pidfile, 'w').write(pid)
	try:
        	app.alarm = PyAlarm()
	        app.start_indicator()
	finally:
	        if os.path.isfile(app.pidfile):
	                os.unlink(app.pidfile)
