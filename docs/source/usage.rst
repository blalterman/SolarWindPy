Usage
=====

The library exposes a set of tools for manipulating solar wind data. After
installation, import the desired functions and classes:

.. code-block:: python

   from solarwindpy.core import Plasma
   from solarwindpy.tools import normal_parameters
   import numpy as np

   m = np.array([0.1, 0.2])
   s = np.array([0.05, 0.08])
   params = normal_parameters(m, s)
   print(params.head())

See the :doc:`tutorial` for a guided introduction and more examples.
