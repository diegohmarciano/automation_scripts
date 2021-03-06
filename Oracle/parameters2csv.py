#%% Load Modules
import csv
import argparse
import cx_Oracle

#Parsing arguments
parser = argparse.ArgumentParser(description="Dump oracle parameter values to CSV file for analysis", epilog="Usage example: parameters2csv.py -u SYSTEM -p mySystemPwd -c MYTNSENTRY.WORLD -pf params.txt -of results.csv")
parser.add_argument("-u", "--user", required=True, type=str, help="Oracle user for DB connection")
parser.add_argument("-p", "--password", required=True,  type=str, help="Oracle password for DB connection")
parser.add_argument("-c", "--oraconn", required=True,  type=str, help="Oracle TNS name or service_name for DB connection")
parser.add_argument("-pf", "--paramfile", required=True,  type=str, help="List of parameters to check")
parser.add_argument("-of", "--outputfile", required=True,  type=str, help="Output CSV with with parameters and values")
args = parser.parse_args()

#%% Variables initialization
csv_file, parameters_listfile=(args.outputfile, args.paramfile)
csv_columns = ['Parameter','Value']
ora_user, ora_pwd, ora_conn=(args.user, args.password, args.oraconn)
parameters_list=[]
parameters_values=[]

#Open parameters text file
with open(parameters_listfile) as fp:
    line = fp.readline()
    while line:
        parameters_list.append(line.strip())
        line = fp.readline()

#Oracle Client Version Check
cx_Oracle.clientversion()
conn = cx_Oracle.connect()
#Database version
print("Database version:", conn.version)

#Prepare cursor for query and execute query
cur = conn.cursor()
for parameter in parameters_list:
    cur.execute("select name, value from v$parameter where name='{0}'".format(parameter))
    res = cur.fetchall()
    #Load results on parameters list
    for row in res:
        parameters_values.append({"Parameter": row[0], "Value": row[1]})

#Dump parameters list to CSV 
try:
    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for row in parameters_values:
            writer.writerow(row)
except IOError:
    print("I/O error")

exit(0)
