# Security policy

## Supported versions

The latest release on the default branch is supported. Older releases receive no fixes.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub security advisories: open the repository's Security tab and choose "Report a vulnerability". Do not open a public issue for a security problem.

You can expect an acknowledgement within a week. Please include the version, the platform, and steps to reproduce.

## Scope worth knowing

Underscore runs local subprocesses (your composing command, Sonic Pi, ffmpeg) and, in `api` mode, sends the composing prompt to the HTTP endpoint you configured. It starts no servers, opens no listening ports, and sends nothing anywhere you did not point it. Generated Sonic Pi programs are validated against a fixed allowlist before they run; treat programs from untrusted sources with the same care as any code you execute.
