# Desktop Environment

The desktop is a pure front-end environment rendered inside the browser after login.

## Shell chrome

| Element | Behavior |
|---------|----------|
| **Desktop icons** | Double-click to open apps |
| **Start menu** | App list + Sign out |
| **Taskbar** | Open windows; clock |
| **Windows** | Drag title bar, minimize, maximize, close |

## Built-in applications

| App | Icon | Description |
|-----|------|-------------|
| Terminal | 💻 | Shell connected to the kernel |
| Files | 📁 | Browse the VFS |
| Settings | ⚙️ | Network, Bluetooth, USB, permissions |
| Packages | 📦 | Install `.apx` packages |
| Calculator | 🧮 | Simple calculator |
| Editor | 📝 | Text editor (read/write VFS files) |
| Browser | 🌐 | iframe browser |
| System | ℹ️ | Kernel / version info |
| Media | 🎬 | Audio/video player |

## Window manager

Windows are DOM nodes with:

- Focus stacking (`z-index`)
- Drag from the title bar
- Taskbar entries for restore

There is no real multi-user window isolation; all UI runs in one browser session.

## Styling

Dark theme, system fonts, monospace for terminal output. All CSS is embedded in `server.py` for a single-file UI deploy.
