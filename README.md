# PlugiPy
`PlugiPy` is a python library to rapidly create a flexible plugin system inside an application. 

Important features are...
- simple and highly configurable plugin discovery
- location-agnostic execution of plugins as portable software components (same api independent of the plugins execution-location)
    - locally in the same interpreter
    - inside a separate process
    - remote on a server e.g. for GPU intensive tasks
    - ... (extendable)
- common utility like
    - parameter system to specify and cofigure a set of parameters
    - persistance-api to load and save plugin instances (allows user-specific implementation of the persistance mechanism)