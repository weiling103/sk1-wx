# -*- coding: utf-8 -*-
#
# 	Copyright (C) 2016 by Igor E. Novikov
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU General Public License as published by
# 	the Free Software Foundation, either version 3 of the License, or
# 	(at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU General Public License
# 	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import wx

from uc2 import uc2const

from sk1 import _, config
from generic import AbstractPrinter, AbstractPS, COLOR_MODE

class MSW_PS(AbstractPS):

	printers = []
	default_printer = ''

	def __init__(self, app, physical_only=False):
		self.app = app
		self.collect_printers()

	def readline(self, fileptr):
		return fileptr.readline().replace('\n', '').replace('\r', '').strip()

	def collect_printers(self):
		script = os.path.join(config.resource_dir, 'templates',
						'list_printers.vbs')
		appdata = self.app.appdata
		stdout = os.path.join(appdata.app_temp_dir, 'stdout.txt')
		os.system('cscript.exe %s>%s' % (script, stdout))
		fileptr = open(stdout, 'rb')
		line = self.readline(fileptr)
		while not line == '===': line = self.readline(fileptr)
		self.printers = []
		line = self.readline(fileptr)
		while not line == '===':
			if '::' in line:
				name, color = line.split('::', 1)
				printer = MSWPrinter(self.app, name)
				if color == '2':
					printer.color_supported = True
					printer.colorspace = uc2const.COLOR_RGB
				self.printers.append(printer)
			line = self.readline(fileptr)
		line = self.readline(fileptr)
		while not line == '===':
			if '::' in line:
				name, val = line.split('::', 1)
				if val == 'True':
					self.default_printer = name
					break


class MSWPrinter(AbstractPrinter):

	color_supported = False
	name = ''

	def __init__(self, app, name=_('Default printer')):
		self.app = app
		self.name = name

	def is_virtual(self): return False
	def is_color(self): return self.color_supported

	def get_print_data(self):
		if self.app.print_data is None:
			self.app.print_data = self.create_print_data()
		return self.app.print_data

	def create_print_data(self):
		print_data = wx.PrintData()
		print_data.SetPaperId(wx.PAPER_A4)
		print_data.SetPrintMode(wx.PRINT_MODE_PRINTER)
		return print_data

	def update_from_psd(self, page_setup_data):
		print_data = self.app.print_data
		self.page_orientation = uc2const.PORTRAIT
		if print_data.GetOrientation() == wx.LANDSCAPE:
			self.page_orientation = uc2const.LANDSCAPE
		page_id = page_setup_data.GetPaperId()
		w, h = page_setup_data.GetPaperSize()
		w *= uc2const.mm_to_pt
		h *= uc2const.mm_to_pt
		self.page_format = (page_id, (w, h))

	def run_propsdlg(self, win):
		data = wx.PageSetupDialogData(self.get_print_data())
		data.CalculatePaperSizeFromId()
		dlg = wx.PageSetupDialog(win, data)
		if dlg.ShowModal() == wx.ID_OK:
			data = wx.PrintData(dlg.GetPageSetupData().GetPrintData())
			self.app.print_data = data
			self.update_from_psd(dlg.GetPageSetupData())
			dlg.Destroy()
			return True
		return False

	def run_printdlg(self, win, printout):
		print_data = self.get_print_data()
		print_data.SetPrinterName(self.name)
		print_data.SetColour(self.color_mode == COLOR_MODE)
		data = wx.PrintDialogData(print_data)
		printer = wx.Printer(data)
		return printer.Print(win, printout, True)
