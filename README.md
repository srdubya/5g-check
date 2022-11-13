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
every start up by placing your password within `~/.5g-secret`.
