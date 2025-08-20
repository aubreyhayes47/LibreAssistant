<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Experts

LibreAssistant relies on a group of specialist "experts" that each analyze a goal from a different angle. Their independent outputs are later combined to provide a balanced response.

## Available experts

- **aggregation** – condenses the analyses from other experts into a concise summary.
- **argumentation** – supplies persuasive points supporting the goal.
- **communications** – crafts a public-facing message and identifies the target audience.
- **devils_advocate** – highlights potential risks or unintended consequences.
- **executive** – breaks the goal into an ordered list of actionable tasks.
- **research** – offers a brief research digest with at least one source.
- **visualizer** – proposes simple chart metadata to illustrate progress.

Each expert runs independently. Their results can be collected in a dictionary and passed to `aggregation.summarize` to produce a final report.

## Example

```python
from libreassistant.experts import argumentation, communications, aggregation

goal = "build a community garden"
analysis = {
    "communications": communications.analyze(goal),
    "argumentation": argumentation.analyze(goal),
}
summary = aggregation.summarize(analysis)
print(summary)
```
