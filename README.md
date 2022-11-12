# 5gcheck

Outputs the status of your Verizon 5G Router every 5 seconds.

## Usage

`./5gcheck.py <authorization cookie value>`

## Authorization Cookie Value

Obtain this value via the follow procedure:
1. Browse to [192.168.0.1](http://192.168.0.1)
2. Login
3. Right-click in your browser window and select `inspect`
4. Select the `Network` tab within the pane you've just opened
5. Select one of the `getStatus` requests
6. Scroll to the `Request Headers` 
7. Right-click on the `Cookie: sysauth=xxx` line and select `Copy value`
8. Paste the value just copied into the command line: `./5fcheck.py` <copied value>

> **Note:** The above procedure is for the `Chrome` browser.

Or, better yet, you can skip having to do the aforementioned procedure at
every start up by following this procedure:
1. Browse to [192.168.0.1](http://192.168.0.1)
2. Right-click in your browser window and select `inspect`
3. Select the `Network` tab within the pane you've just opened
4. Login
5. Stop recording by clicking the **red circle** on the left size of the `inspect` frame
6. Select the `luci/` request with a return code of `302`
7. Copy the contents of the `Payload` `Form Data` viewed as `view source`
8. Place the copied text into the file: `~/.5g-secret`

Upon start up `5gcheck.py` (started with or without an authorization cookie value) 
and the MacOS `5G-Check.app` will read `~/.5g-secret`, saving you time.
