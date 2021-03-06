import copy

# This file contains everything related to managing the directed asyclic graph containing all the inputs of all steps and their targets

import logging
from nurmi.util import strip_trailing_extension

# Dictionary containing set of all targets
# which can be fulfilled by the inputs.
# Key is inputs as frozenset.
# Value is set of targets.
targets_by_complete_inputs = dict()

# Dictionary of mandatory inputs by target.
# Key is target name
# Value is a frozen set of inputs which can make this target.
mandatory_inputs_of_targets = dict()

# Dictionary of optional inputs by target.
# Key is target name
# Value is a frozen set of inputs which can make this target.
optional_inputs_of_targets = dict()


# All targets as set in value having single input as key
targets_having_input = dict()

# Step by their target
# Key is target name
# Value is step
steps_by_target = dict()


all_valuenames = set()

def add(step):
    """ Add step to this bookkeeper
    Adding a step will enable bookkeeper to track target and inputs
    and retrieve the step based on those
    """
    global targets_by_complete_inputs
    global mandatory_inputs_of_targets
    global optional_inputs_of_targets
    global steps_by_target
    global all_valuenames

    target = step.target
    inputs = frozenset(step.inputs)

    all_valuenames.add(target)
    all_valuenames.update(inputs)
    all_valuenames.update(step.optional_inputs)

    # targets_by_complete_inputs
    if inputs not in targets_by_complete_inputs:
        targets_by_complete_inputs[inputs] = set()
    targets_by_complete_inputs[inputs].add(target)

    # inputs_of_targets
    mandatory_inputs_of_targets[target] = inputs
    optional_inputs_of_targets[target] = step.optional_inputs

    # targets_having_input
    for input in inputs:
        if not input in targets_having_input:
            targets_having_input[input] = set()
        targets_having_input[input].add(target)
    steps_by_target[target] = step

def get_step(target):
    """Retrieves the step based on it's target and all non-optional inputs
       Returns None if not found
    """
    global steps_by_target

    try:
        return steps_by_target[target]
    except KeyError:
        return None

def final_targets():
    """Get all targets which are not inputs to any other target

    """
    global mandatory_inputs_of_targets
    global optional_inputs_of_targets

    all_targets = set()
    all_inputs = set()
    for target in mandatory_inputs_of_targets:
        all_targets.add(target)
        all_inputs.update(mandatory_inputs_of_targets[target])
        try:
            all_inputs.update(optional_inputs_of_targets[target])
        except BaseException as be:
            logging.exception(be)
    return all_targets - all_inputs

def get_inputs_to_target(target):
    """ Returns all the mandatory inputs to target
        in the order they have to be executed
    """
    global mandatory_inputs_of_targets
    result = []
    inputs = mandatory_inputs_of_targets[target]
    for input in inputs:
        try:
            result.extend(get_inputs_to_target(input))
        except KeyError:
            result.append(input)
    result.append(target)
    return(result)

def get_steps_to_target(target):
    global steps_by_target
    result = []
    for intermediate_target in get_inputs_to_target(target):
        try:
            intermediate_step = None
            while "." in intermediate_target and intermediate_step is None:
                # If "." in target, find "parent" of given target
                if intermediate_target in steps_by_target:
                    intermediate_step = steps_by_target[intermediate_target]
                intermediate_target = strip_trailing_extension(
                    intermediate_target
                )
            if intermediate_step:
                result.append(intermediate_step)
        except KeyError:
            pass
    return result

def get_all_valuenames():
    global mandatory_inputs_of_targets
    global optional_inputs_of_targets
    result = set()
    for target in {
        **mandatory_inputs_of_targets,
        **optional_inputs_of_targets
    }:
        result.add(target)
        result.update(mandatory_inputs_of_targets[target])
        result.update(optional_inputs_of_targets[target])
    return result


def run_target_with_values(target, *valuedicts):
    steps = get_steps_to_target(target)
    if len(steps) == 1:
        return steps[0].run(*valuedicts)
    else:
        for step in steps:
            step.run(*valuedicts)
