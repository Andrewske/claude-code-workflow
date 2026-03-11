---
description: Generate 5 unique design variations of an existing page at /1, /2, /3, /4, /5 routes
---

# Five Designs

Generate 5 completely different design variations of an existing page. Each design must be visually distinct with its own aesthetic direction.

## Input

Page to redesign: $ARGUMENTS

If no argument provided, ask the user which page to redesign.

## Process

1. **Read the source page** - Understand its structure, content, and functionality
2. **Define 5 distinct aesthetics** - Each must be dramatically different:
   - Vary: color schemes (light/dark/colorful), typography styles, layout approaches, animation intensity, visual density
   - Pick from: brutalist, minimalist, maximalist, retro-futuristic, organic, luxury, playful, editorial, art deco, soft/pastel, industrial, cyberpunk, etc.
3. **Create each variant** - Implement at routes /1, /2, /3, /4, /5

## Tech Stack

- **Tailwind CSS v4** - Use the latest syntax and features
- **shadcn/ui components** - Build on top of these wherever possible, customize heavily via Tailwind

## Design Requirements (per variant)

Follow the frontend-design skill principles:
- **Typography**: Distinctive font choices (never Inter, Roboto, Arial) - use Tailwind's font utilities
- **Color**: Cohesive palette with intentional accents - leverage CSS variables and Tailwind theming
- **Motion**: Appropriate animations - use Tailwind's animation utilities + custom keyframes
- **Layout**: Unexpected, memorable spatial composition - Tailwind grid/flex
- **Details**: Backgrounds, textures, effects that create atmosphere
- **Components**: Use shadcn/ui as the base (Button, Card, Input, etc.) but style them distinctively for each aesthetic

## Output Structure

Create/update routing to serve 5 pages:
- `/1` - First design variant
- `/2` - Second design variant
- `/3` - Third design variant
- `/4` - Fourth design variant
- `/5` - Fifth design variant

## Before Coding

Present a brief table of the 5 aesthetics you'll implement:

| Route | Aesthetic | Key Characteristics |
|-------|-----------|---------------------|
| /1 | ... | ... |
| /2 | ... | ... |
| /3 | ... | ... |
| /4 | ... | ... |
| /5 | ... | ... |

Get user approval before implementing.

## Implementation via Parallel Sub-Agents

After user approves the aesthetics table, implement all 5 designs in parallel using the Task tool:

```
For each design (1-5), spawn a Task agent with:
- subagent_type: "general-purpose"
- model: "sonnet"
- prompt: Include:
  1. The source page content/path
  2. The specific aesthetic assignment from the table
  3. The route to create (/1, /2, etc.)
  4. Tech stack requirements (Tailwind v4, shadcn/ui)
  5. Design requirements from this skill
  6. Instruction to use shadcn-ui-expert agent for component guidance
```

**IMPORTANT**: Launch all 5 agents in a SINGLE message with 5 parallel Task tool calls. Do NOT wait for one to finish before starting others.

Example prompt structure for each agent:
```
Implement design variant [N] for [page].

**Aesthetic**: [name] - [key characteristics from table]
**Route**: /[N]
**Source page**: [path or content]

Requirements:
- Tailwind CSS v4 syntax
- shadcn/ui components as base, styled to match aesthetic
- Distinctive typography (never Inter/Roboto/Arial)
- Cohesive color palette
- Appropriate animations
- Production-quality implementation

Use the shadcn-ui-expert agent for component guidance when needed.
```

## Critical Rules

- NO two designs should feel similar
- Each must be production-quality, not a sketch
- Preserve all original functionality
- Make bold choices - this is about exploration
- All 5 implementations run in PARALLEL via sub-agents
