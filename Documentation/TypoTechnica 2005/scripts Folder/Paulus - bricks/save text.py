
path = "OS X:Users:paulus:Desktop:testfile.txt"

f = open(path, "r+")
f.seek(0,2)
f.write("hello!\tjajaja!\ren nu.")
f.close()
