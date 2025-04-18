import os
from datetime import timedelta
import time 
import redis
from flask import Flask, render_template_string, request, session, redirect, url_for, make_response
from flask_session import Session
import subprocess
import docker 
from docker.errors import NotFound

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', default='/n<)SM<#XH*z%<ikKS%T+=7bl_1_s')

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.from_url('redis://127.0.0.1:6379')

server_session = Session(app)

class PortTracker: 
    def __init__(self): 
        self.count = 8000 # CHANGE START PORT PER CHALLENGE 
    def get_new_port(self): 
        self.count += 1
        return self.count - 1

class ContainerManager: 
    def __init__(self): 
        print("#need this?")
    def create_container(user_port):
       # path_to_chall_docker_compose = os.environ["PATH_TO_CHALL_DOCKER_COMPOSE"]  
       # path_to_user_env_files_dir = os.environ["PATH_TO_USER_ENV_FILES_DIR"] 
       path_to_chall_docker_compose = "/home/asritha/cybersex/devopsclub/sessions-flask/test-chall/docker-compose.yaml"  
       path_to_user_env_files_dir = "/home/asritha/cybersex/devopsclub/sessions-flask/users-envs" 

       user_env_file_name = f'{path_to_user_env_files_dir}/{user_port}.env'
       
       with open(user_env_file_name, 'w') as user_env_file:
            # CHANGE ENV VARS PER CHALLENGE
            user_env_file.write(f'''  
            PORT={user_port} 
            ''') 
       subprocess.run(["docker", "compose", "-p", f"proj-{user_port}", "-f", path_to_chall_docker_compose, "--env-file", user_env_file_name, "up", "-d"], check=True)

    # if temporarily stopped, is_chall_ready will restart the containers  
    def is_chall_ready(user_port, timeout=600, interval=3):
        client = docker.from_env()
        container_names = [
            # CHANGE CONTAINER NAMES PER CHALLENGE
            f'web-{user_port}',
        ]

        start_ts = time.monotonic()
        while time.monotonic() - start_ts < timeout:
            all_up = True
            for name in container_names:
                try:
                    c = client.containers.get(name)
                    c.reload()
                except NotFound:
                    all_up = False
                    break
                if c.status.lower() != "running":
                    all_up = False
                    break

            if all_up:
                return True

            time.sleep(interval)
        return False


port_tracker = PortTracker()
container_manager = ContainerManager

@app.route('/')
def index():
    if 'port' not in session:
        new_port = port_tracker.get_new_port()        
        session.update(port=new_port)
        container_manager.create_container(new_port)
    
    if not container_manager.is_chall_ready(session['port']): 
        return f"Infrastructure problem: Please create a support ticket", 503 

    response = make_response("Containers Ready", 200)
    response.headers['x_user_port'] = session['port'] 
    return response 

if __name__ == '__main__': 
    app.run(host="0.0.0.0", port=2334, debug=True)
