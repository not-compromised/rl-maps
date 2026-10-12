# Map style sheet

Working visual brief for the new map. Source: the owner's requests and corrections through September 8, 2026; consolidated by Codex root agent, thread ID unknown. This records design intent, not implemented or gameplay-tested features.

## Scale and intricacy

Latest direction, verbatim from the owner: "yeah maybe our previous map wasnt too big it just wasn't intricate enough."

Overall size remains open. The earlier request to halve the footprint is no longer a fixed requirement. Judge scale by the density and variety of the journey: interesting flight around landmarks, connected spaces, changing elevations, and detail visible from the car. A large world can work if the route uses it well. Keep the separately requested closer ring spacing and three calibrated ring sizes; more scenery alone does not fix flight pacing.

## Visual identity

Carry forward the haunted coastal shipwreck concept as the working direction. The old implementation is archived; its geometry and dimensions are not the new specification. Ice Rings is the approved mountain and environment-quality reference, not a request to replace the coast with its exact winter theme.

- Playful, eerie Flying Dutchman atmosphere inspired by SpongeBob, with ghostly light, torn sails and crooked silhouettes.
- Detailed physical materials and believable construction: weathered timber, woven canvas, corroded fittings, rope, fractured stone, snow and water. The user requested near-photoreal detail while retaining the haunted mood.
- One connected coastal world with a recognizable main ship, cliffs, mountains, coves and distinct wrecks. The route should make these places feel related.

## Palette and lighting

The carried-forward palette uses dark teal atmosphere, ghost-green route light, warm weathered wood, pale canvas and cold gray rock. Snow provides brighter peak silhouettes. Separate materials by light response and value so the scene remains readable through fog.

Use lanterns and luminous ring edges to guide the player. Keep the next ring clearly visible against its local background. Low fog and distant haze give depth; nearby wood, rock and openings retain contrast. Avoid bathing everything in the same dark green. Tune fog to the final world scale instead of copying Ice Rings' numeric settings.

## Ships and damage

The main ship must read as a complete vessel: curved hull, bowsprit, masts, yards, rigging, upper deck, rails, stairs, raised stern deck and helm. The player flies through its interior and around its structure.

The entrance is a cannon-blasted hole surrounded by splintered timber, with a round ring fitted into the breach. Show hull thickness, exposed ribs and the deck above. Intentional damage must look physically explained rather than unfinished modeling. Keep ropes, sails and broken beams outside the flight opening.

Other wrecks differ in hull plan, silhouette and damage. Examples carried forward from the brief are a low barge, a broken hull with a fallen mast, and an exposed rib skeleton resting on rocks. Rotation and scale changes alone do not create distinct ships.

## Mountains, coast and water

Use Ice Rings' layered mountain forms as the reference: distinct peaks and ridges, jagged smaller rocks, creases, ledges, boulder fields and textured surface relief. Detail needs to work at three distances: whole mountain silhouette, formations beside the route, and material detail near the car.

Snow begins above an adjustable altitude with an irregular transition. Expose rock on steep slopes and break up smooth snow coverage. UDK's vertical axis is Z. Keep rocks and erosion visible below the snow line as well.

Cliffs and shorelines connect the mountains to water and the harbor. Give coastal stretches their own formations and wreck arrangements. Water should have visible surface response and shoreline context. Preserve the requested mountain tunnel, with a convincing entrance, continuous interior and clear lighting; the route must actually pass through the mountain.

## Route composition

One ordered path winds through the world. Vary horizontal and vertical movement: through the ship, around hull and rigging, beside the water, up cliffs, through the mountain, around peaks, down a gorge and around a lookout. These are composition ingredients, not a locked chapter sequence.

Use recurring landmarks from different heights and angles so the journey feels connected. Give each section a distinct approach and reveal. Keep travel between challenges purposeful; empty transfers and repeated local circuits were weaknesses of the archived map. A broad view can provide a deliberate rest, but repeated long flights without a nearby challenge are not the target.

Retain the requested 5–10 checkpoints as the planning range, with progressively harder sections and calm restart areas. Ring difficulty comes from opening size, spacing, turns and surroundings; change these deliberately instead of shrinking every dimension at once. Exactly three round sizes, with the old level 8 small-ring family as the medium calibration reference and one smaller hard size. Final dimensions require the small-course flight test described in the mapmaking guide.

## Rope rings and camera target

Gravity is -650 along UDK's Z axis, explicitly set with WorldInfo.GlobalGravityZ. Do not inherit the editor default. Verify the saved setting after reopening and the effective gravity in authorized runtime testing.

Use exactly round openings with a seamless braided rope surface. Strands follow the circle continuously; the texture direction follows the strands rather than cutting across the hoop. Keep a smooth collision shape aligned with the visible inner opening. Current calibration radii are easy 620, medium 470 and hard 340 UDK units; player flight feedback remains the acceptance test.

The camera guide is a removable training ball at the current stage's completion point. It must be stationary and have collision disabled so the player cannot knock the guide away. Destroy the old target on checkpoint advance and create the next endpoint target. Handle reset, removal/re-enable and finish cleanup explicitly. Ice Rings uses Ball_TA for this purpose; the user's word "fake" describes the required training behavior, not permission to leave a normal movable ball on the course.

## UI and guidance notes

Keep stage, progress, deaths, time and finish feedback readable without obscuring the next approach. Mark checkpoint decks with consistent lanterns and deck markings, and show live activation distinctly from decorative paint. The removable camera target points at the current stage's completion point and updates on advance/reset. Provide an understandable removal/re-enable control without altering camera or controller settings.

The route remains readable with the camera target removed. Decorative objects should not resemble alternative playable rings. Damage, fog and glowing details must preserve the visible opening and approach clearance.

## Visual acceptance

Review at car height as well as from overhead. Show the ship entrance, interior under the upper deck, waterside stretch, cliff ascent, tunnel and snowy peak approach. The next ring should be readable in each view, with enough surrounding detail to identify the place. A wide overview must show a connected world and winding route rather than repeated islands on a line.

Judge detail in Rocket League once testing is authorized. Blender renders and an editor loaded with missing reference assets cannot establish the final material or fog quality. Require working ring validation and checkpoints alongside the visual work.

Technical workflow: [mapmaking guide](docs/reference/mapmaking.md). Measured reference: [Ice Rings study](docs/reference/ice-rings.md). Historical visual brief is preserved locally in `docs/local/originals/archived-map/DESIGN.md`.
