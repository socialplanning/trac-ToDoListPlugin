from setuptools import setup

try:
    long_description = open("README.txt").read()
except:
    long_description = ''
try:
    long_description += open("CHANGES.txt").read()
except:
    pass

setup(name='trac-TaskListPlugin',
      version='0.1',
      description="",
      long_description=long_description,
      packages=['task_list'],
      author='Ethan Jucovy',
      author_email='ejucovy@gmail.com',
      url="http://trac-hacks.org/wiki/TaskListsPlugin",
      install_requires=["tracsqlhelper"],
      license='BSD',
      entry_points = {'trac.plugins': ['task_list = task_list']})
