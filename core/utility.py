#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy
import copy


def re_address_repeaters_key_name(key_name):
    return "".join(['[\'' + _key + '\']' for _key in key_name.split('/')[:-1]])


def generate_new_sub_steps(sub_steps, data_matrix, arrays):
    original_sub_steps = copy.deepcopy(sub_steps)
    steps_array = []
    for array in data_matrix:
        array_name_position = 0
        for array_name in arrays:
            for sub_step in sub_steps:
                exec(
                    "original_sub_steps{key_name} = {matrix_value}".format(
                        key_name=re_address_repeaters_key_name(array_name),
                        matrix_value='"' + str(array[array_name_position]) + '"' if type(
                            array[array_name_position]) == int or type(array[array_name_position]) == str else array[
                            array_name_position]
                    )
                )
            array_name_position += 1
        steps_array.append(copy.deepcopy(original_sub_steps))
    return steps_array


def find_repeaters(sub_content, root, arrays):
    if type(sub_content) == dict and 'nettacker_fuzzer' not in sub_content:
        temprory_content = copy.deepcopy(sub_content)
        original_root = root
        for key in sub_content:
            root = original_root
            root += key + '/'
            temprory_content[key], _root, arrays = find_repeaters(sub_content[key], root, arrays)
        sub_content = copy.deepcopy(temprory_content)
        root = original_root
    if (type(sub_content) != int and type(sub_content) != bool) and (
            type(sub_content) == list or 'nettacker_fuzzer' in sub_content):
        arrays[root] = sub_content
    return (sub_content, root, arrays) if root != '' else arrays


class value_to_class:
    def __init__(self, value):
        self.value = value


# le fucking gacy
def class_to_value(arrays):
    original_arrays = copy.deepcopy(arrays)
    array_index = 0
    for array in arrays:
        value_index = 0
        for value in array:
            if type(value) == value_to_class:
                original_arrays[array_index][value_index] = value.value
            value_index += 1
        array_index += 1
    return original_arrays


def arrays_to_matrix(arrays):
    return numpy.array(
        numpy.meshgrid(*[
            arrays[array_name] for array_name in arrays
        ])
    ).T.reshape(
        -1,
        len(arrays.keys())
    ).tolist()


def string_to_bytes(string):
    return string.encode()


def fuzzer_function_read_file_as_array(filename):
    return open(filename).read().split('\n')


def apply_data_functions(data):
    original_data = copy.deepcopy(data)
    function_results = {}
    globals().update(locals())
    for data_name in data:
        if type(data[data_name]) == str and data[data_name].startswith('fuzzer_function'):
            exec("fuzzer_function = {fuzzer_function}".format(fuzzer_function=data[data_name]), globals(),
                 function_results)
            original_data[data_name] = function_results['fuzzer_function']
    return original_data


def nettacker_fuzzer_repeater_perform(arrays):
    original_arrays = copy.deepcopy(arrays)
    for array_name in arrays:
        if 'nettacker_fuzzer' in arrays[array_name]:
            data = arrays[array_name]['nettacker_fuzzer']['data']
            data_matrix = arrays_to_matrix(apply_data_functions(data))
            prefix = arrays[array_name]['nettacker_fuzzer']['prefix']
            input_format = arrays[array_name]['nettacker_fuzzer']['input_format']
            interceptors = copy.deepcopy(arrays[array_name]['nettacker_fuzzer']['interceptors'])
            if interceptors:
                interceptors = interceptors.split(',')
            suffix = arrays[array_name]['nettacker_fuzzer']['suffix']
            processed_array = []
            for sub_data in data_matrix:
                formatted_data = {}
                index_input = 0
                for value in sub_data:
                    formatted_data[list(data.keys())[index_input]] = value
                    index_input += 1
                interceptors_function = ''
                interceptors_function_processed = ''
                if interceptors:
                    interceptors_function += 'interceptors_function_processed = '
                    for interceptor in interceptors[::-1]:
                        interceptors_function += '{interceptor}('.format(interceptor=interceptor)
                    interceptors_function += 'input_format.format(**formatted_data)' + str(
                        ')' * interceptors_function.count('('))
                    expected_variables = {}
                    globals().update(locals())
                    exec(interceptors_function, globals(), expected_variables)
                    interceptors_function_processed = expected_variables['interceptors_function_processed']
                else:
                    interceptors_function_processed = input_format.format(**formatted_data)
                processed_sub_data = interceptors_function_processed
                if prefix:
                    processed_sub_data = prefix + processed_sub_data
                if suffix:
                    processed_sub_data = processed_sub_data + suffix
                processed_array.append(copy.deepcopy(processed_sub_data))
            original_arrays[array_name] = processed_array
    return original_arrays


def expand_module_steps(content):
    original_content = copy.deepcopy(content)
    for protocol_lib in content:
        for sub_step in content[content.index(protocol_lib)]['steps']:
            arrays = nettacker_fuzzer_repeater_perform(find_repeaters(sub_step, '', {}))
            if arrays:
                original_content[content.index(protocol_lib)]['steps'][
                    original_content[content.index(protocol_lib)]['steps'].index(sub_step)
                ] = generate_new_sub_steps(sub_step, class_to_value(arrays_to_matrix(arrays)), arrays)
            else:
                original_content[content.index(protocol_lib)]['steps'][
                    original_content[content.index(protocol_lib)]['steps'].index(sub_step)
                ] = [  # minimum 1 step in array
                    original_content[content.index(protocol_lib)]['steps'][
                        original_content[content.index(protocol_lib)]['steps'].index(sub_step)
                    ]
                ]
    return original_content