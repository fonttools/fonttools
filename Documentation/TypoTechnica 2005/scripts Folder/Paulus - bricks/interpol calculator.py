# principe van gewichten a -- b -- c

def interPola(b,c):
	a = b**2.0/c
	return a

def interPolb(a,c):
	b = (a*c)**.5
	return b
	
def interPolc(a,b):
	c = b**2.0/a
	return c

print
for n in range(0,100):
	c = interPolb(66,66+n)
	d = interPolb(c,166)
	
	print 66+n,d
	
print interPolb(66,122)
print interPolc(66,90)