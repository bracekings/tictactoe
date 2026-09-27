import os
import subprocess
import requests
import json
import re
import shutil
from flask import Flask, request, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
import socket

app = Flask(__name__)

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
SERVERS_FILE = os.path.join(BASE_DIR, 'servers.json')
ALLOWED_EXTENSIONS = {'zip'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(SERVERS_FILE):
    with open(SERVERS_FILE, 'w') as f:
        json.dump({}, f)

def load_servers():
    with open(SERVERS_FILE, 'r') as f:
        return json.load(f)

def save_servers(servers):
    with open(SERVERS_FILE, 'w') as f:
        json.dump(servers, f)

def find_java_executable():
    """Find the best Java executable available on the system"""
    java_paths = []
    
    # Check environment PATH first
    java_in_path = shutil.which('java')
    if java_in_path:
        java_paths.append(java_in_path)
    
    # Check JAVA_HOME
    java_home = os.environ.get('JAVA_HOME') or os.environ.get('JDK_HOME')
    if java_home:
        java_exe = os.path.join(java_home, 'bin', 'java.exe')
        if os.path.exists(java_exe):
            java_paths.append(java_exe)
    
    # Check common installation directories
    common_paths = [
        r'C:\Program Files\Java',
        r'C:\Program Files (x86)\Java',
        r'C:\Program Files\Eclipse Foundation\jdk',
        r'C:\Program Files\OpenJDK',
        r'C:\Program Files\AdoptOpenJDK',
        r'C:\Program Files\Amazon Corretto',
        r'C:\Program Files\Zulu',
        r'C:\Users\{}\AppData\Local\Programs\OpenJDK'.format(os.environ.get('USERNAME', '*')),
        r'C:\Users\{}\scoop\apps\openjdk'.format(os.environ.get('USERNAME', '*')),
    ]
    
    for base_path in common_paths:
        if os.path.exists(base_path):
            for folder in os.listdir(base_path):
                java_exe = os.path.join(base_path, folder, 'bin', 'java.exe')
                if os.path.exists(java_exe):
                    java_paths.append(java_exe)
    
    # Test each Java to find the newest compatible version
    best_java = None
    best_version = 0
    
    for java_path in java_paths:
        try:
            result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
            output = result.stderr + result.stdout
            match = re.search(r'version ["\']?([0-9.]+)', output)
            if match:
                version_str = match.group(1)
                parts = version_str.split('.')
                if parts[0] == '1':
                    major_version = 8
                else:
                    major_version = int(parts[0])
                
                if major_version > best_version:
                    best_version = major_version
                    best_java = java_path
        except:
            continue
    
    # Return the best Java found, or default to 'java'
    if best_java:
        return best_java
    return 'java'

# Cache the best Java executable
BEST_JAVA = find_java_executable()

def get_java_version(java_path=None):
    """Get installed Java version"""
    if java_path is None:
        java_path = find_java_executable()
    
    try:
        result = subprocess.run([java_path, '-version'], capture_output=True, text=True)
        output = result.stderr + result.stdout
        
        # Parse version like "1.8.0_421" or "17.0.1"
        if 'java version' in output or 'openjdk version' in output:
            match = re.search(r'version ["\']?([0-9.]+)', output)
            if match:
                version_str = match.group(1)
                # Parse version
                parts = version_str.split('.')
                if parts[0] == '1':
                    # Java 8 = version 1.8.x
                    return {'major': 8, 'full': version_str, 'path': java_path}
                else:
                    # Java 11+ = version 11.x, 17.x, etc
                    return {'major': int(parts[0]), 'full': version_str, 'path': java_path}
        return None
    except Exception as e:
        print(f"Error detecting Java version: {e}")
        return None

def is_port_available(port=25565):
    """Check if a port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result != 0  # 0 means port is in use
    except:
        return True

def get_mc_java_requirement(version='1.20.1'):
    """Get Java requirement for Minecraft version"""
    # Minecraft version requirements
    requirements = {
        '1.20': 17,
        '1.20.1': 17,
        '1.19': 17,
        '1.18': 17,
        '1.17': 16,
        '1.16': 8,
        '1.15': 8,
        '1.14': 8,
        '1.13': 8,
        '1.12': 8,
    }
    
    # Check for matching version
    for mc_ver, java_ver in requirements.items():
        if version.startswith(mc_ver):
            return java_ver
    
    # Default to Java 17 for newer versions
    return 17

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        response.raise_for_status()
        data = response.json()
        return data.get('ip')
    except Exception:
        return None

def get_server_status(name):
    """Get detailed server status"""
    if name not in server_processes:
        return {'status': 'Stopped', 'message': 'Process not created yet'}
    
    process = server_processes[name]
    poll_result = process.poll()
    
    if poll_result is None:
        return {'status': 'Running', 'message': 'Server is running', 'pid': process.pid}
    else:
        return {'status': 'Stopped', 'message': f'Process exited with code {poll_result}'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Server processes - now store both process and output
server_processes = {}
server_output = {}

def download_vanilla_server(version='1.20.1', server_dir=None):
    try:
        # Get version manifest
        manifest_url = 'https://launchermeta.mojang.com/mc/game/version_manifest_v2.json'
        response = requests.get(manifest_url, timeout=10)
        response.raise_for_status()
        manifest = response.json()
        
        # Find the version
        version_url = None
        for v in manifest['versions']:
            if v['id'] == version:
                version_url = v['url']
                break
        
        if not version_url:
            raise ValueError(f"Version {version} not found in manifest")
        
        # Get version details
        response = requests.get(version_url, timeout=10)
        response.raise_for_status()
        version_data = response.json()
        server_url = version_data['downloads']['server']['url']
        
        # Download server jar
        jar_filename = f'server-{version}.jar'
        
        if server_dir:
            jar_path = os.path.join(server_dir, jar_filename)
        else:
            jar_path = jar_filename
        
        if not os.path.exists(jar_path):
            print(f"Downloading Minecraft {version} server jar...")
            response = requests.get(server_url, timeout=30)
            response.raise_for_status()
            with open(jar_path, 'wb') as f:
                f.write(response.content)
            print("Download complete.")
        
        return jar_filename
    except Exception as e:
        print(f"Error downloading vanilla server: {e}")
        raise

def install_forge_server(version='1.20.1', server_dir=None, forge_version='47.2.0'):
    try:
        if not server_dir:
            server_dir = '.'
        
        # Download Forge installer
        forge_url = f'https://maven.minecraftforge.net/net/minecraftforge/forge/{version}-{forge_version}/forge-{version}-{forge_version}-installer.jar'
        installer_path = os.path.join(server_dir, f'forge-{version}-{forge_version}-installer.jar')
        
        if not os.path.exists(installer_path):
            print(f"Downloading Forge {version}-{forge_version} installer...")
            response = requests.get(forge_url, timeout=30)
            response.raise_for_status()
            with open(installer_path, 'wb') as f:
                f.write(response.content)
            print("Download complete.")
        
        # Run installer
        print("Installing Forge server...")
        subprocess.run(['java', '-jar', installer_path, '--installServer'], cwd=server_dir, check=True)
        
        # The server jar is usually forge-version.jar
        server_jar = f'forge-{version}-{forge_version}.jar'
        return server_jar
    except Exception as e:
        print(f"Error installing Forge server: {e}")
        raise

def install_fabric_server(version='1.20.1', server_dir=None):
    try:
        if not server_dir:
            server_dir = '.'
        
        # Download Fabric installer
        fabric_url = 'https://maven.fabricmc.net/net/fabricmc/fabric-installer/0.11.2/fabric-installer-0.11.2.jar'
        installer_path = os.path.join(server_dir, 'fabric-installer.jar')
        
        if not os.path.exists(installer_path):
            print("Downloading Fabric installer...")
            response = requests.get(fabric_url, timeout=30)
            response.raise_for_status()
            with open(installer_path, 'wb') as f:
                f.write(response.content)
            print("Download complete.")
        
        # Run installer
        print("Installing Fabric server...")
        subprocess.run(['java', '-jar', installer_path, 'server', '-mcversion', version, '-downloadMinecraft'], cwd=server_dir, check=True)
        
        server_jar = 'fabric-server-launch.jar'
        return server_jar
    except Exception as e:
        print(f"Error installing Fabric server: {e}")
        raise

def create_server(name, version, loader, port='25565'):
    servers = load_servers()
    if name in servers:
        return f"Server {name} already exists"
    
    try:
        port = int(port)
        if not (1024 <= port <= 65535):
            return "Port must be between 1024 and 65535"
    except ValueError:
        return "Port must be a number"
    
    used_ports = {int(info.get('port', 25565)) for info in servers.values()}
    if port in used_ports:
        return f"Port {port} is already used by another server"
    
    server_dir = os.path.join(BASE_DIR, 'servers', name)
    os.makedirs(server_dir, exist_ok=True)
    os.makedirs(os.path.join(server_dir, 'mods'), exist_ok=True)
    
    try:
        if loader == 'vanilla':
            jar_path = download_vanilla_server(version, server_dir)
        elif loader == 'forge':
            jar_path = install_forge_server(version, server_dir)
        elif loader == 'fabric':
            jar_path = install_fabric_server(version, server_dir)
        else:
            return "Invalid loader"
        
        # Accept EULA
        eula_path = os.path.join(server_dir, 'eula.txt')
        with open(eula_path, 'w') as f:
            f.write('eula=true\n')
        
        servers[name] = {
            'version': version,
            'loader': loader,
            'jar_path': jar_path,
            'dir': server_dir,
            'port': port
        }
        save_servers(servers)
        return f"Server {name} created successfully"
    except Exception as e:
        return f"Error creating server: {str(e)}"

def start_server(name):
    servers = load_servers()
    if name not in servers:
        return f"Server {name} not found"
    
    if name in server_processes and server_processes[name].poll() is None:
        return f"Server {name} is already running"
    
    # Check Java version
    java_path = find_java_executable()
    java_info = get_java_version(java_path)
    if not java_info:
        return "ERROR: Java not found! Please install Java 17 or later. Current: Not detected"
    
    server_info = servers[name]
    required_java = get_mc_java_requirement(server_info['version'])
    
    if java_info['major'] < required_java:
        return f"ERROR: Minecraft {server_info['version']} requires Java {required_java}+, but you have Java {java_info['major']} ({java_info['full']}) at {java_info['path']}. Please upgrade Java or use an older Minecraft version."
    
    port = int(server_info.get('port', 25565))
    if not is_port_available(port):
        return f"ERROR: Port {port} is already in use! Check if another Minecraft server is running or close other applications using this port."
    
    server_dir = server_info['dir']
    jar_path = os.path.join(server_dir, server_info['jar_path'])
    
    # Check if jar exists
    if not os.path.exists(jar_path):
        return f"Server jar not found at {jar_path}. Try recreating the server."
    
    # Create server.properties file for network connectivity
    properties_path = os.path.join(server_dir, 'server.properties')
    if not os.path.exists(properties_path):
        with open(properties_path, 'w') as f:
            f.write(f'server-port={port}\n')
            f.write('online-mode=false\n')
            f.write('enable-query=false\n')
            f.write('max-players=20\n')
            f.write('difficulty=1\n')
            f.write('server-ip=\n')
    
    # Create logs directory
    logs_dir = os.path.join(server_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, 'latest.log')
    
    print(f"Starting server {name}...")
    print(f"Java executable: {java_path}")
    print(f"Java version: {java_info['full']}")
    print(f"Required Java: {required_java}+")
    print(f"Working directory: {server_dir}")
    print(f"Jar file: {jar_path}")
    print(f"Command: {java_path} -Xmx1024M -Xms1024M -jar {server_info['jar_path']} nogui")
    
    command = [java_path, '-Xmx1024M', '-Xms1024M', '-jar', server_info['jar_path'], 'nogui']
    
    try:
        with open(log_file, 'w') as log_f:
            server_processes[name] = subprocess.Popen(
                command, 
                cwd=server_dir, 
                stdout=log_f,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE
            )
        server_output[name] = log_file
        print(f"Server {name} started with PID {server_processes[name].pid}")
        return f"Server {name} starting (PID: {server_processes[name].pid})... Wait 30-60 seconds, then check 'View Logs' to confirm it's ready. Look for 'Done!' message."
    except Exception as e:
        print(f"Error starting server: {e}")
        return f"Error starting server: {str(e)}"

def stop_server(name):
    if name not in server_processes or server_processes[name].poll() is not None:
        return f"Server {name} is not running"
    
    server_processes[name].terminate()
    server_processes[name].wait()
    del server_processes[name]
    return f"Server {name} stopped"

@app.route('/create_server', methods=['POST'])
def create_server_route():
    name = request.form['name']
    version = request.form['version']
    loader = request.form['loader']
    port = request.form.get('port', '25565')
    result = create_server(name, version, loader, port)
    return render_template_string('''
    <div>{{ message }}</div>
    <a href="/">Back to Home</a>
    ''', message=result)

@app.route('/start/<name>', methods=['POST'])
def start_server_route(name):
    result = start_server(name)
    return render_template_string('''
    <div>{{ message }}</div>
    <a href="/">Back to Home</a>
    ''', message=result)

@app.route('/logs/<name>', methods=['GET'])
def view_logs(name):
    servers = load_servers()
    if name not in servers:
        return 'Server not found'
    
    if name not in server_output:
        return 'No logs available yet'
    
    log_file = server_output[name]
    try:
        with open(log_file, 'r') as f:
            logs = f.read()
        return render_template_string('''
        <!doctype html>
        <title>{{ server_name }} Logs</title>
        <h1>{{ server_name }} Server Logs</h1>
        <pre style="background-color: #f0f0f0; padding: 10px; overflow-x: auto; height: 600px; overflow-y: auto;">{{ logs }}</pre>
        <a href="/">Back to Home</a>
        <script>
            var pre = document.querySelector('pre');
            pre.scrollTop = pre.scrollHeight;
            setInterval(function() {
                fetch('/logs/{{ server_name }}').then(r => r.text()).then(t => {
                    var pre = document.querySelector('pre');
                    pre.textContent = t;
                    pre.scrollTop = pre.scrollHeight;
                });
            }, 2000);
        </script>
        ''', server_name=name, logs=logs)
    except Exception as e:
        return f'Error reading logs: {str(e)}'

@app.route('/status/<name>', methods=['GET'])
def server_status_route(name):
    status = get_server_status(name)
    return render_template_string('''
    <h2>{{ name }} Status</h2>
    <p><strong>Status:</strong> {{ status.status }}</p>
    <p><strong>Message:</strong> {{ status.message }}</p>
    {% if status.pid %}
    <p><strong>Process ID:</strong> {{ status.pid }}</p>
    {% endif %}
    <a href="/">Back</a>
    ''', name=name, status=status)

@app.route('/upload_mod', methods=['POST'])
def upload_mod():
    server_name = request.form['server']
    servers = load_servers()
    if server_name not in servers:
        return 'Server not found'
    
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename):
        return 'Invalid file'
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    try:
        server_dir = servers[server_name]['dir']
        mods_dir = os.path.join(server_dir, 'mods')
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(mods_dir)
        return 'Mod uploaded successfully!'
    except zipfile.BadZipFile:
        return 'Invalid zip file'
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/', methods=['GET'])
def index():
    servers = load_servers()
    server_list = []
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Get Java info
    java_info = get_java_version()
    public_ip = get_public_ip()
    
    for name, info in servers.items():
        port = int(info.get('port', 25565))
        status = 'Running' if name in server_processes and server_processes[name].poll() is None else 'Stopped'
        required_java = get_mc_java_requirement(info['version'])
        java_compatible = java_info and java_info['major'] >= required_java
        
        server_list.append({
            'name': name,
            'version': info['version'],
            'loader': info['loader'],
            'status': status,
            'localhost': f'localhost:{port}',
            'network_ip': f'{local_ip}:{port}',
            'public_ip': f'{public_ip}:{port}' if public_ip else None,
            'port': port,
            'required_java': required_java,
            'current_java': java_info['major'] if java_info else 'Unknown',
            'java_compatible': java_compatible
        })
    
    return render_template_string('''
    <!doctype html>
    <title>Minecraft Server Manager</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .server { border: 1px solid #ccc; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .running { background-color: #d4edda; }
        .stopped { background-color: #f8d7da; }
        .java-warning { background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ff9800; }
        .java-ok { background-color: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #4caf50; }
        .connection-info { background-color: #e7f3ff; padding: 10px; margin: 10px 0; border-radius: 3px; font-family: monospace; }
        form { display: inline-block; margin-right: 10px; }
        input[type="submit"] { padding: 5px 10px; }
        .server-actions { margin-top: 10px; }
        a { color: #0066cc; }
        .java-info { font-weight: bold; }
        .header-info { background-color: #e3f2fd; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
    </style>
    <h1>Minecraft Server Manager</h1>
    
    <div class="header-info">
        <strong>System Java Version:</strong> 
        {% if current_java_info %}
            Java {{ current_java_info.major }} ({{ current_java_info.full }})
            <br><small>Path: {{ current_java_info.path }}</small>
        {% else %}
            Not detected - Please install Java 17 or later
        {% endif %}
        
        {% if current_java_info.major and current_java_info.major < 17 %}
        <br><br>
        <strong>⚠️ Java 8 Detected</strong> - To run the latest Minecraft versions (1.17+), please install Java 17 or later:
        <ul style="margin: 10px 0;">
            <li><strong>Option 1 (Recommended):</strong> Download <a href="https://www.oracle.com/java/technologies/downloads/#java17" target="_blank">Oracle Java 17 LTS</a> or newer</li>
            <li><strong>Option 2 (Free):</strong> Download <a href="https://adoptium.net/installation/" target="_blank">Eclipse Temurin (OpenJDK)</a></li>
            <li><strong>Option 3 (Simple):</strong> Use <a href="https://www.microsoft.com/openjdk" target="_blank">Microsoft OpenJDK</a></li>
        </ul>
        You can install Java 17+ without removing Java 8 - they can coexist. After installation, restart this app.
        {% endif %}
    </div>
    
    <h2>Create New Server</h2>
    <form action="/create_server" method="post">
      Name: <input type="text" name="name" required><br><br>
      Version: <input type="text" name="version" value="1.20.1" required>
      <span style="font-size: 0.9em; color: #666;">
        (Requires Java: {{ min_java_version }}<br>
        Use older versions for Java 8: 1.12, 1.15, 1.16)
      </span><br><br>
      Port: <input type="number" name="port" value="25565" min="1024" max="65535" required><br>
      <span style="font-size: 0.9em; color: #666;">Use a unique port for each running server.</span><br><br>
      Loader: <select name="loader">
        <option value="vanilla">Vanilla</option>
        <option value="forge">Forge</option>
        <option value="fabric">Fabric</option>
      </select><br><br>
      <input type="submit" value="Create Server">
    </form>
    
    <h2>Servers</h2>
    {% if servers %}
        {% for server in servers %}
        <div class="server {% if server.status == 'Running' %}running{% else %}stopped{% endif %}">
          <h3>{{ server.name }} ({{ server.version }}, {{ server.loader }})</h3>
          <strong>Status: {{ server.status }}</strong><br>
          
          {% if server.java_compatible %}
            <div class="java-ok">
              ✓ Java {{ server.required_java }}+ required - Your Java {{ server.current_java }} ✓ Compatible
            </div>
          {% else %}
            <div class="java-warning">
              ✗ Java {{ server.required_java }}+ required - Your Java {{ server.current_java }} ✗ NOT Compatible<br>
              <small>To run this server, upgrade Java or create a server with version 1.16 or earlier</small>
            </div>
          {% endif %}
          
          {% if server.status == 'Running' %}
          <div class="connection-info">
            <strong>Connection Info:</strong><br>
            Local: {{ server.localhost }}<br>
            Network: {{ server.network_ip }}<br>
            {% if server.public_ip %}
            Public: {{ server.public_ip }}<br>
            {% else %}
            Public: (public IP not detected or blocked by network)<br>
            {% endif %}
          </div>
          {% endif %}
          <div class="server-actions">
            <form action="/start/{{ server.name }}" method="post" style="display:inline;">
              <input type="submit" value="Start" {% if not server.java_compatible %}disabled{% endif %}>
            </form>
            <form action="/stop/{{ server.name }}" method="post" style="display:inline;">
              <input type="submit" value="Stop">
            </form>
            <a href="/status/{{ server.name }}" target="_blank">Check Status</a>
            |
            <a href="/logs/{{ server.name }}" target="_blank">View Logs</a>
          </div>
        </div>
        {% endfor %}
    {% else %}
        <p>No servers created yet.</p>
    {% endif %}
    
    <h2>Upload Mod</h2>
    {% if servers %}
    <form action="/upload_mod" method="post" enctype="multipart/form-data">
      Server: <select name="server">
        {% for server in servers %}
        <option value="{{ server.name }}">{{ server.name }}</option>
        {% endfor %}
      </select><br>
      <input type="file" name="file" accept=".zip" required>
      <input type="submit" value="Upload">
    </form>
    {% else %}
    <p>Create a server first to upload mods.</p>
    {% endif %}
    ''', servers=server_list, current_java_info=java_info, min_java_version='17')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
