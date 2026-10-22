"""TimeSeries SMCs in Variables — the DMP profile of IDTA 02008.

These tests drive the production path (Python Resource -> exported JSON ->
Pydantic -> BaSyx), as the registration service builds a resource.
"""

from __future__ import annotations

import pytest
from basyx.aas.model import datatypes

from aas_pydantic import Key, ModelReference
from aas_model import Resource, build_from_model
from aas_model.submodel_templates.time_series import (
    IDTA_TIME_SERIES, RecordReference, TimeSeriesRecord, linked_segment, operation_log,
    record_field, record_file, record_group, record_range, record_reference, record_text, time_series,
)
from aas_model.submodel_templates.variables import (
    LogGroup, MeasurementsGroup, StateGroup, Variables,
)


CONCEPT = "https://w3id.org/2026/apex/semantic/state/operational"


def _station_state():
    return time_series(name="Station state", measurement="station_state", fields={
        "PackMLState": record_field("xs:string", concept=CONCEPT),
        "Position": record_group({"X": record_field("xs:double")}),
        "Location": record_reference(ModelReference(key=(
            Key(type_="Submodel", value="{aas_id}/submodels/Parameters"),
            Key(type_="SubmodelElementCollection", value="Location"),
        ))),
    })


def _publish(variables: Variables) -> dict:
    asset = Resource(id_short="seriesTestAAS", variables=variables)
    restored = Resource.model_validate_json(asset.model_dump_json())
    sm = {s.id_short: s for s in build_from_model(restored)}["Variables"]
    return {e.id_short: e for e in sm.submodel_element}


def _children(element) -> dict:
    return {c.id_short: c for c in element.value}


def _semantic_id(element) -> str:
    return element.semantic_id.key[0].value


def _series():
    variables = Variables(id_short="Variables", State=StateGroup(value={"Station": _station_state()}))
    return _children(_publish(variables)["State"])["Station"]


def test_groups_appear_only_when_authored():
    assert set(_publish(Variables(id_short="Variables"))) == set()
    groups = _publish(Variables(
        id_short="Variables", State=StateGroup(), Measurements=MeasurementsGroup(), Log=LogGroup(),
    ))
    assert set(groups) == {"State", "Measurements", "Log"}


def test_series_round_trips_through_rest_json():
    from aas_model._serde import parse_submodel_dict
    from basyx.aas.adapter.json import json_serialization
    import json

    variables = Variables(id_short="Variables", id="urn:sm:Variables",
                          State=StateGroup(value={"Station": _station_state()}))
    asset = Resource(id_short="seriesTestAAS", variables=variables)
    sm = {s.id_short: s for s in build_from_model(asset)}["Variables"]
    rest = json.loads(json.dumps(sm, cls=json_serialization.AASToJsonEncoder))
    back = parse_submodel_dict(rest, Variables)
    series = back.State.value["Station"]
    assert type(series).__name__ == "TimeSeriesCollection"
    fields = series.Metadata.Record.field
    assert fields["PackMLState"].value_type == "xs:string"
    assert fields["PackMLState"].supplemental_semantic_ids == [CONCEPT]
    assert fields["Position"].field["X"].value_type == "xs:double"
    assert type(fields["Location"]).__name__ == "RecordReference"
    target = series.Segments.LinkedSegment["Live"].InfluxDb2Target
    assert target.Measurement.value == "station_state"
    assert target.Tags.tag["asset"].value == "seriesTestAAS"


def test_series_is_an_smc_with_the_idta_id_as_supplemental():
    series = _series()
    assert type(series).__name__ == "SubmodelElementCollection"
    assert [k.value for s in series.supplemental_semantic_id for k in s.key] == [IDTA_TIME_SERIES]
    assert set(_children(series)) == {"Metadata", "Segments"}


def test_record_holds_the_row_shape_without_columns():
    record = _children(_children(_series())["Metadata"])["Record"]
    fields = _children(record)
    assert _semantic_id(fields["Time"]) == "https://admin-shell.io/idta/TimeSeries/UtcTime/1/1"
    assert fields["Time"].value_type is datatypes.DateTime
    assert list(fields["PackMLState"].qualifier) == [], "a field's InfluxDB field is its idShortPath"
    position = _children(fields["Position"])
    assert position["X"].value_type is datatypes.Double
    location = fields["Location"]
    assert type(location).__name__ == "ReferenceElement"
    assert _semantic_id(location) == "https://smartproductionlab.aau.dk/timeseries/RecordReference/1/0"
    assert [k.value for k in location.value.key] == [
        "https://smartproductionlab.aau.dk/aas/seriesTestAAS/submodels/Parameters", "Location"]


def test_linked_segment_names_its_target_and_the_owning_aas():
    live = _children(_children(_series())["Segments"])["Live"]
    parts = _children(live)
    assert parts["Endpoint"].value == "http://influxdb:8086/api/v2/query?org=ap2030"
    assert parts["State"].value == "InProgress"
    target = _children(parts["InfluxDb2Target"])
    assert target["Bucket"].value == "ap2030"
    assert target["Measurement"].value == "station_state"
    assert {t.id_short: t.value for t in target["Tags"].value} == {"asset": "seriesTestAAS"}
    query = parts["Query"].value
    assert 'r["_measurement"] == "station_state"' in query
    assert 'r["asset"] == "seriesTestAAS"' in query
    assert '{{y-value}}' in query


def test_a_segment_with_an_end_time_is_completed_and_without_one_in_progress():
    live = linked_segment(measurement="m", tags={}, start_time="2026-10-20T00:00:00Z")
    assert (live.StartTime.value, live.EndTime, live.State.value) == ("2026-10-20T00:00:00Z", None, "InProgress")
    batch = linked_segment(measurement="m", tags={}, start_time="2026-10-20T00:00:00Z",
                           end_time="2026-10-20T08:00:00+02:00")
    assert (batch.EndTime.value, batch.State.value) == ("2026-10-20T08:00:00+02:00", "Completed")


@pytest.mark.parametrize("times", [
    {"start_time": "yesterday"},
    {"start_time": "2026-10-20T00:00:00"},
    {"start_time": "2026-10-20T08:00:00Z", "end_time": "2026-10-20T07:00:00Z"},
])
def test_segment_times_are_offset_date_times_in_order(times):
    with pytest.raises(ValueError):
        linked_segment(measurement="m", tags={}, **times)


def test_ranges_files_and_texts_round_trip_through_rest_json():
    from aas_model._serde import parse_submodel_dict
    from basyx.aas.adapter.json import json_serialization
    import json

    series = time_series(name="Dosing", measurement="dosing", fields={
        "Tolerance": record_range("xs:double"),
        "Report": record_file("application/pdf"),
        "Batch": record_text({"en": "Batch name", "de": "Chargenname"}),
    })
    variables = Variables(id_short="Variables", id="urn:sm:Variables", Measurements=MeasurementsGroup(value={"Dosing": series}))
    sm = {s.id_short: s for s in build_from_model(Resource(id_short="seriesTestAAS", variables=variables))}["Variables"]
    rest = json.loads(json.dumps(sm, cls=json_serialization.AASToJsonEncoder))
    fields = parse_submodel_dict(rest, Variables).Measurements.value["Dosing"].Metadata.Record.field
    assert {name: type(field).__name__ for name, field in fields.items()} == {
        "Tolerance": "RecordRange", "Report": "RecordFile", "Batch": "RecordText"}
    assert fields["Tolerance"].value_type == "xs:double"
    assert fields["Report"].content_type == "application/pdf"
    assert fields["Batch"].value == {"en": "Batch name", "de": "Chargenname"}


def test_a_record_text_declares_its_languages():
    with pytest.raises(ValueError, match="language"):
        record_text({})
    with pytest.raises(ValueError, match="language"):
        record_text({"en": ""})


def test_time_is_not_a_field():
    with pytest.raises(Exception, match="Time"):
        TimeSeriesRecord(field={"Time": record_field("xs:dateTime")})


def test_identifiers_spliced_into_flux_are_checked():
    with pytest.raises(ValueError, match="measurement"):
        linked_segment(measurement='bad"name', tags={})


def test_operation_log_references_the_operation_beside_outcome_and_duration():
    operation = ModelReference(key=(
        Key(type_="Submodel", value="{aas_id}/submodels/ControlComponentInstance"),
        Key(type_="SubmodelElementCollection", value="Skills"),
        Key(type_="SubmodelElementCollection", value="Occupy"),
        Key(type_="Operation", value="operation"),
    ))
    log = operation_log(operation, name="Occupy", measurement="operation_occupy")
    fields = log.Metadata.Record.field
    assert list(fields) == ["Outcome", "DurationMs", "Operation"]
    assert fields["DurationMs"].value_type == "xs:long"
    assert isinstance(fields["Operation"], RecordReference)
    assert fields["Operation"].value.key[-1].value == "operation"


def test_operation_log_rejects_a_field_name_clashing_with_a_log_field():
    with pytest.raises(ValueError, match="clashes"):
        operation_log(ModelReference(key=(Key(type_="Submodel", value="urn:x"),)), name="Occupy",
                      measurement="operation_occupy", field="Outcome")
