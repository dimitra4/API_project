import pytest
from pydantic import ValidationError

from model.data import Data


@pytest.mark.parametrize(
    "payload, is_valid",
    [
        ({"count": 727, "name": "michael", "age": 59, "country_id": "GR"}, True),
        ({"count": 0, "name": "vdvdfbvdbv", "age": None, "country_id": "GR"}, True),
        ({"count": -5, "name": "michael", "age": 59}, False),
        ({"count": 727, "name": "", "age": 59}, False),
        ({"count": 727, "name": " ", "age": 59}, False),
        ({"count": 727, "name": "maria23", "age": 59}, False),
        ({"count": 1, "name": "dimi", "age": 1, "country_id": "GRi"}, False)
    ],
    ids=["found", "not_found", "negative_count", "empty_name", "whitespace_name", "invalid_name", "invalid_country_id"],
)
def test_data_validation(payload, is_valid):
    if is_valid:
        Data(**payload)
    else:
        with pytest.raises(ValidationError):
            Data(**payload)