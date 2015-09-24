import os
#import sys
import psycopg2
import time
import datetime
import re

db_name = "serengeti"
db_username = "serengeti"
#log_path = "/opt/serengeti/logs/serengeti.log"
#cluster_name = '\'tcl5\''
#create_start = "entering createCluster: " + cluster_name;
create_start = "entering createCluster: "
rest_end = "launched with the following parameters: [{clusterFailureStatus=PROVISION_ERROR, clusterName="
print ("db_name: " + db_name + ", db_username: " + db_username)

def get_time(line):
  m = re.match(r'\[(\d+-\d+-\d+T\d+:\d+:\d+\.\d\d\d).*', line, flags=0)
  time = ''
  if m:
    time = m.group(1)
    #print(time)
  return time
def get_name(line):
  m = re.match(r'.*entering createCluster: (\w+)\ *', line, flags=0)
  if m:
    cluster_name = m.group(1)
    print(cluster_name)
  return cluster_name

def connect_db(db, user):
  retry_connect = 5
  while True:
    try:
      db_conn_str = "dbname=%s user=%s host=localhost" % (db, user)
      db_conn = psycopg2.connect(db_conn_str)
      return db_conn
    except psycopg2.OperationalError:
      retry_connect -= 1
      if retry_connect == 0:
        raise
      print ("Will retry %d more times" % retry_connect)
      time.sleep(5)
name_list = []
start_time = []
end_time = []

def read_log(log_path):
  f = open(log_path, 'r')
  for line in f.readlines():
    if create_start in line:
      print('get')
      start_time.append(get_time(line))
      name_list.append(get_name(line))
    if rest_end in line:
      print('tcl')
      end_time.append(get_time(line))
  return name_list, start_time, end_time
try:
  names = os.listdir('/opt/serengeti/logs/test')
  for name in names:
    m = re.match('serengeti.log|\..*', name, flags=0)
    if m :
      print(name)
      read_log('/opt/serengeti/logs/test/' + name)
  db_conn = connect_db(db_name, db_username)
  cursor = db_conn.cursor()

  print(name_list)
  dic = {}
  job_id = []
  index = 0
  for cluster_name in name_list:
    cursor.execute("select job_execution_id,  step_name, start_time, end_time from batch_step_execution  where job_execution_id = (select job_execution_id from batch_job_execution where job_instance_id = (select job_instance_id from batch_job_params where string_val = \'" + cluster_name + "\')) order by start_time")

    values = cursor.fetchall()
    print (values)
    lens = len(values)
    list = []
    for x in range(lens):
      i = values[x][0]
      if i in dic:
        list.append([values[x][1],values[x][2],values[x][3]])
        dic[i] = list
      else:
        list = []
        list.append(['rest', start_time[index], end_time[index]])
        list.append([values[x][1],values[x][2],values[x][3]])
        dic[i] = list
        job_id.append(i)
    index+=1
  print (dic)
  print (job_id)


except:
  print ("failed to connect database")
  raise
db_conn.close()

# dic = {101L: [['rest', '[2015-08-24T02:42:35.125+0000]', '[2015-08-24T02:42:36.325+0000]'], ['createClusterPlanStep', datetime.datetime(2015, 8, 26, 8, 59, 49, 269000), datetime.datetime(2015, 8, 26, 8, 59, 49, 777000)], ['updateClusterDataStep1', datetime.datetime(2015, 8, 26, 8, 59, 49, 827000), datetime.datetime(2015, 8, 26, 8, 59, 50, 161000)], ['createVMStep', datetime.datetime(2015, 8, 26, 8, 59, 50, 203000), datetime.datetime(2015, 8, 26, 9, 1, 39, 314000)], ['updateClusterDataStep2', datetime.datetime(2015, 8, 26, 9, 1, 39, 364000), datetime.datetime(2015, 8, 26, 9, 1, 42, 364000)], ['nodeStatusVerifyStep', datetime.datetime(2015, 8, 26, 9, 1, 42, 415000), datetime.datetime(2015, 8, 26, 9, 1, 42, 448000)]], 102L: [['call', '[2015-08-24T02:42:37.125+0000]', '[2015-08-24T02:42:38.725+0000]'], ['createClusterPlanStep', datetime.datetime(2015, 8, 26, 11, 23, 49, 412000), datetime.datetime(2015, 8, 26, 11, 23, 50, 872000)], ['updateClusterDataStep1', datetime.datetime(2015, 8, 26, 11, 23, 51, 57000), datetime.datetime(2015, 8, 26, 11, 23, 53, 91000)], ['createVMStep', datetime.datetime(2015, 8, 26, 11, 23, 53, 342000), datetime.datetime(2015, 8, 26, 11, 29, 55, 646000)], ['updateClusterDataStep2', datetime.datetime(2015, 8, 26, 11, 29, 55, 848000), datetime.datetime(2015, 8, 26, 11, 30, 11, 665000)], ['nodeStatusVerifyStep', datetime.datetime(2015, 8, 26, 11, 30, 11, 850000), datetime.datetime(2015, 8, 26, 11, 30, 11, 883000)]]}
# job_id = [101L,102L]

def formattime(stime):
  m = re.match(r'.*(\d{4})-(\d{2})-(\d{2})\w(\d{2})\:(\d{2}):(\d{2})\.(\d{3}).*', stime, flags=0)
  t = datetime.datetime.now()  
  if m:
    t = datetime.datetime(int(m.group(1)),int(m.group(2)),int(m.group(3)),int(m.group(4)),int(m.group(5)),int(m.group(6)),int(m.group(7))*1000)
    print(t)
  return t

out_path = './output.html'
api_time = []
p1_time = []
p2_time = []
p3_time = []
p4_time = []
p5_time = []

for key in job_id:
  api_time.append('\''+str((formattime(dic[key][0][2])-formattime(dic[key][0][1])).seconds +(float((formattime(dic[key][0][2])-formattime(dic[key][0][1])).microseconds)/1000000))+'\',')
  p1_time.append('\''+str((dic[key][1][2]-dic[key][1][1]).seconds +(float((dic[key][1][2]-dic[key][1][1]).microseconds)/1000000))+'\',')
  p2_time.append('\''+str((dic[key][2][2]-dic[key][2][1]).seconds +(float((dic[key][2][2]-dic[key][2][1]).microseconds)/1000000))+'\',')
  p3_time.append('\''+str((dic[key][3][2]-dic[key][3][1]).seconds +(float((dic[key][3][2]-dic[key][3][1]).microseconds)/1000000))+'\',')
  p4_time.append('\''+str((dic[key][4][2]-dic[key][4][1]).seconds +(float((dic[key][4][2]-dic[key][4][1]).microseconds)/1000000))+'\',')
  p5_time.append('\''+str((dic[key][5][2]-dic[key][5][1]).seconds +(float((dic[key][5][2]-dic[key][5][1]).microseconds)/1000000))+'\',')

nodes = len(job_id)
print nodes
print (api_time)
print (p1_time)
print (p2_time)
print (p3_time)
print (p4_time)
print (p5_time)


pre_height = './resources/preHeight.txt'
pre_name = './resources/preName.txt'
api_step = './resources/apiStep.txt'
create_cluster_plan_step = './resources/createClusterPlanStep.txt'
update_cluster_data_step1 = './resources/updateClusterDataStep1.txt'
create_vm_step = './resources/createVMStep.txt'
update_cluster_data_step2 = './resources/updateClusterDataStep2.txt'
node_status_verify_step = './resources/nodeStatusVerifyStep.txt'
pre_done = './resources/preDone.txt'

w = open(out_path,'w')
#write pre_height
f = open(pre_height,'r')
w.write(f.read())
f.close()
#calculate div height
if nodes<=5:
  w.write("400px\"")
elif nodes>5 and nodes <10:
  w.write('600px\"')
elif nodes>=10 and nodes <100:
  w.write('1100px\"')
else:
  w.write(nodes*20+'px\"')

f = open(pre_name,'r')
w.write(f.read())
f.close()

#add '' to value,
job_tmp = ['\''+str(line)+'\',' for line in job_id]
w.writelines(job_tmp)

f = open(api_step,'r')
w.write(f.read())
w.writelines(api_time)
f.close()

f = open(create_cluster_plan_step,'r')
w.write(f.read())
w.writelines(p1_time)
f.close()

f = open(update_cluster_data_step1,'r')
w.write(f.read())
w.writelines(p2_time)
f.close()

f = open(create_vm_step,'r')
w.write(f.read())
w.writelines(p3_time)
f.close()

f = open(update_cluster_data_step2,'r')
w.write(f.read())
w.writelines(p4_time)
f.close()

f = open(node_status_verify_step,'r')
w.write(f.read())
w.writelines(p5_time)
f.close()

f = open(pre_done,'r')
w.write(f.read())
f.close()
w.close()
