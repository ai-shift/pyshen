import inspect
import logging
import types
from collections.abc import Callable

log = logging.getLogger(__name__)

FunctionPredicate = Callable[[types.FunctionType], bool]


def call_all_functions(
    module: types.ModuleType, predicate: None | FunctionPredicate = None
) -> None:
    if predicate is None:
        predicate = _default_predicate

    fns_to_call = [
        obj
        for _, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and predicate(obj)
    ]
    if not fns_to_call:
        log.warning("There are no matching functions in module %s", module.__name__)
    for fn in fns_to_call:
        fn()


def _default_predicate(_: FunctionPredicate) -> bool:
    return True
