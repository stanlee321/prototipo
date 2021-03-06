import os
import sys
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt

def exportarInformacionDeHoyO(day = 0,folder = ''):
	if folder != '':
		directorio = folder
	else:
		if os.uname()[1] == 'raspberrypi':
			directorio = os.getenv('HOME')
		else:
			directorio = '/media/alvarohurtado/almacenamiento/casosReportadosOficiales'
		directorio = directorio + '/' + (datetime.datetime.today()+datetime.timedelta(days = day)).strftime('%Y-%m-%d')+'_reporte'
	exportarInformacionEnDir(directorio)

def exportarInformacionEnDir(nombreDirectorio):
	carpetaEncuestion = nombreDirectorio
	#carpetaEncuestion = '/media/alvarohurtado/almacenamiento/casosReportadosOficiales/2018-01-09_report'
	datos = np.load(carpetaEncuestion+'/reporteDiario.npy')
	tiempos = datos.transpose()[0]
	periodos = datos.transpose()[1]
	cruces = datos.transpose()[2]
	infracciones = datos.transpose()[4]

	tiempos = []
	periodos = []
	cruces = []
	infracciones = []

	histograma = []

	for dato in datos:
		if dato[0].time()<datetime.time(6,5,0):
			continue
		tiempo = dato[0]
		tiempos.append(tiempo)
		periodo = dato[1]
		periodos.append(periodo)
		cruce = dato[2]
		giro = dato[3]
		cruces.append(cruce)
		infraccion = dato[4]
		nuevoTiempo = datetime.datetime(tiempo.year,tiempo.month,tiempo.day,tiempo.hour,0,0,0)
		tiempo.replace(second = 0)
		if tiempo.minute < 30:
			nuevoTiempo = datetime.datetime(tiempo.year,tiempo.month,tiempo.day,tiempo.hour,0,0,0)
		else:
			nuevoTiempo = datetime.datetime(tiempo.year,tiempo.month,tiempo.day,tiempo.hour,30,0,0)
		
		#for bloque in histograma:
		if not any(variable[0] == nuevoTiempo for variable in histograma):
			# Hora, Infracciones, Cruces
			histograma.append([nuevoTiempo,0,0,0])
			#print('Se agrego nuevo',histograma[-1])
		for indice in range(len(histograma)):
			if histograma[indice][0] == nuevoTiempo:
				histograma[indice][1] = histograma[indice][1] + infraccion
				histograma[indice][2] = histograma[indice][2] + cruce
				histograma[indice][3] = histograma[indice][3] + cruce + giro

	histograma = np.array(histograma)

	x = histograma.transpose()[0]
	y = histograma.transpose()[1]
	z = histograma.transpose()[2]
	w = histograma.transpose()[3]

	totalCruce = sum(z)
	picoCruce = max(z)
	print('Flujo Directo: ',totalCruce, ' con pico ',picoCruce)

	totalFlujo = sum(w)
	picoFlujo = max(w)
	print('Flujo Total: ',totalFlujo, ' con pico ',picoFlujo)

	totalInfracciones = sum(y)
	picoInfracciones = max(y)
	print('Total de infracciones: ',totalInfracciones,' con pico ',picoInfracciones)

	plt.bar(x,y, width=0.021,color='red')
	plt.ylim((0,picoInfracciones+2))
	plt.ylabel('Hora')
	plt.ylabel('Infracciones')
	plt.title('Infracciones cada media hora \n c. Sargento Flores y Av. 6 de Octubre')
	plt.gcf().autofmt_xdate()
	plt.savefig(carpetaEncuestion+'/infracciones.pdf')

	plt.bar(x,z, width=0.021,color='green')
	plt.ylim((0,picoCruce+2))
	plt.ylabel('Flujo')
	plt.ylabel('Vehículos')
	plt.title('Cruce Directo cada media hora \n c. Sargento Flores y Av. 6 de Octubre')
	plt.gcf().autofmt_xdate()
	plt.savefig(carpetaEncuestion+'/cruces.pdf')

	plt.bar(x,w, width=0.021,color='yellow')
	plt.ylim((0,picoFlujo+2))
	plt.ylabel('Flujo')
	plt.ylabel('Vehículos')
	plt.title('Flujo Vehicular cada media hora \n c. Sargento Flores y Av. 6 de Octubre')
	plt.gcf().autofmt_xdate()
	plt.savefig(carpetaEncuestion+'/flujo.pdf')

if __name__ == '__main__':
	# Tomamos los ingresos para controlar el video
	dia = 0
	folder = ''
	for input in sys.argv:
		if 'day' in input:
			dia = int(input[:-3])
			print('Ingreso numero: ',dia)
			exportarInformacionDeHoyO(day = dia)
		#if 'reporte' in input:
		#	dia = 0
		#	folder = os.getenv('HOME')+'/'+input
		#	print('generando de folder: ',folder)
		#	exportarInformacionDeHoyO(folder = folder)
		if 'media' in input:
			dia = 0
			folder = input
			print('generando de folder: ',folder)
			exportarInformacionDeHoyO(folder = folder)
	
