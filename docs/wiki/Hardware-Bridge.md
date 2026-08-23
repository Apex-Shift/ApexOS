# Hardware Bridge

ApexOS exposes **host browser** capabilities inside the virtual desktop. No native drivers are installed; everything goes through standard Web APIs.

## Network

- **API:** `navigator.onLine`, `navigator.connection`  
- **UI:** Settings → Network  
- **CLI:** `network`  

Shows online status, effective connection type, downlink, and RTT when the Network Information API is available.

## Bluetooth

- **API:** `navigator.bluetooth`  
- **UI:** Settings → Bluetooth → Scan & pair  
- **CLI:** `bluetooth scan`  

Opens the browser BLE picker. Requires a supporting browser (typically Chrome/Edge) and user gesture.

## USB

- **API:** `navigator.usb`  
- **UI:** Settings → USB  
- **CLI:** `lsusb`  

Lists devices the user has authorized. `requestDevice` must be triggered from a button click.

## Media (files)

The Media Player uses:

- Local files via `<input type="file">` and `URL.createObjectURL`  
- Optional remote demo streams (audio/video)  

## Browser requirements

| Feature | Chrome | Edge | Firefox | Safari |
|---------|--------|------|---------|--------|
| Network Information | Yes | Yes | Limited | Limited |
| Web Bluetooth | Yes* | Yes* | Limited | No |
| WebUSB | Yes* | Yes* | No | No |
| HTML5 audio/video | Yes | Yes | Yes | Yes |

\* Best on `localhost` or HTTPS with a user gesture.

## Security note

Hardware access is always confirmed by the **browser** permission prompts. ApexOS adds a second layer via the **app permission registry** for installed packages.
