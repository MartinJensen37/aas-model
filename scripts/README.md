# IDTA Submodel Regeneration

`idta_generate.py` regenerates the IDTA pydantic model modules in
`src/aas_pydantic/submodel_templates/` from the JSON templates in the
`submodel-templates` submodule.

## Layout

- `../submodel-templates/published/` contains the source template JSON.
- `idta_generate.py` maps template elements to pydantic container and leaf
  classes. Its default `TEMPLATES` tuple pins the source paths used by the
  package; generated module docstrings record each source path relative to
  `published/`.
- `../src/aas_pydantic/submodel_templates/` contains the generated modules.

## Regenerate

Run from the repository root:

```bash
python scripts/idta_generate.py
python scripts/idta_generate.py '<Template Path>'
python scripts/idta_generate.py '<Template Path>' /tmp/generated-models
```

A relative template path is resolved under `submodel-templates/published/`.
Without arguments the generator writes all pinned templates to
`src/aas_pydantic/submodel_templates/`. A missing pinned input fails the run
rather than silently generating a partial package.

## Generated model behavior

- Container children are direct named fields. Safe `idShort` spellings retain
  their original casing (for example, `ManufacturerName`); invalid identifier
  characters are sanitized, repeatable `__NN__` suffixes are stripped, and
  Python keywords receive a trailing underscore.
- `SMT/Cardinality` values `One` and missing cardinality qualifiers produce
  required fields; `ZeroToOne` produces optional fields.
- Multi-cardinality elements use dynamic `Dict[str, Element]` fields. A
  `SubmodelElementList` remains a list with homogeneous item typing when the
  template permits it.
- Semantic IDs, descriptions, supplemental semantic IDs, value types, and
  relevant leaf metadata are retained on generated classes. Pydantic field/type
  name collisions use `_t: TypeAlias` aliases.
- Repeated container definitions with the same resolved concept are merged into
  one field union. A single-cardinality field remains required only when it is
  present and required in every variant; consistent dynamic maps and lists
  retain their container defaults. Conflicting field types or repeatable
  defaults fail generation instead of dropping a variant.

Cardinality and list behavior intentionally follow the generator's current
policy; the generator does not rewrite template structures to make a particular
release importable. Review generated diffs and run the focused generator tests
before adopting an upstream template release. Do not generate into the package
directory while another integration is preparing its target-model changes.

# DMP contract fixtures

`dmp_contract_fixtures.py` writes the model fixtures of aas-camel-dmp
(`dmp.component/src/test/resources/runtime-model-contracts/`): synthetic AIDs
and AIMCs built with `aas_model.testing`, one protocol or mapping form each, and
every resource of `RESOURCE_FACTORIES` as registration builds it. The DMP's
`RawModelContractFixtureTest` checks the files' hashes and that each case
compiles as the manifest expects.

```bash
PYTHONPATH=src python scripts/dmp_contract_fixtures.py \
    ../aas-camel-dmp/dmp.component/src/test/resources/runtime-model-contracts
```

Regenerate after changing the builders, a resource or a template, and review
every changed compile outcome in the DMP; never edit the generated JSON.
