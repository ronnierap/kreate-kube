import jinja2
import shutil
import os

target_dir="./target"

class App:
  def __init__(self, name, env, kind='Deployment'):
    self.name = name
    self.env=env
    self.kind = kind
    self.replicas=env.replicas
    self.container=[Container('app')]
    self.container[0].image_name = env.image_repo + name + ".app"
    self.labels=dict()

  def kreate_file(self, name, template):
    tmpl = jinja2.Template( template, undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True )
    tmpl.stream(app=self, env=self.env).dump(target_dir+"/"+name)
    #print(tmpl.render(app=self, env=self.env))

  def clear():
    shutil.rmtree( target_dir )
    os.mkdir( target_dir )



class Container:
  def __init__(self, name, version):
    self.name = name
    self.cpu_limit='500m'
    self.cpu_request='500m'
    self.mem_limit='512Mi'
    self.mem_request='512Mi'
    self.port=8080


class Environment:
  def __init__(self, name):
    self.name = name
    self.replicas=1
    self.image_repo = "somewhere.todo/"
    self.vars=dict()

  def add_var(self, name, value):
    self.vars[name]=value
