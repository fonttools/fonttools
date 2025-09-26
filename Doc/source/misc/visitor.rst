####################################################
visitor: Tools for traversing nested data structures
####################################################

.. contents:: On this page:
    :local:

.. rubric:: Overview
   :heading-level: 2

The :mod:`.visitor` module provides an extensible `visitor pattern`_, which can
be used for traversing, inspecting, and editing nested Python data structures.

The utility class :class:`Visitor <fontTools.misc.visitor.Visitor>`
automatically handles recursion into most common data types, which allows for
user code to skip boilerplate and focus on operation logic. This recursion logic
is documented in full under the :func:`visit() <fontTools.misc.visitor.Visitor>`
function.

Commonly targeted data structures in font projects and ``fonttools`` include:

* :class:`TTFont <fontTools.ttLib.ttFont.TTFont>`: Compiled font files
* :class:`FeatureFile <fontTools.feaLib.ast.FeatureFile>`: Feature code syntax trees

Commonly implemented operations include:

* Summarizing
* Subsetting
* Scaling

.. _visitor pattern: https://en.wikipedia.org/wiki/Visitor_pattern


Specializations
---------------

The :mod:`ttLib.ttVisitor <fontTools.ttLib.ttVisitor>` module provides the
:class:`TTVisitor <fontTools.ttLib.ttVisitor.TTVisitor>` class, which handles
common edge cases when using visitors with :class:`TTFont
<fontTools.ttLib.ttFont.TTFont>` objects. For this reason, it should be
preferred in that scenario.


Guide
-----

1. Create a new class extending :class:`Visitor <fontTools.misc.visitor.Visitor>`.
2. Register operations for specific types or attributes with the *register* annotations.
3. Instantiate the class and call :func:`visit() <fontTools.misc.visitor.Visitor>` on the target object.


Example code
^^^^^^^^^^^^

One can create a visitor class that checks the case of feature names::

    >>> from fontTools.feaLib.ast import FeatureNameStatement
    >>> from fontTools.misc.visitor import Visitor
    >>>
    >>> class SpellCheckVisitor(Visitor):
    ...     found: list[FeatureNameStatement]
    ...
    ...     def __init__(self):
    ...         self.found = []
    >>>
    >>> @SpellCheckVisitor.register(FeatureNameStatement)
    ... def visit(visitor: SpellCheckVisitor, statement: FeatureNameStatement):
    ...     # Find name statements that are not in title case.
    ...     if statement.string != statement.string.title():
    ...         visitor.found.append(statement)

This can then be applied on a feature file object::

    >>> io = StringIO("""
    ...     feature ss01 {
    ...         featureNames {
    ...             name "Monolinear Grotesque";
    ...         };
    ...     } ss01;
    ...
    ...     feature ss02 {
    ...         featureNames {
    ...             name "Optical Apertures";
    ...         };
    ...     } ss02;
    ...
    ...     feature ss03 {
    ...         featureNames {
    ...             name "slanted Humanism";
    ...         };
    ...     } ss03;
    ... """)
    >>> fea = Parser(io).parse()
    >>>
    >>> visitor = SpellCheckVisitor()
    >>> visitor.visit(fea)
    >>>
    >>> for statement in visitor.found:
    ...     print(
    ...         "Found feature name that was not in title case: "
    ...         f"'{statement.string}' at location '{statement.location}'",
    ... )
    Found feature name that was not in title case: 'slanted Humanism' at location '<features>:16:13'


Package contents
----------------

.. automodule:: fontTools.misc.visitor
   :members:
   :undoc-members:
