"""
Shared base class every schema inherits from — this is what makes ALL
of them auto-convert snake_case field names to camelCase in the JSON
output, without writing Field(alias="...") by hand on every single field.

alias_generator=to_camel converts field names automatically:
  created_at -> createdAt, small_url -> smallUrl, etc.

populate_by_name=True means you can still CONSTRUCT these models using
the snake_case Python names internally (Post(created_at=...)), while
the JSON that goes out over HTTP uses the camelCase alias. FastAPI's
response_model_by_alias defaults to True, so this happens automatically
on every route that returns one of these models.
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )