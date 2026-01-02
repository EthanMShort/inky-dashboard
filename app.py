import os
import sys
import subprocess
import psutil
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__, template_folder='web/templates')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, 'tools')
EGGS_DIR = os.path.join(BASE_DIR, 'easter_eggs')

SCRIPTS = {
    'dashboard': os.path.join(TOOLS_DIR, 'systemDashboard.py'),
    'birthday': os.path.join(EGGS_DIR, 'momBirthday.py'),
    'clean': os.path.join(TOOLS_DIR, 'clean.py'),
    'weather': os.path.join(TOOLS_DIR, 'weather.py'),
    'music': os.path.join(TOOLS_DIR, 'lastfm.py')
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run/<script_key>')
def run_script(script_key):
    script_path = SCRIPTS.get(script_key)
    if script_path and os.path.exists(script_path):
        
        # 1. Save State (So the web page knows what is running)
        state_file = os.path.join(BASE_DIR, "state.txt")
        try:
            with open(state_file, "w") as f:
                f.write(script_key)
        except:
            pass

        # 2. Kill old Music scripts if switching to/from Music
        if script_key == 'music':
            subprocess.call(['pkill', '-f', 'lastfm.py'])
            subprocess.Popen([sys.executable, script_path])
        else:
            # If running a normal script, also kill music so it doesn't overwrite
            subprocess.call(['pkill', '-f', 'lastfm.py'])
            subprocess.Popen([sys.executable, script_path])

    return redirect(url_for('home'))

@app.route('/message', methods=['POST'])
def message():
    text = request.form.get('text_input')
    if text:
        script_path = os.path.join(TOOLS_DIR, 'message.py')
        subprocess.Popen([sys.executable, script_path, "--text", text])
    return redirect(url_for('home'))

@app.route('/system/<action>')
def system_action(action):
    try:
        # These commands rely on the sudoers file configuration for svc_inkydisp01
        if action == 'shutdown':
            subprocess.run(['sudo', 'shutdown', '-h', 'now'])
        elif action == 'reboot':
            subprocess.run(['sudo', 'reboot'])
        elif action == 'restart_service':
            subprocess.run(['sudo', 'systemctl', 'restart', 'inky-dashboard.service'])
    except Exception as e:
        print(f"Error executing system action {action}: {e}")
    return redirect(url_for('home'))

@app.route('/api/stats')
def get_stats():
    """Returns JSON with current system resource usage."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    return jsonify({
        'cpu': cpu,
        'ram': mem.percent
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

@app.route('/api/status')
def get_status():
    state_file = os.path.join(BASE_DIR, "state.txt")
    try:
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                # Returns "Music", "Weather", etc.
                return jsonify({'status': f.read().strip().capitalize()})
        return jsonify({'status': 'Idle'})
    except:
        return jsonify({'status': 'Error'})
