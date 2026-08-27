## Summary

<!-- Describe the Unraid-facing change and why it is needed. -->

## Validation

- [ ] `scripts/validate.sh` passes
- [ ] Every changed published XML was saved, reopened, and applied through current Unraid Docker Authoring Mode
- [ ] No credentials, generated secrets, host-specific data, or personal data are included
- [ ] Runtime-affecting changes were tested on current Unraid
- [ ] Persistent `/data`, health checks, signup closure, and recreation were verified when applicable
- [ ] Adapter and derived-image changes pass unit tests, build from the pinned official digest, and retain the inherited startup plus composite healthcheck
- [ ] Fully-local changes verify streamed chat/tools, structured Graphiti output, 1536-dimension search embeddings, native 768-dimension memory embeddings, search backfill, and memory ingestion/retrieval
- [ ] Automated checks, host-local prototype evidence, packaged-image evidence, and Community Applications UI evidence are labeled separately

## Release impact

<!-- Note the official base and derived image digests, every data or vector-width migration, resource or networking change, publication dependency, and rollback implication. -->
