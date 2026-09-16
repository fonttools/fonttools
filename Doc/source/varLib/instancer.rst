#########
instancer
#########

For fonts containing ``VARC``, instancing is limited to axes that are not
referenced by component coordinates, the VARC variation store, or component
conditions. Removing unrelated axes remaps the remaining VARC axis indices.
Pinning or restricting a referenced axis raises ``NotImplementedError``,
including during ``avar`` version 2 partial instancing.

.. automodule:: fontTools.varLib.instancer
   :members:
   :undoc-members:
