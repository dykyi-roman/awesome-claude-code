# DEPTRAC — Bounded Context Separation

Architecture-agnostic overlay that adds bounded-context isolation on top of any other config (Clean, Hexagonal, Layered, N-Tier). Each bounded context becomes its own root layer in addition to the architecture's layers.

## When to use this overlay

- The codebase is multi-context (Order, Payment, Shipping, etc.) and you want deptrac to enforce cross-context isolation.
- The architecture's own ruleset doesn't already partition by context (it usually doesn't — architecture rulesets enforce vertical layering, not horizontal context boundaries).

If your project is **Package-by-Feature**, you do NOT need this overlay — the feature IS the bounded context. Use the [Package-by-Feature](package-by-feature.md) config directly.

## Folder structure assumed

The structure typically has the context name BETWEEN the architectural layer and the inner folders:

```
src/
├── SharedKernel/             # cross-context primitives (Money, Email, IDs)
├── Domain/
│   ├── Order/
│   ├── Payment/
│   └── Shipping/
├── Application/
│   ├── Order/
│   ├── Payment/
│   └── Shipping/
└── Infrastructure/
    ├── Order/
    ├── Payment/
    └── Shipping/
```

Adjust to your project's actual layout. The key is that each bounded context can be identified by a directory pattern.

## deptrac.yaml — context overlay

Add these layers ON TOP of your architecture's existing layers. The architecture rules still apply; this overlay adds horizontal context-isolation rules.

```yaml
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Shared Kernel — available to every context
    #############################################
    - name: SharedKernel
      collectors:
        - type: directory
          value: src/SharedKernel/.*

    #############################################
    # Bounded Context: Order
    #############################################
    - name: Context.Order
      collectors:
        - type: directory
          value: src/(Domain|Application|Infrastructure|Presentation)/Order/.*

    - name: Context.Order.Public
      collectors:
        - type: directory
          value: src/Domain/Order/(Event|Port)/.*

    #############################################
    # Bounded Context: Payment
    #############################################
    - name: Context.Payment
      collectors:
        - type: directory
          value: src/(Domain|Application|Infrastructure|Presentation)/Payment/.*

    - name: Context.Payment.Public
      collectors:
        - type: directory
          value: src/Domain/Payment/(Event|Port)/.*

    #############################################
    # Bounded Context: Shipping
    #############################################
    - name: Context.Shipping
      collectors:
        - type: directory
          value: src/(Domain|Application|Infrastructure|Presentation)/Shipping/.*

    - name: Context.Shipping.Public
      collectors:
        - type: directory
          value: src/Domain/Shipping/(Event|Port)/.*

  ruleset:
    SharedKernel: []

    # Each context may depend on its OWN code + SharedKernel + other contexts' PUBLIC surface
    Context.Order:
      - SharedKernel
      - Context.Payment.Public
      - Context.Shipping.Public
    Context.Payment:
      - SharedKernel
      - Context.Order.Public
      - Context.Shipping.Public
    Context.Shipping:
      - SharedKernel
      - Context.Order.Public
      - Context.Payment.Public

    # Public surfaces only see SharedKernel
    Context.Order.Public:
      - SharedKernel
    Context.Payment.Public:
      - SharedKernel
    Context.Shipping.Public:
      - SharedKernel
```

## Folder-structure variant: Context-first

Some projects put the context name OUTERMOST and architecture inside:

```
src/
├── SharedKernel/
├── Order/
│   ├── Domain/
│   ├── Application/
│   └── Infrastructure/
├── Payment/
│   └── ...
└── Shipping/
    └── ...
```

For this layout, adjust each context layer:

```yaml
    - name: Context.Order
      collectors:
        - type: directory
          value: src/Order/.*

    - name: Context.Order.Public
      collectors:
        - type: directory
          value: src/Order/Domain/(Event|Port)/.*
```

Combine the context layers (this file) with the architecture layers from the architecture-specific config — both rulesets must be satisfied. A class in `src/Order/Domain/Entity/` must obey both the architecture's `Domain.Entity → []` rule AND the context's `Context.Order` rule.

## Cross-context channels

The rules above forbid direct cross-context imports outside the public surface. Cross-context communication then goes through:

1. **Domain Events** — one context publishes; others subscribe. Implementation: `Domain/{Context}/Event/` (in the publisher) is in the public surface.

2. **Anti-Corruption Layer** — one context publishes a Port (interface); the consuming context writes an adapter that translates. Implementation: `Domain/{Context}/Port/` (in the publisher) is in the public surface; consumer's `Infrastructure/{Context}/Acl/` adapter implements it.

3. **Shared Kernel** — only for genuinely cross-cutting primitives (`Money`, `Email`, `Clock`). Resist the temptation to move context-specific types here; the kernel should stay tiny.

## Common violation fixes

```
VIOLATION: Domain\Order\Order depends on Domain\Payment\Payment

FIX: Cross-context direct dependency. Replace with one of:

(a) Domain Event — Payment publishes PaymentCompletedEvent (Event/),
    Order subscribes via a Subscriber inside Order's Application layer.

(b) Anti-Corruption Layer — Payment exposes PaymentGatewayInterface
    (Port/), Order writes an adapter:
    Infrastructure\Order\Acl\PaymentGatewayAdapter
        implements Domain\Payment\Port\PaymentGatewayInterface

(c) Move the shared concept to SharedKernel if it's truly universal
    (e.g. Money). Order-specific data stays in Order.
```

```
VIOLATION: SharedKernel\Order\OrderId found

FIX: OrderId belongs to the Order context, not the kernel. Move:
  src/SharedKernel/Order/OrderId.php
  → src/Domain/Order/ValueObject/OrderId.php

Other contexts that need to reference an Order id should do so through
event payloads or port signatures from Order's public surface.
```

```
VIOLATION: Application\Order\Service\OrderService depends on
           Application\Payment\Service\PaymentService

FIX: Application-layer cross-context calls are also violations. Route
through the public surface (Event or Port). If the call truly must be
synchronous, publish a Port from Payment and write an ACL adapter in
Order's Infrastructure layer.
```
