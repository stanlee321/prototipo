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

fecha = os.getenv('HOME')+'/trafficFlow/'+datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')+'_reporte.txt'

file = open(fecha,'w')
file.close()