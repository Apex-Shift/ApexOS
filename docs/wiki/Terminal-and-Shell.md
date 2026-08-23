# Terminal & Shell

The Terminal app is the primary interface to the kernel.

## Session commands

| Command | Description |
|---------|-------------|
| `login <user> <pass>` | Authenticate (also used by the login screen) |
| `whoami` | Current user |
| `pwd` | Current directory |
| `date` | Server date/time |
| `sysinfo` | OS version, uptime, features |
| `help` | Command list |
| `clear` | Clear terminal view (client-side) |

## Filesystem

| Command | Description |
|---------|-------------|
| `ls` | List current directory |
| `cd <path>` | Change directory |
| `cat <file>` | Print file contents |
| `write <file> <text…>` | Write text to file |
| `touch <file>` | Create empty file |
| `mkdir <dir>` | Create directory |
| `rm <path>` | Remove file or empty directory |

## Process

| Command | Description |
|---------|-------------|
| `ps` | List scheduled tasks |
| `kill <pid>` | Cancel a task |
| `matrix` | Demo streaming process |
| `echo <text>` | Print text |

## Packages & permissions

| Command | Description |
|---------|-------------|
| `apx list` | Installed packages |
| `apx remove <id>` | Uninstall package |
| `perms` | Show permission registry |

## Hardware (browser-side)

These run in the **client**, not as kernel syscalls:

| Command | Description |
|---------|-------------|
| `lsusb` | List authorized WebUSB devices |
| `bluetooth scan` | Open BLE device picker |
| `network` | Host online status and link info |

## Examples

```text
root@apexos:/root# sysinfo
root@apexos:/root# cd /home/apps
root@apexos:/home/apps# ls
root@apexos:/home/apps# apx list
root@apexos:/home/apps# network
```
