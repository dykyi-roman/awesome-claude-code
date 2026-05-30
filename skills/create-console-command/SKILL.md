---
name: create-console-command
description: Generates Console (CLI) Commands that delegate to the application's command bus or use cases. Console Commands handle CLI input parsing only — business logic lives in the dispatched UseCase/Command. Works with Symfony Console, but the pattern (thin CLI shell over a bus) applies across PHP frameworks.
---

# Console Command Generator

Generate CLI command classes that read input from the terminal and delegate to the application's command bus or directly to a UseCase. The CLI layer is a thin shell — all business logic lives in the dispatched Command + Handler.

## Console Command characteristics

- **Thin entry point**: parses CLI input, validates structurally, dispatches to bus / UseCase.
- **No business logic**: same rule as HTTP controllers — translate input and delegate.
- **Single responsibility**: one CLI verb per class (e.g. `app:orders:cleanup`).
- **Exit code via constants**: `Command::SUCCESS`, `Command::FAILURE`, `Command::INVALID`.
- **Idempotent where reasonable**: cron-invoked commands should be safe to re-run.
- **Verbose output controlled by `OutputInterface` levels**: don't bypass with raw `echo`.

## When to use

| Scenario | Use a Console Command |
|----------|------------------------|
| Periodic cleanup (cron) | Yes |
| One-off data migration / backfill | Yes |
| Worker / queue consumer entry point | Yes (delegates to a worker class) |
| Maintenance script (cache warm-up, index rebuild) | Yes |
| Long-running interactive shell | Yes (but use `Symfony\Component\Console\Question`) |
| Quick local debugging | Maybe — for production code, write a proper test |

## Placement

Folder placement varies by your project's architecture; whatever folder hosts entry-point code (CLI / HTTP / console) is where Console Commands belong.

## Templates

### Command-bus-dispatching CLI command

```php
<?php

declare(strict_types=1);

namespace Console\Command;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Messenger\MessageBusInterface;

#[AsCommand(
    name: 'app:orders:cleanup',
    description: 'Remove orders that have been pending for longer than the threshold',
)]
final class CleanupExpiredOrdersCommand extends Command
{
    public function __construct(
        private readonly MessageBusInterface $commandBus,
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this->addArgument(
            'days',
            InputArgument::OPTIONAL,
            'Age threshold in days',
            '30',
        );
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $days = (int) $input->getArgument('days');

        if ($days < 1) {
            $output->writeln('<error>days must be ≥ 1</error>');

            return Command::INVALID;
        }

        $command = new CleanupExpiredOrdersCommandMessage(daysThreshold: $days);
        $this->commandBus->dispatch($command);

        $output->writeln(sprintf('<info>Cleanup dispatched for orders older than %d day(s)</info>', $days));

        return Command::SUCCESS;
    }
}
```

### Direct-UseCase CLI command (no bus)

```php
<?php

declare(strict_types=1);

namespace Console\Command;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Console\Style\SymfonyStyle;

#[AsCommand(
    name: 'app:reports:daily',
    description: 'Generate daily sales report',
)]
final class GenerateDailyReportCommand extends Command
{
    public function __construct(
        private readonly GenerateDailyReportUseCase $useCase,
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this->addOption('date', null, InputOption::VALUE_REQUIRED, 'Target date (Y-m-d)');
        $this->addOption('dry-run', null, InputOption::VALUE_NONE, 'Skip persistence');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $io = new SymfonyStyle($input, $output);

        $date = $input->getOption('date')
            ? new \DateTimeImmutable($input->getOption('date'))
            : new \DateTimeImmutable('yesterday');

        $io->title(sprintf('Daily report for %s', $date->format('Y-m-d')));

        try {
            $result = $this->useCase->execute(
                new GenerateDailyReportInput(date: $date, dryRun: (bool) $input->getOption('dry-run')),
            );
        } catch (\DomainException $e) {
            $io->error($e->getMessage());

            return Command::FAILURE;
        }

        $io->success(sprintf('Report generated: %d rows', $result->rowCount));

        return Command::SUCCESS;
    }
}
```

### Worker entry-point (queue consumer)

```php
<?php

declare(strict_types=1);

namespace Console\Command;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(
    name: 'app:worker:outbox',
    description: 'Publish outbox messages to the message broker',
)]
final class OutboxWorkerCommand extends Command
{
    public function __construct(
        private readonly OutboxWorkerInterface $worker,
    ) {
        parent::__construct();
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        // Long-running loop until interrupted
        $this->worker->run(
            onMessage: static fn (string $id) => $output->writeln(sprintf('Published %s', $id)),
        );

        return Command::SUCCESS;
    }
}
```

### Unit test pattern

```php
<?php

declare(strict_types=1);

use Symfony\Component\Console\Tester\CommandTester;
use PHPUnit\Framework\TestCase;

final class CleanupExpiredOrdersCommandTest extends TestCase
{
    public function testDispatchesCommandWithProvidedDays(): void
    {
        $bus = $this->createMock(MessageBusInterface::class);
        $bus->expects($this->once())
            ->method('dispatch')
            ->with($this->callback(fn (CleanupExpiredOrdersCommandMessage $cmd) =>
                $cmd->daysThreshold === 15,
            ))
            ->willReturn(new Envelope(new \stdClass()));

        $tester = new CommandTester(new CleanupExpiredOrdersCommand($bus));
        $exitCode = $tester->execute(['days' => '15']);

        self::assertSame(Command::SUCCESS, $exitCode);
    }

    public function testRejectsZeroDays(): void
    {
        $bus = $this->createMock(MessageBusInterface::class);
        $bus->expects($this->never())->method('dispatch');

        $tester = new CommandTester(new CleanupExpiredOrdersCommand($bus));
        $exitCode = $tester->execute(['days' => '0']);

        self::assertSame(Command::INVALID, $exitCode);
    }
}
```

## Generation steps

1. **Name the command** following the project's verb-namespace convention (`app:orders:cleanup`, `app:reports:daily`). Use the `name:` constructor in `#[AsCommand]`.
2. **List arguments + options** in `configure()`. Required arguments use `InputArgument::REQUIRED`; optional inputs use `InputOption`.
3. **Decide the dispatch mode** — through the message bus (preferred for production) or directly to a UseCase.
4. **Return the right exit code** — `Command::SUCCESS`, `Command::FAILURE` (recoverable), `Command::INVALID` (bad input).
5. **Use `SymfonyStyle`** for consistent CLI output (titles, success/error/info messages, tables).
6. **Generate a `CommandTester` unit test** for each command.

## Detection patterns

```bash
# Find console commands
Glob: **/*Command.php
Grep: "#\[AsCommand|extends Command" --glob "**/*.php"

# Commands with business logic (potential violation)
Grep: "->save\(|->persist\(|new Order\(|new User\(" --glob "**/*Command.php"

# Commands that bypass the bus / UseCase layer
Grep: "Repository|EntityManager" --glob "**/*Command.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Business logic in `execute()` | CLI is an entry point, not where business rules live | Dispatch to a UseCase / Command bus |
| Direct repository / `EntityManager` usage | Bypasses application layer | Inject a UseCase instead |
| Echoing instead of `$output->writeln()` | Breaks Symfony output level controls | Use `OutputInterface` / `SymfonyStyle` |
| Returning `0` / `1` literals instead of constants | Magic numbers; missed `Command::INVALID` semantics | Use `Command::SUCCESS|FAILURE|INVALID` |
| Long-running commands without graceful shutdown | SIGTERM kills mid-batch | Install `pcntl_signal` handlers; break the loop on signal |
| Hard-coded date / config values | Hard to test, hard to operate | Accept as options with sensible defaults |
