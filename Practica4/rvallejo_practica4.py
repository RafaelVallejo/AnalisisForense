#!/usr/bin/python
# -*- coding: utf-8 -*-

# Vallejo Fernández Rafael Alejandro
# Practica 4. Programa filecarving
from sys import exit, stderr, argv
import time
import re
import argparse

def printError(msg, eexit = False):
	"""Función que imprime mensaje de error y sale del programa
	Recibe: mensaje a mostrar y booleano que indica si se debe terminar la ejecución del programa"""
	stderr.write('Error:\t%s\n' % msg)
	if eexit:
		exit(1)

def checkOptions(options):
    """
    Función para verificar que los argumentos no estén vacíos.
    Recibe: options (de argparse)
    Devuelve: mensaje de error y llama a la función printError
    """
    if options.read_file is None:
		printError('Debes especificar el archivo a leer.', True)

def addOptions():
	"""
	Función para agregar las opciones al script
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('-r','--file', dest='read_file', default=None, help='Archivo del que se quiere realizar la recuperacion de archivos.')
	parser.add_argument('-t', '--type_file', dest= 'type_file', default=['all'], nargs='+', help ='Indica el/los formato(s) de archivos a recuperar separados por coma (zip, exe, gif, png, jpg, jpeg, all). Por defecto son todos.')
	parser.add_argument('-c','--conf', dest='conf_file', default="rvallejo_conf.conf", help='Archivo de configuracion con formatos de recuperacion. Por defecto: rvallejo_conf.conf')
	parser.add_argument('-s','--size', dest='size_file', default=None, help='Tamaño del archivo a recuperar numero[BKMG]. Ejemplo: 2K')
	
	opts = parser.parse_args()
	return opts

def type_file_formato(type_file):
	"""
	Función para parsear la lista de tipos de archivos leída, ya sea separada por comas o por espacios
	Recibe: type_file (argumento leído con -t)
	Devuelve: lista con los tipos de archivos
	"""
	if ',' in type_file[0]:
		return [i for i in type_file[0].split(',')]
	else:
		return [i for i in type_file]

def format_HF(cad):
	"""
	Función que cambia el foramto del header y footer de 0x12BC -> \x12\xBC
	Recibe: cad (header o footer)
	Devuelve: hf_final (header o footer en el formato de bytes)
	"""
	if re.search(r'0x[0-9a-f]+',cad):
		hf = cad.split('x')[-1]
		hf_final = ''
		for i in range(len(hf)):
			if i%2==0:	hf_final +='\\x'+hf[i]
			else:	hf_final += hf[i]
	return hf_final

def read_conf_file(conf_file, type_file):
	"""
	Función que lee el archivo de configuración y parsea el contenido para realizar la recuperación de archivos.
	En el archivo se tiene: tipo_de_archivo 	header	footer	size
	Recibe: conf_file (archivo que contiene los valores para la configuración), type_file (lista de tipos de archivo que se eligió recuperar)
	Devuelve: format_files (diccionario con los valores de configuración para cada tipo de archivo)
	"""
	format_files = {}
	with open(conf_file, 'rb') as conf_options:
		for line in conf_options:
			if not "#" in line:
				options = re.search(r'([a-z]+)\s*([\\a-zA-Z0-9]+)\s*([\\a-zA-Z0-9]*)\s*(([0-9]+[MGKB])*)', line, re.I)
				type_f = options.group(1)
				if type_f in type_file or 'all' in type_file:
					if type_f in format_files:	type_f = type_f + "1"
					if re.search(r'0x[0-9a-f]+', options.group(2), re.I):	header = format_HF(options.group(2))
					else:	header = options.group(2)
					if re.search(r'0x[0-9a-f]+', options.group(3), re.I):	footer = format_HF(options.group(3))
					else:	footer = options.group(3)
					format_files[type_f] = header, footer, options.group(4)  # header, footer, size
	return format_files

def sizes(start_files, size):
	"""
	Función que asigna el tamanio del tipo de archivo a buscar y lo suma al índice encontrado por el header.
	Recibe: start_files (lista de posiciones donde se encontró el header del archivo), 
			size (tamanio del archivo a buscar)
	Devuelve: size_list (lista de tamanios a partir de la posición donde fueron encontrados los headers)
	"""
	if 'B' in size: tam = int(size[:-1])
	elif 'K' in size: tam = int(size[:-1])*1024
	elif 'M' in size: tam = int(size[:-1])*1048576
	elif 'G' in size: tam = int(size[:-1])*1073741824
	sizes_list = []
	for file in start_files:
		sizes_list.append(file+tam)
	return sizes_list


def readFile(read_file, type_files, size_file):
	"""
	Función que lee el archivo del que se quieren recuperar los tipos de archivos que se soliciten.
	Recibe: read_file (archivo del que se recuperarán los archivos), type_files (lista de tipos de archivo que se eligió recuperar)
	Devuelve: guarda los archivos recuperados mediante la función save_files()
	"""
	with open(read_file, 'rb') as rfile:
		data = rfile.read()
	for key in type_files:
		start_f = [ S.start() for S in re.finditer(type_files[key][0], data, re.I) ]
		if size_file is not None:
			end_f = sizes(start_f, size_file)
		elif re.search(r'[0-9]+[MGKB]',type_files[key][1]):
			end_f = sizes(start_f, type_files[key][1])
		else:
			end_f =  [ E.end() for E in re.finditer(type_files[key][1], data, re.I) ]
		for file in range(len(start_f)):
			for f in end_f:
				if start_f[file] < f:
					output_file = str(time.time()).replace('.','_') + "_" + str(f) +"." + key
					if f == len(data):	save_files(output_file, data[start_f[file]:])
					else:	save_files(output_file, data[start_f[file]:f+1])

def save_files(of, recover):
	"""
	Función que guarda los archivos recuperados de cada tipo dea rchivo que se indicó al ejecutar el script.
	Recibe: of (nombre del archivo de salida, donde se escriben los datos recuperados)
			recover (datos correspondientes al tipo de archivo que se recupera y son extraídos del archivode recuperación
					que se indicó al ejecutar el script)
	Devuelve: escribe en un archivo el archvio recuperado y muestra un mensaje que indica su nombre.
	"""
	with open(of, 'wb') as output:
		output.write(recover)
	print "Archivo recuperado: " + of

if __name__ == '__main__':
	opts = addOptions()
	checkOptions(opts)
	type_files = type_file_formato(opts.type_file)
	search_files = read_conf_file(opts.conf_file, type_files)
	readFile(opts.read_file, search_files, opts.size_file)
