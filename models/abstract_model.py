#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 14.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 

class AbstractModel(object):
    """ Сlass for data wrapping.
        
    
    Private methods:
    
    - __str__(self) used dumpable_attributes
    - set_with_dict(self, dictionary)

    Initiation. Create attributes accordong to

    public properties:
    

    - dumpable_attributes
    - int_attributes
    - float_attributes
    - list_attributes
    - list_attributes_types
    - other_attributes

    """

    dumpable_attributes = []
    int_attributes = []
    float_attributes = []
    list_attributes = []
    list_attributes_types = {}
    other_attributes = {}

    def __init__(self):
        ''' Create attributes accordong to

        - dumpable_attributes
        - int_attributes
        - float_attributes
        - list_attributes
        - list_attributes_types
        - other_attributes
        '''
        for attr in self.dumpable_attributes:
            setattr(self, attr, None)
        for attr in self.int_attributes:
            setattr(self, attr, 0)
        for attr in self.float_attributes:
            setattr(self, attr, 0.0)
        for attr in self.other_attributes:
            setattr(self, attr, self.other_attributes[attr])

    def __str__(self):
        """ Get string representation with fields
            defined in dumpable_attributes."""
        self.preprocess_data()
        result = ""
        for attr in self.dumpable_attributes:
            result += "%s\t" % getattr(self, attr)
        result = "%s\n" % result.strip()
        return result

    def set_with_dict(self, dictionary):
        """ Set object with dictionaty."""
        for key, value in dictionary.items():
            if value == "None" or value is None:
                value = None
            elif key in self.int_attributes:
                value = int(value)
            elif key in self.float_attributes:
                value = float(value)
            elif key in self.list_attributes:
                value = value.split(",")
                value = [self.list_attributes_types[key](x) for x in value]
            setattr(self, key, value)

    def set_with_list(self, data):
        """ Set object with list."""
        for i, value in enumerate(data):
            key = self.dumpable_attributes[i]
            if value == "None":
                value = None
            elif key in self.int_attributes:
                value = int(value)
            elif key in self.float_attributes:
                value = float(value)
            elif key in self.list_attributes:
                value = value.split(",")
                value = [self.list_attributes_types[key](x) for x in value]
            setattr(self, key, value)

    def get_as_dict(self):
        """ Get dictionary representation with fields
            defined in dumpable_attributes """
        self.preprocess_data()
        result = {}
        for attr in self.dumpable_attributes:
            result[attr] = getattr(self, attr)
        return result

    def preprocess_data(self):
        """ Any data preprocessing until returning."""
        pass

