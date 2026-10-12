# Revision 99 validation

Map: Story of Toys. Status: playable work in progress.

Tested package: `AndysRoomRings03_antifreeze.upk`
Size: 689,561,614 bytes
SHA256: `01662749ad05083631fb2ac37850bbad66c10c042d5d88f327ecd6203a4af34c`

The saved, reopened, backed-up, installed and offline-tested package has this same hash. Public packaging changes only the loader title, author, preview and accompanying documents; it does not modify the tested map bytes.

## Verified

- Production lighting completed all 193 mappings. Editor Lighting Results and Map Check were empty with all filters enabled.
- Reopen checks passed 193 mesh components, 85 room meshes, 1,809 origins, 14 target bindings and 3,495 graph nodes. Temporary review cameras are absent.
- Source checks passed connected globe geometry, all 18 crib spindle joins, UV overlap, export shading, hat support and route clearance. Toolkit tests: 57 passed, one optional skip.
- All 100 controlled physical crossings advanced through seven stages with zero deaths. These tests placed the car and set velocity to cross each gate; they did not assign progression variables to force completion.
- Five invalid approaches were rejected: skipped gate, reverse first gate, early checkpoint, early finish and early restart contact.
- Twenty-one state checks passed, including exploration with a frozen 104-second result, physical golden-alien restart, and one bed-stage floor reset preserving ten rings.
- Twelve target snapshots verified one target at each active endpoint, replacement across stages and reset, removal at completion and restoration on restart. The old object reference persisted briefly after the live target disappeared; a later exploration snapshot confirmed it cleared.
- Effective gravity measured -661.02 units/s² over 0.49 seconds, within the predefined tolerance of -650 ±30. Log timestamps have 0.01-second precision.
- Ordinary W/S input drove 1,896.52 units along the hat while remaining supported.
- Actual game captures reviewed the pillow, globe and hat. The detailed crib/mobile review used baked editor views; attempted car-height crib views were obstructed.

## Remaining work

Crib/trim striping remains in both Lit and Unlit editor modes. A flat-normal experiment and larger arch lightmap charts did not resolve it. Bedding artwork is still soft.

Full-course ordinary-input flight, physical target contact/nonblocking, repeated-crossing and rim-contact probes, exhaustive prop/boundary contacts, fast falls, independent map-owned boost, other game resolutions and performance measurements remain unproved.

The observed game window was 2560 by 1440. No frame-time or formal load-time benchmark was recorded. Source tests and controlled crossings are not a substitute for ordinary-input flight feedback.

Test sessions were closed and temporary files removed; input and graphics settings retained their pre-test hashes.
