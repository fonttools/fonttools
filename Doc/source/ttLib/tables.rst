#######################################
tables: Access TrueType/OpenType tables
#######################################

.. contents:: On this page
    :local:


.. rubric:: Overview
   :heading-level: 2

This folder is a subpackage of :py:mod:`fontTools.ttLib`. Each module here is a
specialized TrueType/OpenType table converter: they can convert raw data
to Python objects and vice versa. Usually you do not need to
use these modules directly: they are imported and used
automatically when needed by :py:mod:`fontTools.ttLib`.

In addition to the tables defined in the official TrueType/OpenType
specification documents, several specialty tables are supported that
are used by specific vendors (including the Graphite shaping engine
and Apple's AAT). Note that fontTools supports the tables that provide
the core functionality of AAT, but does not guarantee everything.

Similarly, fontTools supports some third-party tables used by external
applications (such as FontForge and Microsoft's VTT), but may not
support every private table employed by those applications.


Accessing tables
----------------

The Python modules representing the tables have pretty strange names: this is due to the
fact that we need to map TT/OT table tags (which are case sensitive)
to filenames (which on macOS and Windows are not case sensitive) as well
as to Python identifiers. The latter means that each table identifier
can only contain ``[A-Za-z0-9_]`` and cannot start with a number.

The convention adopted is that capital letters in a table tag are
transformed into the letter followed by an underscore (e.g., ``A_``), while lowercase
letters and numbers are preceded by an underscore (e.g., ``_a``).

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

The converter itself is a class, named ``table_`` + expandedtag. Eg::


	class table__g_l_y_f:
		etc.

Note that if you _do_ need to use such modules or classes manually,
there are two convenient API functions that let you find them by tag::

    >>> ttLib.getTableModule('glyf')
    <module 'ttLib.tables._g_l_y_f'>
    >>> ttLib.getTableClass('glyf')
    <class ttLib.tables._g_l_y_f.table__g_l_y_f at 645f400>
    >>


Helper modules
--------------

In addition to the core table-conversion implementations, a set of
helper and utility modules is also found in this package. 
You should not normally need to access these modules directly,
but consulting them might be valuable if you need to add fontTools
support for a new table type.
 
In that case, a good place to start is with the documentation for
the base table classes:
 
.. toctree::
   :maxdepth: 1
 
   tables/table_api
 
The modules that provide lower-level helper functionality
include implementations of common OpenType data structures, support
for OpenType font variations, and various classes needed for
tables containing bitmap data or for tables used by the Graphite engine:
 	
.. toctree::
   :maxdepth: 1
 
   tables/OpenType_related
   tables/TupleVariation
   tables/Bitmap_related
   tables/grUtils
 
A module is also included for assembling and disassembling
TrueType bytecode:
 
.. toctree::
   :maxdepth: 1

   tables/ttProgram
       

    
Tables currently supported
--------------------------

.. toctree::
   :maxdepth: 1

   tables/_a_n_k_r
   tables/_a_v_a_r
   tables/B_A_S_E_
   tables/_b_s_l_n
   tables/C_B_D_T_
   tables/C_B_L_C_
   tables/C_F_F_
   tables/C_F_F__2
   tables/_c_i_d_g
   tables/_c_m_a_p
   tables/C_O_L_R_
   tables/C_P_A_L_
   tables/_c_v_a_r
   tables/_c_v_t
   tables/D_S_I_G_
   tables/E_B_D_T_
   tables/E_B_L_C_
   tables/F__e_a_t
   tables/_f_e_a_t
   tables/F_F_T_M_
   tables/_f_p_g_m
   tables/_f_v_a_r
   tables/_g_a_s_p
   tables/_g_c_i_d
   tables/G_D_E_F_
   tables/G__l_a_t
   tables/G__l_o_c
   tables/_g_l_y_f
   tables/G_M_A_P_
   tables/G_P_K_G_
   tables/G_P_O_S_
   tables/G_S_U_B_
   tables/_g_v_a_r
   tables/_h_d_m_x
   tables/_h_e_a_d
   tables/_h_h_e_a
   tables/_h_m_t_x
   tables/H_V_A_R_
   tables/J_S_T_F_
   tables/_k_e_r_n
   tables/_l_c_a_r
   tables/_l_o_c_a
   tables/_l_t_a_g
   tables/L_T_S_H_
   tables/M_A_T_H_
   tables/_m_a_x_p
   tables/M_E_T_A_
   tables/_m_e_t_a
   tables/_m_o_r_t
   tables/_m_o_r_x
   tables/M_V_A_R_
   tables/_n_a_m_e
   tables/_o_p_b_d
   tables/O_S_2f_2
   tables/_p_o_s_t
   tables/_p_r_e_p
   tables/_p_r_o_p
   tables/_s_b_i_x
   tables/S__i_l_f
   tables/S__i_l_l
   tables/S_I_N_G_
   tables/S_T_A_T_
   tables/S_V_G_
   tables/_t_r_a_k
   tables/T_T_F_A_
   tables/V_D_M_X_
   tables/_v_h_e_a
   tables/_v_m_t_x
   tables/V_O_R_G_
   tables/VTT_related
   tables/V_V_A_R_

.. automodule:: fontTools.ttLib.tables
   :members:
   :undoc-members:


