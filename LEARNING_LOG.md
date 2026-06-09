# Learning log


## Week 1, day 1, 15/05/26

### What I built
- pyenv + poetry project scaffold
- a simple vector class using dunder methods

### Surprises
- pyenv and poetry as useful frameworks to project management
- the importance of dunder methods and how they make sense when coding in Python
- what `__repr__`  and `__hash__` do. In particular, why the latter defaults to `None` when it is not defined while `__eq__` is defined

### Still unclear
- how to customise `sys.path`
- how to use pyend and poetry in practice
- the full use of dunder methods within the language


## Week 1, day 2, 18/05

### What I built
- A Trade class using `@dataclass`: reduces boilerplate.
- A Trade class using `Pydantic`: ideal for validation and serialisation
- A test file to be run with `pytest`

### Surprises
- Usefulness of `__slots__` dunder
- Usefulness of `poetry` to fix bugs and clean up the code
- Pydantic's high structure

### Still unclear
- Whether dataclass and Pydantic are used in practice as opposed to numpy arrays


## Week 1, day 3, 09/06

### What I built
- A `pydantic.BaseModel` `Portfolio` class of `Trades` with custom dunder methods
- An `Instrument` ABC and two concrete subclasses 
- A Protocol for `Priceable` instruments

### Surprises
- That there is a movement against inheritance and in favour of Protocols (more pythonic)

### Still unclear
- `@runtime_checkable` decorator for Protocols
- how easy it is to keep mypy clean
- how to maintain the `docs` folder