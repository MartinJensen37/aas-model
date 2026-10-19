#!/usr/bin/env python3
"""Generate aas_pydantic models from IDTA submodel template JSON.

Emits named-field pydantic models from IDTA templates:

    Submodel:  ManufacturerName: ManufacturerName
    SMC:       InterfaceTemplateForMQTT: InterfaceTemplateForMQTT
    SML:       value: List[Item]

Container children are emitted as direct fields using their idShort spelling.
Required and optional fields follow SMT/Cardinality; multi-cardinality
elements become dynamic name-keyed maps, while SubmodelElementLists retain
their list behavior. IDTA example children define the class metadata, including
semantic_id, description, value_type, and supplemental semantic IDs.
"""

import json
import keyword
import os
import re
import sys
from dataclasses import dataclass

# modelType → Python type name
ELEMENT_MAP = {
    "Property": "Property",
    "MultiLanguageProperty": "MultiLanguageProperty",
    "Range": "Range",
    "ReferenceElement": "ReferenceElement",
    "RelationshipElement": "RelationshipElement",
    "File": "File",
    "Blob": "Blob",
    "Capability": "Capability",
    "Operation": "Operation",
}


def safe_name(name: str) -> str:
    # IDTA placeholders like ``Mode__00__`` mean "a repeatable instance whose
    # id_short the user picks" — strip the ``__NN__`` suffix so class and field
    # names are the clean base name (``Mode`` → field ``mode``).
    name = re.sub(r"__\d+__$", "", name or "")
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


_CONCRETE_ID_SHORT = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def id_short_default(el: dict) -> list:
    """The class-level ``id_short`` default: the template's idShort when it is
    a concrete name. Placeholders (``{property_name}``, ``Mode__00__``) and
    missing idShorts (SML items) get none, since the instance name is chosen
    by the author (a dict key or a list position)."""
    raw = el.get("idShort") or ""
    if not _CONCRETE_ID_SHORT.fullmatch(raw) or re.search(r"__\d+__$", raw):
        return []
    return [f"    id_short: AasIdString = {json.dumps(raw)}"]


def snake(name: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    return s.replace("-", "_").lower()


def field_name(name: str) -> str:
    """Preserve idShort spelling while producing a valid Python identifier.

    IDTA ``__NN__`` placeholder suffixes are stripped; invalid characters are
    replaced with underscores and Python keywords receive a trailing underscore.
    """
    name = re.sub(r"__\d+__$", "", name or "")
    s = safe_name(name)
    if s and s[0].isdigit():
        s = f"_{s}"
    if keyword.iskeyword(s):
        s += "_"
    return s


_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_ROOT = os.path.join(_ROOT, "submodel-templates", "published")
OUTPUT_ROOT = os.path.join(_ROOT, "src", "aas_pydantic", "submodel_templates")
TEMPLATES = (
    "Capability Description/1/0/1/IDTA 02020_Template_Capability_Description.json",
    "Control Component Instance/2/0/1/IDTA 02016-2-0-1 _Template_ControlComponentInstance_forAASMetamodelV3.1.json",
    "Control Component Type/2/0/2/IDTA 02015-2-0-2 _Template_ControlComponentType_forAASMetamodelV3.1.json",
    "Hierarchical Structures enabling Bills of Material/1/1/2/IDTA 02011-1-1-2_Template_HSEBoM_forAASMetamodelV3.1.json",
    "Digital nameplate/3/0/2/IDTA 02006-3-0-2_Template_Digital Nameplate.json",
    "Asset Interfaces Mapping Configuration/2/1/IDTA 02027_Template_AIMC.json",
    "Asset Interfaces Description/1/2/IDTA 02017_Template_Asset Interfaces Description.json",
    "Time Series Data/1/1/2/IDTA 02008-1-1-2_Template_TimeSeriesData_forAASMetamodelV3.1.json",
)


def to_camel(name: str) -> str:
    """CamelCase a (snake_case) id_short for a dedicated leaf class name:
    ``year_of_construction`` → ``YearOfConstruction``, ``u_r_i_of_the_product``
    → ``URIOfTheProduct``.  The class name therefore never equals the
    snake_case field name (pydantic rejects field==annotation self-refs), and
    each element's template defaults live on its own named class."""
    parts = re.split(r"[^0-9a-zA-Z]+", name or "")
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def sid_namespace_suffix(base_name: str, sid: str) -> str:
    """Readable disambiguation suffix for a class whose id_short collides with
    another element of a *different* semanticId (e.g. AID's nested object-
    schema ``properties`` / ``property_name`` under ``json-schema#properties``
    / ``json-schema#propertyName``).  Prefers the semanticId fragment when it
    differs from the id_short (``json-schema#propertyName`` →
    ``property_name_json_schema``); otherwise uses the last namespace path
    segment (``.../ControlComponent/Skill/Errors/2/0`` → ``Errors_skill``)."""
    frag = sid.split("#")[-1] if "#" in sid else ""
    path = [p for p in sid.split("#")[0].split("/") if p and not p.isdigit()]
    if frag and snake(frag) != snake(base_name):
        return snake(frag)
    ns = path if frag else (path[:-1] if path else [])
    return snake(ns[-1]) if ns else ""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    types: tuple[str, ...]
    shape: str = "single"
    required: bool = False
    aas_id_short: str = ""
    minimum: int = 0

    def render(self, aliases: set[str]) -> str:
        types = list(self.types)
        if len(types) == 1 and types[0] == self.name:
            aliases.add(self.name)
            types[0] = f"{self.name}_t"
        annotation = types[0] if len(types) == 1 else f"Union[{', '.join(types)}]"
        if self.shape == "map":
            annotation = f"Dict[str, {annotation}]"
        elif self.shape == "list":
            annotation = f"List[{annotation}]"
        elif not self.required:
            annotation = f"Optional[{annotation}]"

        extra = {}
        if self.aas_id_short:
            extra["aas_id_short"] = self.aas_id_short
        if self.minimum:
            extra["idta_min_cardinality"] = self.minimum
        if self.shape == "map":
            default = (f"Field(default_factory=dict, json_schema_extra={json.dumps(extra)})"
                       if extra else "{}")
        elif self.shape == "list":
            default = "[]"
        elif extra:
            args = "" if self.required else "default=None, "
            default = f"Field({args}json_schema_extra={json.dumps(extra)})"
        elif self.required:
            default = None
        else:
            default = "None"
        suffix = f" = {default}" if default is not None else ""
        return f"    {self.name}: {annotation}{suffix}"


def merge_fields(class_name: str, bodies: list, compatible=None) -> list[FieldSpec]:
    """Merge repeated definitions of one semantic container concept.

    Fields present in every variant stay required only when they are required
    in every variant. Dynamic maps and list fields keep their empty-container
    defaults when absent from another variant. Conflicting field types or
    repeatable metadata are rejected instead of silently choosing one variant.
    """
    variants = []
    field_order = []
    for body in bodies:
        fields = {}
        for field in body:
            if field.name in fields:
                raise ValueError(f"Duplicate field {class_name}.{field.name}")
            fields[field.name] = field
            if field.name not in field_order:
                field_order.append(field.name)
        variants.append(fields)

    merged = []
    for name in field_order:
        definitions = [variant[name] for variant in variants if name in variant]
        first = definitions[0]
        types = list(dict.fromkeys(t for spec in definitions for t in spec.types))
        if any(spec.shape != first.shape for spec in definitions) or (
            len({spec.types for spec in definitions}) > 1 and (
                first.shape != "single" or compatible is None or
                not all(compatible(types[0], candidate) for candidate in types[1:])
            )
        ):
            raise ValueError(
                f"Incompatible field types for {class_name}.{name}: "
                f"{', '.join(sorted(types))}"
            )
        if first.shape in ("map", "list"):
            if any((spec.aas_id_short, spec.minimum) !=
                   (first.aas_id_short, first.minimum) for spec in definitions[1:]):
                raise ValueError(
                    f"Incompatible repeatable defaults for {class_name}.{name}"
                )
            merged.append(first)
            continue
        required_everywhere = (
            len(definitions) == len(variants)
            and all(spec.required for spec in definitions)
        )
        merged.append(FieldSpec(name, tuple(types), required=required_everywhere,
                                aas_id_short=first.aas_id_short,
                                minimum=first.minimum))
    return merged


def extract_semantic_id(el: dict) -> str:
    sem = el.get("semanticId") or {}
    for k in sem.get("keys", []) or []:
        if k.get("value"):
            return k.get("value", "")
    return ""


def extract_supplemental_semantic_ids(el: dict) -> list:
    """Supplemental semanticIds (list of IRIs) from ``supplementalSemanticIds``.
    These disambiguate elements that share a main semanticId — e.g. the AID
    ``InterfaceTemplateFor*`` all use ``.../Interface`` but each protocol has a
    unique supplemental IRI (per the IDTA PDF; the published JSON had OPC UA /
    BACnet copy-pasted from MQTT and is patched in the vendored copy)."""
    out = []
    for s in (el.get("supplementalSemanticIds") or []):
        for k in (s.get("keys") or []):
            if k.get("value"):
                out.append(k["value"])
    return out


def extract_description(el: dict) -> str:
    d = el.get("description")
    if isinstance(d, list):  # AAS JSON: [{"language": "en", "text": "..."}]
        return d[0].get("text", "") if d else ""
    if isinstance(d, dict):
        texts = d.get("texts") or []
        return texts[0].get("text", "") if texts else ""
    return ""


def extract_value_type(el: dict) -> str:
    return el.get("valueType", "")


def metadata_lines(el: dict, *, include_empty_semantic_id: bool = True) -> list:
    """Class defaults common to leaves, containers, and list wrappers."""
    lines = id_short_default(el)
    sid = extract_semantic_id(el)
    if sid or include_empty_semantic_id:
        lines.append(f'    semantic_id: str = {json.dumps(sid)}')
    desc = extract_description(el)
    if desc:
        lines.append(f'    description: str = {json.dumps(desc)}')
    supp = extract_supplemental_semantic_ids(el)
    if supp:
        lines.append(f'    supplemental_semantic_ids: List[str] = {json.dumps(supp)}')
    return lines


def extract_cardinality(el: dict) -> str:
    """Cardinality qualifier value (e.g. ``ZeroToMany``, ``ZeroToOne``, ``One``)
    — how many instances of this element a container may hold.

    Templates encode it under the standard qualifier ``type``
    ``SMT/Cardinality``."""
    for q in (el.get("qualifiers") or []):
        if q.get("type") == "SMT/Cardinality":
            return (q.get("value") or "").strip()
    return ""


# Cardinalities that allow more than one instance of an element → the
# values model field becomes a dynamic ``Dict[str, Element]`` (name-keyed),
# so MANY instances are possible — exactly like the pre-values-model dicts.
_MULTI_CARDINALITY = {
    "ZeroToMany", "OneToMany",  # standard SMT encodings
    "TwoToMany", "Three",       # other >1 encodings in the wild
    "Recursive",                # recursive structures allow unbounded nesting
}


def emit_reference(ref: dict, indent: str) -> list:
    """Source lines constructing a pydantic Reference from an AAS JSON
    reference dict (``{"type": ..., "keys": [...]}``)."""
    cls = "ModelReference" if ref.get("type") == "ModelReference" else "ExternalReference"
    key_src = [
        f'{indent}        Key(type_={json.dumps(k.get("type", ""))}, '
        f'value={json.dumps(k.get("value", ""))}),'
        for k in (ref.get("keys") or [])
    ]
    lines = [f"{indent}{cls}("]
    if key_src:
        lines.append(f"{indent}    key=(")
        lines.extend(key_src)
        lines.append(f"{indent}    ),")
    lines.append(f"{indent})")
    return lines


def is_placeholder_endpoint(ref) -> bool:
    """True when a RelationshipElement endpoint is a template placeholder.

    Several templates (e.g. HSEM ``SameAs``) declare ``first``/``second`` as a
    ``ModelReference`` whose only key is a ``GlobalReference`` "EMPTY" — a
    ModelReference's FIRST key must be an Identifiable (AASd-123), so such
    endpoints carry no real target and would make the generated class fail
    validation at import.  Skip them (endpoints stay unset/None).
    """
    if not isinstance(ref, dict):
        return True
    if ref.get("type") == "ModelReference":
        keys = ref.get("keys") or []
        if keys and keys[0].get("type") == "GlobalReference":
            return True
    return False


def children_of(el: dict) -> list:
    return [
        c
        for c in (el.get("submodelElements") or el.get("value")
                  or el.get("statements") or [])
        if isinstance(c, dict)
    ]


_RESERVED_FIELDS = {
    "id", "id_short", "description", "display_name", "semantic_id",
    "supplemental_semantic_ids", "qualifiers", "entity_type", "global_asset_id",
    "type_value_list_element", "value_type_list_element",
    "semantic_id_list_element", "order_relevant", "value",
}


def element_field(name: str, raw: str, types: tuple[str, ...], *,
                  shape: str = "single", required: bool = False,
                  minimum: int = 0) -> FieldSpec:
    """Represent a child before formatting its Python declaration."""
    renamed = field_name(raw) != raw and not re.search(r"__\d+__$", raw)
    return FieldSpec(name, types, shape=shape, required=required,
                     aas_id_short=raw if renamed else "", minimum=minimum)


def gen_template(template_path: str, output_dir: str):
    with open(template_path) as f:
        data = json.load(f)
    submodels = data.get("submodels", [])
    if not submodels:
        print(f"No submodels in {template_path}")
        return
    sm = submodels[0]
    sm_name = safe_name(sm["idShort"])

    # ── SemanticId-aware class naming ──
    # IDTA templates may use one id_short for several distinct element types
    # distinguished by semanticId (AID: ``properties`` = td#PropertyAffordance
    # vs json-schema#properties; ``property_name`` = PropertyDefinition vs
    # json-schema#propertyName; CCT: Type/Errors vs Skill/Errors).  The first
    # occurrence in document order keeps the plain class name (so every
    # top-level name stays stable — subclasses like mqtt_aid.py keep working);
    # later occurrences with a different semanticId get a disambiguated name
    # via :func:`sid_namespace_suffix`.  All template detail is preserved: the
    # id_short stays the field name and default instance id_short, and each
    # distinct semanticId lives on its own class.
    primary_sid = {}

    def _prescan_primary(el):
        if not isinstance(el, dict):
            return
        nm = safe_name(el.get("idShort", ""))
        if nm and el.get("modelType") in (
            "Submodel", "SubmodelElementCollection", "Entity", "SubmodelElementList",
        ):
            s = extract_semantic_id(el)
            if s and nm not in primary_sid:
                primary_sid[nm] = s
        for c in children_of(el):
            _prescan_primary(c)

    _prescan_primary(sm)

    # resolved class name → (base id_short, semanticId); guards uniqueness
    _name_identity = {}

    def check_class_name(name: str) -> None:
        if not name.isidentifier() or keyword.iskeyword(name):
            raise ValueError(f"Invalid class name from template idShort: {name!r}")

    def resolve_class_name(base: str, sid: str) -> str:
        """Class name for an element with id_short *base* and semanticId *sid*:
        plain name for the primary (document-first) occurrence, disambiguated
        otherwise.  Deterministic — the same (base, sid) always resolves to the
        same name, so recursion-stack lookups and definitions agree."""
        if sid == primary_sid.get(base, sid):
            cand = base
        else:
            suf = sid_namespace_suffix(base, sid)
            cand = f"{base}_{suf}" if suf else base
        i = 2
        c = cand
        while c in _name_identity and _name_identity[c] != (base, sid):
            c = f"{cand}_{i}"
            i += 1
        _name_identity.setdefault(c, (base, sid))
        return c

    # name → (meta_lines, body_lines); order of definition
    classes = {}
    class_body_variants = {}
    order = []
    entity_classes = set()
    sml_classes = set()
    leaf_bases = {}  # dedicated leaf element class name → base (leaf) class name
    leaf_identities = {}  # full definition (including metadata) → class name
    base_aliases = set()
    _used_leaf_types = {
        "Submodel", "SubmodelElement", "SubmodelElementCollection",
        "SubmodelElementList",
    }

    def register(name, meta, body, is_entity=False, is_sml=False):
        if name in leaf_bases or (
            name in classes and (is_entity != (name in entity_classes) or
                                 is_sml != (name in sml_classes))
        ):
            raise ValueError(f"Conflicting element types for generated class {name}")
        if name not in classes:
            classes[name] = (meta, body)
            class_body_variants[name] = [body]
            order.append(name)
        else:
            class_body_variants[name].append(body)
            classes[name] = (
                classes[name][0],
                merge_fields(
                    name, class_body_variants[name],
                    compatible=lambda a, b: all(
                        item in leaf_bases for item in (a, b)
                    ) and leaf_bases[a] == leaf_bases[b] and
                    _name_identity.get(a) == _name_identity.get(b),
                ),
            )
        if is_entity:
            entity_classes.add(name)
        if is_sml:
            sml_classes.add(name)

    def _disambiguated_leaf_name(base_name: str, sid: str, leaf_cls: str) -> str:
        """Unique class name for a leaf whose plain CamelCase name is owned by
        a DIFFERENT element (same id_short, different semanticId — e.g. CCI's
        ``Type``: ReferenceElement ``Instance/Type`` vs Property
        ``Skill/Parameter/Type``).  Uses the semanticId namespace suffix
        (``Type`` + ``.../Instance/Type/2/0`` → ``Type_instance``), then
        numeric dedup."""
        suf = sid_namespace_suffix(base_name, sid) or leaf_cls
        cand = f"{base_name}_{suf}"
        i = 2
        c = cand
        while c in leaf_bases or c in classes or (
            c in _name_identity and _name_identity[c] != (base_name, sid)
        ):
            c = f"{cand}_{i}"
            i += 1
        return c

    def leaf_class_for(c: dict, leaf_cls: str) -> str:
        """Register a leaf subclass for each distinct set of template defaults.

        Matching occurrences reuse a class; different semantic IDs, model
        types, or metadata receive disambiguated names. The authored Capability
        field retains its generic type for existing consumers.
        """
        sid = extract_semantic_id(c)
        elem_name = to_camel(safe_name(c.get("idShort", "")))
        # Capability is an author-supplied concept in existing subclasses;
        # specializing its field would reject authored Capability instances.
        if not elem_name or (elem_name == leaf_cls and leaf_cls == "Capability") or (
            not sid and not extract_description(c) and not extract_value_type(c)
            and not extract_supplemental_semantic_ids(c)
            and not (c.get("contentType") or c.get("content_type"))
            and not (c.get("first") or c.get("second"))
        ):
            return leaf_cls
        check_class_name(elem_name)
        meta = metadata_lines(c, include_empty_semantic_id=False)
        vt = extract_value_type(c)
        if vt and leaf_cls in ("Property", "Range"):
            meta.append(f'    value_type: str = {json.dumps(vt)}')
        ct = c.get("contentType") or c.get("content_type")
        if ct and leaf_cls in ("File", "Blob"):
            meta.append(f'    content_type: str = {json.dumps(ct)}')
        if leaf_cls == "RelationshipElement":
            for key_name in ("first", "second"):
                ref = c.get(key_name)
                if isinstance(ref, dict) and not is_placeholder_endpoint(ref):
                    ref_src = emit_reference(ref, "    ")
                    # The template's endpoint is an example: it is the default,
                    # not a restriction to its reference kind. A realized-by
                    # skill in the same AAS is a ModelReference, an external
                    # implementation an ExternalReference.
                    meta.append(f"    {key_name}: Reference = " + ref_src[0].lstrip())
                    meta.extend(ref_src[1:])
                    # The closing parenthesis is the value; no trailing comma.
        identity = (elem_name, sid, leaf_cls, tuple(meta))
        if identity in leaf_identities:
            return leaf_identities[identity]
        if (elem_name == leaf_cls or elem_name in classes or
                (_name_identity.get(elem_name) is not None and
                 _name_identity[elem_name] != (elem_name, sid))):
            name = _disambiguated_leaf_name(elem_name, sid, leaf_cls)
        else:
            name = elem_name
        register(name, meta, [])
        leaf_bases[name] = leaf_cls
        leaf_identities[identity] = name
        # Reserve the name so a later container/leaf of the same base id_short
        # dedups (``SerialNumber_2``) instead of silently shadowing this class.
        _name_identity.setdefault(name, (elem_name, sid))
        return name

    def leaf_annotation(c: dict, cls: str) -> tuple[str, ...]:
        """Accept an existing authored primary leaf alongside its variant."""
        primary = to_camel(safe_name(c.get("idShort", "")))
        if primary == cls:
            return (cls,)
        if primary in ELEMENT_MAP.values() and cls in leaf_bases:
            base_aliases.add(primary)
            return (cls, f"{primary}_base")
        if (primary != cls and primary in leaf_bases and cls in leaf_bases and
                leaf_bases[primary] == leaf_bases[cls] and
                _name_identity.get(primary) == _name_identity.get(cls)):
            return (cls, primary)
        return (cls,)

    def walk(el: dict, stack: tuple = (), name: str = None) -> list:
        """Register the ``{Name}`` container class for *el* with its children
        as DIRECT named fields (field name == id_short) — no ``value`` /
        ``submodel_element`` / ``statements`` wrapper (the standardized
        containers are abolished).

        Children whose template cardinality allows more than one
        (``SMT/Cardinality`` ZeroToMany/OneToMany) become dynamic
        ``Dict[str, Element]`` maps — MANY instances keyed by name.

        ``name`` overrides the class name (used for SML items whose template
        idShort is missing — falls back to ``{ListName}Item``).  ``stack``
        holds ``(id_short, semanticId, resolved_class_name)`` tuples of the
        elements currently being defined.  Recursion is detected by the pair
        (id_short, semanticId) — NOT the bare id_short — so a same-named child
        of a *different* semanticId (AID's nested object-schema ``properties``)
        is a real class, not a false recursion.  Recursive multi-cardinality
        children (HSEM ``Node`` in ``Node``) become empty ``Dict[str, Node]``
        maps; recursive single-cardinality children (AID's ``property_name`` →
        ``properties`` → ``property_name``) are optional (``Optional[X] =
        None``) so nesting stays representable without recursing forever.

        Single-cardinality children obey the template's ``SMT/Cardinality``:
        ``One`` (or a missing qualifier, which the templates use for mandatory
        elements) is required with NO default — pydantic rejects a constructed
        instance that omits it, so a mandatory element must be explicitly
        configured or the build fails; ``ZeroToOne`` is ``Optional[X] = None``
        and only present once set.
        """
        cname = resolve_class_name(name or safe_name(el.get("idShort", "")),
                                   extract_semantic_id(el))
        mt_el = el.get("modelType", "")
        check_class_name(cname)
        kids = children_of(el)
        stack_map = {(b, s): r for b, s, r in stack}
        fields = []
        field_id_shorts = {}
        for c in kids:
            child_name = safe_name(c.get("idShort", ""))
            child_sid = extract_semantic_id(c)
            child_resolved = resolve_class_name(child_name, child_sid)
            skey = field_name(c.get("idShort", child_name))  # field = id_short
            if skey in _RESERVED_FIELDS:
                raise ValueError(f"Child field reserved by AAS model: {skey} in {cname}")
            raw_name = c.get("idShort", child_name)
            if skey in field_id_shorts:
                raise ValueError(f"Duplicate or colliding idShorts in {cname}: {raw_name!r} and {field_id_shorts[skey]!r}")
            field_id_shorts[skey] = raw_name
            mt = c.get("modelType", "")
            if mt not in ELEMENT_MAP and mt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported modelType {mt!r} for {cname}.{skey}")
            if mt == "Operation" and any(c.get(k) for k in (
                "inputVariables", "outputVariables", "inoutputVariables", "inOutputVariables"
            )):
                raise ValueError(f"Operation variables are not supported for {cname}.{skey}")
            card = extract_cardinality(c)
            multi = card in _MULTI_CARDINALITY
            minimum = {"OneToMany": 1, "TwoToMany": 2, "Three": 3}.get(card, 0)
            # A missing ``SMT/Cardinality`` qualifier defaults to ``One`` — the
            # element is mandatory (the only missing-qualifier cases in the
            # templates are ``forms`` / ``fileName`` / ``definesSecurityScheme``
            # / ``iolv_payloadMappingElement``).
            required = card in ("One", None, "")
            if multi:
                # multi-cardinality → dynamic name-keyed map of this element.
                # Generic-leaf elements get a dedicated subclass carrying the
                # concept semanticId (e.g. ``class SameAs(RelationshipElement)``
                # with ``semantic_id``) — back-conversion groups by the
                # resolved element class, so no ``_multi_cardinality`` ClassVar
                # is needed.
                if mt in ("SubmodelElementCollection", "Entity"):
                    if (child_name, child_sid) in stack_map:
                        # recursive child (e.g. HSEM Node in Node) — an empty
                        # Dict[str, <container>] map; no instantiation, so the
                        # default cannot recurse.
                        fields.append(element_field(
                            skey, raw_name, (stack_map[(child_name, child_sid)],),
                            shape="map", minimum=minimum,
                        ))
                        continue
                    walk(c, stack + ((child_name, child_sid, child_resolved),))
                    fields.append(element_field(skey, raw_name, (child_resolved,),
                                                shape="map", minimum=minimum))
                elif mt == "SubmodelElementList":
                    _walk_sml(c, stack)
                    fields.append(element_field(skey, raw_name, (child_resolved,),
                                                shape="map", minimum=minimum))
                else:
                    leaf_cls = ELEMENT_MAP.get(mt, "Property")
                    _used_leaf_types.add(leaf_cls)
                    elem_cls = leaf_class_for(c, leaf_cls)
                    fields.append(element_field(skey, raw_name, (elem_cls,),
                                                shape="map", minimum=minimum))
                continue
            if mt in ("SubmodelElementCollection", "Entity"):
                if (child_name, child_sid) in stack_map:
                    # Recursive single-cardinality child (AID object schema:
                    # ``property_name → properties → property_name``).  These
                    # are ZeroToOne in the templates — optional, so not
                    # instantiated unless set (this also breaks the recursion
                    # cleanly).
                    rec = stack_map[(child_name, child_sid)]
                    fields.append(element_field(skey, raw_name, (rec,)))
                    continue
                walk(c, stack + ((child_name, child_sid, child_resolved),))
                fields.append(element_field(skey, raw_name, (child_resolved,),
                                            required=required))
            elif mt == "SubmodelElementList":
                _walk_sml(c, stack)
                fields.append(element_field(skey, raw_name, (child_resolved,),
                                            required=required))
            else:
                leaf_cls = ELEMENT_MAP.get(mt, "Property")
                _used_leaf_types.add(leaf_cls)
                types = leaf_annotation(c, leaf_class_for(c, leaf_cls))
                fields.append(element_field(skey, raw_name, types,
                                            required=required))
        # container class: attributes (semantic_id, ...) + the typed child
        # fields directly (no ``value``/``submodel_element``/``statements``
        # wrapper).  Required children have NO default — pydantic enforces they
        # are provided.
        meta = metadata_lines(el)
        is_entity = mt_el == "Entity"
        if is_entity:
            _used_leaf_types.add("Entity")
            meta.append(
                f'    entity_type: str = {json.dumps(el.get("entityType", "CoManagedEntity"))}'
            )
            gid = el.get("globalAssetId")
            if gid:
                meta.append(f'    global_asset_id: str = {json.dumps(gid)}')
        register(cname, meta, fields, is_entity=is_entity)
        return fields

    def _walk_sml(c: dict, stack: tuple):
        """Register an SML class with a typed ``value: List[Item]`` (AASd-108:
        homogeneous lists only — heterogeneous ones start empty)."""
        cname = resolve_class_name(safe_name(c.get("idShort", "")),
                                   extract_semantic_id(c))
        check_class_name(cname)
        item_kids = children_of(c)
        sub_meta = metadata_lines(c)
        declared_item = c.get("typeValueListElement")
        if declared_item:
            sub_meta.append(f'    type_value_list_element: str = {json.dumps(declared_item)}')
        declared_value_type = c.get("valueTypeListElement")
        if declared_value_type:
            sub_meta.append(f'    value_type_list_element: str = {json.dumps(declared_value_type)}')
        declared_sid = extract_semantic_id({"semanticId": c.get("semanticIdListElement")})
        if declared_sid:
            sub_meta.append(f'    semantic_id_list_element: str = {json.dumps(declared_sid)}')
        if "orderRelevant" in c:
            sub_meta.append(f'    order_relevant: bool = {bool(c["orderRelevant"])}')
        item_classes = set()  # for AASd-108 homogeneity check
        stack_map = {(b, s): r for b, s, r in stack}
        for item in item_kids:
            imt = item.get("modelType", "")
            if imt not in ELEMENT_MAP and imt not in (
                "SubmodelElementCollection", "Entity", "SubmodelElementList"
            ):
                raise ValueError(f"Unsupported list item modelType {imt!r} for {cname}")
            if imt in ("SubmodelElementCollection", "Entity"):
                item_name = safe_name(item.get("idShort", f"{cname}Item"))
                item_sid = extract_semantic_id(item)
                if (item_name, item_sid) in stack_map:
                    # Recursive item — skip entirely.
                    continue
                item_resolved = resolve_class_name(item_name, item_sid)
                walk(item, stack + ((item_name, item_sid, item_resolved),),
                     name=item_name)
                item_classes.add(item_resolved)
            elif imt == "SubmodelElementList":
                item_classes.add("SubmodelElementList")
            else:
                leaf_cls = ELEMENT_MAP[imt]
                _used_leaf_types.add(leaf_cls)
                item_classes.add(leaf_cls)
        if declared_item in ELEMENT_MAP and not any(
            item.get("modelType") in ("SubmodelElementCollection", "Entity")
            for item in item_kids
        ):
            item_classes = {ELEMENT_MAP[declared_item]}
        if declared_value_type and item_classes == {"Property"}:
            item_name = f"{cname}Item"
            item_meta = [f'    value_type: str = {json.dumps(declared_value_type)}']
            if item_name in classes and classes[item_name][0] != item_meta:
                raise ValueError(f"Conflicting list item class metadata: {item_name}")
            if item_name not in classes:
                register(item_name, item_meta, [])
                leaf_bases[item_name] = "Property"
            item_classes = {item_name}
        if item_classes and len(item_classes) == 1:
            # Homogeneous list — declare item_type so back-conversion can
            # restore item types (AASd-114 strips item semanticIds in basyx),
            # but start EMPTY: the template's example items are empty
            # scaffolding and would leak into every generated instance (e.g.
            # nameplate ``Markings`` carrying an empty ``marking_name`` SMC).
            item_cls = next(iter(item_classes))
            sub_meta.append(f"    item_type: ClassVar = {item_cls}")
            sml_body = [FieldSpec("value", (item_cls,), shape="list")]
        else:
            # Heterogeneous or empty (e.g. CapabilityPropertyType lists
            # Range/Property/MLP exemplars) — basyx cannot represent a
            # mixed-type SML (AASd-108), so start empty; users populate it
            # with a homogeneous list.
            sml_body = [FieldSpec("value", ("Any",), shape="list")]
        register(cname, sub_meta, sml_body, is_sml=True)

    sm_meta = metadata_lines(sm)
    walk(sm)

    admin = sm.get("administration", {})
    sm_meta.append(f'    VERSION: ClassVar[str] = "{admin.get("version", "1")}"')
    sm_meta.append(f'    REVISION: ClassVar[str] = "{admin.get("revision", "0")}"')
    # prepend the Submodel-level meta (walk registered semantic_id/description)
    classes[sm_name] = (sm_meta, classes[sm_name][1])

    # ── Assemble file ──
    # Build the body first, then derive imports from the assembled text.
    body = []
    aliases_emitted = set()
    alias_definitions = []
    for name in order:
        meta, cbody = classes[name]
        if name == sm_name:
            base = "Submodel"
        elif name in entity_classes:
            base = "Entity"
        elif name in sml_classes:
            base = "SubmodelElementList"
        elif name in leaf_bases:
            base = leaf_bases[name]
        else:
            base = "SubmodelElementCollection"
        body.append(f"class {name}({base}):")
        body.extend(meta)
        if not cbody and base in ("Submodel", "Entity", "SubmodelElementCollection"):
            body.append('    pass')
        for field in cbody:
            # Pydantic resolves a same-named annotation to the field itself.
            # Postponed annotations allow the alias to follow all classes.
            if (field.types == (field.name,) and
                    field.name not in aliases_emitted):
                alias_definitions.extend((
                    f"# alias so field ``{field.name}_t`` can name a class of the same id_short",
                    f"{field.name}_t: TypeAlias = {field.name}",
                ))
            body.append(field.render(aliases_emitted))
        body.append('')

    # Postponed annotations let aliases follow their definitions. This matters
    # for recursive/list graphs where a same-named referenced container is
    # registered later in document traversal order.
    body.extend(alias_definitions)
    for base in sorted(base_aliases):
        body.append(f"{base}_base: TypeAlias = {base}")

    body.append('# ── Resolve forward references (Pydantic circular refs) ──')
    for name in order:
        body.append(f'{name}.model_rebuild()')
    body.append('')

    all_src = "\n".join(body)
    lines = []
    template_abs = os.path.abspath(template_path)
    relative_to = (
        TEMPLATE_ROOT
        if os.path.commonpath((TEMPLATE_ROOT, template_abs)) == TEMPLATE_ROOT
        else _ROOT
    )
    # The same on every platform: the checked-in modules are compared with a regeneration.
    source_path = os.path.relpath(template_abs, relative_to).replace(os.sep, "/")
    lines.append(f'"""{sm_name} - generated from IDTA template.')
    lines.append(f"Source: {source_path}")
    lines.append('"""')
    lines.append('')
    lines.append('from __future__ import annotations')
    lines.append('')
    typing_names = ["Any", "ClassVar", "List"]
    if "Dict[" in all_src:
        typing_names.append("Dict")
    if "Optional[" in all_src:
        typing_names.append("Optional")
    if "Union[" in all_src:
        typing_names.append("Union")
    if ": TypeAlias" in all_src:
        typing_names.append("TypeAlias")
    lines.append(f"from typing import {', '.join(typing_names)}")
    lines.append('from aas_pydantic import (')
    aas_types = {"Submodel", "SubmodelElement", "SubmodelElementCollection",
                 "SubmodelElementList", "Entity", "Qualifier",
                 "ExternalReference", "ModelReference", "Key"}
    aas_types |= set(ELEMENT_MAP.values())
    imports = sorted(t for t in _used_leaf_types if t in aas_types)
    # Reference endpoints (first/second) are typed Reference and default to an
    # ExternalReference/ModelReference of Keys.
    if ": Reference = " in all_src:
        imports = sorted(set(imports) | {"Reference"})
    if "ExternalReference(" in all_src:
        imports = sorted(set(imports) | {"ExternalReference", "Key"})
    if "ModelReference(" in all_src:
        imports = sorted(set(imports) | {"ModelReference", "Key"})
    lines.append('    ' + ', '.join(imports) + ',')
    lines.append(')')
    if "Field(" in all_src:
        lines.append('from pydantic import Field')
    if ": AasIdString" in all_src:
        lines.append('from aas_pydantic.aas_model import AasIdString')
    lines.append('')

    lines.extend(body)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{snake(sm_name)}.py")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"✅ {out_path}")
    print(f"   {sm_name}(Submodel) + {len(order) - 1} classes")


if __name__ == "__main__":
    # Resolve relative to the aas-model repo root (scripts/ is one level down),
    # so this works from any working directory.
    if len(sys.argv) >= 2:
        tmpl = sys.argv[1]
        if not os.path.isabs(tmpl):
            tmpl = os.path.join(TEMPLATE_ROOT, tmpl)
        gen_template(tmpl, sys.argv[2] if len(sys.argv) > 2 else OUTPUT_ROOT)
    else:
        for template in TEMPLATES:
            gen_template(os.path.join(TEMPLATE_ROOT, template), OUTPUT_ROOT)
        print(f"\nGenerated {len(TEMPLATES)} templates into {OUTPUT_ROOT}")
