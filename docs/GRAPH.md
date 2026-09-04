# Graph

The production graph is a **hypergraph-like dependency model**, not just a simple item-to-item graph.

A normal recipe can require multiple inputs to produce multiple outputs:

```text
        +-- iron --+
        |           |
andesite|        [PROCESS] ---> brass
        |           |
        +-- zinc ---+
```

A simple directed edge loses the fact that the inputs belong to one execution. Therefore the canonical representation keeps `RECIPE`/`PROCESS` as an intermediate node.

## Two directions

Forward:

```text
item -> recipes it can participate in -> outputs
```

Reverse:

```text
output item -> every producing recipe -> required inputs
```

Both directions must be retained because a user can ask either "what makes this?" or "what can this make?".

## Recursive resolver

`get_tree(item_id, amount)` will:

1. validate the target registry ID
2. find every producing recipe
3. keep alternatives as sibling branches
4. resolve each input
5. expand tags without selecting an arbitrary member
6. recurse until no producing route is known
7. detect cycles using the current recursion stack
8. attach machines, fluids, catalysts and conditions
9. return a structured tree

## Cycles

The resolver must track a path-local set/stack, not a global visited set. A node can legitimately appear in multiple independent branches.

```text
A -> B -> C -> A
          ^ cycle
```

The result should contain an explicit cycle marker and the path that caused it.

## Alternative recipes

Never collapse multiple producing recipes into one during database construction. Ranking is a query-time concern. Possible deterministic ranking later includes fewest steps, fewest machines, lowest raw materials, lowest energy, fastest, and simplest.

## Tags

A tag is an OR constraint:

```text
#c:ingots/iron
   |
   +-- minecraft:iron_ingot
   +-- some_mod:iron_ingot
```

The resolver should preserve this logical choice until a policy explicitly asks it to select members.

## Quantities

For a recipe producing `P` units and a requested quantity `Q`, execution count is:

```text
ceil(Q / P)
```

Inputs are multiplied by that execution count. A later optimizer may share common sub-products across branches, but the first correct implementation should preserve recipe-execution semantics clearly.

## Probabilities

Guaranteed and expected materials are different products of the analysis. A 25% byproduct must not be reported as a guaranteed one-item requirement. The output schema should expose both where the source semantics allow it.
