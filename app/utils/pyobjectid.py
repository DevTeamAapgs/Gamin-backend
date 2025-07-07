from bson import ObjectId
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing import Any

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return str(ObjectId(v))
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: JsonSchemaValue, handler: GetCoreSchemaHandler) -> JsonSchemaValue:
        return {"type": "string"}
