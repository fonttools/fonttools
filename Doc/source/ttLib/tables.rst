######
tables
######

This folder is a subpackage of :py:mod:`fontTools.ttLib`. Each module here is a
specialized TT/OT table converter: they can convert raw data
to Python objects and vice versa. Usually you don't need to
use the modules directly: they are imported and used
automatically when needed by :py:mod:`fontTools.ttLib`.

If you are writing you own table converter the following is
important.

The modules here have pretty strange names: this is due to the
fact that we need to map TT table tags (which are case sensitive)
to filenames (which on Mac and Win aren't case sensitive) as well
as to Python identifiers. The latter means it can only contain
[A-Za-z0-9_] and cannot start with a number.

:py:mod:`fontTools.ttLib` provides functions to expand a tag into the format used here::

    >>> from fontTools import ttLib
    >>> ttLib.tagToIdentifier("FOO ")
    'F_O_O_'
    >>> ttLib.tagToIdentifier("cvt ")
    '_c_v_t'
    >>> ttLib.tagToIdentifier("OS/2")
    'O_S_2f_2'
    >>> ttLib.tagToIdentifier("glyf")
    '_g_l_y_f'
    >>>

And vice versa::

    >>> ttLib.identifierToTag("F_O_O_")
    'FOO '
    >>> ttLib.identifierToTag("_c_v_t")
    'cvt '
    >>> ttLib.identifierToTag("O_S_2f_2")
    'OS/2'
    >>> ttLib.identifierToTag("_g_l_y_f")
    'glyf'
    >>>

Eg. the 'glyf' table converter lives in a Python file called::

	_g_l_y_f.py

The converter itself is a class, named "table_" + expandedtag. Eg::


	class table__g_l_y_f:
		etc.


Note that if you _do_ need to use such modules or classes manually,
there are two convenient API functions that let you find them by tag::

    >>> ttLib.getTableModule('glyf')
    <module 'ttLib.tables._g_l_y_f'>
    >>> ttLib.getTableClass('glyf')
    <class ttLib.tables._g_l_y_f.table__g_l_y_f at 645f400>
    >>

You must subclass from :py:mod:`fontTools.ttLib.tables.DefaultTable.DefaultTable`. It provides some default
behavior, as well as a constructor method (__init__) that you don't need to
override.

Your converter should minimally provide two methods::


    class table_F_O_O_(DefaultTable.DefaultTable): # converter for table 'FOO '

        def decompile(self, data, ttFont):
            # 'data' is the raw table data. Unpack it into a
            # Python data structure.
            # 'ttFont' is a ttLib.TTfile instance, enabling you to
            # refer to other tables. Do ***not*** keep a reference to
            # it: it will cause a circular reference (ttFont saves
            # a reference to us), and that means we'll be leaking
            # memory. If you need to use it in other methods, just
            # pass it around as a method argument.

        def compile(self, ttFont):
            # Return the raw data, as converted from the Python
            # data structure.
            # Again, 'ttFont' is there so you can access other tables.
            # Same warning applies.


If you want to support TTX import/export as well, you need to provide two
additional methods::


	def toXML(self, writer, ttFont):
		# XXX

	def fromXML(self, (name, attrs, content), ttFont):
		# XXX



.. automodule:: fontTools.ttLib.tables
   :inherited-members:
   :members:
   :undoc-members:

_a_n_k_r
--------

.. automodule:: fontTools.ttLib.tables._a_n_k_r
   :inherited-members:
   :members:
   :undoc-members:

_a_v_a_r
--------

.. automodule:: fontTools.ttLib.tables._a_v_a_r
   :inherited-members:
   :members:
   :undoc-members:

_b_s_l_n
--------

.. automodule:: fontTools.ttLib.tables._b_s_l_n
   :inherited-members:
   :members:
   :undoc-members:

_c_i_d_g
--------

.. automodule:: fontTools.ttLib.tables._c_i_d_g
   :inherited-members:
   :members:
   :undoc-members:

_c_m_a_p
--------

.. automodule:: fontTools.ttLib.tables._c_m_a_p
   :inherited-members:
   :members:
   :undoc-members:

_c_v_a_r
--------

.. automodule:: fontTools.ttLib.tables._c_v_a_r
   :inherited-members:
   :members:
   :undoc-members:

_c_v_t
------

.. automodule:: fontTools.ttLib.tables._c_v_t
   :inherited-members:
   :members:
   :undoc-members:

_f_e_a_t
--------

.. automodule:: fontTools.ttLib.tables._f_e_a_t
   :inherited-members:
   :members:
   :undoc-members:

_f_p_g_m
--------

.. automodule:: fontTools.ttLib.tables._f_p_g_m
   :inherited-members:
   :members:
   :undoc-members:

_f_v_a_r
--------

.. automodule:: fontTools.ttLib.tables._f_v_a_r
   :inherited-members:
   :members:
   :undoc-members:

_g_a_s_p
--------

.. automodule:: fontTools.ttLib.tables._g_a_s_p
   :inherited-members:
   :members:
   :undoc-members:


_g_c_i_d
--------

.. automodule:: fontTools.ttLib.tables._g_c_i_d
   :inherited-members:
   :members:
   :undoc-members:

_g_l_y_f
--------

.. automodule:: fontTools.ttLib.tables._g_l_y_f
   :inherited-members:
   :members:
   :undoc-members:

_g_v_a_r
--------

.. automodule:: fontTools.ttLib.tables._g_v_a_r
   :inherited-members:
   :members:
   :undoc-members:

_h_d_m_x
--------

.. automodule:: fontTools.ttLib.tables._h_d_m_x
   :inherited-members:
   :members:
   :undoc-members:

_h_e_a_d
--------

.. automodule:: fontTools.ttLib.tables._h_e_a_d
   :inherited-members:
   :members:
   :undoc-members:

_h_h_e_a
--------

.. automodule:: fontTools.ttLib.tables._h_h_e_a
   :inherited-members:
   :members:
   :undoc-members:

_h_m_t_x
--------

.. automodule:: fontTools.ttLib.tables._h_m_t_x
   :inherited-members:
   :members:
   :undoc-members:

_k_e_r_n
--------

.. automodule:: fontTools.ttLib.tables._k_e_r_n
   :inherited-members:
   :members:
   :undoc-members:

_l_c_a_r
--------

.. automodule:: fontTools.ttLib.tables._l_c_a_r
   :inherited-members:
   :members:
   :undoc-members:

_l_o_c_a
--------

.. automodule:: fontTools.ttLib.tables._l_o_c_a
   :inherited-members:
   :members:
   :undoc-members:

_l_t_a_g
--------

.. automodule:: fontTools.ttLib.tables._l_t_a_g
   :inherited-members:
   :members:
   :undoc-members:

_m_a_x_p
--------

.. automodule:: fontTools.ttLib.tables._m_a_x_p
   :inherited-members:
   :members:
   :undoc-members:

_m_e_t_a
--------

.. automodule:: fontTools.ttLib.tables._m_e_t_a
   :inherited-members:
   :members:
   :undoc-members:

_m_o_r_t
--------

.. automodule:: fontTools.ttLib.tables._m_o_r_t
   :inherited-members:
   :members:
   :undoc-members:


_m_o_r_x
--------

.. automodule:: fontTools.ttLib.tables._m_o_r_x
   :inherited-members:
   :members:
   :undoc-members:

_n_a_m_e
--------

.. automodule:: fontTools.ttLib.tables._n_a_m_e
   :inherited-members:
   :members:
   :undoc-members:

_o_p_b_d
--------

.. automodule:: fontTools.ttLib.tables._o_p_b_d
   :inherited-members:
   :members:
   :undoc-members:

_p_o_s_t
--------

.. automodule:: fontTools.ttLib.tables._p_o_s_t
   :inherited-members:
   :members:
   :undoc-members:

_p_r_e_p
--------

.. automodule:: fontTools.ttLib.tables._p_r_e_p
   :inherited-members:
   :members:
   :undoc-members:


_p_r_o_p
--------

.. automodule:: fontTools.ttLib.tables._p_r_o_p
   :inherited-members:
   :members:
   :undoc-members:

_s_b_i_x
--------

.. automodule:: fontTools.ttLib.tables._s_b_i_x
   :inherited-members:
   :members:
   :undoc-members:

_t_r_a_k
--------

.. automodule:: fontTools.ttLib.tables._t_r_a_k
   :inherited-members:
   :members:
   :undoc-members:

_v_h_e_a
--------

.. automodule:: fontTools.ttLib.tables._v_h_e_a
   :inherited-members:
   :members:
   :undoc-members:

_v_m_t_x
--------

.. automodule:: fontTools.ttLib.tables._v_m_t_x
   :inherited-members:
   :members:
   :undoc-members:

asciiTable
----------

.. automodule:: fontTools.ttLib.tables.asciiTable
   :inherited-members:
   :members:
   :undoc-members:

B_A_S_E_
--------

.. automodule:: fontTools.ttLib.tables.B_A_S_E_
   :inherited-members:
   :members:
   :undoc-members:

BitmapGlyphMetrics
------------------

.. automodule:: fontTools.ttLib.tables.BitmapGlyphMetrics
   :inherited-members:
   :members:
   :undoc-members:

C_B_D_T_
--------

.. automodule:: fontTools.ttLib.tables.C_B_D_T_
   :inherited-members:
   :members:
   :undoc-members:

C_B_L_C_
--------

.. automodule:: fontTools.ttLib.tables.C_B_L_C_
   :inherited-members:
   :members:
   :undoc-members:

C_F_F_
------

.. automodule:: fontTools.ttLib.tables.C_F_F_
   :inherited-members:
   :members:
   :undoc-members:

C_F_F__2
--------

.. automodule:: fontTools.ttLib.tables.C_F_F__2
   :inherited-members:
   :members:
   :undoc-members:

C_O_L_R_
--------

.. automodule:: fontTools.ttLib.tables.C_O_L_R_
   :inherited-members:
   :members:
   :undoc-members:

C_P_A_L_
--------

.. automodule:: fontTools.ttLib.tables.C_P_A_L_
   :inherited-members:
   :members:
   :undoc-members:

D_S_I_G_
--------

.. automodule:: fontTools.ttLib.tables.D_S_I_G_
   :inherited-members:
   :members:
   :undoc-members:

DefaultTable
------------

.. automodule:: fontTools.ttLib.tables.DefaultTable
   :inherited-members:
   :members:
   :undoc-members:

E_B_D_T_
--------

.. automodule:: fontTools.ttLib.tables.E_B_D_T_
   :inherited-members:
   :members:
   :undoc-members:

E_B_L_C_
--------

.. automodule:: fontTools.ttLib.tables.E_B_L_C_
   :inherited-members:
   :members:
   :undoc-members:

F__e_a_t
--------

.. automodule:: fontTools.ttLib.tables.F__e_a_t
   :inherited-members:
   :members:
   :undoc-members:


F_F_T_M_
--------

.. automodule:: fontTools.ttLib.tables.F_F_T_M_
   :inherited-members:
   :members:
   :undoc-members:


G__l_a_t
--------

.. automodule:: fontTools.ttLib.tables.G__l_a_t
   :inherited-members:
   :members:
   :undoc-members:

G__l_o_c
--------

.. automodule:: fontTools.ttLib.tables.G__l_o_c
   :inherited-members:
   :members:
   :undoc-members:

G_D_E_F_
--------

.. automodule:: fontTools.ttLib.tables.G_D_E_F_
   :inherited-members:
   :members:
   :undoc-members:

G_M_A_P_
--------

.. automodule:: fontTools.ttLib.tables.G_M_A_P_
   :inherited-members:
   :members:
   :undoc-members:

G_P_K_G_
--------

.. automodule:: fontTools.ttLib.tables.G_P_K_G_
   :inherited-members:
   :members:
   :undoc-members:

G_P_O_S_
--------

.. automodule:: fontTools.ttLib.tables.G_P_O_S_
   :inherited-members:
   :members:
   :undoc-members:

G_S_U_B_
--------

.. automodule:: fontTools.ttLib.tables.G_S_U_B_
   :inherited-members:
   :members:
   :undoc-members:

grUtils
-------

.. automodule:: fontTools.ttLib.tables.grUtils
   :inherited-members:
   :members:
   :undoc-members:

H_V_A_R_
--------

.. automodule:: fontTools.ttLib.tables.H_V_A_R_
   :inherited-members:
   :members:
   :undoc-members:

J_S_T_F_
--------

.. automodule:: fontTools.ttLib.tables.J_S_T_F_
   :inherited-members:
   :members:
   :undoc-members:

L_T_S_H_
--------

.. automodule:: fontTools.ttLib.tables.L_T_S_H_
   :inherited-members:
   :members:
   :undoc-members:

M_A_T_H_
--------

.. automodule:: fontTools.ttLib.tables.M_A_T_H_
   :inherited-members:
   :members:
   :undoc-members:

M_E_T_A_
--------

.. automodule:: fontTools.ttLib.tables.M_E_T_A_
   :inherited-members:
   :members:
   :undoc-members:

M_V_A_R_
--------

.. automodule:: fontTools.ttLib.tables.M_V_A_R_
   :inherited-members:
   :members:
   :undoc-members:

O_S_2f_2
--------

.. automodule:: fontTools.ttLib.tables.O_S_2f_2
   :inherited-members:
   :members:
   :undoc-members:

otBase
------

.. automodule:: fontTools.ttLib.tables.otBase
   :inherited-members:
   :members:
   :undoc-members:

otConverters
------------

.. automodule:: fontTools.ttLib.tables.otConverters
   :inherited-members:
   :members:
   :undoc-members:

otData
------

.. automodule:: fontTools.ttLib.tables.otData
   :inherited-members:
   :members:
   :undoc-members:

otTables
--------

.. automodule:: fontTools.ttLib.tables.otTables
   :inherited-members:
   :members:
   :undoc-members:

S__i_l_f
--------

.. automodule:: fontTools.ttLib.tables.S__i_l_f
   :inherited-members:
   :members:
   :undoc-members:

S__i_l_l
--------

.. automodule:: fontTools.ttLib.tables.S__i_l_l
   :inherited-members:
   :members:
   :undoc-members:

S_I_N_G_
--------

.. automodule:: fontTools.ttLib.tables.S_I_N_G_
   :inherited-members:
   :members:
   :undoc-members:

S_T_A_T_
--------

.. automodule:: fontTools.ttLib.tables.S_T_A_T_
   :inherited-members:
   :members:
   :undoc-members:

S_V_G_
------

.. automodule:: fontTools.ttLib.tables.S_V_G_
   :inherited-members:
   :members:
   :undoc-members:

sbixGlyph
---------

.. automodule:: fontTools.ttLib.tables.sbixGlyph
   :inherited-members:
   :members:
   :undoc-members:

sbixStrike
----------

.. automodule:: fontTools.ttLib.tables.sbixStrike
   :inherited-members:
   :members:
   :undoc-members:

T_S_I__0
--------

.. automodule:: fontTools.ttLib.tables.T_S_I__0
   :inherited-members:
   :members:
   :undoc-members:

T_S_I__1
--------

.. automodule:: fontTools.ttLib.tables.T_S_I__1
   :inherited-members:
   :members:
   :undoc-members:

T_S_I__2
--------

.. automodule:: fontTools.ttLib.tables.T_S_I__2
   :inherited-members:
   :members:
   :undoc-members:

T_S_I__3
--------

.. automodule:: fontTools.ttLib.tables.T_S_I__3
   :inherited-members:
   :members:
   :undoc-members:

T_S_I__5
--------

.. automodule:: fontTools.ttLib.tables.T_S_I__5
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_B_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_B_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_C_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_C_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_D_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_D_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_J_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_J_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_P_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_P_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_S_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_S_
   :inherited-members:
   :members:
   :undoc-members:

T_S_I_V_
--------

.. automodule:: fontTools.ttLib.tables.T_S_I_V_
   :inherited-members:
   :members:
   :undoc-members:

T_T_F_A_
--------

.. automodule:: fontTools.ttLib.tables.T_T_F_A_
   :inherited-members:
   :members:
   :undoc-members:

ttProgram
---------

.. automodule:: fontTools.ttLib.tables.ttProgram
   :inherited-members:
   :members:
   :undoc-members:

TupleVariation
--------------

.. automodule:: fontTools.ttLib.tables.TupleVariation
   :inherited-members:
   :members:
   :undoc-members:

V_D_M_X_
--------

.. automodule:: fontTools.ttLib.tables.V_D_M_X_
   :inherited-members:
   :members:
   :undoc-members:

V_O_R_G_
--------

.. automodule:: fontTools.ttLib.tables.V_O_R_G_
   :inherited-members:
   :members:
   :undoc-members:

V_V_A_R_
--------

.. automodule:: fontTools.ttLib.tables.V_V_A_R_
   :inherited-members:
   :members:
   :undoc-members:


