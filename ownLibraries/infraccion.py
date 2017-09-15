import datetime
from shooter import Shooter
import os
# modified

class Infraccion():
    """
    La presente clase representa un caso de infraccion, pudiendo este ser refutado o aprobado para su reporte por el programa principal a traves de un Agente Reportero o una maquina de estados
    """
    def __init__(self,indiceInicial,fps,directorioAlmacenamiento='./'):
        #self.shotter
        self.fechaYHoraDeCaptura = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self.momentum=[0,0,0]
        self.indice = [indiceInicial,0,0,0]
        

        # Constantes
        self.momentumInicialMinimo = 30
        self.momentumFinalMinimo = 20
        self.tiempoInicialMinimo = 0.4          # En segundos
        self.miFPS = fps
        self.directorioAlmacenamientoInfraccion = directorioAlmacenamiento

        # Estado
        self.estado = 1
        self.matrizEstados = [[0,0,0,0],[1,2,1,1],[2,2,3,2],[3,3,4,4],[4,4,4,4]]

        """
        Estados
        1 - Creado
        2 - Pase primera verificación
        3 - Pase segunda verificación
        4 - Pase verificación final
        5 - Listo para reportar
        0 - Descartado
        """

    def introducirPanoramaCompleto(self,indiceDelFrame,indice1,indice2,indice3,overallView = -1):
        controlCamara = 'lol'
        mensaje = ''
        capturoDato = False
        indiceEvolve1,indiceEvolve2,indiceEvolve3 = indice1,indice2,indice3
        estadoActualizado = False
        # Evoluciono la máquina de estados
        estadoAuxiliar = self.estado
        momentumActual = 0
        ##### OJO, EL PROGRAMA ACTUAL SOLO TOMA UN CAMBIO DE ESTADO POR FRAME Y SE APROPIA DEL MISMO######
        # Selecciono si una señal fue introducida
        signal = 0      # Verificar si el switch no es mejor
        if (indice3<0)&(self.estado==3):   # Señal para ir del estado 3 al 4
            signal = 3
            momentumActual = -indice3
            indiceEvolve3 = 0
            mensaje += 'Emito Senal 3 con momentum '+str(momentumActual)+'\t'
        if (indice2<0)&(self.estado==2):   # Señal para ir del estado 2 al 3
            signal = 2
            momentumActual = -indice2
            indiceEvolve2 = 0
            mensaje += 'Emito Senal 2 con momentum '+str(momentumActual)+'\t'
            # En la senial 2 se destruye el shooter si esta activo
            controlCamara = self.fechaYHoraDeCaptura
        if (indice1<0)&(self.estado==1):   # Señal para ir del estado 1 al 2
            signal = 1
            momentumActual = -indice1
            indiceEvolve1 = 0
            mensaje +=' Emito Senal 1 con momentum '+str(momentumActual)+'\t'
            # Se activa el shooter
            controlCamara = 'TURN OFF'
        # Evoluciono el estado actual del sistema
        self.estado = self.matrizEstados[self.estado][signal]
        # Si hubo un cambio en el estado determino que tome el dato y me apropio del mismo:
        # Tambien solo si tome un dato lo actualizo en el indice correspondiente:

        if estadoAuxiliar != self.estado:
            estadoActualizado = True
            capturoDato = True
            self.indice[signal] = indiceDelFrame
            self.momentum[signal-1] = momentumActual
            mensaje +='Evolucione de estado exitosamente de: '+str(estadoAuxiliar)+' a '+str(self.estado)+'\t'
        # Tomo algunos recaudos para evitar falsos positivos

        # Si recien llegue al estado 2, lo descarto a menos que tenga suficiente momentum y tiempo
        if (self.estado == 2)&estadoActualizado:
            if (self.momentum[0]<self.momentumInicialMinimo):
                self.estado=0
                mensaje +='Descarto infraccion por momentum insuficiente: '+str(self.momentum[0])+' tiempo: '+ str(self.indice[1]-self.indice[0])+' fps: '+str(self.miFPS)+'\t'
            if ((self.indice[1]-self.indice[0])<self.tiempoInicialMinimo*self.miFPS):
                self.estado=0
                mensaje +='Descarto infraccion por tiempo:' +str(self.indice[1]-self.indice[0])+' fps: '+str(self.miFPS)+'\t'
        # Si recien actualice el dato y llegue al estado cuatro, verifico el momentum minimo, de lo contrario descarto:
        if (self.estado == 4)&estadoActualizado:
            mensaje+= 'Infraccion confirmada, momentum de llegada:'+str(self.momentum[2])+' tiempo: '+str(self.indice[1]-self.indice[0])+' fps: '+str(self.miFPS)+'\t'
            if self.momentum[2]<=self.momentumFinalMinimo:
                self.estado=0
                mensaje+='Descarto infraccion por momentum insuficiente'+'\t'
        # Experimental, si el panorama general indica que no hay movimiento en ningun area se descarta el caso
        # Otros descartes aqui
        # Si llegue al estado 2 y recibo un nuevo pulso de creacion de infraccion reseteo la infraccion
        if (self.estado == 2)&(indice1==1):
            self.momentum=[0,0,0]   # Reseteo momentum
            self.indice = [indiceDelFrame,0,0,0]
            
            # Estado
            self.estado = 1         # Como si el caso se hubiera creado recien



        # retorno un valor especificando si el utilice el valor que tome o no
        return controlCamara, capturoDato, indiceEvolve1,indiceEvolve2,indiceEvolve3, mensaje

    def obtenerEstado(self):
        return self.estado

    def obtenerIndices(self):
        return [self.indice[0], self.indice[1], self.indice[2], self.indice[3]]

        
