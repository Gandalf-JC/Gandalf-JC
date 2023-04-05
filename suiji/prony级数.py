# Shear deformation--Burgers model
# Volumetric deformation--Elastic
# Transform Burgers model into Prony series
# E1 Young's modulus of the Hookean spring (MPa)
# E2 Young's modulus of the Kelvin Unit (MPa)
# n1 Viscosity Coefficient of the seperate dashpot (MPa.s)
# n2 Viscosity Coefficient of the Kelvin Unit (MPa.s)
# v0 Poisson's ratio

E1 = 87.04
E2 = 20.87
n1 = 5.7e4
n2 = 1.44e4
v0 = 0.3

# Laplace transformation
G1 = E1 / (2 * (1 + v0))
G2 = E2 / (2 * (1 + v0))
p1 = n1 / G1 + (n1 + n2) / G2
p2 = (n1 * n2) / (G1 * G2)
q1 = 2 * n1
q2 = 2 * n1 * n2 / G2
a = (p1 + pow(p1 ** 2 - 4 * p2, 0.5)) / (2 * p2)
b = (p1 - pow(p1 ** 2 - 4 * p2, 0.5)) / (2 * p2)
print('a=', a, 'b=', b)

# Transform shear modulus into Prony series
g1 = (G2/n2-b) / (a-b)
t1 = 1 / b
g2 = -(G2/n2-a) / (a-b)
t2 = 1 / a
print("g1=", g1)
print("g2=", g2)
print("t1=", t1)
print("t2=", t2)
