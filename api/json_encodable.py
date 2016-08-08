# pylint: disable=redefined-builtin
from builtins import bytes
import json


class JSONEncodable(object):

    def __repr__(self):
        return str(self.__dict__)

    def __iter__(self):
        return iter(self.__dict__)

    def to_json(self):
        return json.dumps(self.to_json_encodable())

    def to_json_encodable(self):
        json_encodable_dict = dict(self.__dict__)
        for key in json_encodable_dict:
            if isinstance(json_encodable_dict[key], bytes):
                json_encodable_dict[key] = list(json_encodable_dict[key])
            elif isinstance(json_encodable_dict[key], JSONEncodable):
                json_encodable_dict[key] = json_encodable_dict[key].to_json_encodable()
        return json_encodable_dict

    @staticmethod
    def encode_list(input_list):
        output_list = []
        for obj in input_list:
            if isinstance(obj, JSONEncodable):
                output_list.append(obj.to_json_encodable())
            elif isinstance(obj, bytes):
                output_list.append(list(obj))
            else:
                output_list.append(obj)
        return output_list
