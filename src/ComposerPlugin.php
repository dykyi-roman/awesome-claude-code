<?php

declare(strict_types=1);

namespace Dykyi\AwesomeClaudeCode;

use Composer\Composer;
use Composer\EventDispatcher\EventSubscriberInterface;
use Composer\Installer\PackageEvent;
use Composer\Installer\PackageEvents;
use Composer\IO\IOInterface;
use Composer\Plugin\PluginInterface;
use RecursiveDirectoryIterator;
use RecursiveIteratorIterator;

final class ComposerPlugin implements PluginInterface, EventSubscriberInterface
{
    private const DIRECTORIES = ['commands', 'agents', 'skills'];

    private Composer $composer;
    private IOInterface $io;

    public function activate(Composer $composer, IOInterface $io): void
    {
        $this->composer = $composer;
        $this->io = $io;
    }

    public function deactivate(Composer $composer, IOInterface $io): void
    {
    }

    public function uninstall(Composer $composer, IOInterface $io): void
    {
    }

    public static function getSubscribedEvents(): array
    {
        return [
            PackageEvents::POST_PACKAGE_INSTALL => 'onPackageInstall',
            PackageEvents::POST_PACKAGE_UPDATE => 'onPackageUpdate',
        ];
    }

    public function onPackageInstall(PackageEvent $event): void
    {
        $package = $event->getOperation()->getPackage();
        if ($package->getName() === 'dykyi/awesome-claude-code') {
            $this->copyClaudeFiles();
        }
    }

    public function onPackageUpdate(PackageEvent $event): void
    {
        $package = $event->getOperation()->getTargetPackage();
        if ($package->getName() === 'dykyi/awesome-claude-code') {
            $this->copyClaudeFiles();
        }
    }

    private function copyClaudeFiles(): void
    {
        $vendorDir = $this->composer->getConfig()->get('vendor-dir');
        $projectDir = dirname($vendorDir);

        $sourceBase = $vendorDir . '/dykyi/awesome-claude-code/.claude';
        $targetBase = $projectDir . '/.claude';

        if (!is_dir($sourceBase)) {
            return;
        }

        $this->io->write('<info>Installing Claude Code components...</info>');

        foreach (self::DIRECTORIES as $dir) {
            $source = $sourceBase . '/' . $dir;
            $target = $targetBase . '/' . $dir;

            if (!is_dir($source)) {
                continue;
            }

            $this->copyDirectory($source, $target);
        }

        $this->io->write('<info>Claude Code components installed to .claude/</info>');
    }

    private function copyDirectory(string $source, string $target): void
    {
        if (!is_dir($target)) {
            mkdir($target, 0755, true);
        }

        $iterator = new RecursiveIteratorIterator(
            new RecursiveDirectoryIterator($source, RecursiveDirectoryIterator::SKIP_DOTS),
            RecursiveIteratorIterator::SELF_FIRST
        );

        foreach ($iterator as $item) {
            $targetPath = $target . '/' . $iterator->getSubPathname();

            if ($item->isDir()) {
                if (!is_dir($targetPath)) {
                    mkdir($targetPath, 0755, true);
                }
            } else {
                if (file_exists($targetPath)) {
                    $this->io->write("  <comment>Skipping (exists):</comment> " . $iterator->getSubPathname());
                    continue;
                }

                copy($item->getPathname(), $targetPath);
                $this->io->write("  <info>Copied:</info> " . $iterator->getSubPathname());
            }
        }
    }
}
