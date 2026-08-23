# Virtual Filesystem

ApexOS uses a **JSON virtual filesystem (VFS)** stored in `storage/disk.img`.

## Persistence

- On boot, the kernel loads `disk.img` if present  
- Every write commits the full tree back to disk  
- Delete `disk.img` to reset to a clean system image  

## Default layout

```text
/
├── bin/              # Logical binaries (names only)
├── home/
│   └── apps/         # Installed .apx packages
├── root/             # root home
├── system/
│   ├── apps/
│   └── etc/
│       └── permissions.json
└── readme.txt
```

## Node format

Each path maps to an object:

```json
{
  "/home": {
    "type": "dir",
    "content": ["apps"],
    "owner": "root"
  },
  "/readme.txt": {
    "type": "file",
    "content": "Welcome to ApexOS…",
    "owner": "root"
  }
}
```

## Path resolution

- Absolute paths start with `/`  
- Relative paths resolve against the session `cwd`  
- `..` and `.` are supported  

## Limits

- Not a real block device (no inode semantics)  
- Binary files are not first-class (text-oriented)  
- Suitable for demos, configs, source, and package metadata  

## Permissions file

`/system/etc/permissions.json` example:

```json
{
  "com.apex.mediaplayer": {
    "hardware.usb.read": true,
    "filesystem.read": true
  }
}
```
