#!/usr/bin/python
# -*- coding: utf-8 -*-

# Vallejo Fernández Rafael Alejandro
# Practica 2. Programa particiones
from sys import exit,argv
from binascii import unhexlify

def readDD(device):
	"""
	Función que lee el contenido del dispositivo que recibe como argumento. Lee la parte relativa
	a los 512 bytes del MBR y almacena los elementos de la estructura MBR en un diccionario para 
	manejarlo después y realizar la creación de las particiones.
	Recibe: device (string) -> dispositivo o imagen de disco del que se crearán sus particiones.
	Devuelve: strcut_mbr (diccionario) -> tiene los 3 elementos de la estructura MBR
	"""
	with open(device, 'rb') as dd:
		mbr = dd.read(512)
		mbr_hex = [ str(hex(ord(byte)).split('x')[-1]).zfill(2) for byte in mbr ]
	struct_mbr = { 0 : mbr_hex[:446],  # estructura mbr
				   1 : mbr_hex[446:446+64],  # tabla de particiones
				   2 : mbr_hex[446+64:] # fin mbr - numero magico
	}
	struct_mbr[2] = ["55","aa"]
	return struct_mbr

def writeDD(struct_mbr, dev):
	"""
	Función que escribe en el dispositivo que recibe como argumento las particiones que se hayan 
	indicado durante la ejecución del script.
	Recibe: struct_mbr (diccionario) -> elementos de la estructura MBR
			dev (string) -> dispositivo o imagen de disco al que se crearán sus particiones
	Return: particion creada en dev
	"""
	with open(dev, 'wb') as dd:
		mbr = ""
		for key in struct_mbr:
			for val in struct_mbr[key]:
				if len(val) == 3: val = val[1:]
				mbr += unhexlify(val)
		dd.write(mbr)

def get_size():
	"""
	Función que pide el tamaño de la partición y lo devuelve en formato little endian 
	para crear la partición. Lee en KiB, MiB o GiB.
	Recibe: nada
	Devuelve: sizeLE (lista) -> los valores en little endian para agregarse a la partición
	"""
	while True:
		size = raw_input("size{K,M,G}: ")
		if size[-1] in ['K','M','G']: break
	if 'K' in size:  # 1 KiB = 1024 bytes
		size = int(size[:-1]) * 1024
	elif 'M' in size:  # 1 MiB = 1048576 bytes
		size = int(size[:-1]) * 1048576
	elif 'G' in size:  # 1 GiB = 1073741824 bytes
		size = int(size[:-1]) * 1073741824
	size = str(hex(size/512)).split('x')[-1].zfill(8)
	sizeLE = []
	tmp = 0
	for i in range(4):  # se separa por cada byte
		sizeLE.append(size[tmp:tmp+2])
		tmp += 2
	return sizeLE[::-1]  # se invierte para tenerlo en little endian

def set_size(partition, sizeLE):
	"""
	Función que asigna a los Bytes 12-15 el tamaño de la partición.
	Recibe: partition (lista) -> lista de 16 bytes de la partición que se está creando
			sizeLE (lista) -> lista que contiene los valores que se asignarán a los 
								bytes 12-15 para indicar el tamaño de la partición
	Devuelve: partition (lista) -> lista de 16 bytes con los bytes 12-15 asignados
	"""
	partition[12:] = sizeLE
	return partition

def starting_sector(partition, sizeLE, sizeLE_1 = []):
	"""
	Función que asigna a los bytes 8-11 el sector de inicio.
	Recibe: partition (lista) -> lista de 16 bytes de la partición que se está creando
			sizeLE (lista) -> lista que contiene los valores que se asignarán a los 
								bytes 8-11 para indicar el sector de inicio
			sizeLE_1 (lista) -> lista que contiene los valores que se sumará a los 
								bytes 12-15 para indicar el sector de inicio (cuando es
								una partici+on 2-4)
	Devuelve: partition (lista) -> lista de 16 bytes con los bytes 8-11 asignados
	"""
	if sizeLE_1 == []:
		partition[8:12] = ['00','08','00','00']  # partición de inicio por defecto 2048 en decimal
	else:
		partition[8:12] = map(lambda x, y: str(hex(int(x,16) + int(y,16))).split('x')[-1].zfill(2), sizeLE, sizeLE_1) 
	return partition

def get_partitions(partition_table):
	"""
	Función para asignar los 16 bytes a cada partición correspondiente y poder crear el tipo de partición
	que se indique después.
	Recibe: partition_table (lista) -> contiene los 64 bytes correspondientes a las particiones
	Devuelve: partitions (diccionario) -> los 16 bytes asignados a cada una de las 4 particiones
	"""
	partitions = { 1 : partition_table[:16],  # particion 1
				   2 : partition_table[16:32], # particion 2
				   3 : partition_table[32:48], # particion 3
				   4 : partition_table[48:], # particion 4
	}
	return partitions

def update_mbr(num_part, partition, partition_table):
	"""
	Función que actualiza los valores de la partición que se indique para escribirse en el 
	dispositivo o disco posteriormente.
	Recibe: num_part (int) -> indica el número de la partición
			partition (lista) -> lista de 16 bytes de la partición que se está creando
			partition_table (lista) -> contiene los 64 bytes correspondientes a las particiones
	Devuelve: partition_table (lista) -> los 64 bytes de las particiones actualizado
	"""
	if num_part == 1: inicio, fin = 0, 16
	elif num_part == 2: inicio, fin = 16, 32
	elif num_part == 3: inicio, fin = 32, 48
	elif num_part == 4: inicio, fin = 48, 64
	partition_table[inicio:fin] = partition
	return partition_table
	
def set_partition():
	"""
	Función para pedir al usuario el sistema de archivos que se creará.
	Recibe: nada
	Devuelve: k, filesystem[k] (tupla) -> el valor correspondiente al tipo de partición,
											el nombre del sistema de archivos
	"""
	filesystem = {	"07" : "HPFS/NTFS/exFAT", 
					"82" : "Linux swap",
					"83" : "Linux",
					"a5" : "FreeBSD",
					"a6" : "OpenBSD"
	}
	while True:
		print "Sistemas de archivos disponibles:"
		for key in filesystem:	print "\t" + key + " " + filesystem[key]
		partition = raw_input("Selecciona el sistema de archivos [Valor|Nombre]: ")
		for k in filesystem:
			if partition == k or partition == filesystem[k]:
				return k, filesystem[k]

def partition_type():
	"""
	Función que pide al usuario la partición que se creara (primary o extended).
	Recibe: nada
	Devuelve: partition (tupla) -> el valor correspondiente al tipo de partición,
									el nombre del sistema de archivos 
	"""
	part_type = raw_input("p primary\ne extended\nq exit\nSelect (default p): ")
	if part_type == "q": exit()
	elif part_type == "" or part_type != "e": part_type = "p"
	if part_type == "p":	partition = set_partition()
	elif part_type == "e":	partition = "05", "Extended"
	return partition

def partition_number():
	"""
	Función que pide al usuario el número de la partción que será creada.
	Recibe: nada
	Devuelve: part_num (int) -> número de la partición seleccionada
	"""
	while True:
		part_num = raw_input("Partition number (1-4): ")
		part_num = int(part_num)
		if part_num in range(1,5):	break
	return part_num

def write_partitions(partition, fs_value):
	"""
	Función que asigna el tipo de partición que se haya indicado a la partición correspondiente.
	"""
	partition[4] = fs_value
	return partition

if __name__ == '__main__':
	struct_mbr = readDD(argv[1])
	partitions = get_partitions(struct_mbr[1])
	while True:
		fs_value, fs_name = partition_type()
		part_num = partition_number()
		tam = get_size()

		print("NOTA: Se deben guardar los cambios por cada partición que se cree.")
		opcion = raw_input("Guardar [w], salir [q], regresar [ENTER]: ")
		if opcion == "w":
			if part_num == 1:
				partitions[part_num] = starting_sector(partitions[part_num], tam)
			else:
				partitions[part_num] = starting_sector(partitions[part_num], tam, partitions[part_num-1][8:12])
			partitions[part_num] = set_size(partitions[part_num], tam)
			partitions[part_num] = write_partitions(partitions[part_num], fs_value)
			struct_mbr[1] = update_mbr(part_num, partitions[part_num], struct_mbr[1])
			writeDD(struct_mbr, argv[1])
			print "Se creo en la particion " + str(part_num) + "el tipo de particion " + fs_name
		elif opcion == "q":	break
