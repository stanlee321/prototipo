#!/usr/bin/python3

import os
import sys
import cv2
import time
import psutil
import logging
import datetime
import numpy as np

from ownLibraries.irswitch import IRSwitch
from ownLibraries.mireporte import MiReporte
from ownLibraries.visualizacion import Acetato
from ownLibraries.herramientas import total_size
from ownLibraries.videostream import VideoStream
from ownLibraries.semaforov2 import CreateSemaforo
from ownLibraries.determinacionCruces import PoliciaInfractor

print(os.__file__)
#/usr/lib/python3.5/os.py
print(cv2.__file__)
#/usr/local/lib/python3.5/dist-packages/cv2.cpython-35m-x86_64-linux-gnu.so
print(psutil.__file__)
#/usr/lib/python3/dist-packages/psutil/__init__.py
print(np.__file__)
#/home/alvarohurtado/.local/lib/python3.5/site-packages/numpy/__init__.py

fecha = os.getenv('HOME')+'/trafficFlow/'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_reporte.txt'

file = open(fecha,'w')
file.close()
