import numpy as np

class AnalisisOnda():
	def __init__(self,):
		"""
		This class uses digital signal processing to clean data from the artificial vision
		"""
		# Variables para los ultimos valores
		self.MagnitudesVelocidad = np.array((0.0,0.0,0.0,0.0))
		self.MagnitudesVelocidadFiltradas = np.array((0.0,0.0,0.0,0.0))
		# Se definen las constantes
		self.a_coeff = np.array(( 1.,-2.37409474,1.92935567,-0.53207537))# AGRESSIVE
		self.b_coeff = np.array(( 0.00289819,0.00869458,0.00869458,0.00289819))
		#self.a_coeff = np.array(( 1.,-1.45424359,0.57406192,0,0,0)) #0.5 hz
		#self.b_coeff = np.array((0.02995458,0.05990916,0.02995458,0,0,0))
		#self.a_coeff = np.array((1.,-1.1429805,0.4128016,0,0,0)) #0.8hz
		#self.b_coeff = np.array((0.06745527, 0.13491055, 0.06745527,0,0,0))
		self.velocidadesSinNegativo = np.array((0.0,0.0))
		self.pulsosAutomoviles_funcionSigno = np.array((0.0,0.0))

		self.minimoValorVelocidad = 12
		self.momentumActual = 0
		self.indiceActual = 0


	def obtenerOndaFiltrada(self, value):
		"""
		Filter, get flanc and integrate
		"""
		self.MagnitudesVelocidad[3] = self.MagnitudesVelocidad[2]
		self.MagnitudesVelocidad[2] = self.MagnitudesVelocidad[1]
		self.MagnitudesVelocidad[1] = self.MagnitudesVelocidad[0]
		self.MagnitudesVelocidad[0] = value

		self.MagnitudesVelocidadFiltradas[3] = self.MagnitudesVelocidadFiltradas[2]
		self.MagnitudesVelocidadFiltradas[2] = self.MagnitudesVelocidadFiltradas[1]
		self.MagnitudesVelocidadFiltradas[1] = self.MagnitudesVelocidadFiltradas[0]
		self.MagnitudesVelocidadFiltradas[0] = - self.a_coeff[1]*self.MagnitudesVelocidadFiltradas[1]-self.a_coeff[2]*self.MagnitudesVelocidadFiltradas[2]-self.a_coeff[3]*self.MagnitudesVelocidadFiltradas[3]+self.b_coeff[0]*self.MagnitudesVelocidad[0]+self.b_coeff[1]*self.MagnitudesVelocidad[1]+self.b_coeff[2]*self.MagnitudesVelocidad[2]+self.b_coeff[3]*self.MagnitudesVelocidad[3]

		if self.MagnitudesVelocidadFiltradas[0] <= self.minimoValorVelocidad:
			self.velocidadesSinNegativo[1] = self.velocidadesSinNegativo[0]
			self.velocidadesSinNegativo[0] = 0
		else:
			self.velocidadesSinNegativo[1] = self.velocidadesSinNegativo[0]
			self.velocidadesSinNegativo[0] = self.MagnitudesVelocidadFiltradas[0]

		self.pulsosAutomoviles_funcionSigno[1] = self.pulsosAutomoviles_funcionSigno[0]
		self.pulsosAutomoviles_funcionSigno[0] = np.sign(self.velocidadesSinNegativo[0]-self.velocidadesSinNegativo[1])

		self.momentumActual += self.velocidadesSinNegativo[0]
		flancoDeSubida = self.pulsosAutomoviles_funcionSigno[0]-self.pulsosAutomoviles_funcionSigno[1]
		self.indiceActual = 0
		# En el flanco de subida se resetea el momentum
		if (flancoDeSubida > 0)&(self.pulsosAutomoviles_funcionSigno[0]==1):
			self.indiceActual = 1
		# En el flanco de bajada se resetea el momentum a -1 simbolizando que no hay automovil

		if (flancoDeSubida > 0):
			self.momentumActual = 0

		if (flancoDeSubida < 0):
			self.indiceActual = -self.momentumActual//10

		return [self.MagnitudesVelocidadFiltradas[0], self.indiceActual]