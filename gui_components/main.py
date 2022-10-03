import subprocess
import threading as thr
from os import path
import sys
import time
import webbrowser

server_loaded=thr.Event()
# Kill the server if a dash app is already running
def kill_server():
    subprocess.run("lsof -t -i tcp:8050 | xargs kill -9", shell=True)
# Start Dash app. "dash_app" is the name that will be given to executable dash app file, if your executable file has another name, change it over here.
def start_dash_app_frozen():
    path_dir = str(path.dirname(sys.executable))
    process=subprocess.Popen(path_dir+"/biomod-gui", shell=False)

# Putting everything together in a function
def main():
    kill_server() # kill open server on port
    thread = thr.Thread(target=start_dash_app_frozen) 
    print('Starting up dash app...')
    thread.start() # start dash app on port
    time.sleep(15)
    webbrowser.open("http://127.0.0.1:8050/",new=1)
if __name__ == '__main__':
    main()