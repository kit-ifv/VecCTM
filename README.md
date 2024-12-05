The traffic flow model Cell-Transmission Model (CTM) was implemented in Python in various ways. 
The vectorized implementation was published in:

Hauke, R., Kübler, J., Baumann, M., & Vortisch, P. (2024).
A Vectorized Formulation of the Cell Transmission Model for Efficient Simulation of Large-Scale Freeway Networks. 
Procedia Computer Science, 238, 143-150.

A detailed documentation of the repository can be found in `Documentation/Documentation.md`.

The CTM implementations can be found in the traffic package. 
To run a simulation, the corresponding script must be executed as a Python module.
This can be done via the command line, e.g., using the command:
```python -m traffic.oo.networkseq``` oder ```python -m traffic.vector.vector_full```.
or through an IDE.

To execute these files, the required packages must first be installed. 
For this, a virtual environment should be created where the packages can be installed. 
This can be done via the command line using the command:
```python -m venv venv-name```.

After activating the virtual environment with the command
```venv-name\Scripts\activate.bat``` or ```venv-name\Scripts\activate.ps1``` 
the required packages can be installed using the command:
```pip install -r requirement.txt``` .

Example input files can be found in the folder ```networks```. 
The file ```small.yml``` has a total length of 21 km, ```medium.yml``` 187 km, and ```huge.yml``` 1500 km.

In the folder ```benchmark```, there is a script named ```benchmark.py```, which can be used to compare the runtimes of the different implementations. 
