# DEPTRAC — MVC (Model-View-Controller)

Three folders: **Model**, **View**, **Controller**. Suitable for thinner applications that don't warrant a domain/application split.

## Defining trait

```
              Controller
              (handles request)
                   │
         ┌─────────┼──────────┐
         │                    │
         ▼                    ▼
       Model                View
   (business logic,       (render output
    persistence)           from Model)
```

Rules:
- **Controllers** read input, call Models, choose Views to render.
- **Views** read Model data to render output. Views never write to Models or call Controllers.
- **Models** contain business logic and persistence. Models do not import Views or Controllers.

## Folder structure assumed

```
src/
├── Model/                     # entities, services, persistence
├── View/                      # templates, view-models, formatters
├── Controller/                # request handlers
└── Support/                   # optional — cross-cutting helpers (Clock, Logger)
```

Note: PHP frameworks vary. Laravel uses `app/Models/`, `app/Http/Controllers/`, `resources/views/`. Yii uses `models/`, `views/`, `controllers/`. Adjust the `value:` paths below to your framework's layout.

## deptrac.yaml

```yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Model
      collectors:
        - type: directory
          value: src/Model/.*

    - name: View
      collectors:
        - type: directory
          value: src/View/.*

    - name: Controller
      collectors:
        - type: directory
          value: src/Controller/.*

    # Optional cross-cutting helpers — Clock, Logger, generic services
    - name: Support
      collectors:
        - type: directory
          value: src/Support/.*

  ruleset:
    # Models are self-contained — no Controller or View knowledge
    Model:
      - Support

    # Views read Models to render
    View:
      - Model
      - Support

    # Controllers orchestrate — read Models, choose Views
    Controller:
      - Model
      - View
      - Support

    # Support is the leaf — generic utilities
    Support: []
```

## Architecture-specific notes

1. **MVC is structural, not architectural.** It enforces "no upward dependency" between three boxes but leaves the internal shape of each box loose. For DDD-style projects with rich domain logic, prefer Clean, Hexagonal, or Layered configs.

2. **No Model → Controller, no Model → View.** Models must not know how they're displayed or what triggered their use. This is the rule MVC actually enforces.

3. **No View → Controller.** Views are passive renderers. If a View needs to dispatch an action, it does so via the next request — not by calling back into a Controller object.

4. **The Support layer is optional.** Useful for cross-cutting concerns like Clock, Logger, or a generic IdGenerator. Skip it entirely if your project doesn't need it; just remove the `Support` layer block and its ruleset entries.

## Common violation fixes

```
VIOLATION: Model\User depends on View\UserPage

FIX: Models must not know about Views. Move the rendering concern into
the View layer:
- View\UserPage takes a Model\User and renders it.
- Model\User has no awareness of how it's displayed.
```

```
VIOLATION: Model\Order depends on Controller\OrderController

FIX: Models must not know how they're invoked. Whatever the Model needed
from the Controller (request data, current user) should be passed as
parameters or constructor dependencies.
```

```
VIOLATION: View\OrderPage depends on Doctrine\ORM\EntityManagerInterface

FIX: Views render from Models that are already loaded. If a View is
loading entities from the database, the data fetching belongs in the
Controller (or in the Model exposed for the View to consume).
```

```
VIOLATION: Controller\OrderController contains 200 lines of order
           total calculation, discount logic, tax computation

FIX: Controllers should be thin. Move business logic into the Model
(or into a service inside Model\). The Controller's job is to gather
input, call the Model, pick a View.
```

## Bounded contexts

MVC is typically used for small applications where bounded-context separation isn't necessary. If your project DOES split by feature on top of MVC (`src/Order/Model/`, `src/Order/View/`, `src/Order/Controller/`), use the [Package-by-Feature](package-by-feature.md) config instead — it's a better fit.
