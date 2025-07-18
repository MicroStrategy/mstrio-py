import inspect
import logging
from collections import defaultdict
from collections.abc import Callable
from pprint import pformat

logger = logging.getLogger(__name__)


def _get_function_signature_as_formatted_str(func: Callable) -> str:
    return pformat(
        tuple(
            str(v)
            for v in inspect.signature(func).parameters.values()
            if v.name != 'self'
        )
    )


def what_can_i_do_with(source) -> None:
    logger.info('\n{mstrio-py WHAT CAN I DO WITH helper info}\n')

    module = inspect.getmodule(source)
    is_callable = callable(source)
    is_builtin = inspect.isbuiltin(source) or not module or inspect.isbuiltin(module)
    valid = bool(source) and not is_builtin

    if not valid:
        raise ValueError(
            'The provided source is neither callable nor an instance of '
            'a class. Please provide a reference to a callable object, '
            'like a class, a function or a method or to an instance of a class.',
        )

    is_mstrio_based: bool = not is_builtin and (
        module.__name__.startswith('mstrio') if module else False
    )

    if not is_callable:  # aka some class instance
        cls_name = source.__class__.__name__
        is_module = cls_name == 'module'
        if is_module:
            cls_name = source.__name__

        if not is_mstrio_based:
            logger.info(
                f'Artefact "{cls_name}" does not originate from '
                'mstrio-py library. Information below may not be fully accurate. '
                'Please refer to the official documentation of the source library.\n',
            )

        if is_module:
            logger.info(
                f'You have imported a module "{cls_name}". You can access '
                f'its contents using `{cls_name.split(".")[-1]}.<attr>`. '
                'Learn more about the module in documentation.\n',
            )
        else:
            logger.info(
                f'You have initialized an instance of the "{cls_name}" class. '
                'Preferably, you stored a reference to it in a variable, for example '
                f'like this: `<some_var> = {cls_name}(<args>)`',
            )

            # group all available props and methods
            kinds = defaultdict(list)
            for opt in inspect.classify_class_attrs(source.__class__):
                if not opt.name.startswith('_'):
                    kinds[opt.kind].append(opt.name)

            if 'property' in kinds:
                logger.info(
                    '\nPROPERTIES:\n'
                    'You can access a value stored under any of those via: '
                    '`<some_var>.<property>`',
                )
                logger.info(kinds['property'])
                del kinds['property']

            if 'method' in kinds:
                logger.info(
                    '\nMETHODS:\n'
                    'You can call any of the methods using '
                    '`<some_var>.<method>(<args>)` or you can learn more using '
                    '`what_can_i_do_with(<some_var>.<method>)` '
                    '(<method> without brackets!).',
                )
                logger.info(kinds['method'])
                del kinds['method']

            if 'class method' in kinds:
                logger.info(
                    '\nCLASS METHODS:\n'
                    'Those are methods that behave similarly to regular methods, '
                    'however they are not necessarily bound to any instance. '
                    'You can call them like any method above, or using: \n'
                    f'  {cls_name}.<class_method>(<instance>, *<args>)',
                )
                logger.info(kinds['class method'])
                del kinds['class method']

            if 'static method' in kinds:
                logger.info(
                    '\nSTATIC METHODS:\n'
                    'Those have nothing to do with <some_var> instance. '
                    'You can call them directly via '
                    f'`{cls_name}.<static_method>(<args>)` or learn more using '
                    f'`what_can_i_do_with({cls_name}.<static_method>)` '
                    '(<static_method> without brackets!).',
                )
                logger.info(kinds['static method'])
                del kinds['static method']

            if kinds:
                logger.info(
                    '\nOTHERS:\n'
                    'There are some other non-standard attributes. '
                    'Learn more about them in documentation.',
                )
                for kind, names in kinds.items():
                    logger.info(f'\n  {kind.upper()}:\n  {names}')
    else:  # a callable, like a function or a class instance method
        artefact_name = source.__name__
        is_class_factory = inspect.isclass(source) and hasattr(source, '__init__')

        # check if `source` is a method of a class
        is_class_method = hasattr(source, '__self__')

        if not is_mstrio_based:
            logger.info(
                f'Artefact "{artefact_name}" does not originate from mstrio-py '
                'library. Information below may not be fully accurate. '
                'Please refer to the official documentation of the source library.\n',
            )

        if is_class_factory:
            src = source.__init__
            logger.info(
                f'"{artefact_name}" is a module class. '
                'You can initialize an instance of it using '
                f'`<some_var> = {artefact_name}(<args>)`.\n',
            )
        else:
            src = source
            cls_name = source.__self__.__class__.__name__ if is_class_method else None
            is_static_method = False
            if cls_name == 'type':
                is_static_method = True
                # static method: we need to reassign name to a level higher
                cls_name = source.__self__.__name__

            if not is_class_method:
                msg = (
                    f'"{artefact_name}" is a function. You can call it using '
                    f'`{artefact_name}(<args>)` (assign to a variable if the call '
                    'result is needed).\n'
                )
            else:
                if is_static_method:
                    msg = (
                        f'"{artefact_name}" is a static method on {cls_name} class. '
                        f'You can call it using `{cls_name}.{artefact_name}(<args>)` '
                        '(assign to a variable if the call result is needed).\n'
                    )
                else:
                    msg = (
                        f'"{artefact_name}" is a method on {cls_name} class instance. '
                        f'You can call it using `<some_var>.{artefact_name}(<args>)` '
                        f'where <some_var> is a variable you store {cls_name} '
                        'instance in (assign to a variable if the call '
                        'result is needed).\n'
                    )

            logger.info(msg)

        logger.info('DOCSTRING:\n' + source.__doc__) if source.__doc__ else None
        logger.info('\nCALL SIGNATURE:')
        logger.info(_get_function_signature_as_formatted_str(src))

    logger.info('\n{mstrio-py WHAT CAN I DO WITH helper ended}\n')
