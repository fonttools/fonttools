import sys, types

try:
	import describeFunction
except ImportError:
	print "(Can't check interfaces, describeFunction could not be imported)"
	describeFunction = None


def collectMethodNames(theClass, names=None):
	if names is None:
		names = {}
	names.update(theClass.__dict__)
	for baseClass in theClass.__bases__:
		collectMethodNames(baseClass, names)
	names = names.keys()
	names.sort()
	return names
	

def checkClass(moduleName, theClass):
	className = theClass.__name__
	if theClass.__module__ <> moduleName:
		return
	if not hasattr(theClass, "__implements__"):
		print "Interfaceless class: %s (%s)" % (className, theClass.__module__)
		return
	interfaces = theClass.__implements__
	if interfaces is None:
		return
	if isinstance(interfaces, types.ClassType):
		interfaces = (interfaces,)
	gotOne = 0
	for interface in interfaces:
		methodNames = collectMethodNames(interface)
		methodNames.sort()
		for methodName in methodNames:
			method = getattr(interface, methodName)
			if not isinstance(method, types.UnboundMethodType):
				continue
			method = method.im_func
			if not hasattr(theClass, methodName):
				if not gotOne:
					print "\nWarnings for module %s\n" % moduleName
					gotOne = 1
				print "class %s misses required method:\n  %s" % (className, describeFunction.describe(method))
				continue
			method2 = getattr(theClass, methodName).im_func
			argList = describeFunction._describe(method)
			argList2 = describeFunction._describe(method2)
			if len(argList2) < len(argList):
				if not gotOne:
					print "\nWarnings for module %s\n" % moduleName
					gotOne = 1
				print "Method doesn't have enough arguments:"
				print "  interface:      %s.%s" % (className, describeFunction.describe(method))
				print "  implementation: %s.%s" % (className, describeFunction.describe(method2))
				continue
			for i in range(len(argList)):
				if argList[i] <> argList2[i]:
					if not gotOne:
						print "\nWarnings for module %s\n" % moduleName
						gotOne = 1
					print "Method has different arguments:"
					print "  interface:      %s.%s" % (className, describeFunction.describe(method))
					print "  implementation: %s.%s" % (className, describeFunction.describe(method2))
					break
			for arg in argList2[len(argList):]:
				if type(arg) == types.StringType:
					if not gotOne:
						print "\nWarnings for module %s\n" % moduleName
						gotOne = 1
					print "Additional argument(s) should have default value(s):"
					print "  interface:      %s.%s" % (className, describeFunction.describe(method))
					print "  implementation: %s.%s" % (className, describeFunction.describe(method2))
					break



def checkInterface(moduleName):
	if describeFunction is None:
		return
	items = sys.modules[moduleName].__dict__.items()
	items.sort()
	for name, value in items:
		if not isinstance(value, types.ClassType):
			continue
		checkClass(moduleName, value)

