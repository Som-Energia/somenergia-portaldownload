#!/usr/bin/env python


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import os
import time

class SwitchingPortalIberdrola:
	name = 'Iberdrola'
	def __init__(self, user, password) :
		self.targetDirectory = os.getcwd()

		profile = webdriver.FirefoxProfile()
		profile.set_preference('browser.download.folderList', 2)
		profile.set_preference('browser.download.manager.showWhenStarting', False)
		profile.set_preference('browser.download.dir', self.targetDirectory)
		profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/zip')

		self.driver = webdriver.Firefox(profile)
		self.driver.get("https://www.iberdrola.es/pwmultid/ServletAutentificacion?pwmultid=iberdrolad")

		userbox = self.driver.find_element_by_name("usuario")
		userbox.send_keys(user)
		passbox = self.driver.find_element_by_name("clave")
		passbox.send_keys(password)

		loginbt = self.driver.find_element_by_class_name("textoboton")
		loginbt.click()

	def downloadXml(self, inici, final, proces, pas):
		self.driver.get("https://www.iberdrola.es/pwmultid/ServletOpcion?opcion=0021_MENSA_CONSULTAMENSAJES")

		originalWindows = [handle for handle in self.driver.window_handles ]

		self.driver.execute_script("document.getElementById('fec_recep_desde').setAttribute('value','{:%d/%m/%Y}')".format(inici))
		self.driver.execute_script("document.getElementById('fec_recep_hasta').setAttribute('value','{:%d/%m/%Y}')".format(final))
#		self.driver.execute_script("document.getElementById('fec_descarga_desde').setAttribute('value','11/11/2014')")
#		self.driver.execute_script("document.getElementById('fec_descarga_hasta').setAttribute('value','11/12/2014')")
		self.driver.execute_script("document.getElementsByName('cod_emisora')[0].value='0021'")
		self.driver.execute_script("document.getElementsByName('cod_destino')[0].value='0762'")
		processlist = self.driver.find_element_by_name("cod_proceso")

		processOption = [ option
			for option in processlist.find_elements_by_tag_name("option")
			if option.get_attribute('value') == proces ]

		if not processOption:
			raise Exception('Proces {} no trobat al formulari'.format(proces, ' ', join([
				option.get_attribute('value')
				for option in processlist.find_elements_by_tag_name('option') ])))
		processOption[0].click()

		self.driver.execute_script("document.getElementsByName('cod_paso')[0].value='{}'".format(pas))
		self.driver.execute_script("document.getElementsByName('tipo')[0].value='Todos'")
		self.driver.execute_script("Enviar()")

		previousFiles = os.listdir(self.targetDirectory)
		self.driver.execute_script("RecibirTodos()")

		alert = self.driver.switch_to_alert()
		alert.accept()

		currentWindow = self.driver.current_window_handle
		popup = [handle for handle in self.driver.window_handles if handle not in originalWindows ]
		self.driver.switch_to_window(popup[0])
		self.driver.close()
		self.driver.switch_to_window(currentWindow)
		downloaded = [f for f in os.listdir(self.targetDirectory) if f not in previousFiles ][0]

		newName = '{}_{}_{}_{}_{}.zip'.format(
			proces,pas,inici,final,self.name)
		os.rename(downloaded, newName)

		print downloaded, '->', newName


	def close(self):
		self.driver.close()

class SwitchingPortalEndesa:
	name = 'Endesa'

	def __init__(self, user, password) :
		self.targetDirectory = os.getcwd()
		self.pendingDownloads = []

		profile = webdriver.FirefoxProfile()
		profile.set_preference('browser.download.folderList', 2)
		profile.set_preference('browser.download.manager.showWhenStarting', False)
		profile.set_preference('browser.download.dir', self.targetDirectory)
		profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'application/zip')

		self.driver = webdriver.Firefox(profile)
		self.driver.get("https://www.canalweb.endesa.es/canalweb/servlet/ServletAutentificacion")

		userbox = self.driver.find_element_by_name("usuario")
		userbox.send_keys(user)
		passbox = self.driver.find_element_by_name("clave")
		passbox.send_keys(password)

		loginbt = self.driver.find_element_by_class_name("textoboton")
		loginbt.click()

	def downloadXml(self, inici, final, proces, pas):
		self.driver.get('https://www.canalweb.endesa.es/canalweb/consulta/mensajes/ConsultaMensajes.jsp')

		originalWindows = [handle for handle in self.driver.window_handles ]

		self.driver.execute_script("document.getElementById('fec_desde').setAttribute('value','{:%d/%m/%Y}')".format(inici))
		self.driver.execute_script("document.getElementById('fec_hasta').setAttribute('value','{:%d/%m/%Y}')".format(final))
		self.driver.execute_script("document.getElementsByName('cod_destino')[0].value='0762'")
		processlist = self.driver.find_element_by_name("cod_proceso")

		processOption = [
			option
			for option in processlist.find_elements_by_tag_name("option")
			if option.get_attribute('value') == proces ]

		if not processOption:
			raise Exception('Proces {} no trobat al formulari'.format(proces, ' ', join([
				option.get_attribute('value')
				for option in processlist.find_elements_by_tag_name('option') ])))
		processOption[0].click()

		self.driver.execute_script("document.getElementsByName('cod_paso')[0].value='{}'".format(pas))

		radio = self.driver.find_element_by_id('todos')
		radio.click()

		self.driver.execute_script("Enviar()")

		self.driver.execute_script("RecibirTodos()")

		textoAceptacion = self.driver.find_element_by_class_name('ListaCabecera').text
		codigoSolicitud = [int(s) for s in textoAceptacion.split() if s.isdigit()] [0]

		newName = '{}_{}_{}_{}_{}.zip'.format(
			proces,pas,inici,final,self.name)

		self.pendingDownloads.append((codigoSolicitud, newName))

	def downloadPending(self):
		while self.pendingDownloads:
			self.driver.get('https://www.canalweb.endesa.es/canalweb/consulta/mensajes/ConsultaDescargas.jsp')
			self.driver.execute_script("document.getElementById('fec_desde').setAttribute('value','{:%d/%m/%Y}')".format(datetime.date.today()))
			self.driver.execute_script("document.getElementById('fec_hasta').setAttribute('value','{:%d/%m/%Y}')".format(datetime.date.today()))
			self.driver.execute_script("Validar()")

			for solicitud, newName in self.pendingDownloads:

				disponibilitats = self.driver.find_elements_by_xpath("//table//table//table//td[contains(., '{}')]/../td[6]".format(solicitud))
				if not disponibilitats : 
					print "Compte quelcom ha passat amb el formulari"
					continue
				disponibilitat = disponibilitats[0]

				if disponibilitat.text.strip() not in ('NO','DISPONIBLE'):
					raise Exception("Disponibilitat desconeguda: {}".format(disponibilitat.text))

				if disponibilitat.text.strip() != 'DISPONIBLE':
					continue
					
				link = disponibilitat.find_element_by_tag_name("a").get_attribute('href')

				previousFiles = os.listdir(self.targetDirectory)
				self.driver.get(link)
				downloaded = [f for f in os.listdir(self.targetDirectory) if f not in previousFiles ][0]
				os.rename(downloaded, newName)
				self.pendingDownloads.remove((solicitud, newName))

				print downloaded, '->', newName

			print "Encara no tenim la peticio {}, esperant mig minutet...".format(solicitud)
			time.sleep(30)


	def close(self):
		self.driver.close()

import datetime
import config

inici = datetime.date(2015,01,01)
final = datetime.date(2015,01,12)
processos = 'C1,C2'.split(',')
passos = '02,05'.split(',')
distris = 'Endesa,Iberdrola'.split(',')
distris = ['Endesa']

configs=dict(
	Iberdrola = config.portal_iberdrola,
	Endesa = config.portal_endesa,
	)

portals = dict(
	(Portal.name, Portal)
	for Portal in [
		SwitchingPortalIberdrola,
		SwitchingPortalEndesa,
		])

for distri in distris:
	Portal = portals[distri]
	pconfig = configs[distri]
	portal = Portal(**pconfig)
	for proces in processos:
		for pas in passos:
			print "Descarregant", portal.name, proces, pas
			portal.downloadXml(
				inici=inici,
				final=final,
				proces=proces,
				pas=pas,
				)
	if hasattr(portal, 'downloadPending') :
		portal.downloadPending()
	portal.close()







