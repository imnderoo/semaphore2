"""Fork helper. Replaced by use of make"""
"""This is currently not used"""
import subprocess

def run_command(command):
      child_pid = os.fork()
      if child_pid == 0:
          log(command)
          print "%s" % command
	  time.sleep(2)
          exit(0)
      else:
          log("Parent Process: PID# %s" % os.getpid())
      return child_pid

def my_wait(children):
  for child in children:
    pid = os.waitpid(child, 0)
    log("Child process finished: %d" % pid[0])

def run_parallel_bwa(files, read_group, reference):
        children = []
	for file in files:
		log("Running parallel BWA..")
                pid = run_command(bwa_command(file, read_group, reference))
                if pid != 0:
	           log("Spawned child %d" % pid)
                   children.append(pid)
		#print "Running aln %s" % file
		#print "Running samse %s" % file
 	log("Children %s" % ", ".join(map(lambda x: str(x), children)))
 	my_wait(children)

