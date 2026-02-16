# Mermaid Syntax Reference

## Flowchart

### Directions

```
TB / TD - Top to Bottom
BT - Bottom to Top
LR - Left to Right
RL - Right to Left
```

### Node Shapes

```mermaid
flowchart LR
    A[Rectangle] --> B(Rounded)
    B --> C{Diamond}
    C --> D([Stadium])
    D --> E[[Subroutine]]
    E --> F[(Database)]
    F --> G((Circle))
    G --> H>Asymmetric]
    H --> I{{Hexagon}}
    I --> J[/Parallelogram/]
    J --> K[\Parallelogram Alt\]
    K --> L[/Trapezoid\]
    L --> M[\Trapezoid Alt/]
```

### Arrow Types

```
A --> B    Solid line with arrow
A --- B    Solid line
A -.-> B   Dotted line with arrow
A -.- B    Dotted line
A ==> B    Thick line with arrow
A === B    Thick line
A --o B    Circle end
A --x B    Cross end
A <--> B   Bidirectional
```

### Arrow Labels

```mermaid
flowchart LR
    A -->|text| B
    C -- text --> D
    E -.->|text| F
```

### Subgraphs

```mermaid
flowchart TB
    subgraph one[First Group]
        A --> B
    end
    subgraph two[Second Group]
        C --> D
    end
    one --> two
```

## Sequence Diagram

### Participants

```mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    actor U as User

    U ->> A: Request
    A ->> B: Process
    B -->> A: Response
    A -->> U: Result
```

### Message Types

```
->>   Solid line (synchronous)
-->>  Dashed line (response/async)
-)    Solid line, open arrow
--)   Dashed line, open arrow
-x    Solid line, cross end
--x   Dashed line, cross end
```

### Control Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    C ->> S: Request

    alt Success
        S -->> C: 200 OK
    else Error
        S -->> C: 500 Error
    end

    loop Every 5s
        C ->> S: Heartbeat
    end

    opt Optional
        S ->> C: Notification
    end

    par Parallel
        S ->> C: Message 1
    and
        S ->> C: Message 2
    end
```

### Notes

```mermaid
sequenceDiagram
    participant A
    participant B

    Note left of A: Note on left
    Note right of B: Note on right
    Note over A: Note over single
    Note over A,B: Note over both

    A ->> B: Message
```

### Activation

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server

    C ->> +S: Request
    S -->> -C: Response

    C ->> +S: Request
    S ->> +S: Internal
    S -->> -S: Done
    S -->> -C: Response
```

## Class Diagram

### Class Definition

```mermaid
classDiagram
    class Order {
        <<entity>>
        -OrderId id
        -OrderStatus status
        -Money total
        +confirm() void
        +cancel() void
        +addItem(item) void
        +getTotalAmount() Money
    }
```

### Visibility

```
+ Public
- Private
# Protected
~ Package/Internal
```

### Relationships

```mermaid
classDiagram
    classA <|-- classB : Inheritance
    classC *-- classD : Composition
    classE o-- classF : Aggregation
    classG --> classH : Association
    classI -- classJ : Link
    classK ..> classL : Dependency
    classM ..|> classN : Realization
```

### Cardinality

```mermaid
classDiagram
    Customer "1" --> "*" Order : places
    Order "1" --> "1..*" OrderItem : contains
```

## State Diagram

### Basic States

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing : start
    Processing --> Completed : finish
    Processing --> Failed : error
    Completed --> [*]
    Failed --> [*]
```

### Composite States

```mermaid
stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> Idle
        Idle --> Working : task
        Working --> Idle : done
    }

    Active --> Inactive : pause
    Inactive --> Active : resume
```

### Choice and Fork

```mermaid
stateDiagram-v2
    state check <<choice>>
    [*] --> check
    check --> Valid : if valid
    check --> Invalid : if invalid

    state fork <<fork>>
    [*] --> fork
    fork --> State1
    fork --> State2
```

## ER Diagram

### Entities and Attributes

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string name
        timestamp created_at
    }

    ORDER {
        uuid id PK
        uuid user_id FK
        string status
        decimal total
    }
```

### Relationships

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEM : contains
    PRODUCT ||--o{ ORDER_ITEM : "ordered in"
```

### Cardinality Notation

```
||--||  Exactly one to exactly one
||--o{  One to zero or more
||--|{  One to one or more
}|--|{  One or more to one or more
```

## Styling

### Inline Styles

```mermaid
flowchart LR
    A[Start] --> B[Process]
    B --> C[End]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:2px
```

### Class Definitions

```mermaid
flowchart LR
    A[Start]:::startClass --> B[Process]:::processClass
    B --> C[End]:::endClass

    classDef startClass fill:#f9f,stroke:#333
    classDef processClass fill:#bbf,stroke:#333
    classDef endClass fill:#bfb,stroke:#333
```
