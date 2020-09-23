from pyOER import ISS

data = ISS('Reshma4F')
data.plot(show=False)
data._active[0].AddMassLines([16, 18])
data.show()
