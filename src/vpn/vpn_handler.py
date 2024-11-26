import subprocess
import time

VPN_WAIT_TIME = 1
vpn_connected = False

def connect_to_vpn():
    global vpn_connected
    if not vpn_connected:
        print("[INFO] Connecting to VPN...")
        try:
            script = '''
            tell application "ProtonVPN"
                activate
            end tell
            tell application "System Events"
                try
                    click button "Quick Connect" of window 1 of application process "ProtonVPN"
                    delay 10
                on error
                    display dialog "Failed to find Connect button"
                end try
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            vpn_connected = True
            time.sleep(VPN_WAIT_TIME)
            print("[INFO] VPN connected.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to connect to VPN: {e}")

def disconnect_vpn():
    global vpn_connected
    if vpn_connected:
        print("[INFO] Disconnecting from VPN...")
        try:
            script = '''
            tell application "ProtonVPN"
                activate
            end tell
            tell application "System Events"
                try
                    click button "Disconnect" of window 1 of application process "ProtonVPN"
                    delay 5
                on error
                    display dialog "Failed to find Disconnect button"
                end try
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True)
            vpn_connected = False
            print("[INFO] VPN disconnected.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to disconnect VPN: {e}")