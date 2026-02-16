---
name: acc-check-command-injection
description: Analyzes PHP code for command injection vulnerabilities. Detects shell_exec, exec, system, passthru with user input, missing escapeshellarg/escapeshellcmd.
---

# Command Injection Security Check

Analyze PHP code for OS command injection vulnerabilities (OWASP A03:2021).

## Detection Patterns

### 1. Direct Command Execution with User Input

```php
// CRITICAL: shell_exec with user input
$output = shell_exec("ls " . $_GET['dir']);
$output = shell_exec("ping -c 3 {$host}");

// CRITICAL: exec with user input
exec("convert " . $filename . " output.png", $output);
exec("grep '$search' /var/log/app.log");

// CRITICAL: system with user input
system("cat " . $logFile);
system("tar -xzf $archive");

// CRITICAL: passthru with user input
passthru("ffmpeg -i $videoFile output.mp4");

// CRITICAL: proc_open with user input
$process = proc_open("mail -s '$subject' $email", $descriptors, $pipes);
```

### 2. Backtick Operator

```php
// CRITICAL: Backticks with variables
$result = `ls $directory`;
$output = `grep $pattern $file`;
$data = `curl $url`;

// CRITICAL: Backticks in string
$files = `find /uploads -name "*{$extension}"`;
```

### 3. popen/proc_open

```php
// CRITICAL: popen with user input
$handle = popen("sort " . $filename, "r");

// CRITICAL: proc_open with user input
$descriptors = [
    0 => ['pipe', 'r'],
    1 => ['pipe', 'w'],
    2 => ['pipe', 'w'],
];
$process = proc_open("php $script", $descriptors, $pipes);
```

### 4. Command Building

```php
// CRITICAL: String concatenation
$cmd = "convert " . $input . " -resize " . $size . " " . $output;
shell_exec($cmd);

// CRITICAL: sprintf without escaping
$cmd = sprintf("mysqldump -u%s -p%s %s", $user, $password, $database);
exec($cmd);

// CRITICAL: implode for arguments
$args = implode(' ', $userInputArray);
shell_exec("process $args");
```

### 5. Missing Escaping Functions

```php
// VULNERABLE: No escapeshellarg
exec("ls " . $directory); // Should be escapeshellarg($directory)

// VULNERABLE: No escapeshellcmd
$cmd = $_GET['cmd'];
shell_exec($cmd); // Should be escapeshellcmd($cmd)

// WRONG: Escaping entire command instead of arguments
shell_exec(escapeshellarg("ls $dir")); // Entire command escaped, won't work

// CORRECT: Escape arguments only
shell_exec("ls " . escapeshellarg($dir));
```

### 6. Indirect Command Injection

```php
// CRITICAL: Filename injection
$filename = $_FILES['upload']['name'];
shell_exec("process " . $filename);
// Filename: "file.txt; rm -rf /"

// CRITICAL: Environment variable injection
putenv("PATH=" . $_GET['path']);
// Later: shell_exec("mycommand"); uses modified PATH

// CRITICAL: Argument injection via flags
$format = $_GET['format'];
exec("convert input.png --format=$format output");
// format: "png --help" or "png; rm -rf /"
```

### 7. PDF/Image Processing Commands

```php
// CRITICAL: ImageMagick with user input
exec("convert " . $uploadedFile . " -resize 100x100 thumb.png");

// CRITICAL: Ghostscript
shell_exec("gs -dBATCH -sDEVICE=pdfwrite -sOutputFile=merged.pdf $files");

// CRITICAL: ffmpeg
passthru("ffmpeg -i " . $videoUrl . " -c:v libx264 output.mp4");
```

### 8. Git/SCM Commands

```php
// CRITICAL: Git with user input
exec("git clone " . $repoUrl);
exec("git checkout " . $branch);
shell_exec("git log --author='$author'");

// CRITICAL: SVN
exec("svn checkout " . $svnUrl);
```

### 9. Mail Commands

```php
// CRITICAL: mail() fifth parameter
mail($to, $subject, $message, $headers, "-f$from");
// $from could contain: "attacker@evil.com -X/var/www/shell.php"

// CRITICAL: sendmail
exec("sendmail -t < " . $emailFile);
```

### 10. Database CLI Commands

```php
// CRITICAL: mysqldump with user credentials
$cmd = "mysqldump -u{$user} -p{$pass} {$database}";
exec($cmd);
// Password could contain: "pass' | cat /etc/passwd #"

// CRITICAL: psql
exec("psql -U {$user} -d {$database} -c '{$query}'");
```

## Grep Patterns

```bash
# Command execution functions
Grep: "(shell_exec|exec|system|passthru|popen|proc_open)\s*\(" --glob "**/*.php"

# Backticks with variables
Grep: "`[^`]*\\\$[^`]*`" --glob "**/*.php"

# Command building with variables
Grep: "(shell_exec|exec|system)\s*\([^)]*\.\s*\\\$" --glob "**/*.php"

# Missing escape functions
Grep: "(shell_exec|exec)\s*\([^)]*(?!escapeshell)" --glob "**/*.php"
```

## Secure Patterns

### Use escapeshellarg for Arguments

```php
// SECURE: Escape each argument
$safeDir = escapeshellarg($directory);
$output = shell_exec("ls $safeDir");

// SECURE: Multiple arguments
$cmd = sprintf(
    "convert %s -resize %s %s",
    escapeshellarg($input),
    escapeshellarg($size),
    escapeshellarg($output)
);
exec($cmd);
```

### Use escapeshellcmd for Commands

```php
// SECURE: Escape special characters in command
$cmd = escapeshellcmd($userCommand);
shell_exec($cmd);

// Note: escapeshellcmd escapes: &#;`|*?~<>^()[]{}$\, \x0A, \xFF
// Does NOT prevent argument injection
```

### Whitelist Approach

```php
// SECURE: Whitelist allowed commands
final class SafeCommandExecutor
{
    private const ALLOWED_COMMANDS = [
        'convert',
        'ffmpeg',
        'gs',
    ];

    public function execute(string $command, array $args): string
    {
        if (!in_array($command, self::ALLOWED_COMMANDS, true)) {
            throw new SecurityException('Command not allowed');
        }

        $safeArgs = array_map('escapeshellarg', $args);
        $cmd = $command . ' ' . implode(' ', $safeArgs);

        return shell_exec($cmd) ?? '';
    }
}
```

### Use Process Libraries

```php
// SECURE: Symfony Process component
use Symfony\Component\Process\Process;

$process = new Process(['ls', '-la', $directory]);
$process->run();
// Arguments are automatically escaped

// SECURE: With timeout and error handling
$process = new Process(['convert', $input, '-resize', $size, $output]);
$process->setTimeout(30);
$process->run();

if (!$process->isSuccessful()) {
    throw new ProcessFailedException($process);
}
```

### Avoid Shell When Possible

```php
// AVOID: Shell command for file operations
shell_exec("rm " . escapeshellarg($file));

// BETTER: PHP function
unlink($file);

// AVOID: Shell for directory listing
$files = shell_exec("ls $dir");

// BETTER: PHP function
$files = scandir($dir);

// AVOID: Shell for file reading
$content = shell_exec("cat " . escapeshellarg($file));

// BETTER: PHP function
$content = file_get_contents($file);
```

## Severity Classification

| Pattern | Severity | CWE |
|---------|----------|-----|
| exec/shell_exec with $_GET/$_POST | 🔴 Critical | CWE-78 |
| Backticks with user variable | 🔴 Critical | CWE-78 |
| Missing escapeshellarg | 🔴 Critical | CWE-78 |
| mail() fifth parameter injection | 🔴 Critical | CWE-78 |
| Environment variable injection | 🟠 Major | CWE-78 |
| Filename in command | 🟠 Major | CWE-78 |

## Output Format

```markdown
### Command Injection: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-78 (OS Command Injection)

**Issue:**
User input is passed directly to shell command without escaping.

**Attack Vector:**
1. Input: `file.txt; cat /etc/passwd`
2. Executed: `process file.txt; cat /etc/passwd`
3. Attacker reads system files

**Code:**
```php
// Vulnerable
exec("process " . $filename);
```

**Fix:**
```php
// Secure: Use escapeshellarg
exec("process " . escapeshellarg($filename));

// Better: Use Process component
$process = new Process(['process', $filename]);
$process->run();
```

**References:**
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
```
