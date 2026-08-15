---
type: llm
criteria: "Take every `class` declaration in the response. Is there any class declared `readonly` (e.g. `final readonly class X extends Y`) whose parent class in the same response is NOT declared readonly?"
focus: "Answer PASS only if no such pair exists. A readonly class extending a non-readonly class is a guaranteed 'Fatal error: Readonly class X cannot extend non-readonly class Y' on PHP 8.2+. Also fail if a property inside a class already declared readonly repeats the readonly modifier — that is 'Cannot decorate readonly property' and is equally fatal."
---

Guards the exact fatal-error pair this plugin used to emit: `final readonly class …Decorator
extends Abstract…Decorator` where the abstract base was a plain class.
