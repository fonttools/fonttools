/*
**  Copyright 1996-2001 by Letterror: Just van Rossum, The Netherlands.
**	
**  Open source.
**
**  Module implementing the eexec and charstring encryption algorithm as 
**  used by PostScript Type 1 fonts.
**	
*/

#include "Python.h"
#include <ctype.h>

static PyObject *ErrorObject;

/* ----------------------------------------------------- */

static char eexec_decrypt__doc__[] =
""
;

static PyObject *
eexec_decrypt(PyObject *self, PyObject *args)
{
	PyObject *_res = NULL;
	unsigned short R;
	int tempR;  /* can't portably use unsigned shorts between Python versions */
	unsigned short c1 = 52845;
	unsigned short c2 = 22719;
	unsigned char * inbuf;
	unsigned char * outbuf;
	unsigned long counter, insize;
	
	if (!PyArg_ParseTuple(args, "s#i", &inbuf, &insize, &tempR))
		return NULL;
	
	R = (unsigned short)tempR;
	
	if ((outbuf = malloc(insize)) == NULL)
	{
		PyErr_NoMemory();
		return NULL;
	}
	for(counter = 0;counter < insize; counter++) {
		outbuf[counter] = (inbuf[counter] ^ (R>>8));
		R = (inbuf[counter] + R) * c1 + c2;
	}
	
	_res = Py_BuildValue("s#l", outbuf, insize, (unsigned long)R);
	free(outbuf);
	return _res;
}

static char eexec_encrypt__doc__[] =
""
;

static PyObject *
eexec_encrypt(PyObject *self, PyObject *args)
{
	PyObject *_res = NULL;
	unsigned short R;
	int tempR;  /* can't portably use unsigned shorts between Python versions */
	unsigned short c1 = 52845;
	unsigned short c2 = 22719;
	unsigned char * inbuf;
	unsigned char * outbuf;
	unsigned long counter, insize;
	
	if (!PyArg_ParseTuple(args, "s#i", &inbuf, &insize, &tempR))
		return NULL;
	
	R = (unsigned short)tempR;
	
	if ((outbuf = malloc(insize)) == NULL)
	{
		PyErr_NoMemory();
		return NULL;
	}
	for(counter = 0;counter < insize; counter++) {
		outbuf[counter] = (inbuf[counter] ^ (R>>8));
		R = (outbuf[counter] + R) * c1 + c2;
	}
	
	_res = Py_BuildValue("s#l", outbuf, insize, (unsigned long)R);
	free(outbuf);
	return _res;
}

static char eexec_hexString__doc__[] =
""
;

static PyObject *
eexec_hexString(PyObject *self, PyObject *args)
{
	PyObject *_res = NULL;
	unsigned char * inbuf;
	unsigned char * outbuf;
	static const unsigned char hexchars[] = "0123456789ABCDEF";
	unsigned long i, insize;
	
	if (!PyArg_ParseTuple(args, "s#", &inbuf, &insize))
		return NULL;
	
	outbuf = malloc(2 * insize);
	if (outbuf == NULL) {
		PyErr_NoMemory();
		return NULL;
	}
	
	for (i = 0; i < insize; i++) {
		outbuf[2 * i] = hexchars[(inbuf[i] >> 4) & 0xF];
		outbuf[2 * i + 1] = hexchars[inbuf[i] & 0xF];
	}
	_res = Py_BuildValue("s#", outbuf, 2 * insize);
	free(outbuf);
	return _res;
}


#define HEX2DEC(c) ((c) >= 'A' ? ((c) - 'A' + 10) : ((c) - '0'))

static char eexec_deHexString__doc__[] =
""
;

static PyObject *
eexec_deHexString(PyObject *self, PyObject *args)
{
	PyObject *_res = NULL;
	unsigned char * inbuf;
	unsigned char * outbuf;
	unsigned char c1, c2;
	unsigned long insize, i;
	
	if (!PyArg_ParseTuple(args, "s#", &inbuf, &insize))
		return NULL;
	
	if (insize % 2) {
		PyErr_SetString(ErrorObject, "hex string must have even length");
		return NULL;
	}
	
	outbuf = malloc(insize / 2);
	if (outbuf == NULL) {
		PyErr_NoMemory();
		return NULL;
	}
	
	for ( i = 0; i < insize; i += 2) {
		c1 = toupper(inbuf[i]);
		c2 = toupper(inbuf[i+1]);
		if (!isxdigit(c1) || !isxdigit(c1)) {
			PyErr_SetString(ErrorObject, "non-hex character found");
			goto error;
		}
		outbuf[i/2] = (HEX2DEC(c2)) | (HEX2DEC(c1) << 4);
	}
	_res = Py_BuildValue("s#", outbuf, insize / 2);
error:
	free(outbuf);
	return _res;
}

/* List of methods defined in the module */

static struct PyMethodDef eexec_methods[] = {
	{"decrypt",	(PyCFunction)eexec_decrypt,		METH_VARARGS,	eexec_decrypt__doc__},
	{"encrypt",	(PyCFunction)eexec_encrypt,		METH_VARARGS,	eexec_encrypt__doc__},
 	{"hexString",	(PyCFunction)eexec_hexString,		METH_VARARGS,	eexec_hexString__doc__},
	{"deHexString",	(PyCFunction)eexec_deHexString,	METH_VARARGS,	eexec_deHexString__doc__},
	{NULL, (PyCFunction)NULL, 0, NULL}		/* sentinel */
};


/* Initialization function for the module (*must* be called initeexec) */

static char eexec_module_documentation[] = 
""
;

void initeexecOp(void); /* prototype to shut up the compiler */

void initeexecOp(void)
{
	PyObject *m, *d;

	/* Create the module and add the functions */
	m = Py_InitModule4("eexecOp", eexec_methods,
		eexec_module_documentation,
		(PyObject*)NULL,PYTHON_API_VERSION);

	/* Add some symbolic constants to the module */
	d = PyModule_GetDict(m);
	ErrorObject = PyString_FromString("eexec.error");
	PyDict_SetItemString(d, "error", ErrorObject);

	/* Check for errors */
	if (PyErr_Occurred())
		Py_FatalError("can't initialize module eexec");
}

