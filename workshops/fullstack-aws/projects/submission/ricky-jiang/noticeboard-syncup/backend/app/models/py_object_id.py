# Object ID
# Every MongolDB documenet stores gets an id field automatically 
# It is stored as a bson.ObjectId type, which is a 12-byte binary value.
# Pydantic does not know this by default, so we need to create a custom type that can handle it.
# The two adapters below are used tell Pydantic to accept a string or a real ObjectId as input 
# and output it as a plain string

from typing import Any
# bson is the binary JSON format used by MongoDB to store documents
from bson import ObjectId
# pydantic_core is the core library used by Pydantic to handle data validation and serialization
from pydantic import GetCoreSchemaHandler
# core_schema is the schema definition used by Pydantic to define how data should be validated and serialized
from pydantic_core import core_schema


class PyObjectId(ObjectId):

    @classmethod
    #Hook for how to validate and serialize the ObjectId type in Pydantic models
    def __get_pydantic_core_schema__(cls, _source: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            # if input is from JSON, treat it as a string 
            json_schema=core_schema.str_schema(),
            # if input is from our own code, accept if its already 
            # a bson.ObjectId type, or if its a string, 
            # validate it and convert it to an ObjectId
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [core_schema.str_schema(), core_schema.no_info_plain_validator_function(cls.validate)]
                    ),
                ]
            ),
            # no matter what the input is, always serialize it as a string
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    # This is the function that validates if a string is a valid ObjectId and converts it to an ObjectId
    def validate(cls, value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value!r}")
        return ObjectId(value)