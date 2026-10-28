"""TimeSeries SMC — the DMP profile of IDTA 02008 (Time Series Data 1.1).

Layering: the generated IDTA template
(``aas_pydantic.submodel_templates.time_series``) stays PRISTINE. This module
shapes one time series as an SMC inside ``Variables`` instead of a submodel of
its own: the SMC carries this project's id with the IDTA TimeSeries id as a
supplemental id, and everything inside it keeps the IDTA ids, so splitting it
out into a TimeSeries submodel stays mechanical.

Structure::

    <series>                     TimeSeriesCollection (TS_COLLECTION + IDTA TimeSeries)
    ├── Metadata
    │   ├── Name
    │   └── Record               the row schema: one row = one sample
    │       ├── Time             UtcTime (xs:dateTime)
    │       ├── <field>          RecordField: one InfluxDB field, named by its idShortPath
    │       ├── <range>          RecordRange: two fields, <path>.min and <path>.max
    │       ├── <file>           RecordFile: one string field, the file's path or URL
    │       ├── <text>           RecordText: one string field per declared language, <path>.en
    │       ├── <group>          RecordGroup of further fields (Position.X)
    │       └── <reference>      RecordReference to an AAS element, resolved as if inline
    └── Segments
        └── LinkedSegment[]
            ├── Endpoint         InfluxDB 2 query URL (IDTA)
            ├── Query            Flux for the web UI (IDTA)
            └── InfluxDb2Target  Bucket, Measurement, Tags, WriteMode (DMP extension, InfluxDB 2)

A series groups what is sampled together, never one variable each. The DMP
addresses the LinkedSegment; it reads the Record as the row shape and writes or
reads one point per row. A field's InfluxDB field is its idShortPath below the
Record (list members by index, ``Waypoints[0].x``), so renaming a field starts a
new InfluxDB field. A RecordReference counts exactly as if the referenced
element were declared at its place: a Property is one field, an SMC or SML a
group, an Operation a group of its input, InOut and output variables. The tags
name the AAS that owns the series (``{aas_id_short}``, resolved when the
resource is built). The WriteMode says how the DMP writes a row: Synchronous
(the default) waits for InfluxDB to acknowledge each point, so a failed write
fails the evaluation; Asynchronous hands the point to a batching buffer and
goes on, for logs and other rows whose loss must not stop the data flow.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import ClassVar, Dict, List, Literal, Optional, Union

from pydantic import model_validator

from aas_pydantic import (
    File, ModelReference, MultiLanguageProperty, Property, Range, ReferenceElement, SubmodelElementCollection,
)
from aas_pydantic.aas_model import AasIdString
from aas_pydantic.submodel_templates.time_series import (
    EndTime, Endpoint, LinkedSegment as _LinkedSegment, Metadata as _Metadata, Name,
    Query, Segments as _Segments, StartTime, State,
)

from aas_model.constants import (
    INFLUX_BUCKET, INFLUX_ORG, INFLUX_ORIGIN,
    TS_COLLECTION, TS_INFLUX_TARGET, TS_INFLUX_TARGET_BUCKET,
    TS_INFLUX_TARGET_MEASUREMENT, TS_INFLUX_TARGET_TAG, TS_INFLUX_TARGET_TAGS, TS_INFLUX_TARGET_WRITE_MODE,
    TS_RECORD_FIELD, TS_RECORD_FILE, TS_RECORD_GROUP, TS_RECORD_RANGE, TS_RECORD_REFERENCE,
    TS_RECORD_TEXT,
)

IDTA_TIME_SERIES = "https://admin-shell.io/idta/TimeSeries/1/1"
IDTA_RECORD = "https://admin-shell.io/idta/TimeSeries/Record/1/1"
IDTA_UTC_TIME = "https://admin-shell.io/idta/TimeSeries/UtcTime/1/1"

# Measurement names, tag keys and values are spliced into Flux string literals.
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.\-{}]+$")


# ── Record ───────────────────────────────────────────────────────────────────

class UtcTime(Property):
    """The row's time. A value the transformation returns is the point's time;
    without one the DMP stamps the time of evaluation."""
    id_short: AasIdString = "Time"
    semantic_id: str = IDTA_UTC_TIME
    value_type: str = "xs:dateTime"


class RecordField(Property):
    """One field of the row. The concept it measures rides as a supplemental
    semantic id, as on a ``VariableProp``."""
    semantic_id: str = TS_RECORD_FIELD


class RecordRange(Range):
    """A band of the row: two fields, ``<path>.min`` and ``<path>.max``, of its valueType."""
    semantic_id: str = TS_RECORD_RANGE


class RecordFile(File):
    """A file belonging to the row: one string field, its path or URL. The
    file itself stays in the AAS or wherever the path points."""
    KEEP_WITHOUT_VALUE: ClassVar[bool] = True
    semantic_id: str = TS_RECORD_FILE


class RecordText(MultiLanguageProperty):
    """A text in several languages: one string field per language, ``<path>.en``.
    Its value declares the languages, each with the field's label in it."""
    semantic_id: str = TS_RECORD_TEXT


class RecordGroup(SubmodelElementCollection):
    """Fields that belong together within a row (``Position.X``)."""
    semantic_id: str = TS_RECORD_GROUP
    field: Dict[str, "RecordEntry"] = {}


class RecordReference(ReferenceElement):
    """An AAS element whose structure is part of the row, as if declared at this
    place under this idShort: a Property, an SMC or SML, or an Operation (its
    input, InOut and output variables). The DMP resolves it; values still come
    from the transformation."""
    semantic_id: str = TS_RECORD_REFERENCE


RecordEntry = Union[RecordField, RecordRange, RecordFile, RecordText, RecordGroup, RecordReference]


class TimeSeriesRecord(SubmodelElementCollection):
    id_short: AasIdString = "Record"
    semantic_id: str = IDTA_RECORD
    Time: UtcTime = UtcTime()
    field: Dict[str, RecordEntry] = {}

    @model_validator(mode="after")
    def _time_is_not_a_field(self):
        if "Time" in self.field:
            raise ValueError("'Time' is the row's time, not a field")
        return self


class TimeSeriesMetadata(_Metadata):
    Record: TimeSeriesRecord


# ── LinkedSegment write target (DMP extension) ───────────────────────────────

class Bucket(Property):
    id_short: AasIdString = "Bucket"
    semantic_id: str = TS_INFLUX_TARGET_BUCKET


class Measurement(Property):
    id_short: AasIdString = "Measurement"
    semantic_id: str = TS_INFLUX_TARGET_MEASUREMENT


class Tag(Property):
    """One series tag: the idShort is the tag key, the value its value."""
    semantic_id: str = TS_INFLUX_TARGET_TAG


class Tags(SubmodelElementCollection):
    id_short: AasIdString = "Tags"
    semantic_id: str = TS_INFLUX_TARGET_TAGS
    tag: Dict[str, Tag] = {}


WriteModeValue = Literal["Synchronous", "Asynchronous"]


class TargetWriteMode(Property):
    """How the DMP writes a row: ``Synchronous`` waits for InfluxDB's
    acknowledgement of each point; ``Asynchronous`` batches points and does
    not wait. Absent means Synchronous."""
    id_short: AasIdString = "WriteMode"
    semantic_id: str = TS_INFLUX_TARGET_WRITE_MODE
    value: WriteModeValue = "Synchronous"


class InfluxDb2Target(SubmodelElementCollection):
    """Where the DMP writes and reads the segment's points on InfluxDB 2. Each
    database has its own target, told apart by semanticId; a segment carries
    exactly one. The IDTA Query is for people and the web UI; the DMP never
    parses it."""
    id_short: AasIdString = "InfluxDb2Target"
    semantic_id: str = TS_INFLUX_TARGET
    Bucket: Bucket
    Measurement: Measurement
    Tags: Tags
    WriteMode: Optional[TargetWriteMode] = None


class DmpLinkedSegment(_LinkedSegment):
    InfluxDb2Target: InfluxDb2Target


class TimeSeriesSegments(_Segments):
    LinkedSegment: Dict[str, DmpLinkedSegment] = {}


class TimeSeriesCollection(SubmodelElementCollection):
    semantic_id: str = TS_COLLECTION
    supplemental_semantic_ids: List[str] = [IDTA_TIME_SERIES]
    Metadata: TimeSeriesMetadata
    Segments: TimeSeriesSegments


RecordGroup.model_rebuild()
TimeSeriesRecord.model_rebuild()


# ── Authoring helpers ────────────────────────────────────────────────────────

def record_field(value_type: str, *, concept: str = "", description: str = "") -> RecordField:
    """A Record field; its InfluxDB field is its idShortPath below the Record."""
    return RecordField(
        value_type=value_type, description=description,
        supplemental_semantic_ids=[concept] if concept else [],
    )


def record_range(value_type: str, *, concept: str = "", description: str = "") -> RecordRange:
    """A Record range: the fields ``<path>.min`` and ``<path>.max``."""
    return RecordRange(value_type=value_type, description=description,
                       supplemental_semantic_ids=[concept] if concept else [])


def record_file(content_type: str, *, concept: str = "", description: str = "") -> RecordFile:
    """A Record file: one string field, the path or URL of a file of *content_type*."""
    return RecordFile(content_type=content_type, description=description,
                      supplemental_semantic_ids=[concept] if concept else [])


def record_text(labels: Dict[str, str], *, concept: str = "", description: str = "") -> RecordText:
    """A Record text in the languages of *labels* (language → the field's label
    in it): one string field per language, ``<path>.<language>``."""
    if not labels or any(not language or not label for language, label in labels.items()):
        raise ValueError("a Record text declares at least one language, each with a label")
    return RecordText(value=dict(labels), description=description,
                      supplemental_semantic_ids=[concept] if concept else [])


def record_group(fields: Dict[str, RecordEntry], *, description: str = "") -> RecordGroup:
    return RecordGroup(field=fields, description=description)


def record_reference(reference: ModelReference, *, description: str = "") -> RecordReference:
    """The referenced element's structure at this place of the row."""
    return RecordReference(value=reference, description=description)


def _check_identifier(kind: str, value: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"{kind} {value!r} must match {_IDENTIFIER.pattern}")
    return value


def flux_query(bucket: str, measurement: str, tags: Dict[str, str]) -> str:
    """The segment's Query: its points in the web UI's time range, one field
    per selected Record field (``{{y-value}}``, substituted by the UI)."""
    lines = [
        f'from(bucket: "{bucket}")',
        "  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)",
        f'  |> filter(fn: (r) => r["_measurement"] == "{measurement}")',
        *(f'  |> filter(fn: (r) => r["{key}"] == "{value}")' for key, value in tags.items()),
        '  |> filter(fn: (r) => r["_field"] == "{{y-value}}")',
    ]
    return "\n".join(lines)


def _check_time(kind: str, value: Optional[str]) -> Optional[str]:
    """A segment time: an xs:dateTime with an offset, the format of a UtcTime series."""
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{kind} {value!r} is not an xs:dateTime") from None
    if parsed.tzinfo is None:
        raise ValueError(f"{kind} {value!r} needs an offset, e.g. Z")
    return value


def linked_segment(*, measurement: str, tags: Dict[str, str],
                   bucket: str = INFLUX_BUCKET, description: str = "",
                   start_time: Optional[str] = None, end_time: Optional[str] = None,
                   write_mode: Optional[WriteModeValue] = None) -> DmpLinkedSegment:
    """A segment on the workspace's InfluxDB. Its *start_time* and *end_time*
    bound what the DMP reads; a segment with an *end_time* is ``Completed`` and
    read-only, one without is ``InProgress`` and open for writes. *write_mode*
    is authored only when given; absent, the DMP writes synchronously."""
    _check_time("start_time", start_time)
    _check_time("end_time", end_time)
    if start_time and end_time and datetime.fromisoformat(end_time) <= datetime.fromisoformat(start_time):
        raise ValueError("end_time must lie after start_time")
    _check_identifier("bucket", bucket)
    _check_identifier("measurement", measurement)
    for key, value in tags.items():
        _check_identifier("tag key", key)
        _check_identifier("tag value", value)
    return DmpLinkedSegment(
        description=description,
        StartTime=StartTime(value=start_time) if start_time else None,
        EndTime=EndTime(value=end_time) if end_time else None,
        State=State(value="Completed" if end_time else "InProgress"),
        Endpoint=Endpoint(value=f"{INFLUX_ORIGIN}/api/v2/query?org={INFLUX_ORG}"),
        Query=Query(value=flux_query(bucket, measurement, tags)),
        InfluxDb2Target=InfluxDb2Target(
            Bucket=Bucket(value=bucket),
            Measurement=Measurement(value=measurement),
            Tags=Tags(tag={key: Tag(value=value) for key, value in tags.items()}),
            WriteMode=TargetWriteMode(value=write_mode) if write_mode else None,
        ),
    )


def time_series(*, name: str, measurement: str, fields: Dict[str, RecordEntry],
                tags: Optional[Dict[str, str]] = None, description: str = "",
                segment: str = "Live", start_time: Optional[str] = None,
                end_time: Optional[str] = None,
                write_mode: Optional[WriteModeValue] = None) -> TimeSeriesCollection:
    """A series with one LinkedSegment. *tags* default to the owning AAS."""
    tags = {"asset": "{aas_id_short}"} if tags is None else tags
    return TimeSeriesCollection(
        description=description,
        Metadata=TimeSeriesMetadata(
            Name=Name(value={"en": name}),
            Record=TimeSeriesRecord(field=fields),
        ),
        Segments=TimeSeriesSegments(LinkedSegment={
            segment: linked_segment(measurement=measurement, tags=tags,
                                    start_time=start_time, end_time=end_time,
                                    write_mode=write_mode),
        }),
    )



def operation_log(operation: ModelReference, *, name: str, measurement: str,
                  field: str = "Operation") -> TimeSeriesCollection:
    """A log series of one Operation: its outcome and duration next to the
    Operation itself, referenced, so its input, InOut and output variables are
    fields (``Operation.Uuid``) with their valueTypes and follow its definition."""
    fields: Dict[str, RecordEntry] = {
        "Outcome": record_field("xs:string", description="How the invocation ended"),
        "DurationMs": record_field("xs:long", description="Time from accepting the call to its answer"),
    }
    if field in fields:
        raise ValueError(f"the Operation's field {field!r} clashes with a log field")
    fields[field] = record_reference(operation, description="The invoked Operation's variables")
    return time_series(name=name, measurement=measurement, fields=fields)
