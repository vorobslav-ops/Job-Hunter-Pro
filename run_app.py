import os
import sys
import streamlit.web.cli as stcli

if __name__ == "__main__":
    # PyInstaller extracts files to a temporary folder (_MEIPASS) when running the binary
    if getattr(sys, 'frozen', False):
        app_path = os.path.join(sys._MEIPASS, 'app.py')
    else:
        app_path = 'app.py'
    
    # Simulate typing 'streamlit run app.py' in the terminal
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false"]
    sys.exit(stcli.main())
